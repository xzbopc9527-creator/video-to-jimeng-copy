#!/usr/bin/env python3
"""Collect public Xiaohongshu note images for per-segment Jimeng references."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

from PIL import Image, ImageDraw
from playwright.sync_api import Page, sync_playwright


DEFAULT_PROFILE = Path.home() / ".codex" / "xhs-browser-profile"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def safe_name(value: str, limit: int = 60) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" ._")
    return (cleaned or "未命名")[:limit]


def relevant_search_cards(page: Page, query: str, limit: int) -> list[dict[str, Any]]:
    terms = [term for term in re.split(r"\s+", query.strip()) if len(term) >= 2]
    brand = "塔斯汀" if "塔斯汀" in terms else None
    ranked: list[tuple[int, dict[str, Any]]] = []
    seen: set[str] = set()
    for anchor in page.locator('a[href*="/explore/"]').all():
        section = anchor.locator("xpath=ancestor::section[1]")
        if not section.count():
            continue
        href = (anchor.get_attribute("href") or "").split("#", 1)[0]
        if not href or href in seen:
            continue
        seen.add(href)
        raw_text = section.inner_text().strip()
        text = re.sub(r"\s+", " ", raw_text)
        if brand and brand not in text:
            continue
        score = sum(term in text for term in terms)
        if not score:
            continue
        cover: dict[str, Any] | None = None
        for image in section.locator("img").all():
            info = image.evaluate(
                "i => ({src: i.currentSrc || i.src, width: i.naturalWidth || 0, height: i.naturalHeight || 0})"
            )
            if info["src"] and "xhscdn" in info["src"] and info["width"] >= 400 and info["height"] >= 350:
                cover = info
                break
        if not cover:
            continue
        title = next((line.strip() for line in raw_text.splitlines() if line.strip()), query)
        ranked.append((score, {
            "href": href,
            "title": title,
            "text": text,
            "src": cover["src"].replace("http://", "https://"),
        }))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [card for _, card in ranked[:limit]]


def wait_for_search(page: Page, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        body = page.locator("body").inner_text()
        if page.locator('a[href*="/explore/"]').count() and "登录后查看搜索结果" not in body:
            return
        page.wait_for_timeout(2000)
    raise RuntimeError("Xiaohongshu login/search results were not available before timeout")


def extension(content_type: str, url: str) -> str:
    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"


def create_contact_sheet(files: list[Path], destination: Path) -> None:
    thumbs: list[Image.Image] = []
    for file in files:
        try:
            image = Image.open(file).convert("RGB")
            image.thumbnail((360, 480))
            canvas = Image.new("RGB", (380, 540), "white")
            canvas.paste(image, ((380 - image.width) // 2, 10))
            ImageDraw.Draw(canvas).text((10, 500), file.parent.name + "/" + file.name, fill="black")
            thumbs.append(canvas)
        except Exception:
            continue
    if not thumbs:
        return
    columns = 3
    rows = (len(thumbs) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 380, rows * 540), (235, 235, 235))
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % columns) * 380, (index // columns) * 540))
    sheet.save(destination, quality=90)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", required=True, help="JSON mapping segment names to search-query arrays")
    parser.add_argument("--output", required=True, help="Directory in which images are saved directly")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--headful", action="store_true", help="Open visible browser for interactive login")
    parser.add_argument("--notes-per-query", type=int, default=3)
    parser.add_argument("--images-per-note", type=int, default=2)
    parser.add_argument("--max-images-per-segment", type=int, default=4)
    parser.add_argument("--login-timeout", type=int, default=360)
    args = parser.parse_args()

    requirements = json.loads(Path(args.requirements).read_text(encoding="utf-8"))
    if not isinstance(requirements, dict):
        raise ValueError("requirements must be a JSON object")
    output = Path(args.output).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    profile = Path(args.profile).expanduser().resolve()
    profile.mkdir(parents=True, exist_ok=True)
    browser_path = str(EDGE) if EDGE.exists() else None
    manifest: list[dict[str, Any]] = []
    downloaded: list[Path] = []
    hashes: set[str] = set()

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(profile), executable_path=browser_path, headless=not args.headful,
            viewport={"width": 1440, "height": 1000}, user_agent=UA,
            args=["--disable-blink-features=AutomationControlled"],
        )
        search_page = context.pages[0] if context.pages else context.new_page()
        for segment_index, (segment, queries) in enumerate(requirements.items(), 1):
            segment_dir = output / f"片段{segment_index:02d}_{safe_name(segment)}"
            segment_dir.mkdir(parents=True, exist_ok=True)
            saved_for_segment = 0
            for query in queries:
                if saved_for_segment >= args.max_images_per_segment:
                    break
                search_url = (
                    "https://www.xiaohongshu.com/search_result?keyword=" + quote(str(query))
                    + "&source=web_search_result_notes&type=51"
                )
                search_page.goto(search_url, wait_until="domcontentloaded", timeout=60_000)
                wait_for_search(search_page, args.login_timeout)
                search_page.wait_for_timeout(4000)
                for card in relevant_search_cards(search_page, str(query), args.notes_per_query):
                    if saved_for_segment >= args.max_images_per_segment:
                        break
                    response = context.request.get(
                        card["src"], headers={"Referer": search_url, "User-Agent": UA}, timeout=60_000
                    )
                    if not response.ok:
                        continue
                    content = response.body()
                    digest = hashlib.sha256(content).hexdigest()
                    if digest in hashes:
                        continue
                    hashes.add(digest)
                    ext = extension(response.headers.get("content-type", ""), card["src"])
                    filename = f"{saved_for_segment + 1:02d}_{safe_name(card['title'], 35)}{ext}"
                    local = segment_dir / filename
                    local.write_bytes(content)
                    try:
                        with Image.open(local) as opened:
                            width, height = opened.size
                    except Exception:
                        local.unlink(missing_ok=True)
                        continue
                    if max(width, height) < 640:
                        local.unlink(missing_ok=True)
                        continue
                    saved_for_segment += 1
                    downloaded.append(local)
                    manifest.append({
                        "segment": segment,
                        "local_file": str(local),
                        "width": width,
                        "height": height,
                        "query": query,
                        "note_title": card["title"],
                        "note_url": card["href"],
                        "search_url": search_url,
                        "image_url": card["src"],
                    })
                search_page.wait_for_timeout(1200)
        context.close()

    (output / "素材清单.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 小红书参考图片来源清单", "",
        "> 图片仅作为即梦生成参考；版权与使用权归各原作者。请根据实际用途确认授权。", "",
    ]
    for item in manifest:
        lines.extend([
            f"## {item['segment']} — {Path(item['local_file']).name}", "",
            f"- 尺寸：{item['width']}×{item['height']}",
            f"- 搜索词：{item['query']}",
            f"- 笔记标题：{item['note_title']}",
            f"- 笔记来源：{item['note_url']}",
            f"- 原图地址：{item['image_url']}", "",
        ])
    (output / "素材来源清单.md").write_text("\n".join(lines), encoding="utf-8")
    create_contact_sheet(downloaded, output / "联系表.jpg")
    print(json.dumps({"output": str(output), "images": len(downloaded)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
