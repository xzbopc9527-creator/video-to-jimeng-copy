# Keyframe cleanup with ChatGPT image editing

Use this workflow after selecting each segment's original full-resolution source timestamps.

## Required order

1. Keep the untouched extracted frame as evidence.
2. Prefer a nearby source frame that already has no Douyin/platform overlays while preserving the intended composition.
3. When text or watermarks are unavoidable, use ChatGPT image editing as the default cleanup method.
4. Load the local keyframe with an image-viewing tool before editing so ChatGPT has the exact image target.
5. Ask ChatGPT to remove only Douyin/platform overlays: subtitles, stickers, watermarks, account IDs, search bars, UI chrome, ad markers, and platform end-card elements.
6. Preserve real-world brand/product text and logos by default: packaging marks, cup logos, storefront signs, menu boards, product labels, and printed tray paper. Remove these only when the user explicitly requests it.
7. Inspect the original and edited image at full size. Iterate if any platform text remains or if the food, person, hand contact, product geometry, brand mark, lighting, or composition changed unintentionally.
8. Deliver only the cleaned derivative to Jimeng; retain the original and any rejected edits for audit when useful.

## ChatGPT edit prompt pattern

Use a tight edit prompt like:

```text
Edit the shown source keyframe. Remove only Douyin/platform overlays: subtitles, stickers, watermarks, account IDs, search bars, UI chrome, and ad markers. Preserve the photographed scene exactly: food, hands, face, clothing, product shape, real-world brand/product text and logos, packaging, store signs, menu boards, lighting, shadows, camera angle, 9:16 composition, and phone-video texture. Fill removed overlay areas naturally from surrounding pixels. Do not beautify, relight, upscale, stylize, redesign, add text, or add a watermark.
```

If the source contains no real-world brand text, say so only when it helps avoid over-removal. If the source contains important brand text, name it explicitly, for example: "Preserve the KFC cup logos and mashed-potato cup text."

## Ask before replacing key visual parts

If the user supplies a reference image for hands, face, body, wardrobe, product, prop, or another key visual part, do not silently apply it during cleanup. Ask a concise confirmation before editing:

- whether to apply the replacement;
- exactly which part to replace, such as hands only, face only, body only, wardrobe only, product only, or prop only;
- which original elements must remain locked, such as sleeve cuffs, food positions, hand pose, brand text, camera angle, lighting, and composition;
- whether the replacement should be applied to all relevant keyframes or only selected frames.

After confirmation, include the replacement scope in every ChatGPT edit prompt. Example:

```text
Also replace only the visible hands with the supplied reference person's hand appearance: young East Asian female hands, slim fingers, fair warm skin, neat natural nails. Keep the original sleeve cuffs, exact hand pose, food contact, food position, brand text, lighting, and composition unchanged.
```

If the replacement causes the model to redraw food, alter brand marks, change sleeves, or shift composition, reject that edit or mark it as an experiment instead of a final Jimeng reference.

## Fidelity guardrails

- Keep original composition, aspect ratio, people, food/product geometry, packaging shape, colors, lighting, shadows, textures, and contact relationships.
- Do not crop as a substitute for cleanup unless a detail crop is explicitly needed; keep an uncropped cleaned scene frame for layout.
- Do not upscale, sharpen, beautify, relight, face-restore, restyle, or make the frame look like a studio product photo.
- Do not remove real-world brand/product text by default.
- If platform text overlaps a face, hand, food edge, product edge, or important texture, try a nearby equivalent frame first. If ChatGPT editing still damages the subject, flag the limitation and choose the least damaging reference.
- Reject edits with smears, repeated texture, warped edges, missing fingers, altered facial features, changed food quantity, deformed packaging, changed brand marks, or visible AI redraw artifacts.

## Required record

For every Jimeng reference, record:

- original source video path and timestamp;
- untouched frame path;
- cleaned frame path;
- cleanup method: `ChatGPT image edit`, `naturally clean frame`, or `local fallback`;
- whether real-world brand/product text was preserved or intentionally removed;
- whether a key-part replacement was applied, and the user's confirmation/scope;
- visual verification result;
- role: primary composition, character consistency, food/product detail, hand contact, or end pose.

Use local OCR masking or inpainting only as a fallback when ChatGPT image editing is unavailable or the user explicitly asks for deterministic local cleanup. Local fallback still follows the same preserve-brand and ask-before-replacement rules.
