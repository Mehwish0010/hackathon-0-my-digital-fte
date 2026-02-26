---
name: linkedin-poster
description: Use when posting content to LinkedIn. Reads approved post drafts from /Approved/, automates LinkedIn posting via Playwright browser automation, and saves proof screenshots.
---

# LinkedIn Auto-Poster Skill

Automate LinkedIn posting using Playwright browser automation.

## When to Use
- When the user says "post to LinkedIn", "publish LinkedIn post"
- When approved LinkedIn drafts appear in `/Approved/`
- When creating and scheduling LinkedIn content

## Workflow

### Step 1: Create a Post Draft
Create a file in `/Pending_Approval/` with the `LINKEDIN_` prefix:

```markdown
# AI_Employee_Vault/Pending_Approval/LINKEDIN_{topic}_{date}.md
---
type: linkedin_post
status: pending_approval
created: {ISO timestamp}
scheduled_for: {optional date}
---

## LinkedIn Post Draft

{The actual post content to be published on LinkedIn}

## Hashtags
#hashtag1 #hashtag2 #hashtag3

## Notes
- Target audience: {description}
- Goal: {engagement/awareness/lead gen}
```

### Step 2: Human Approval
The human reviews the draft in Obsidian:
- **Approve**: Move the file from `/Pending_Approval/` to `/Approved/`
- **Reject**: Move the file to `/Rejected/` (optionally add rejection notes)
- **Edit**: Modify the content in place before approving

### Step 3: Auto-Post via Playwright
Once the file is in `/Approved/`, run the poster:

```bash
uv run python scripts/linkedin_poster.py --vault ./AI_Employee_Vault
```

The script will:
1. Find `LINKEDIN_*.md` files in `/Approved/`
2. Extract the post content (between `## LinkedIn Post Draft` and `## Hashtags` or `## Notes`)
3. Append hashtags to the post
4. Open LinkedIn in a Playwright browser (persistent session)
5. Navigate to the post composer
6. Paste the content and submit
7. Take a screenshot as proof → save to `/Done/`
8. Move the draft file to `/Done/` with updated status

### Step 4: Verify
Check `/Done/` for:
- The original draft file (status updated to "posted")
- Screenshot proof: `LINKEDIN_{topic}_{date}_proof.png`

## First-Time Setup

LinkedIn requires a one-time manual login to establish a persistent browser session:

```bash
# Launch headed browser for manual LinkedIn login
uv run python scripts/linkedin_poster.py --login
```

This opens a Chromium browser. Log in to LinkedIn manually. The session is saved in `linkedin_session/` for future automated posts.

## Post Content Guidelines
- LinkedIn posts have a ~3000 character limit
- First 2-3 lines are crucial (shown before "see more")
- Include a call-to-action
- Use line breaks for readability
- 3-5 hashtags recommended

## Safety Features
- **Never auto-posts without human approval** — files must be in `/Approved/`
- Screenshots saved as proof of every post
- All posting activity logged in `/Logs/`
- Persistent browser session avoids storing LinkedIn credentials

## Troubleshooting

### "Browser session expired"
Re-run with `--login` flag to re-authenticate manually.

### "Element not found on LinkedIn"
LinkedIn may have updated their UI. Check selectors in `linkedin_poster.py` and update if needed.

### "Post failed"
Check the screenshot in `/Done/` — it captures the state at time of failure. Review and retry manually if needed.

## Integration
- Use `hitl-approval` skill for the approval workflow
- Use `reasoning-loop` to generate post content from business goals
- Scheduler can trigger daily posting checks
