#!/usr/bin/env python3
"""Turn a video into a review packet the panel agents can read.

  python3 prep.py <video> <out_dir>

Writes into out_dir:
  hook.png          first 3 s at 4 fps (12 frames, timestamped) - the hook up close
  sheet_NN.png      the whole video at 1 frame/s, 12 frames per sheet, timestamped
  transcript.txt    word-timed transcript (local whisper via hyperframes), one line per phrase
  stats.md          duration, resolution, cut times, cuts/min, longest shot, loudness per second
  PACKET.md         index of the above - the one file each agent starts from
Needs ffmpeg/ffprobe, Pillow, and npx (hyperframes transcribe) for the transcript.
"""
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

video, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
os.makedirs(out, exist_ok=True)
tmp = tempfile.mkdtemp(prefix="reelpanel-")


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


probe = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                         "-of", "json", video]).stdout)
dur = float(probe["format"]["duration"])
vs = next(s for s in probe["streams"] if s["codec_type"] == "video")
W, H = vs["width"], vs["height"]
has_audio = any(s["codec_type"] == "audio" for s in probe["streams"])
try:
    FONT = ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", 22)
except OSError:
    FONT = ImageFont.load_default()

thumb_w = 480 if W >= H else 270
thumb_h = round(thumb_w * H / W)


def grab(t, path):
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1",
         "-vf", f"scale={thumb_w}:{thumb_h}", path])


def sheet(times, path, cols=4):
    rows = math.ceil(len(times) / cols)
    img = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + 30)), (20, 20, 20))
    d = ImageDraw.Draw(img)
    for i, t in enumerate(times):
        p = os.path.join(tmp, f"g{i}.png")
        grab(t, p)
        x, y = (i % cols) * thumb_w, (i // cols) * (thumb_h + 30)
        if os.path.exists(p):
            img.paste(Image.open(p), (x, y + 30))
        d.text((x + 8, y + 4), f"{t:5.2f}s", font=FONT, fill=(205, 245, 100))
    img.save(path)


# hook close-up + full sheets
sheet([i * 0.25 for i in range(12) if i * 0.25 < dur], os.path.join(out, "hook.png"))
times = [t + 0.5 for t in range(int(dur))]
sheets = []
for k in range(0, len(times), 12):
    name = f"sheet_{k // 12 + 1:02d}.png"
    sheet(times[k:k + 12], os.path.join(out, name))
    sheets.append((name, times[k], times[min(k + 11, len(times) - 1)]))

# cuts (scene changes)
# 0.08 catches cuts between shots that share a background colour (0.3 missed most of them);
# hits closer than 0.25 s are one event (a flicker or a glitch), not separate cuts
sc = run(["ffmpeg", "-i", video, "-vf", "select='gt(scene,0.08)',showinfo", "-f", "null", "-"]).stderr
cuts = []
for m in re.findall(r"pts_time:([\d.]+)", sc):
    tc = round(float(m), 2)
    if not cuts or tc - cuts[-1] >= 0.25:
        cuts.append(tc)
shots = [0.0] + cuts + [dur]
longest = max(b - a for a, b in zip(shots, shots[1:]))

# loudness per second
loud = []
if has_audio:
    wav = os.path.join(tmp, "a.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-vn", "-ac", "1", "-ar", "16000", wav])
    import wave
    import struct
    with wave.open(wav) as w:
        n = w.getnframes()
        data = struct.unpack(f"<{n}h", w.readframes(n))
    for s in range(int(dur) + 1):
        chunk = data[s * 16000:(s + 1) * 16000]
        if chunk:
            rms = math.sqrt(sum(x * x for x in chunk) / len(chunk)) / 32768
            loud.append(round(20 * math.log10(rms + 1e-9), 1))

    # transcript
    tdir = os.path.join(tmp, "tr")
    os.makedirs(tdir)
    shutil.copy(wav, os.path.join(tdir, "a.wav"))
    run(["npx", "--yes", "hyperframes", "transcribe", "a.wav", "--json"], cwd=tdir, timeout=600)
    lines = []
    tj = os.path.join(tdir, "transcript.json")
    if os.path.exists(tj):
        d = json.load(open(tj))
        words = d if isinstance(d, list) else d.get("words", [])
        cur, start = [], None
        for wd in words:
            if start is None:
                start = wd["start"]
            cur.append(wd["text"])
            if wd["text"].rstrip().endswith((".", "?", "!", ",")) or len(cur) >= 10:
                lines.append(f"[{start:6.2f}-{wd['end']:6.2f}] {' '.join(cur)}")
                cur, start = [], None
        if cur:
            lines.append(f"[{start:6.2f}-{words[-1]['end']:6.2f}] {' '.join(cur)}")
    first_word = lines[0][1:7].strip() if lines else "n/a"
    open(os.path.join(out, "transcript.txt"), "w").write("\n".join(lines) or "(no speech detected)")
else:
    first_word = "n/a"
    open(os.path.join(out, "transcript.txt"), "w").write("(no audio track)")

with open(os.path.join(out, "stats.md"), "w") as f:
    f.write(f"# Stats\n\n- file: {os.path.basename(video)}\n- duration: {dur:.2f}s\n- resolution: {W}x{H} "
            f"({'landscape' if W > H else 'vertical' if H > W else 'square'})\n- audio: {'yes' if has_audio else 'NO'}\n"
            f"- first spoken word at: {first_word}s\n- cuts detected: {len(cuts)} ({len(cuts) / dur * 60:.1f} per minute)\n"
            f"- cut times: {', '.join(map(str, cuts)) or 'none'}\n- longest unbroken shot: {longest:.2f}s\n")
    if loud:
        f.write("- loudness per second (dBFS, -60 = silence): " + ", ".join(f"{i}s:{v}" for i, v in enumerate(loud)) + "\n")

with open(os.path.join(out, "PACKET.md"), "w") as f:
    f.write(f"# Review packet: {os.path.basename(video)}\n\nRead every file listed here before scoring.\n\n"
            f"- `stats.md` - duration, cuts, pacing, loudness\n- `transcript.txt` - what is said, with timestamps\n"
            f"- `hook.png` - first 3 seconds at 4 fps (12 frames)\n")
    for name, a, b in sheets:
        f.write(f"- `{name}` - frames from {a:.1f}s to {b:.1f}s, one per second\n")
shutil.rmtree(tmp, ignore_errors=True)
print(f"packet ready: {out} ({len(sheets)} sheets, {len(cuts)} cuts, {dur:.1f}s)")
