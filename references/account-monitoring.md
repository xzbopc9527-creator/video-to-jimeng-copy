# Douyin account monitoring

Use this workflow to detect new public food-commerce videos and notify for human approval. Never download or analyze a newly detected video automatically.

## Runtime files

Keep runtime data outside the skill directory:

- `accounts.json`: monitored account identities and fetch settings;
- `state.json`: initialized baseline, seen video IDs, and check timestamps.

Use stable `sec_uid` values resolved from account share links. Do not rely on short links as the account identity because share URLs may expire.

## Configuration

```json
{
  "version": 1,
  "mode": "food_commerce",
  "wait_ms": 7000,
  "max_posts": 30,
  "retries": 1,
  "accounts": [
    {
      "nickname": "账号名称",
      "share_url": "https://v.douyin.com/.../",
      "sec_uid": "MS4wLjAB...",
      "author_uid": "123456"
    }
  ],
  "notify": {
    "provider": "feishu",
    "chat_id": "oc_xxx",
    "requires_approval": true
  }
}
```

## Initialize a baseline

The first run must not alert on existing videos:

```powershell
python scripts/monitor_douyin_accounts.py --config "<accounts.json>" --state "<state.json>" --initialize
```

The script records all currently visible video IDs. Sorting uses numeric video IDs rather than page order so pinned old videos cannot become the false “latest” item.

## Check for new videos

```powershell
python scripts/monitor_douyin_accounts.py --config "<accounts.json>" --state "<state.json>"
```

The script marks every newly visible ID as seen, but treats a post as newly published only when its numeric video ID is greater than the account's previous `latest_visible_aweme_id` high-water mark. This prevents older videos that rotate into the profile page from being misreported as new. It emits events only when the caption looks like public food-commerce content. It requires both a food/product signal and a commerce signal such as a price, offer, coupon, package, preorder, new-product launch, or group-buy phrase. Education, school admissions, courses, answer keys, and recruiting are excluded.

Treat rule-based classification as a notification filter, not proof. The user decides whether to analyze.

## Feishu notification

Send only after the user approves the recipient, bot identity, and notification template:

```powershell
python scripts/monitor_douyin_accounts.py --config "<accounts.json>" --state "<state.json>" --notify-feishu --chat-id "oc_xxx"
```

The message contains account name, caption, public link, detection time, and the approval command `分析 <URL>`. Do not start download, transcription, audio extraction, or Jimeng prompt generation until that command is received.

If one account fails to load, preserve its previous state and report the failure. Do not treat a temporarily empty or login-blocked page as account deletion.
