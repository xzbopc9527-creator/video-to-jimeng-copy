#!/usr/bin/env python3
"""Resolve/download Douyin video, create Jimeng evidence, and optionally extract full audio."""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
    "Mobile/15E148 Safari/604.1"
)

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi"}
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
URL_TRAILING_PUNCTUATION = ".,;:!?，。；：！？、)]}〉》】）”’"


def is_douyin_url(value: str) -> bool:
    hostname = (urlparse(value).hostname or "").lower()
    return (
        hostname == "douyin.com"
        or hostname.endswith(".douyin.com")
        or hostname == "iesdouyin.com"
        or hostname.endswith(".iesdouyin.com")
    )


def extract_douyin_url(text: str) -> str | None:
    for match in URL_PATTERN.finditer(text):
        candidate = match.group(0).rstrip(URL_TRAILING_PUNCTUATION)
        if is_douyin_url(candidate):
            return candidate
    return None


def detect_input(raw_input: str) -> dict[str, Any]:
    value = raw_input.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1].strip()
    if not value:
        raise RuntimeError("Input is empty.")

    try:
        supplied = Path(value).expanduser()
        if supplied.exists():
            resolved = supplied.resolve()
            if resolved.is_dir():
                return {"type": "video_folder", "value": resolved}
            if resolved.is_file():
                suffix = resolved.suffix.lower()
                if suffix not in SUPPORTED_VIDEO_EXTENSIONS:
                    supported = ", ".join(sorted(SUPPORTED_VIDEO_EXTENSIONS))
                    raise RuntimeError(f"Unsupported local video extension: {suffix or '(none)'}. Use {supported}.")
                return {"type": f"local_{suffix[1:]}", "value": resolved}
    except OSError:
        pass

    url = extract_douyin_url(value)
    if url:
        normalized_text = value.rstrip(URL_TRAILING_PUNCTUATION).strip()
        input_type = "douyin_share_link" if normalized_text == url else "douchat_share_text"
        return {"type": input_type, "value": url, "share_text": value if input_type == "douchat_share_text" else None}

    raise RuntimeError(
        "Unsupported input. Supply a Douyin link, share text containing a Douyin link, "
        "a local MP4/MOV/AVI file, or a folder containing those videos."
    )


def discover_videos(folder: Path, excluded_dir: Path | None = None) -> list[Path]:
    videos: list[Path] = []
    excluded = excluded_dir.resolve() if excluded_dir and excluded_dir.exists() else excluded_dir
    for candidate in folder.rglob("*"):
        if not candidate.is_file() or candidate.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
            continue
        resolved = candidate.resolve()
        if excluded and (resolved == excluded or excluded in resolved.parents):
            continue
        videos.append(resolved)
    return sorted(videos, key=lambda item: str(item).casefold())


def safe_output_name(stem: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", stem).strip(" ._")
    return (cleaned or "video")[:80]


def executable(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    candidate = Path.home() / "ffmpeg" / "ffmpeg-8.1.1-essentials_build" / "bin" / f"{name}.exe"
    if candidate.exists():
        return str(candidate)
    raise RuntimeError(f"Required executable not found: {name}")


def run(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=check, encoding="utf-8", errors="replace")


def find_browser(explicit: str | None) -> str:
    candidates = [
        explicit,
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for item in candidates:
        if item and Path(item).exists():
            return item
    raise RuntimeError("Edge/Chrome executable not found. Pass --browser-executable.")


def resolve_douyin(url: str, browser_executable: str | None) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is required: python -m pip install playwright") from exc

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=find_browser(browser_executable),
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(viewport={"width": 390, "height": 844}, user_agent=MOBILE_UA)
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(8_000)
        resolved_url = page.url
        title = page.title()
        videos = page.locator("video").evaluate_all(
            "els => els.map(v => ({src: v.src, currentSrc: v.currentSrc, poster: v.poster}))"
        )
        html = page.content()
        browser.close()

    video_url = next((v.get("currentSrc") or v.get("src") for v in videos if v.get("currentSrc") or v.get("src")), None)
    if not video_url:
        raise RuntimeError("No playable video URL found. The page may require fresh cookies or verification.")

    video_id_match = re.search(r"/video/(\d+)", resolved_url)
    aweme_id = video_id_match.group(1) if video_id_match else None
    music_match = re.search(r'"music":\{"mid":"([^"]+)","title":"([^"]*)","author":"([^"]*)"', html)
    music = None
    if music_match:
        music = {"mid": music_match.group(1), "title": music_match.group(2), "author": music_match.group(3)}

    return {
        "source_url": url,
        "resolved_url": resolved_url,
        "title": title,
        "aweme_id": aweme_id,
        "video_url": video_url,
        "music": music,
    }


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": MOBILE_UA, "Referer": "https://www.iesdouyin.com/"},
    )
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


def probe(video: Path) -> dict[str, Any]:
    command = [
        executable("ffprobe"), "-v", "error", "-show_entries",
        "format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate",
        "-of", "json", str(video),
    ]
    data = json.loads(run(command).stdout)
    fmt = data.get("format", {})
    streams = data.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})

    def ratio(value: str | None) -> float | None:
        if not value or value == "0/0":
            return None
        numerator, denominator = value.split("/", 1)
        return float(numerator) / float(denominator)

    return {
        "duration": float(fmt.get("duration", 0)),
        "size": int(fmt.get("size", 0)),
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "codec": video_stream.get("codec_name"),
        "nominal_fps": ratio(video_stream.get("r_frame_rate")),
        "average_fps": ratio(video_stream.get("avg_frame_rate")),
    }


