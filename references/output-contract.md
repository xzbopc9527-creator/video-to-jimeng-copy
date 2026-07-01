# Jimeng replica output contract

Use this contract after the source has been downloaded and visually inspected.

## 1. Evidence checklist

Record only what is visible or audible:

- duration, resolution, nominal frame rate, aspect ratio;
- exact hard cuts and authored end time;
- recurring characters, wardrobe, age range, facial features, props;
- location layout, dominant colors, signs, lighting, background people;
- lens impression, camera height, distance, movement, focus, exposure;
- action sequence and object continuity;
- dialogue speakers and timing;
- caption wording, font family approximation, size, fill, outline, position;
- ambience, music, sound effects;
- watermarks and platform end cards.

Mark low-confidence observations. Verify ASR against visible captions whenever possible.

## 2. Segment grouping algorithm

1. Start from the visually confirmed source cut map.
2. Separate app-generated end cards from authored footage.
3. Group adjacent shots by one semantic purpose: hook/payment, offer validation, product demonstration, tour, prize reveal, objection handling, call to action.
4. Target 4–8 seconds per generated clip.
5. Keep every generated duration in the inclusive 4–15 second range.
6. Make generated duration and final retained duration identical. Default trim amount to zero.
7. Never add a removable safety tail, padding, freeze hold, repeated action, or surplus footage solely to satisfy a source timestamp.
8. Merge sub-4-second source shots with semantically adjacent shots, then retime all actions so the complete generated clip remains useful.
9. Use no more than two internal hard cuts per generated clip.
10. Preserve source order and key content beats, but freely compress or extend the total recreated runtime. Matching the source's fractional duration is not a goal.
11. If the user explicitly requires an exact source runtime, prefer action retiming and edit-speed adjustment. Generate footage that will be discarded only when no zero-waste grouping works.

For each segment publish these values:

- source reference range, used only as analysis evidence;
- generated duration;
- final duration, equal to generated duration;
- final recreated timeline;
- trim amount, normally `0秒`.

## 3. Compute-cost rule

Optimize for useful seconds, not frame-identical runtime:

- Choose the shortest duration that can express the complete semantic beat without rushed or empty action.
- Fill every second with intentional setup, action, reveal, reaction, or product hold that belongs in the final edit.
- Do not create a 5-second clip to keep 4.2 seconds; redesign the beat as a fully usable 4- or 5-second clip.
- Do not preserve fractional source cut times in prompts. Convert them into clean local timings suited to the chosen clip duration.
- Keep end cards, exact logos, UI, and static legal text out of generation compute; build them in post.

## 4. Standalone prompt schema

Write each Chinese prompt in natural prose using this order:

```text
生成时长、9:16、手机帧率观感、内容类型。

固定人物：年龄范围、国籍/外观、脸型、发型、体型、服装、饰品、角色关系。

完整场景：地点、布局、道具、主色、光线、背景活动。

0.00—X.XX秒：人物动作、物体运动、表情、对白。
X.XX秒处快速直接硬切（仅在需要时）。
X.XX—结束：后续动作、对白和画面落点。

镜头：机位、焦段观感、景别、距离、运动、对焦、曝光、手持幅度。
声音：对白说话人、口型、环境声、拟音、音乐。
文字：是否禁用模型字幕，哪些内容后期添加。
避免：本段最可能发生的角色、手部、道具、文字和镜头错误。
```

Never use references such as “人物同上”, “环境同前”, or “沿用全局负面词.” A copied segment must work alone.

Every timeline must end on the exact generated duration with a meaningful final action or composed product hold. Never label any portion as a safe tail or removable footage.

## 5. Text and audio policy

- Ask Jimeng not to synthesize exact Chinese captions, prices, coupon pages, brand marks, account IDs, or search bars. Generate the visual plate and rebuild these in post.
- Provide the exact post-production caption text and time ranges.
- Measure caption styling from frames; do not reuse fixed font parameters from an unrelated video.
- Keep dialogue in the visual prompt for body language and lip motion.
- For an exact replica, replace generated speech with the recovered or re-recorded dialogue, then align captions.
- Treat Douyin's moving watermark and creator end slate as platform elements; append them in post or let Douyin generate them.

## 6. Quality bar

The final response is incomplete if it contains only analysis, a master prompt, prompts that depend on earlier shorthand, or planned surplus footage. It is complete only when it includes a zero-waste timeline and every final standalone prompt.
