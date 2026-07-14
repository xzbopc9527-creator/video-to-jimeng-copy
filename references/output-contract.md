# Jimeng replica output contract

Use this contract after the source has been downloaded and visually inspected.

## 1. Evidence checklist

Record only what is visible or audible:

- duration, resolution, nominal frame rate, aspect ratio;
- exact hard cuts and authored end time;
- recurring characters, wardrobe, age range, facial features, props;
- food/product geometry, quantity, portion size, arrangement, packaging, surface texture, moisture, oil, crumbs, fibers, steam, and contact shadows;
- location layout, dominant colors, signs, lighting, background people;
- lens impression, camera height, distance, movement, focus, exposure;
- action sequence, hand-object contact, eyeline, scale, and object continuity;
- dialogue speakers and timing;
- caption wording, font approximation, size, fill, outline, position;
- ambience, music, sound effects;
- watermarks and platform end cards.

Mark low-confidence observations. Verify ASR against visible captions whenever possible.

## 2. Segment grouping algorithm

1. Start from the visually confirmed source cut map.
2. Separate app-generated end cards from authored footage.
3. Group adjacent shots by one semantic purpose: hook/payment, offer validation, product demonstration, tour, prize reveal, objection handling, call to action.
4. Target 4 or 5 seconds per generated clip. Every generated duration must be an integer in `{4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}`; never publish `4.5秒`, `6.2秒`, or another decimal duration.
5. Make generated duration and final retained duration the same integer number of seconds. Default trim amount to zero.
6. Never add a removable safety tail, padding, freeze hold, repeated action, or surplus footage solely to satisfy a source timestamp.
7. Merge sub-4-second source shots with semantically adjacent shots, then retime actions so the complete generated clip remains useful.
8. Use no more than two internal hard cuts per generated clip.
9. Preserve source order and key content beats, but freely compress or extend total recreated runtime.
10. If the exact source runtime cannot be expressed as a sum of integer clip durations, do not publish decimal Jimeng durations. Report the nearest integer total and require an explicit post-production timing choice.

For each segment publish:

- source reference range;
- generated duration, written as an integer from 4 through 15 seconds;
- final duration, equal to the same integer generated duration;
- final recreated timeline;
- trim amount, normally `0秒`;
- primary keyframe timestamp and purpose;
- optional support keyframe timestamps and purposes.
- reference-frame insertion points inside the generated timeline;
- dialogue/口播 timing aligned to visible action and lip movement.

## 3. Keyframe contract

Keep original full-resolution video frames as audit evidence. Give Jimeng only visually verified cleaned derivatives made by selecting a naturally clean frame or by using ChatGPT image editing to remove platform overlays and watermarks. Preserve real-world brand/product text and logos by default. Do not use AI-upscaled, beautified, relit, face-restored, restyled, or style-transferred copies.

For every segment:

1. Choose one primary keyframe. It controls composition, identity, food/product geometry, quantity, scale, placement, and lighting direction.
2. Add no more than two support keyframes. Use them only to clarify face/wardrobe, food texture/packaging, hand interaction, or the final pose.
3. Prefer a primary frame containing both the person and food when both are visible. This preserves relative scale, contact, eyeline, and placement.
4. Assign every keyframe to a precise generated-timeline insertion point or interval. State whether it locks the opening pose, mid-action hand/food contact, mouth shape, product close-up, camera reframing, expression change, or final hold.
5. Use the insertion point inside both the keyframe block and the action timeline. A reference frame is incomplete if it has only a source timestamp but no generated-timeline role.
6. Remove platform/app writing: subtitles, prices/coupons presented as overlays, account IDs, search bars, UI chrome, stickers, watermarks, ad markers, and platform end-card elements. A keyframe containing readable or glyph-like platform residue is not deliverable.
7. Preserve real-world brand/product text and logos by default: packaging marks, cup logos, store signage, menu boards, tray-paper printing, labels, and product names. Remove these only when the user explicitly asks.
8. Inspect the original and cleaned image. Reject smears, repeated texture, altered edges, or damage to faces, hands, food, products, brand marks, packaging geometry, contact points, or lighting.
9. If platform text overlaps important subject detail, choose a nearby timestamp with the same composition before asking ChatGPT to repair a larger area.
10. If a detail crop is required, also retain an uncropped cleaned scene frame for spatial layout.
11. Record the source timestamp, original path, cleaned file path, cleanup method, generated-timeline insertion point, and whether brand/product text was preserved or intentionally removed. State explicitly that references are fidelity constraints, not style-transfer inputs. Change only the motion required by the prompt.

### Key-part replacement consent

If a reference image could be used to replace hands, face, body, wardrobe, product, prop, or another key visual part, ask the user before applying it. Record the confirmation and replacement scope. Do not silently use a supplied character image to change hands, face, sleeve cuffs, body shape, wardrobe, products, props, lighting, or composition during ordinary text/watermark cleanup.

After confirmation, every edit prompt must name:

- the exact replacement part;
- the reference identity or visual source;
- the original elements that must remain locked;
- whether the replacement applies to all selected keyframes or only named frames.