def probe_audio(media: Path) -> dict[str, Any]:
    command = [
        executable("ffprobe"), "-v", "error", "-select_streams", "a:0",
        "-show_entries", "format=duration,size:stream=codec_name,sample_rate,channels,bit_rate",
        "-of", "json", str(media),
    ]
    data = json.loads(run(command).stdout)
    streams = data.get("streams", [])
    if not streams:
        raise RuntimeError(f"No audio stream found: {media}")
    stream = streams[0]
    fmt = data.get("format", {})

    def integer(value: Any) -> int | None:
        return int(value) if value not in (None, "") else None

    return {
        "codec": stream.get("codec_name"),
        "sample_rate": integer(stream.get("sample_rate")),
        "channels": integer(stream.get("channels")),
        "bit_rate": integer(stream.get("bit_rate")),
        "duration": float(fmt.get("duration", 0)),
        "size": integer(fmt.get("size")),
    }


def extract_audio(video: Path, output_dir: Path, audio_format: str, mp3_bitrate: str) -> dict[str, Any]:
    source_audio = probe_audio(video)
    basename = f"{video.stem}-full-audio"
    outputs: dict[str, Any] = {}

    if audio_format in {"m4a", "both"}:
        m4a = output_dir / f"{basename}.m4a"
        can_copy = source_audio["codec"] in {"aac", "alac"}
        codec_args = ["-c:a", "copy"] if can_copy else ["-c:a", "aac", "-b:a", "192k"]
        run([
            executable("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(video), "-map", "0:a:0", "-vn", *codec_args, str(m4a),
        ])
        outputs["m4a"] = {
            "path": str(m4a),
            "mode": "stream-copy" if can_copy else "aac-transcode",
            "technical": probe_audio(m4a),
        }

    if audio_format in {"mp3", "both"}:
        mp3 = output_dir / f"{basename}.mp3"
        run([
            executable("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(video), "-map", "0:a:0", "-vn",
            "-c:a", "libmp3lame", "-b:a", mp3_bitrate, str(mp3),
        ])
        outputs["mp3"] = {
            "path": str(mp3),
            "mode": "mp3-transcode",
            "technical": probe_audio(mp3),
        }

    return {"source": source_audio, "files": outputs}


def detect_cuts(video: Path, threshold: float) -> list[float]:
    command = [
        executable("ffmpeg"), "-hide_banner", "-i", str(video),
        "-filter:v", f"select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-",
    ]
    result = run(command, check=False)
    values = [float(item) for item in re.findall(r"pts_time:([0-9.]+)", result.stderr)]
    cuts: list[float] = []
    for value in values:
        if not cuts or abs(value - cuts[-1]) > 0.08:
            cuts.append(round(value, 3))
    return cuts


def create_contact_sheet(video: Path, output: Path, duration: float) -> None:
    sample_rate = min(1.0, 35.0 / max(duration, 1.0))
    tile_rows = max(1, math.ceil(min(36, math.ceil(duration * sample_rate)) / 6))
    vf = f"fps={sample_rate:.6f},scale=240:427,tile=6x{tile_rows}:padding=3:margin=3"
    command = [
        executable("ffmpeg"), "-y", "-i", str(video), "-vf", vf,
        "-frames:v", "1", str(output),
    ]
    run(command)


def transcribe(video: Path, model_name: str) -> list[dict[str, Any]]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("faster-whisper is required for --transcribe") from exc
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        str(video), language="zh", beam_size=5, vad_filter=False,
        word_timestamps=True, condition_on_previous_text=False,
    )
    output = []
    for segment in segments:
        output.append({
            "start": round(segment.start, 3),
            "end": round(segment.end, 3),
            "text": segment.text.strip(),
            "words": [
                {"start": round(word.start, 3), "end": round(word.end, 3), "text": word.word}
                for word in (segment.words or [])
            ],
        })
    return output


def analyze_video(
    video: Path,
    output_dir: Path,
    args: argparse.Namespace,
    original_input: str,
    input_type: str,
    normalized_input: str,
    page_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    technical = probe(video)
    cuts = detect_cuts(video, args.scene_threshold)
    contact_sheet = output_dir / "contact-sheet.jpg"
    create_contact_sheet(video, contact_sheet, technical["duration"])

    result: dict[str, Any] = {
        "input": original_input,
        "input_type": input_type,
        "normalized_input": normalized_input,
        "video_path": str(video),
        "contact_sheet": str(contact_sheet),
        "page": page_metadata or {},
        "technical": technical,
        "scene_threshold": args.scene_threshold,
        "candidate_scene_cuts": cuts,
    }
    if args.extract_audio:
        result["audio"] = extract_audio(video, output_dir, args.extract_audio, args.mp3_bitrate)
    if args.transcribe:
        result["transcript"] = transcribe(video, args.whisper_model)

    analysis_file = output_dir / "analysis.json"
    result["analysis_file"] = str(analysis_file)
    analysis_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        help="Douyin link, share text, local MP4/MOV/AVI, or folder containing videos",
    )
    parser.add_argument("--out", required=True, help="Analysis output directory")
    parser.add_argument("--transcribe", action="store_true", help="Run Chinese faster-whisper ASR")
    parser.add_argument(
        "--extract-audio", nargs="?", const="both", choices=("m4a", "mp3", "both"),
        help="Extract the complete source audio; omit the value to produce both M4A and MP3",
    )
    parser.add_argument("--mp3-bitrate", default="192k", help="MP3 bitrate used by --extract-audio")
    parser.add_argument("--whisper-model", default="small")
    parser.add_argument("--scene-threshold", type=float, default=0.12)
    parser.add_argument("--browser-executable")
    args = parser.parse_args()

    output_dir = Path(args.out).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    detected = detect_input(args.input)
    input_type = detected["type"]

    if input_type == "video_folder":
        folder: Path = detected["value"]
        videos = discover_videos(folder, excluded_dir=output_dir)
        if not videos:
            supported = ", ".join(sorted(SUPPORTED_VIDEO_EXTENSIONS))
            raise RuntimeError(f"No supported videos found under {folder}. Expected {supported}.")

        items: list[dict[str, Any]] = []
        success_count = 0
        for index, video in enumerate(videos, start=1):
            item_dir = output_dir / f"{index:03d}-{safe_output_name(video.stem)}"
            try:
                result = analyze_video(
                    video=video,
                    output_dir=item_dir,
                    args=args,
                    original_input=str(video),
                    input_type=f"local_{video.suffix.lower()[1:]}",
                    normalized_input=str(video),
                )
                items.append({"status": "ok", **result})
                success_count += 1
            except Exception as error:
                items.append({
                    "status": "error",
                    "input": str(video),
                    "input_type": f"local_{video.suffix.lower()[1:]}",
                    "error": str(error),
                })

        batch = {
            "input": args.input,
            "input_type": input_type,
            "normalized_input": str(folder),
            "video_count": len(videos),
            "success_count": success_count,
            "error_count": len(videos) - success_count,
            "items": items,
        }
        batch_file = output_dir / "batch-analysis.json"
        batch["batch_analysis_file"] = str(batch_file)
        batch_file.write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(batch, ensure_ascii=False, indent=2))
        return 0 if success_count else 1

    page_metadata: dict[str, Any] = {}
    if input_type in {"douyin_share_link", "douchat_share_text"}:
        normalized_url: str = detected["value"]
        page_metadata = resolve_douyin(normalized_url, args.browser_executable)
        identifier = page_metadata.get("aweme_id") or "video"
        video = output_dir / f"douyin-{identifier}.mp4"
        download(page_metadata["video_url"], video)
        normalized_input = normalized_url
    else:
        video = detected["value"]
        normalized_input = str(video)

    result = analyze_video(
        video=video,
        output_dir=output_dir,
        args=args,
        original_input=args.input,
        input_type=input_type,
        normalized_input=normalized_input,
        page_metadata=page_metadata,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
