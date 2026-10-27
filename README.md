# reel-panel

**Get 11 brutally honest viewers to watch your reel before the internet does.**

`reel-panel` is a [Claude Code](https://claude.com/claude-code) skill. Point it at any short video and it convenes a simulated review panel: 11 AI personas watch the same frames, transcript and audio stats **in parallel and independently**, score it, and Claude merges the results into one report: a swipe-away curve, a ranked fix list with timestamps, and an honest post / fix / rebuild call.

> Panelists are simulated viewers, not real audience data. Use it to catch problems early, not to predict views.

## What you get

- **Watch-to-end share**: how many of the 11 would still be watching at the last frame, and the second each of the rest would swipe.
- **Scores for 7 categories**: hook, pacing, retention, visuals, sound, story, CTA (median + range, with disagreements called out).
- **Ranked fixes**: clustered across panelists and ordered by how many raised them times impact. Concrete ("cut the 1.2 s silent open, start on the ringing phone"), never generic.
- **The sharpest verdicts**, including the Skeptic's and the target buyer's.
- **A straight recommendation**: post it, fix and post, or rebuild.

## The panel

| # | Panelist | Judges |
|---|---|---|
| 1 | Hook Specialist | Seconds 0-3: would it stop a thumb? |
| 2 | Retention Editor | Dead air, cuts per minute, where attention drops |
| 3 | Scroll-happy Gen Z viewer | The 1.5 s swipe decision, in their own words |
| 4 | Target Buyer | Do I believe it, would I message them? |
| 5 | Sound Designer | Voice, music, SFX, mix, loudness numbers |
| 6 | Motion Designer | Camera, easing, character appeal, variety |
| 7 | Copywriter | Every script line; rewrites the weakest |
| 8 | Instagram Algorithm Analyst | Rewatch, share, loop, format fit |
| 9 | Brand Strategist | Premium vs. template, ownable brand |
| 10 | Conversion / CTA Reviewer | Is the ask clear, earned, readable |
| 11 | The Skeptic | Says what everyone else is too polite to |

Panelists never see each other's scores, so independence is preserved.

## How it works

1. `scripts/prep.py` turns your video into a packet: a 4 fps hook strip of the first 3 s, a 1 fps timestamped contact sheet, a word-timed transcript, and `stats.md` (duration, cut times, cuts/min, longest shot, per-second loudness).
2. Claude launches all 11 panelists in one parallel batch, each reading the packet and returning strict JSON.
3. Claude merges: medians, ranges, swipe-away curve, clustered fixes, final call.

## Install

```bash
git clone https://github.com/imabot2604/reel-panel ~/.claude/skills/reel-panel
```

Needs `ffmpeg`/`ffprobe`, Python with `Pillow`, and `npx` (for local Whisper transcription via [HyperFrames](https://github.com/heygen-com/hyperframes)).

## Use

In Claude Code:

```
/reel-panel path/to/video.mp4
```

Tell it who the video is for, where it'll be posted, and what it should make people do. The panel can't see that from the files.

## Customize

- Swap personas in [`references/personas.md`](references/personas.md): make them your actual audience.
- Tune the scoring anchors in [`references/rubric.md`](references/rubric.md).

## License

MIT
