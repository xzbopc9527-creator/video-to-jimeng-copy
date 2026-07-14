#!/usr/bin/env python3
"""Monitor public Douyin account pages without downloading or analyzing videos."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VIDEO_RE = re.compile(r"/video/([0-9]+)")
PRICE_RE = re.compile(r"(?:\d+(?:\.\d+)?)\s*(?:元|块|折|起|/杯|/份)")
FOOD_TERMS = (
    "肯德基", "必胜客", "塔斯汀", "华莱士", "瑞幸", "古茗", "沪上阿姨", "茶百道",
    "锅圈", "八喜", "薛记", "汉堡", "炸鸡", "烤翅", "翅根", "蛋挞", "套餐", "小食",
    "饮品", "奶茶", "咖啡", "冰淇淋", "蛋糕", "烤肉", "烤鱼", "花卷", "餐厅", "美食",
    "火锅", "海鲜", "猪肉脯", "果茶", "酸奶", "冰奶", "披萨", "塔可", "食品",
)
COMMERCE_TERMS = (
    "只要", "才", "优惠", "团购", "套餐", "囤", "划算", "福利", "买一送一", "立减",
    "折扣", "预售", "上新", "新品", "回归", "秒杀", "券", "到手", "限时", "特价",
    "就能买到", "就能吃到", "开业", "快冲", "冲呀", "不可用日期", "每人最多买",
)
EXCLUDE_TERMS = (
    "招生", "学校", "职高", "中专", "升学", "就业", "期末考", "物理答案", "数学答案",
    "课程", "老师", "高考答案", "招聘",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temp, path)


def find_browser(explicit: str | None) -> str:
    candidates = [
        explicit,
        os.environ.get("DOUYIN_MONITOR_BROWSER"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate))
    raise RuntimeError("Edge/Chrome was not found. Pass --browser-executable.")


def normalize_nickname(title: str, fallback: str) -> str:
    value = re.sub(r"的抖音\s*-\s*抖音.*$", "", title).strip()
    return value or fallback


def extract_posts(raw_links: list[dict[str, str]], limit: int) -> list[dict[str, Any]]:
    posts: dict[str, dict[str, Any]] = {}
    for item in raw_links:
        match = VIDEO_RE.search(str(item.get("href", "")))
        if not match:
            continue
        aweme_id = match.group(1)
        lines = [line.strip() for line in str(item.get("text", "")).splitlines() if line.strip()]
        description = next((line for line in reversed(lines) if len(line) > 8 and line != "置顶"), "")
        posts[aweme_id] = {
            "aweme_id": aweme_id,
            "url": f"https://www.douyin.com/video/{aweme_id}",
            "description": description,
            "pinned_hint": "置顶" in lines,
        }
    return sorted(posts.values(), key=lambda post: int(post["aweme_id"]), reverse=True)[:limit]


def fetch_account(
    playwright: Any,
    account: dict[str, Any],
    browser_executable: str,
    wait_ms: int,
    max_posts: int,
    headless: bool,
    retries: int,
) -> dict[str, Any]:
    sec_uid = str(account["sec_uid"])
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        browser = playwright.chromium.launch(
            headless=headless,
            executable_path=browser_executable,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/136.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        try:
            page.goto(
                f"https://www.douyin.com/user/{sec_uid}",
                wait_until="domcontentloaded",
                timeout=60_000,
            )
            page.wait_for_timeout(wait_ms)
            raw_links = page.locator("a").evaluate_all(
                "els => els.map(e => ({text:(e.innerText||'').trim(),href:e.href}))"
                ".filter(x => x.href.includes('/video/'))"
            )
            posts = extract_posts(raw_links, max_posts)
            if not posts:
                raise RuntimeError("No public video links were visible; page may be rate-limited or require login.")
            return {
                "nickname": normalize_nickname(page.title(), str(account.get("nickname", sec_uid))),
                "profile_url": f"https://www.douyin.com/user/{sec_uid}",
                "posts": posts,
            }
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        finally:
            context.close()
            browser.close()
        if attempt < retries:
            time.sleep(2 + attempt)
    raise RuntimeError(str(last_error) if last_error else "Unknown account fetch failure")


def is_food_commerce(description: str) -> bool:
    text = description.strip()
    if not text or any(term in text for term in EXCLUDE_TERMS):
        return False
    food_hit = any(term in text for term in FOOD_TERMS)
    commerce_hit = PRICE_RE.search(text) is not None or any(term in text for term in COMMERCE_TERMS)
    return food_hit and commerce_hit


def notification_text(event: dict[str, Any]) -> str:
    return (
        "发现新的公开餐饮带货视频\n"
        f"账号：{event['nickname']}\n"
        f"标题：{event['description']}\n"
        f"链接：{event['url']}\n"
        f"检测时间：{event['detected_at']}\n\n"
        f"如需分析，请回复：分析 {event['url']}\n"
        "如不处理，请回复：跳过"
    )


def resolve_lark_cli(explicit: str | None) -> str:
    candidates = [
        explicit,
        os.environ.get("FEISHU_CODEX_LARK_CLI"),
        os.path.expandvars(r"%APPDATA%\npm\node_modules\@larksuite\cli\bin\lark-cli.exe"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate))
    raise RuntimeError("lark-cli executable was not found. Pass --lark-cli.")


def send_feishu(event: dict[str, Any], chat_id: str, lark_cli: str) -> None:
    completed = subprocess.run(
        [
            lark_cli,
            "im",
            "+messages-send",
            "--as",
            "bot",
            "--chat-id",
            chat_id,
            "--text",
            notification_text(event),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"Feishu notification failed ({completed.returncode}): {detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--initialize", action="store_true", help="Create a no-notification baseline")
    parser.add_argument("--headful", action="store_true")
    parser.add_argument("--browser-executable")
    parser.add_argument("--wait-ms", type=int)
    parser.add_argument("--max-posts", type=int)
    parser.add_argument("--notify-feishu", action="store_true")
    parser.add_argument("--chat-id")
    parser.add_argument("--lark-cli")
    args = parser.parse_args()

    config = load_json(args.config)
    accounts = config.get("accounts")
    if not isinstance(accounts, list) or not accounts:
        raise ValueError("config.accounts must be a non-empty list")
    for account in accounts:
        if not isinstance(account, dict) or not account.get("sec_uid"):
            raise ValueError("Every account requires sec_uid")

    state_exists = args.state.is_file()
    state = load_json(args.state) if state_exists else {"version": 1, "accounts": {}}
    state_accounts = state.setdefault("accounts", {})
    initialize = args.initialize or not state_exists
    wait_ms = args.wait_ms or int(config.get("wait_ms", 7_000))
    max_posts = args.max_posts or int(config.get("max_posts", 30))
    retries = int(config.get("retries", 1))
    browser_executable = find_browser(args.browser_executable)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is required: python -m pip install playwright") from exc

    results: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    with sync_playwright() as playwright:
        for account in accounts:
            sec_uid = str(account["sec_uid"])
            try:
                fetched = fetch_account(
                    playwright,
                    account,
                    browser_executable,
                    wait_ms,
                    max_posts,
                    not args.headful,
                    retries,
                )
                previous = state_accounts.get(sec_uid, {})
                seen = {str(value) for value in previous.get("seen_aweme_ids", [])}
                current_ids = [str(post["aweme_id"]) for post in fetched["posts"]]
                previous_latest_id = str(previous.get("latest_visible_aweme_id", "")).strip()
                previous_id_numbers = [int(value) for value in seen if value.isdigit()]
                if previous_latest_id.isdigit():
                    previous_id_numbers.append(int(previous_latest_id))
                previous_high_water = max(previous_id_numbers, default=None)
                if initialize:
                    new_posts = []
                elif previous_high_water is not None:
                    # Douyin profile pages can rotate older, previously hidden posts into view.
                    # Only IDs newer than the last numeric high-water mark are publications;
                    # unseen lower IDs are historical page churn and must not trigger alerts.
                    new_posts = [
                        post
                        for post in fetched["posts"]
                        if int(post["aweme_id"]) > previous_high_water
                    ]
                else:
                    new_posts = [post for post in fetched["posts"] if post["aweme_id"] not in seen]
                matching = [post for post in new_posts if is_food_commerce(post["description"])]
                checked_at = utc_now()
                for post in matching:
                    events.append(
                        {
                            "event_id": f"{sec_uid[-8:]}-{post['aweme_id']}",
                            "nickname": fetched["nickname"],
                            "sec_uid": sec_uid,
                            "aweme_id": post["aweme_id"],
                            "url": post["url"],
                            "description": post["description"],
                            "detected_at": checked_at,
                            "requires_approval": True,
                        }
                    )
                merged_seen = list(dict.fromkeys(current_ids + list(seen)))[:200]
                current_high_water = max((int(value) for value in current_ids), default=0)
                latest_observed_number = max(previous_high_water or 0, current_high_water)
                state_accounts[sec_uid] = {
                    "nickname": fetched["nickname"],
                    "share_url": account.get("share_url", ""),
                    "profile_url": fetched["profile_url"],
                    "seen_aweme_ids": merged_seen,
                    "latest_visible_aweme_id": str(latest_observed_number) if latest_observed_number else "",
                    "latest_matching_aweme_id": next(
                        (post["aweme_id"] for post in fetched["posts"] if is_food_commerce(post["description"])),
                        previous.get("latest_matching_aweme_id", ""),
                    ),
                    "last_checked_at": checked_at,
                }
                results.append(
                    {
                        "nickname": fetched["nickname"],
                        "sec_uid": sec_uid,
                        "visible_posts": len(fetched["posts"]),
                        "new_posts": len(new_posts),
                        "new_food_commerce_posts": len(matching),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    {"nickname": str(account.get("nickname", sec_uid)), "sec_uid": sec_uid, "error": str(exc)}
                )

    state["initialized_at"] = state.get("initialized_at") or utc_now()
    state["last_run_at"] = utc_now()
    state["mode"] = "food_commerce"
    atomic_write_json(args.state, state)

    notifications: list[dict[str, Any]] = []
    if args.notify_feishu and events:
        chat_id = args.chat_id or str(config.get("notify", {}).get("chat_id", ""))
        if not chat_id:
            raise ValueError("--chat-id or config.notify.chat_id is required with --notify-feishu")
        lark_cli = resolve_lark_cli(args.lark_cli)
        for event in events:
            send_feishu(event, chat_id, lark_cli)
            notifications.append({"event_id": event["event_id"], "sent": True})

    report = {
        "ok": not failures,
        "initialized": initialize,
        "checked_at": utc_now(),
        "accounts": results,
        "events": events,
        "notifications": notifications,
        "failures": failures,
        "state_path": str(args.state.resolve()),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
