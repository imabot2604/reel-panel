---
name: reel-panel
description: Send an 11-agent review panel to watch a video (reel, short, ad, film) and rate it - hook, pacing, retention, sound, visuals, story, CTA - each panelist from a different viewer or craft angle, then merge the scores into one ranked fix list. Use when the user asks to rate, review, score, critique or "send agents at" a video, asks if a video is good / boring / slow / viral, or wants hook and retention feedback before posting.
---

# Reel Panel

Eleven panelists watch the same packet in parallel, score independently, then you merge. Independence is the point - panelists never see each other's scores.

## 1. Build the packet

```bash
python3 ~/.claude/skills/reel-panel/scripts/prep.py <video> <out_dir>
```
Put `<out_dir>` in the scratchpad (or next to the video if the user wants to keep it). It writes `PACKET.md`, `stats.md`, `transcript.txt`, `hook.png` (first 3 s at 4 fps) and `sheet_NN.png` (1 frame/s). Check `PACKET.md` exists and glance at `hook.png` yourself before sending anyone.

Also note the **context** the panel needs and can't see in the files: who the video is for, where it will be posted (IG reel, laptop-screen film filmed for a reel, YouTube...), and what it should make the viewer do. Pass this to every panelist.

## 2. Send all 11 at once

One message, 11 `Agent` calls (general-purpose; `model: "sonnet"` is enough), each with the prompt template below and one persona from `references/personas.md`. Never chain them.

Prompt template (fill the brackets):
```
You are [PERSONA NAME] on a video review panel. [PERSONA BRIEF from personas.md]

Context: [who it's for, where it's posted, the goal].
Read [out_dir]/PACKET.md, then Read EVERY file it lists (images too - look at them). Do not edit anything.

Score 1-10 on each: hook (first 3 s), pacing, retention (would you still be watching at 50% and at the end), visuals, sound (voice + music + sfx), story, cta. Use the scale in the rubric: 5 = forgettable, 7 = good enough to post, 9 = would share.
Rubric: [paste references/rubric.md]

Reply with ONLY this JSON, no prose before or after:
{"panelist": "...", "scores": {"hook": n, "pacing": n, "retention": n, "visuals": n, "sound": n, "story": n, "cta": n},
 "would_watch_to_end": true/false, "swipe_away_at": seconds or null,
 "best_moment": {"t": seconds, "why": "..."},
 "worst_moment": {"t": seconds, "why": "..."},
 "top_fixes": [{"fix": "specific change", "t": seconds or null, "impact": "high|med|low"}],
 "one_line_verdict": "..."}
```
Max 3 fixes each. Fixes must be concrete ("cut the 1.2 s silent open, start on the ringing phone") not generic ("make it more engaging").

## 3. Merge

- Parse each JSON (if one is malformed, use what's readable; don't re-run unless more than 2 failed).
- Per category: median and range across the 11. Overall = mean of the 7 medians. Call out categories where the range is 4+ (the panel disagrees - say who and why).
- **Swipe-away curve:** list each `swipe_away_at`, and the share who'd watch to the end. This is the headline number.
- **Fix list:** cluster similar fixes, rank by (how many panelists raised it) x (impact). Keep the timestamp. Top 5-7 only.
- Quote the 2-3 sharpest one-line verdicts (especially the skeptic and the target buyer).

## 4. Report

A short table (category | median | range | panel note), the watch-to-end share, the ranked fix list, the quotes, then your own call: post it, fix and post, or rebuild. Be honest - if the panel says it's boring, lead with that. Offer to apply the top fixes.

Panelists are simulated viewers, not real audience data - say so once, in one line, and don't oversell the scores as predictions.
