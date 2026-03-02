---
name: facebook-poster
description: Use when posting content to Facebook. Reads approved post drafts from /Approved/, automates Facebook posting via Playwright browser automation, and saves proof screenshots.
---

# Facebook Auto-Poster Skill

Automate Facebook posting using Playwright browser automation.

## When to Use
- When the user says "post to Facebook", "publish Facebook post"
- When approved Facebook drafts appear in `/Approved/`
- When creating and scheduling Facebook content

## Workflow

### Step 1: Create a Post Draft
Create a file in `/Pending_Approval/` with the `FACEBOOK_` prefix:

```markdown
# AI_Employee_Vault/Pending_Approval/FACEBOOK_{topic}_{date}.md
---
type: facebook_post
status: pending_approval
created: {ISO timestamp}
scheduled_for: {optional date}
---

## Facebook Post Draft

{The actual post content to be published on Facebook}

## Hashtags
#hashtag1 #hashtag2 #hashtag3

## Notes
- Target audience: {description}
- Goal: {engagement/awareness/community building}
```

### Step 2: Human Approval
The human reviews the draft in Obsidian:
- **Approve**: Move the file from `/Pending_Approval/` to `/Approved/`
- **Reject**: Move the file to `/Rejected/` (optionally add rejection notes)
- **Edit**: Modify the content in place before approving

### Step 3: Auto-Post via Playwright
Once the file is in `/Approved/`, run the poster:

```bash
uv run python scripts/facebook_poster.py --vault ./AI_Employee_Vault --platform facebook
```

The script will:
1. Find `FACEBOOK_*.md` files in `/Approved/`
2. Extract the post content (between `## Facebook Post Draft` and next `##`)
3. Append hashtags to the post
4. Open Facebook in a Playwright browser (persistent session)
5. Navigate to the post composer
6. Paste the content and submit
7. Take a screenshot as proof → save to `/Done/`
8. Move the draft file to `/Done/` with updated status

### Step 4: Verify
Check `/Done/` for:
- The original draft file (status updated to "posted")
- Screenshot proof: `FACEBOOK_{topic}_{date}_proof.png`

## First-Time Setup

Facebook requires a one-time manual login to establish a persistent browser session:

```bash
# Launch headed browser for manual Facebook login
uv run python scripts/facebook_poster.py --login
```

This opens a Chromium browser. Log in to Facebook manually. The session is saved in `facebook_session/` for future automated posts.

## Post Content Guidelines
- Facebook posts have a ~63,206 character limit (but keep it concise)
- First 2-3 lines are shown before "See more"
- Include engaging questions or calls-to-action
- Use line breaks for readability
- 2-5 hashtags recommended (fewer than LinkedIn)
- Emojis can boost engagement on Facebook

## Safety Features
- **Never auto-posts without human approval** — files must be in `/Approved/`
- Screenshots saved as proof of every post
- All posting activity logged in `/Logs/`
- Persistent browser session avoids storing Facebook credentials

## Troubleshooting

### "Browser session expired"
Re-run with `--login` flag to re-authenticate manually.

### "Element not found on Facebook"
Facebook may have updated their UI. Check selectors in `facebook_poster.py` and update if needed.

### "Post failed"
Check the screenshot in `/Done/` — it captures the state at time of failure. Review and retry manually if needed.

## Integration
- Use `hitl-approval` skill for the approval workflow
- Use `social-media-manager` skill for cross-platform strategy
- Use `reasoning-loop` to generate post content from business goals
- Scheduler checks for approved posts every 30 minutes
