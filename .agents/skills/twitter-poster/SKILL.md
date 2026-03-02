---
name: twitter-poster
description: Use when posting content to Twitter/X. Reads approved post drafts from /Approved/, automates Twitter posting via Playwright browser automation with 280-character limit enforcement.
---

# Twitter/X Auto-Poster Skill

Automate Twitter/X posting using Playwright browser automation.

## When to Use
- When the user says "post to Twitter", "tweet this", "post to X"
- When approved Twitter drafts appear in `/Approved/`
- When creating and scheduling tweets

## Workflow

### Step 1: Create a Post Draft
Create a file in `/Pending_Approval/` with the `TWITTER_` prefix:

```markdown
# AI_Employee_Vault/Pending_Approval/TWITTER_{topic}_{date}.md
---
type: twitter_post
status: pending_approval
created: {ISO timestamp}
scheduled_for: {optional date}
---

## Twitter Post Draft

{Tweet content — must be under 280 characters}

## Hashtags
#hashtag1 #hashtag2

## Notes
- Character count: {count}/280
- Thread: {yes/no — if yes, add ## Thread sections}
- Target audience: {description}
```

### Step 2: Character Limit Check
**CRITICAL**: Twitter has a strict 280-character limit.
- Before creating the approval file, count the characters
- Include hashtags in the character count
- If over 280 chars, either shorten or split into a thread
- The poster script will warn if content exceeds 280 characters

### Step 3: Human Approval
The human reviews the draft in Obsidian:
- **Approve**: Move the file from `/Pending_Approval/` to `/Approved/`
- **Reject**: Move to `/Rejected/`
- **Edit**: Modify the tweet before approving (check char count!)

### Step 4: Auto-Post via Playwright
Once the file is in `/Approved/`, run the poster:

```bash
uv run python scripts/twitter_poster.py --vault ./AI_Employee_Vault
```

The script will:
1. Find `TWITTER_*.md` files in `/Approved/`
2. Extract tweet content
3. Validate 280-character limit (warn if exceeded)
4. Open Twitter/X in a Playwright browser
5. Compose and submit the tweet
6. Take a screenshot as proof → save to `/Done/`
7. Move the draft file to `/Done/` with updated status

### Step 5: Verify
Check `/Done/` for:
- The original draft file (status updated to "posted")
- Screenshot proof: `TWITTER_{topic}_{date}_proof.png`

## First-Time Setup

Twitter requires a one-time manual login:

```bash
uv run python scripts/twitter_poster.py --login
```

This opens a Chromium browser. Log in to Twitter/X manually. The session is saved in `twitter_session/`.

## Post Content Guidelines
- **280 characters max** (including hashtags, links, mentions)
- URLs count as 23 characters (t.co shortener)
- Front-load the important message
- 1-2 hashtags max (more looks spammy on Twitter)
- Use threads for longer content (split across multiple tweets)
- Emojis can save space and add personality
- Questions and opinions drive engagement

## Safety Features
- **Never auto-posts without human approval** — files must be in `/Approved/`
- 280-character limit enforced with warning
- Screenshots saved as proof of every tweet
- All posting activity logged in `/Logs/`
- Persistent session avoids storing Twitter credentials

## Troubleshooting

### "Browser session expired"
Re-run with `--login` flag to re-authenticate.

### "Character limit exceeded"
The script warns but does not auto-truncate. Edit the draft to fit under 280 characters.

### "Post failed"
Check the screenshot proof. Twitter may have rate-limited or UI may have changed.

## Integration
- Use `hitl-approval` skill for the approval workflow
- Use `social-media-manager` skill for cross-platform strategy
- Use `reasoning-loop` to craft concise tweet content
- Scheduler checks for approved tweets every 30 minutes
