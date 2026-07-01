---
name: douyin-to-jimeng
description: Automatically recognize and analyze a Douyin share link, full Douchat/Douyin share text containing a link, local MP4/MOV/AVI, or a folder of videos; extract complete source audio as M4A/MP3; inspect footage frame by frame; recover cuts/dialogue/captions; produce copy-ready Chinese Jimeng (即梦) recreation prompts; and optionally collect public Xiaohongshu reference images. Use for 抖音视频解析、分享文案识别、批量视频文件夹解析、下载或提取整段音频、完美复刻、一比一复刻、即梦提示词、按即梦4–15秒重组镜头、抓取小红书实图素材。
---

# Douyin to Jimeng

Turn a supplied Douyin link, full share text, local video, or video folder into evidence-based, self-contained Jimeng prompts. Analyze the footage itself; never infer the video only from its title or description.

## Workflow

1. Detect the input type and normalize it to a Douyin URL, local video, or video list.
2. Resolve and download remote sources, or enumerate supported local videos.
3. When requested, extract the complete source audio and verify its duration and stream properties.
4. Measure duration, dimensions, frame rate, cuts, dialogue, captions, camera behavior, lighting, characters, props, environment, sound, and end cards.
5. Inspect the generated contact sheet with an image-viewing tool. Extract additional full-resolution frames around ambiguous cuts or text.
6. Build the original cut map, then redesign it into zero-waste Jimeng clips that each last 4–15 seconds.
7. Build a per-segment real-image requirement list and, when requested, collect matching images from public Xiaohongshu notes.
8. Deliver a final answer whose prompts can each be copied independently without consulting another section.

## Detect the input type

Pass the user input unchanged to the analyzer. It recognizes these values automatically:

| Input | Recorded `input_type` | Behavior |
|---|---|---|
| Douyin share link | `douyin_share_link` | Resolve and download one remote video |
| Full Douchat/Douyin share text containing a Douyin URL | `douchat_share_text` | Extract the first supported Douyin URL, then resolve it |
| Local `.mp4` | `local_mp4` | Analyze the file directly |
| Local `.mov` | `local_mov` | Analyze the file directly |
| Local `.avi` | `local_avi` | Analyze the file directly |
| Folder containing supported videos | `video_folder` | Recursively analyze every MP4/MOV/AVI |

```powershell
python scripts/analyze_douyin.py "<input exactly as supplied>" --out "<analysis directory>" --transcribe
```

For a folder, discover files recursively in stable path order, skip the output directory when it is nested under the input folder, and create one numbered subfolder per video. Continue after an individual video failure. Write per-video `analysis.json` files plus a root `batch-analysis.json` containing counts, status, paths, and errors. Reject empty folders, unsupported local extensions, nonexistent paths without a Douyin URL, and share text without a supported Douyin URL.

## Analyze the source

Run the bundled analyzer from this skill directory:

```powershell
python scripts/analyze_douyin.py "<link, share text, video, or folder>" --out "<analysis directory>" --transcribe
```

The script produces:

- the downloaded MP4 when the input is a URL;
- `analysis.json` with technical metadata, detected cuts, page metadata, and optional transcript;
- `batch-analysis.json` plus numbered per-video subfolders for folder inputs;
- `contact-sheet.jpg` for visual inspection;
- complete M4A and/or MP3 audio when `--extract-audio` is supplied.

If Playwright, ffmpeg, ffprobe, or faster-whisper is unavailable, install only the missing dependency or continue with the available evidence. Treat ASR as a draft: verify wording against burned-in captions and frames. Do not claim an uncertain line is exact.

Use the detected cuts as candidates, not ground truth. Confirm every meaningful cut visually. Note app-generated watermarks and Douyin end cards separately from the authored video.

## Extract the complete audio

Use the analyzer after the source is available. Supplying `--extract-audio` with no value creates both formats:

```powershell
python scripts/analyze_douyin.py "<Douyin URL or local video>" --out "<analysis directory>" --extract-audio
```

Choose one format when appropriate:

```powershell
python scripts/analyze_douyin.py "<input>" --out "<analysis directory>" --extract-audio m4a
python scripts/analyze_douyin.py "<input>" --out "<analysis directory>" --extract-audio mp3 --mp3-bitrate 192k
```

Apply these rules:

- Extract the entire downloaded file, including any platform end card. Do not stop at the authored-video end time unless the user explicitly requests a trimmed track.
- Prefer M4A for fidelity. Stream-copy AAC/ALAC audio without re-encoding; if the source codec is incompatible with M4A, transcode to AAC at 192 kbps.
- Produce MP3 at 192 kbps for broad compatibility unless the user requests another bitrate.
- Do not normalize, denoise, separate vocals, change loudness, or mix music during extraction unless explicitly requested.
- Verify the delivered file with `ffprobe`. Confirm duration, codec, sample rate, channel count, and nonzero file size. The extracted duration should match the source within normal container rounding.
- Treat audio extraction and ASR as separate operations: `--extract-audio` preserves sound; `--transcribe` produces text.
- Link each requested audio file directly in the final answer and identify the fidelity-preserving M4A as the recommended version.