Reject replacement edits that redraw food quantity, shift contact points, change brand text, alter clothing outside the confirmed scope, or make the frame look AI-polished.

Keyframe prompt block:

```text
【关键帧约束（最高优先级）】
主参考图：[清理图文件]，源视频 [时间戳]，已确认无任何平台字幕、账号、UI、水印或广告角标；真实品牌/产品文字 [已保留/已按用户要求去除]；锁定人物/食物/产品的构图、数量、比例、位置、材质与光线方向。
插入时间线：主参考图对齐本段 [0.00秒开场 / X.XX秒动作节点 / 结束姿势]，作为该时间点的构图与主体几何锚点。
辅助参考图1：[清理图文件]，源视频 [时间戳]，插入本段 [X.XX—Y.YY秒或X.XX秒]，已确认无任何平台叠字；仅锁定 [脸部与服装 / 食物纹理与包装 / 手部接触 / 口型表情 / 结束姿势]。
辅助参考图2：[清理图文件]，源视频 [时间戳]，插入本段 [X.XX—Y.YY秒或X.XX秒]，已确认无任何平台叠字；仅锁定 [必要细节]；无必要则删除本行。
如已获用户确认替换关键部位：仅将 [手部/脸部/身体/服装/产品/道具] 替换为 [参考来源] 的对应特征，并严格保留 [原袖口/食物位置/品牌字样/构图/光线/接触关系等锁定项]。如未获确认，禁止替换任何关键部位。
参考图只用于保持真实主体与空间关系，不进行风格迁移、自动美化、重新设计、换脸、未确认的关键部位替换或重新布光；不重新引入任何平台文字，只生成本段要求的动作变化。
```

## 4. Timeline synchronization contract

Build one shared timeline for visuals, reference frames, dialogue, mouth movement, and sound. Do not write separate unsynchronized “动作” and “声音” sections that could drift.

For every segment:

1. Start the timeline at `0.00秒` and end exactly on the integer generated duration.
2. Place every reference frame at the exact generated-time beat it controls. Use interval anchors when the model should preserve a pose across a motion, such as `1.20—2.40秒保持辅助参考图1的手部握持和鸡翅位置`.
3. Tie each important action to the active reference anchor: hand reaches, package turns, bite begins, mouth closes, food tears, product moves toward camera, camera reframes, or final product hold.
4. Add every spoken line as a timed cue with speaker, exact text, mouth state, facial expression, and visible action during the line.
5. If the speaker is chewing, drinking, biting, or turning away, state how the mouth movement changes and where the audio should be handled in post.
6. Align captions to the same dialogue cue times when captions are required in post.
7. Use hard cuts only at declared times, and restart the reference-frame anchor after the cut.

Use this compact table before each standalone prompt when it improves clarity:

| 本段时间 | 参考图锚点 | 动作/镜头 | 口播/口型 | 声音/后期 |
|---|---|---|---|---|
| 0.00–1.20秒 | 主参考图，锁定开场构图 | 人物举起产品，镜头轻微手持 | 主播说“……”；嘴型清楚张合 | 环境声，原声建议后期替换 |
| 1.20–3.60秒 | 辅助参考图1，锁定手部接触 | 食物靠近镜头，保持数量和比例 | 无口播或短促气口 | 食物摩擦声 |
| 3.60–5.00秒 | 辅助参考图2，锁定结束姿势 | 产品停在画面中央 | 主播说“……”并看镜头 | 字幕后期添加 |

## 5. Mandatory photorealism modules

Every standalone segment prompt must contain the baseline module. Add the food module whenever food, drinks, ingredients, tableware, or packaging are visible. Add the human module whenever a face, body, hand, or skin is visible. If both appear, include both in full.

### Baseline module — always include

```text
【写实基线】真实手机实拍或真实商业摄影质感，遵循真实物理尺度、重力、材质、接触关系与环境光；保留自然曝光波动、轻微手持微抖、合理运动模糊和真实景深，不过度磨皮、不过度锐化、不过度HDR。画面不是插画、动漫、CG、3D渲染、游戏建模或广告概念图。
```

### Food module — include when relevant

```text
【食物写实】食物的品类、外形、数量、份量、摆放、包装和与手/餐具的比例严格匹配关键帧；保留源画面可见的焦化纹理、肉纤维、脆皮孔隙、酱汁黏度、克制的油脂反光、水汽、碎屑与接触阴影，不凭空增加关键帧中没有的蒸汽或配料。颜色自然不过饱和，食物不蜡质、不塑料、不橡胶化，不融化变形、不漂浮、不穿模、不复制增生，包装不变形；可参考关键帧中的品牌视觉，精确可读文字或标识需要完全一致时留给后期。
```

### Human module — include when relevant

```text
【人物写实】人物脸型、五官比例、年龄、发型、肤色、体型、服装与饰品严格匹配固定人物关键帧；保留毛孔、细纹、小瑕疵和自然面部不对称，眼球高光、牙齿、嘴唇与表情自然。手掌、手指、关节、握持和受力符合真实解剖，皮肤与物体接触处有合理遮挡和阴影；不磨皮、不网红滤镜、不蜡像脸、不假人感、不换脸漂移，不多指少指、不粘连、不穿模，瞳孔、牙齿与四肢不畸形。
```

