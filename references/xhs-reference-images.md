# Xiaohongshu reference-image workflow

Use this workflow only when the user requests real images from Xiaohongshu.

## 1. Build requirements from final segments

Create 1–3 narrow searches per segment. Include the brand or place, subject, action, and shot purpose when known.

Example:

```json
{
  "片段01_产品开箱": ["品牌 产品名 开箱", "品牌 包装 特写"],
  "片段02_门店展示": ["品牌 门店 环境", "品牌 柜台" ]
}
```

Avoid generic searches such as only a brand name. Search for the visual evidence the prompt needs: product shape, hand interaction, packaging, store layout, outfit, or lighting.

## 2. Access rules

- Access only public search results and public notes.
- Respect the login wall. Use an interactive persistent browser profile when Xiaohongshu requires login.
- Never extract, display, or distribute authentication data.
- Use conservative request rates and stop on verification or account warnings.
- Do not like, comment, follow, save, publish, or otherwise mutate account state.

## 3. Selection rules

For each segment, prefer 2–4 images that jointly cover:

- subject identity and accurate appearance;
- close product/prop detail;
- environment or composition;
- action pose when relevant.

Reject images that are unrelated, near-duplicates, smaller than 640 pixels on the long edge, dominated by text/UI, severely watermarked, collaged, AI-generated, or inconsistent with the source video.

Use reference images to anchor factual appearance, not to copy another creator's exact composition. Keep source attribution.

## 4. Folder contract

Save directly to the requested asset directory:

```text
<asset directory>/
  片段01_<purpose>/
    01_<short-description>.jpg
    02_<short-description>.jpg
  片段02_<purpose>/
  素材来源清单.md
  素材清单.json
  联系表.jpg
```

The manifest must record:

- final Jimeng segment;
- local filename;
- image dimensions;
- search query;
- Xiaohongshu note title and public URL;
- original image URL;
- intended use in the prompt.

Do not package a ZIP unless the user explicitly asks for one.

## 5. Final handoff

Report the number of retained images per segment, link the local manifest, and identify any segment for which no sufficiently relevant public image was found. Never silently substitute images from another platform when Xiaohongshu was requested.