The generated filenames are `<video-stem>-full-audio.m4a` and `<video-stem>-full-audio.mp3`. The M4A record in `analysis.json` reports whether extraction used `stream-copy` or `aac-transcode`.

## Optimize for Jimeng

Read [references/output-contract.md](references/output-contract.md) before composing the final answer.

Apply these non-negotiable rules:

- Keep every generated clip between 4 and 15 seconds.
- Treat generation compute as a paid resource. Make every generated second usable by default.
- Set each generated duration equal to its final edited duration. Do not add removable safety tails, padding, freeze holds, or footage intended only for trimming.
- Prefer 4–8 second clips and 4–6 generated segments for a 20–45 second source.
- Merge sub-4-second micro-shots with adjacent shots that form one semantic unit. Retime their actions to fill the selected duration naturally.
- Permit at most two internal hard cuts in one generated segment.
- Preserve the source order and key content beats, but allow the total recreated duration and individual beat timing to differ from the source. Do not spend compute merely to match fractional source timestamps.
- If an exact source runtime is explicitly required, first retime adjacent actions or adjust editing speed; generate surplus footage for trimming only as a last resort and disclose the unavoidable waste.
- Add platform end cards in post rather than asking Jimeng to synthesize them.
- Generate clean visual plates. Add exact Chinese captions, prices, coupons, logos, UI, and watermarks in post unless the user explicitly accepts approximate text.
- Reuse one character reference and stable scene references across every segment. Recommend exact source timestamps for those references.

## Write every prompt as a standalone artifact

Every segment prompt must repeat all relevant information rather than saying “同上” or “使用前面的设定.” Include:

1. generation duration, aspect ratio, frame-rate feel, and content style;
2. complete character appearance, wardrobe, and consistency anchors;
3. complete environment, props, colors, and background activity;
4. second-by-second actions and any internal hard-cut time;
5. camera position, lens feel, framing, focus, exposure, and handheld behavior;
6. exact dialogue, speaker identity, ambience, sound effects, and music handling;
7. instructions about captions/logos/UI/watermarks;
8. segment-specific negative constraints.

Keep dialogue in the prompt to drive performance and lip motion, but separately recommend replacing model audio in post when exact wording or speaker identity matters.

## Collect Xiaohongshu reference images

Read [references/xhs-reference-images.md](references/xhs-reference-images.md) before collecting images.

Create a JSON requirements file that maps each final Jimeng segment to one or more precise Xiaohongshu search queries, then run:

```powershell
python scripts/collect_xhs_refs.py --requirements "<requirements.json>" --output "<user asset directory>" --headful
```

Apply these rules:

- Use only public Xiaohongshu search results and public note images. Never bypass a login wall or anti-bot challenge.
- If login is required, open a dedicated persistent browser profile and let the user log in interactively. Never print, copy, package, or expose cookies, passwords, phone numbers, or verification codes.
- Save directly to the user's requested directory. When no directory is supplied, use a `reference-images` folder beside the analysis output.
- Create one clearly named subfolder per Jimeng segment and a `素材来源清单.md` manifest containing the local filename, segment purpose, query, note title, note URL, and image URL.
- Prefer 2–4 high-resolution, visually distinct images per segment. Download the smallest sufficient set; more images are not automatically better.
- Inspect the saved contact sheet or thumbnails and remove irrelevant, duplicate, low-resolution, screenshot-heavy, or compositionally misleading images.
- Preserve attribution and source URLs. State that third-party images are reference inputs and that reuse rights remain with their respective creators.
- Do not create a ZIP unless the user explicitly requests one.

## Deliver the result

Return, in this order:

1. verified source facts and the number of authored shots;
2. a zero-waste generation/edit table with source reference range, generated/final duration, final timeline, and `0秒` trim for every clip;
3. one complete copy-ready code block per Jimeng segment;
4. when requested, direct links to the complete M4A/MP3 audio files with codec and duration verification;
5. when requested, a segment-to-reference-image mapping and a link to the saved asset directory or manifest;
6. exact dialogue/caption timing and caption styling when present;
7. post-production instructions for end cards, logos, UI, music, and export;
8. a concise limitation: prompt-only generation cannot guarantee exact faces, readable text, logos, or frame-identical motion.

Do not stop after a generic master prompt. The required endpoint is the final, independently copyable prompt set.
