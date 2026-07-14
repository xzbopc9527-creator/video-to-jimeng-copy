# Douyin to Jimeng Copy

这是一个 Codex skill，用来把抖音餐饮/带货短视频拆解成可复刻的即梦提示词工作流。它不只生成“风格提示词”，而是围绕视频证据做完整拆解：下载/解析视频、提取整段音频、确认镜头切点、清理关键帧文字水印、把参考图插入时间线，并输出可直接复制到即梦的分段写实提示词。

## 适合做什么

- 解析抖音分享链接、完整分享文案、本地视频或视频文件夹。
- 下载并检查视频素材，生成 `analysis.json`、contact sheet 和关键元数据。
- 提取整段音频为 M4A/MP3，并验证时长、编码、采样率和文件大小。
- 按镜头和语义重新设计 4–15 秒整数时长的即梦生成片段。
- 清理关键帧中的平台字幕、账号、UI、水印和广告角标，同时默认保留真实世界里的品牌/产品文字。
- 在每段提示词中把参考图插入到具体时间线，锁定开场、手部接触、食物特写、口型表情和结束姿势。
- 将口播、口型、人物动作、食物动作、镜头运动和声音放在同一条时间线上，避免画面和对白脱节。
- 监控公开抖音账号的新餐饮带货视频：发现新视频后先通知，收到人工确认后再分析。
- 按分镜需求收集公开小红书参考图素材，并保留来源清单。

## 输入类型

skill 会自动识别以下输入：

| 输入 | 行为 |
|---|---|
| 抖音分享链接 | 解析并下载单条远程视频 |
| 抖音/聊天分享全文 | 提取其中第一个支持的抖音 URL |
| 本地 `.mp4` | 直接分析本地视频 |
| 本地 `.mov` | 直接分析本地视频 |
| 本地 `.avi` | 直接分析本地视频 |
| 视频文件夹 | 递归分析其中的 MP4/MOV/AVI |

## 安装到 Codex

把本仓库放到 Codex skills 目录下即可。仓库根目录本身就是一个 skill。

```powershell
git clone https://github.com/xzbopc9527-creator/video-to-jimeng-copy.git "$env:USERPROFILE\.codex\skills\douyin-to-jimeng"
```

如果你已经有本地目录，可以直接拉取更新：

```powershell
cd "$env:USERPROFILE\.codex\skills\douyin-to-jimeng"
git pull
```

安装后，在 Codex 中用类似下面的请求触发：

```text
使用 $douyin-to-jimeng 解析这条抖音视频：<抖音分享链接或分享全文>
```

## 依赖

基础视频分析建议安装：

```powershell
pip install playwright
python -m playwright install chromium
```

并确保系统可调用 `ffmpeg` 和 `ffprobe`。

可选依赖：

```powershell
pip install faster-whisper
pip install opencv-python numpy easyocr
pip install pillow playwright
```

- `faster-whisper`：用于口播草稿转写。
- `opencv-python numpy easyocr`：用于关键帧文字候选区域检测和修补。
- `pillow playwright`：用于小红书公开参考图收集和联系表生成。

## 常用命令

分析视频并生成元数据：

```powershell
python scripts/analyze_douyin.py "<抖音链接、分享全文、本地视频或文件夹>" --out "<analysis directory>" --transcribe
```

提取整段音频：

```powershell
python scripts/analyze_douyin.py "<输入>" --out "<analysis directory>" --extract-audio
```

只导出 M4A 或 MP3：

```powershell
python scripts/analyze_douyin.py "<输入>" --out "<analysis directory>" --extract-audio m4a
python scripts/analyze_douyin.py "<输入>" --out "<analysis directory>" --extract-audio mp3 --mp3-bitrate 192k
```

清理关键帧文字候选区域：

```powershell
python scripts/clean_keyframes.py "<关键帧图片或文件夹>" --out "<clean-keyframes directory>"
```

手动指定需要清理的框：

```powershell
python scripts/clean_keyframes.py "<frame.png>" --out "<output>" --skip-ocr --box "x1,y1,x2,y2"
```

初始化账号监控基线：

```powershell
python scripts/monitor_douyin_accounts.py --config "<accounts.json>" --state "<state.json>" --initialize
```

后续检查新视频：

```powershell
python scripts/monitor_douyin_accounts.py --config "<accounts.json>" --state "<state.json>"
```

发送飞书通知时：

```powershell
python scripts/monitor_douyin_accounts.py --config "<accounts.json>" --state "<state.json>" --notify-feishu --chat-id "<oc_xxx>"
```

收集小红书参考图：

```powershell
python scripts/collect_xhs_refs.py --requirements "<requirements.json>" --output "<asset directory>" --headful
```

## 输出规范

最终交付应包含：

1. 视频事实核验：时长、比例、帧率、镜头数、人物、食物、场景、对白、字幕和声音。
2. 零浪费生成表：每段源视频参考区间、整数生成时长、最终保留时长、最终时间线、`0秒` trim。
3. 参考图计划：每段一张主参考图、最多两张辅助参考图，且每张都必须有源视频时间戳、清理图路径和插入到生成时间线的位置。
4. 动作/口播同步时间线：逐秒写明人物动作、食物动作、镜头、当前参考图锚点、口播、口型和声音。
5. 每段一个独立可复制的中文即梦提示词代码块。
6. 如用户要求，附完整 M4A/MP3 音频文件路径和验证信息。
7. 后期说明：字幕、价格贴片、UI、水印、Logo、平台结尾卡、精确口播替换等。

## 关键约束

- 即梦片段时长只能使用整数秒：`4` 到 `15` 秒。
- 每段生成时长必须等于最终保留时长，不做可裁剪安全尾巴。
- 参考图是“真实主体与空间关系约束”，不是风格迁移输入。
- 关键帧上传给即梦前必须去除平台文字、水印、UI、账号和广告角标。
- 默认保留真实世界中的品牌/产品文字、包装标识、门店招牌和菜单板；需要删除时必须由用户明确要求。
- 如需替换手、脸、身体、服装、产品或道具，必须先获得用户确认，不能悄悄替换。
- 口播必须绑定到动作时间线；精确声音建议后期用原音或重录音轨替换。
- 提示词必须包含完整写实基线；有人物时加入人物写实约束，有食物/饮料/包装时加入食物写实约束。

## 目录结构

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── account-monitoring.md
│   ├── keyframe-cleaning.md
│   ├── output-contract.md
│   └── xhs-reference-images.md
└── scripts/
    ├── analyze_douyin.py
    ├── clean_keyframes.py
    ├── collect_xhs_refs.py
    └── monitor_douyin_accounts.py
```

## 注意事项

- 抖音页面结构可能变化，远程解析失败时优先使用本地视频文件。
- ASR 转写只能作为草稿，正式口播需要结合画面字幕和听辨核对。
- 自动去字/修补关键帧需要人工复核；如果平台文字覆盖人物、食物或品牌细节，优先选择相邻干净帧。
- 第三方图片和视频素材的版权仍归原作者所有，本项目仅用于分析和复刻提示词准备。