### Segment-specific avoid block — always include and customize

```text
【避免】避免主体身份漂移、脸部重绘、食物/包装数量变化、比例跳变、材质塑料化、色彩过饱和、过度锐化、假HDR、漂浮物、重复物体、手部畸形、接触穿模、背景人物复制、镜头瞬移、无原因变焦、焦点抽动、错误文字、错误Logo和水印。再补充本段最可能发生的具体连续性错误。
```

Do not write only “写实”“电影感” or “避免AI感.” The concrete physical and anatomical constraints above are required.

## 6. Standalone prompt schema

Write every Chinese segment prompt in this order:

```text
【生成参数】4–15秒范围内的整数时长、9:16、手机帧率观感、内容类型。
【关键帧约束（最高优先级）】主参考清理图与最多两张辅助清理图的文件名、源时间戳、插入本段时间线的位置、用途、无平台叠字验证、真实品牌文字保留状态和不可改变项。
【固定人物】年龄、脸型、发型、体型、服装、饰品、角色关系；无人时明确“本段无人”。
【完整场景】地点、布局、道具、主色、光线、背景活动。
【动作/口播同步时间线】0.00—X.XX秒的动作、物体运动、表情、当前参考图锚点、对白、口型、声音；需要时注明内部硬切时间；结束于精确生成时长。
【镜头】机位、焦段观感、景别、距离、运动、对焦、曝光、手持幅度。
【声音】说话人、口型校准、环境声、拟音、音乐；精确口播建议后期替换并按同一时间线对齐。
【文字】禁止模型生成平台字幕、价格贴片、账号信息、UI、水印和广告角标；真实品牌/产品字样按清理图保留状态处理，若要求完全可读则列为后期添加项。
【写实基线】粘贴完整基线模块。
【食物写实】画面含食物/饮料/包装时粘贴完整食物模块并按本段细化。
【人物写实】画面含人物/手/皮肤时粘贴完整人物模块并按本段细化。
【避免】粘贴完整避免模块并补充本段特有错误。
```

Never use “人物同上”, “环境同前”, “沿用全局负面词”, or “参考上一段.” A copied segment must work alone.

Every timeline must end on the exact integer generated duration with a meaningful final action or composed product hold. Internal action nodes and source timestamps may use decimals, but the generated/final clip duration may not. Never label any portion as a safe tail or removable footage.

Do not let dialogue float outside the visual timeline. A spoken line without start/end seconds, speaker, mouth/face instruction, and simultaneous visible action is incomplete. A reference image without a generated-timeline insertion point is incomplete.

## 7. Text and audio policy

- Ask Jimeng not to synthesize exact Chinese captions, prices, coupon pages, platform UI, account IDs, or search bars. Generate a clean visual plate and rebuild those elements in post.
- Supply only verified platform-text-free cleaned keyframes to Jimeng. Keep originals for evidence and use ChatGPT-cleaned derivatives as the uploaded references.
- Preserve real-world brand/product text in reference frames by default. If exact readable brand marks must be guaranteed, rebuild them in post rather than relying on the video model.
- Provide exact post-production caption text and time ranges.
- Measure caption styling from frames; do not reuse fixed font parameters from an unrelated video.
- Keep dialogue in the visual prompt for body language and lip motion.
- For an exact replica, replace generated speech with recovered or re-recorded dialogue, then align captions.
- Align recovered/re-recorded dialogue to the same timed action cues used in the prompt. If mouth contact with food makes exact lip sync unreliable, keep the visual performance approximate and flag the line for post-production audio/caption alignment.
- Treat Douyin's moving watermark and creator end slate as platform elements; append them in post or let Douyin generate them.

## 8. Validation checklist

Reject and rewrite a segment prompt if any applicable item is missing:

- one primary source keyframe with timestamp and lock purpose;
- no more than two non-conflicting support keyframes;
- every reference keyframe has a generated-timeline insertion point or interval and is named again in the action timeline at the controlled beat;
- dialogue/口播 lines have start/end seconds, speaker, intended mouth movement, expression, and simultaneous visible action;
- complete photorealistic baseline;
- complete food module when food, drink, ingredients, tableware, or packaging appear;
- complete human module when a face, body, hand, or skin appears;
- concrete segment-specific avoid block;
- explicit quantities and object/person continuity;
- exact generated duration and fully usable ending;
- generated duration and final retained duration are matching integer seconds from 4 through 15;
- every supplied keyframe is visually verified platform-text-free, has a recorded brand-text preservation/removal state, and links to its untouched source timestamp;
- no dependency on another prompt or a global negative prompt.

The final response is incomplete if it contains only analysis, a master prompt, prompts that depend on shorthand, AI-stylized keyframes, platform-text-bearing keyframes, unconfirmed key-part replacement, decimal generated durations, generic “写实” wording, or planned surplus footage.
