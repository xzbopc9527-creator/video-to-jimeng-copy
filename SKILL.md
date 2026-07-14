---
name: douyin-to-jimeng
description: Analyze Douyin share links/text, local videos, or video folders; monitor public Douyin food-commerce accounts after human approval; extract complete audio; inspect footage frame by frame; recover cuts/dialogue/captions; prepare ChatGPT-edited keyframes that remove platform text/watermarks while preserving real-world brand/product text by default; ask before replacing key visual parts such as hands, faces, bodies, wardrobe, products, or props with a supplied reference; and produce copy-ready Chinese Jimeng (即梦) prompts using integer 4–15 second clips, timeline-inserted reference frames, synchronized action/dialogue beats, and photorealistic food/human/anti-AI constraints. Use for 抖音视频解析、关键帧去字去水印、ChatGPT图片清理、手部/人物/关键部位参考替换确认、无平台文字参考图、即梦整数秒写实复刻提示词、参考图插入时间线、口播动作同步、小红书实图素材。
---

# Douyin to Jimeng

Turn a supplied Douyin link, full share text, local video, or video folder into evidence-based, self-contained Jimeng prompts. Analyze the footage itself; never infer the video only from its title or description.

## Workflow

1. Detect the input type and normalize it to a Douyin URL, local video, or video list.
2. Resolve and download remote sources, or enumerate supported local videos.
3. When requested, extract the complete source audio and verify its duration and stream properties.
4. Measure duration, dimensions, frame rate, cuts, dialogue, captions, camera behavior, lighting, characters, props, environment, sound, and end cards.
5. Inspect the generated contact sheet with an image-viewing tool. Extract additional full-resolution frames around ambiguous cuts or text.
6. Build the original cut map, then redesign it into zero-waste Jimeng clips whose durations are integer seconds from 4 through 15.
7. Select one primary source keyframe and at most two supporting keyframes for every final segment, then prepare and visually verify ChatGPT-cleaned platform-text-free derivatives for Jimeng.
8. Assign every reference frame to an exact insertion point or interval inside the segment timeline so it locks the start pose, product reveal, bite/contact moment, expression change, or end pose it is meant to control.
9. If the user supplies or implies a reference for replacing hands, face, body, wardrobe, product, prop, or another key visual part, pause before editing and ask whether to apply the replacement, which parts to replace, and which parts must remain unchanged.
10. Build a per-segment real-image requirement list and, when requested, collect matching images from public Xiaohongshu notes.
11. Deliver a final answer whose prompts can each be copied independently without consulting another section.

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

## Prepare text-free keyframes

Read [references/keyframe-cleaning.md](references/keyframe-cleaning.md) before preparing Jimeng references. Keep the untouched full-resolution frame as evidence, but upload only a visually verified cleaned derivative to Jimeng.

Use ChatGPT image editing as the default cleanup method for keyframes that contain Douyin/platform overlays, subtitles, account IDs, UI, stickers, watermarks, or ad markers. First load the local keyframe with an image-viewing tool so it is available as the edit target, then ask ChatGPT to remove only those overlays and preserve the photographed scene. Do not remove real-world brand/product text, packaging marks, store signage, menu boards, or logos unless the user explicitly asks.

If the user asks to replace a key visual part, or provides a reference image that could be used for replacement, ask for explicit confirmation before applying it. Name the proposed replacement scope, for example: "是否把手部替换成参考人物的手部？是否保留原袖口、食物位置和品牌字样？" Do not silently change identity, hands, face, body, wardrobe, products, props, lighting, or composition during ordinary text/watermark cleanup.

Inspect the original and cleaned image with an image-viewing tool. Reject residual glyphs, obvious smears, repeated texture, or altered face, hand, food, product, packaging, contact, lighting, or brand details. Record the source timestamp, original path, cleaned file path, cleanup method, and whether any confirmed key-part replacement was applied.

## Monitor public accounts

Read [references/account-monitoring.md](references/account-monitoring.md) before registering accounts or scheduling checks.

Resolve account share links to stable `sec_uid` values, store runtime configuration outside the skill folder, and initialize a no-notification baseline:

```powershell
python scripts/monitor_douyin_accounts.py --config "<accounts.json>" --state "<state.json>" --initialize
```

For later checks, omit `--initialize`. Emit events only for newly visible public food-commerce videos. Mark unrelated new posts as seen without notifying. Never download or analyze a detected video until the user replies with an approval command such as `分析 <URL>`.

When Feishu notification is approved, use `--notify-feishu --chat-id <oc_xxx>`. Keep the message deterministic: account, caption, public link, detection time, and approval command. Do not send a “no updates” message.

## Optimize for Jimeng

Read [references/output-contract.md](references/output-contract.md) before composing the final answer.

Apply these non-negotiable rules:

- Set every generated clip duration to an integer number of seconds in `{4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}`. Reject decimal durations such as `4.5秒`.
- Treat generation compute as a paid resource. Make every generated second usable by default.
- Set each generated duration equal to its final edited duration, and write both as integer seconds. Do not add removable safety tails, padding, freeze holds, or footage intended only for trimming.
- Prefer 4–8-second integer clips and 4–6 generated segments for a 20–45 second source.
- Merge sub-4-second micro-shots with adjacent shots that form one semantic unit. Retime their actions to fill the selected duration naturally.
- Permit at most two internal hard cuts in one generated segment.
- Preserve the source order and key content beats, but allow the total recreated duration and individual beat timing to differ from the source. Do not spend compute merely to match fractional source timestamps.
- If an exact source runtime is not representable as a sum of integer segment durations, never invent a decimal Jimeng duration. Report the nearest integer total and require an explicit post-production timing choice.
- Add platform end cards in post rather than asking Jimeng to synthesize them.
- Generate clean visual plates. Remove platform captions, prices, coupons, UI, stickers, and watermarks from Jimeng reference frames and add those elements in post unless the user explicitly accepts approximate text. Preserve real-world brand/product text, packaging marks, store signs, menu boards, and logos in the reference images by default; if exact readable text or logo fidelity matters, still rebuild it in post.
- Reuse one character reference and stable scene references across every segment. Recommend exact source timestamps for those references.
- Treat original full-resolution video frames as evidence and their verified ChatGPT-cleaned derivatives as Jimeng references. ChatGPT editing is allowed for removing platform overlays/watermarks and for user-confirmed key-part replacement only. Do not upscale, beautify, relight, face-restore, restyle, redesign, or otherwise enhance a reference image.
- Make the keyframe plan explicit: one primary frame controls composition and subject geometry; up to two support frames may clarify face, wardrobe, food texture, packaging, or the end pose.
- Insert each keyframe into the segment action timeline at the exact second or interval it controls. State whether the frame locks the opening pose, mid-action contact, mouth shape, product close-up, camera reframing, or final hold.
- Align dialogue with the same action timeline. For every spoken line, specify start/end seconds, speaker, intended mouth movement, and the visible action happening during the line.
- If people and food share a shot, prefer a primary frame containing both so their scale, hand contact, eyeline, and placement remain physically consistent.

## Use keyframes without introducing AI stylization

For each segment, record the exact source timestamp, cleaned file path, intended use, and segment timeline insertion point of every reference frame. Deliver only verified platform-text-free references. Prefer frames without motion blur or occlusion; remove Douyin/app overlays, subtitles, stickers, watermarks, account IDs, search bars, and ad markers; preserve real-world brand/product text unless the user asks otherwise. Crop only when a close detail is necessary; retain an uncropped cleaned scene frame for layout.

Apply this priority order inside every prompt:

1. primary source keyframe: composition, identity, product/food geometry, quantity, scale, and placement;
2. stable character keyframe: face, age, hair, skin tone, body shape, wardrobe, and accessories;
3. optional detail keyframe: food surface, packaging, hand interaction, prop detail, or final pose;
4. text prompt: motion, timing, camera behavior, dialogue, and sound.

Use the keyframes as timeline anchors, not loose mood references. In the action timeline, name the active reference frame at each important beat, for example `0.00秒对齐主参考图开场构图`, `2.20秒对齐辅助参考图1的手部接触`, `4.00秒落到辅助参考图2的结束姿势`. Do not ask Jimeng to interpolate freely through a food bite, hand contact, product turn, or face expression change without a named visual anchor when one exists.

State that reference images are fidelity constraints, not style-transfer inputs. Require the model to preserve the photographed subject and change only the motion needed for the segment. If a reference identity is used to replace hands, face, body, wardrobe, product, or another key part, state that the replacement was explicitly confirmed by the user and list the exact locked invariants. Never ask the model to beautify, redesign, re-light, or “enhance” a reference frame.

## Write every prompt as a standalone artifact

Every segment prompt must repeat all relevant information rather than saying “同上” or “使用前面的设定.” Include:

1. integer generation duration from 4 to 15 seconds, aspect ratio, frame-rate feel, and content style;
2. exact primary/support keyframe timestamps, timeline insertion points, and what each frame must lock;
3. complete character appearance, wardrobe, and consistency anchors;
4. complete environment, props, colors, and background activity;
5. second-by-second actions, active reference-frame anchors, dialogue/口型 timing, and any internal hard-cut time;
6. camera position, lens feel, framing, focus, exposure, and handheld behavior;
7. exact dialogue, speaker identity, ambience, sound effects, and music handling;
8. instructions about captions/logos/UI/watermarks;
9. a photorealistic baseline in every segment;
10. food realism constraints whenever food, beverages, ingredients, or packaging are visible;
11. human realism constraints whenever a face, body, hand, or skin is visible;
12. segment-specific anti-AI and continuity constraints.

Reject a prompt as incomplete if it lacks the photorealistic baseline, lacks a required food/human module, or refers to a global negative prompt instead of repeating the relevant constraints. Use the exact constraint modules and validation checklist in [references/output-contract.md](references/output-contract.md).

Keep dialogue in the prompt to drive performance and lip motion. Put every口播 line into the action timeline with start/end seconds, matching expression, mouth opening/closing, breath or chew state when visible, and hand/food movement during the line. Separately recommend replacing model audio in post when exact wording or speaker identity matters.

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
2. a zero-waste generation/edit table with source reference range, matching integer generated/final duration, final timeline, reference-frame insertion points, dialogue timing, and `0秒` trim for every clip;
3. one complete copy-ready code block per Jimeng segment;
4. when requested, direct links to the complete M4A/MP3 audio files with codec and duration verification;
5. when requested, a segment-to-reference-image mapping and a link to the saved asset directory or manifest;
6. exact dialogue/caption timing and caption styling when present;
7. post-production instructions for end cards, logos, UI, music, and export;
8. a concise limitation: prompt-only generation cannot guarantee exact faces, readable text, logos, or frame-identical motion.

Do not stop after a generic master prompt. The required endpoint is the final, independently copyable prompt set.
