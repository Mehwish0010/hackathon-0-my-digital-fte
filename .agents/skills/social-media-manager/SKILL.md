---
name: social-media-manager
description: Use for cross-platform social media strategy. Manages content across LinkedIn, Facebook, Instagram, and Twitter with platform-specific adaptation, scheduling, and engagement tracking.
---

# Social Media Manager Skill

Cross-platform social media strategy and management. Coordinates content across LinkedIn, Facebook, Instagram, and Twitter/X.

## When to Use
- When the user says "create a social media post", "post across all platforms"
- When planning a cross-platform content strategy
- When the user says "social media update", "cross-post this"
- When reviewing social media engagement or metrics
- When creating content that should be adapted for multiple platforms

## Workflow

### Step 1: Content Strategy
Before creating posts, consider the platform differences:

| Platform | Character Limit | Tone | Best For | Hashtags |
|----------|----------------|------|----------|----------|
| LinkedIn | ~3,000 | Professional | B2B, thought leadership | 3-5 |
| Facebook | ~63,000 | Casual/engaging | Community, long-form | 2-5 |
| Instagram | 2,200 (caption) | Visual/lifestyle | Brand, visual stories | 5-15 |
| Twitter/X | 280 | Concise/punchy | News, hot takes, threads | 1-2 |

### Step 2: Create Platform-Adapted Drafts
Use the Social Media MCP Server for cross-posting:

```
Use the cross_post MCP tool with:
- content: {the core message}
- platforms: ["linkedin", "facebook", "instagram", "twitter"]
```

This automatically:
- Creates full-length version for LinkedIn and Facebook
- Adapts caption for Instagram
- Truncates to 280 chars for Twitter (with warning if content is cut)
- Creates separate `{PLATFORM}_*.md` files in `/Pending_Approval/`

Or create individual drafts manually using platform-specific skills:
- `facebook-poster` skill for Facebook
- `instagram-poster` skill for Instagram
- `twitter-poster` skill for Twitter/X
- `linkedin-poster` skill for LinkedIn

### Step 3: Human Review
All drafts go to `/Pending_Approval/` for human review:
- Review each platform's version for tone and length
- Approve by moving to `/Approved/`
- Edit platform-specific versions as needed

### Step 4: Automated Posting
The scheduler or manual triggers post approved content:

```bash
# Post to all platforms
uv run python scripts/facebook_poster.py --platform both     # Facebook + Instagram
uv run python scripts/twitter_poster.py                       # Twitter/X
uv run python scripts/linkedin_poster.py                      # LinkedIn
```

### Step 5: Track Engagement
After posting, use the social media summarizer:

```bash
uv run python scripts/social_media_summarizer.py --vault ./AI_Employee_Vault
```

This generates a summary in `/Briefings/social_summary_{date}.md` with engagement metrics from each platform.

## Cross-Platform Content Adaptation Rules

### From long-form to Twitter
1. Extract the core message (1 sentence)
2. Add a hook or question
3. Keep under 280 chars including hashtags
4. Link to the full post if needed

### From text to Instagram
1. Lead with the most visual/emotional line
2. Use line breaks and emojis for readability
3. Put hashtags at the end (or in first comment)
4. Note: Instagram requires an image

### Timing Strategy
| Platform | Best Times | Frequency |
|----------|-----------|-----------|
| LinkedIn | Tue-Thu 8-10 AM | 2-3x/week |
| Facebook | Wed-Fri 1-4 PM | 3-5x/week |
| Instagram | Mon-Fri 11 AM-1 PM | 3-7x/week |
| Twitter/X | Mon-Fri 8 AM-4 PM | 1-5x/day |

## MCP Tools Available

| Tool | Purpose |
|------|---------|
| `create_social_post_draft` | Create a draft for one platform |
| `list_pending_social_posts` | See all pending social posts |
| `get_social_post_status` | Check status of a specific post |
| `cross_post` | Create adapted drafts for multiple platforms |

## Important Notes
- **All posts require human approval** — nothing goes live automatically
- Each platform has its own poster script and browser session
- LinkedIn uses `linkedin_session/`, Facebook/Instagram use `facebook_session/`, Twitter uses `twitter_session/`
- Content should feel native to each platform, not copy-pasted
- Check Business_Goals.md for brand voice and content strategy alignment
- Social media summary feeds into the weekly CEO Briefing

## Integration
- `hitl-approval` — all posts need approval
- `ceo-briefing` — social metrics included in weekly briefing
- `reasoning-loop` — use for content generation from business goals
- Scheduler runs posting checks every 30 minutes
