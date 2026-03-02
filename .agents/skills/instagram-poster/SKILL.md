---
name: instagram-poster
description: Use when posting content to Instagram. Reads approved post drafts from /Approved/, automates Instagram posting via Playwright with mobile viewport emulation, and saves proof screenshots.
---

# Instagram Auto-Poster Skill

Automate Instagram posting using Playwright browser automation with mobile device emulation.

## When to Use
- When the user says "post to Instagram", "publish Instagram post"
- When approved Instagram drafts appear in `/Approved/`
- When creating visual content with captions for Instagram

## Workflow

### Step 1: Create a Post Draft
Create a file in `/Pending_Approval/` with the `INSTAGRAM_` prefix:

```markdown
# AI_Employee_Vault/Pending_Approval/INSTAGRAM_{topic}_{date}.md
---
type: instagram_post
status: pending_approval
created: {ISO timestamp}
scheduled_for: {optional date}
---

## Instagram Post Draft

{Caption text for the Instagram post}

## Hashtags
#hashtag1 #hashtag2 #hashtag3 #hashtag4 #hashtag5

## Notes
- Image: {path to image or description of image needed}
- Target audience: {description}
- Goal: {engagement/awareness/brand building}
```

### Step 2: Human Approval
The human reviews the draft in Obsidian:
- **Approve**: Move the file from `/Pending_Approval/` to `/Approved/`
- **Reject**: Move the file to `/Rejected/`
- **Edit**: Modify the caption or hashtags before approving

### Step 3: Auto-Post via Playwright
Once the file is in `/Approved/`, run the poster:

```bash
uv run python scripts/facebook_poster.py --vault ./AI_Employee_Vault --platform instagram
```

The script uses mobile viewport emulation (iPhone-style) to access Instagram's mobile interface. It will:
1. Find `INSTAGRAM_*.md` files in `/Approved/`
2. Extract the caption content
3. Open Instagram in mobile-emulated browser
4. Navigate to post creation
5. Complete the posting workflow
6. Take a screenshot as proof → save to `/Done/`
7. Move the draft file to `/Done/` with updated status

### Step 4: Verify
Check `/Done/` for:
- The original draft file (status updated to "posted")
- Screenshot proof: `INSTAGRAM_{topic}_{date}_proof.png`

## First-Time Setup

Instagram shares the Facebook session (same Meta account). Run Facebook login first:

```bash
uv run python scripts/facebook_poster.py --login
```

## Post Content Guidelines
- Instagram captions: up to 2,200 characters
- First line is critical (shown before "more")
- Up to 30 hashtags allowed (5-15 is optimal for reach)
- Use line breaks and emojis for visual appeal
- Instagram is image-first — the caption complements the visual
- Include a call-to-action in the caption

## Important: Image Requirement
Instagram requires an image or video for every post. The automation handles caption/hashtag insertion, but image selection may need manual assistance for the first implementation.

## Safety Features
- **Never auto-posts without human approval** — files must be in `/Approved/`
- Mobile viewport emulation for proper Instagram rendering
- Screenshots saved as proof of every post
- All posting activity logged in `/Logs/`

## Troubleshooting

### "Not logged in"
Instagram uses the Facebook session. Re-run `--login` for Facebook.

### "Create button not found"
Instagram's mobile UI may have changed. Check selectors in `facebook_poster.py`.

## Integration
- Use `hitl-approval` skill for the approval workflow
- Use `social-media-manager` skill for cross-platform strategy
- Facebook and Instagram share the same `facebook_session/` directory
- Scheduler checks for approved posts every 30 minutes
