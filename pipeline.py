#!/usr/bin/env python3
"""
Free History Video Pipeline — v2 (adapted from the finance v1)
===============================================================
Builds ONE finished vertical history video per run, 100% on free services,
for the channel "The Money Guide" (YouTube, TikTok, Facebook — same video
on all three, posted by the channel owner).

  1. Topic   : first unused topic from topics.md (usage logged in used_topics.json)
  2. Script  : Google Gemini free API when GEMINI_API_KEY is set,
               otherwise a built-in template fallback (no key needed).
               The key comes ONLY from the GitHub Actions secret
               GEMINI_API_KEY — it is never written into any file.
  3. Voice   : edge-tts (free Microsoft voices) — voice en-US-ChristopherNeural.
               Set TTS_BACKEND=house ONLY for local demo runs on a machine that
               has the /opt/hatch/bin/tts tool; never used in production.
  4. Images  : Pollinations free image API (https://image.pollinations.ai),
               one image per scene. Falls back to a generated gradient still
               if the download fails, so a run never dies on images.
  5. Music   : a fresh, quiet, original music bed synthesized locally
               (pure Python stdlib — no files, no licences, no cost).
  6. Assembly: ffmpeg — vertical 1080x1920, slow zoompan per scene,
               explicit stream mapping (-map 0:v:0 -map 1:a:0),
               no alimiter, no -shortest.
  7. Output  : a posting pack folder with the MP4 + title.txt +
               description.txt + hashtags.txt + script.txt.

Usage:
  python3 pipeline.py                      # today's topic, default output dir
  python3 pipeline.py --topic "Some Title" # force a topic
  python3 pipeline.py --out some/folder    # choose the posting-pack folder
  python3 pipeline.py --slug my_video      # choose the MP4 file-name slug

Environment:
  GEMINI_API_KEY   optional — enables AI-written scripts (free tier key).
  HISTORY_TTS_VOICE  optional — edge-tts voice name (default below).
  TTS_BACKEND      "edge" (default, production) or "house" (local demo only).
"""

import argparse
import asyncio
import json
import math
import os
import re
import struct
import subprocess
import sys
import urllib.parse
import urllib.request
import wave
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
TOPICS_FILE = os.path.join(HERE, "topics.md")
USED_FILE = os.path.join(HERE, "used_topics.json")

DEFAULT_VOICE = os.environ.get("HISTORY_TTS_VOICE", "en-US-ChristopherNeural")
FPS = 30
SCENE_PAUSE = 0.4          # seconds of breathing room after each scene's voice
WIDTH, HEIGHT = 1080, 1920

# ---------------------------------------------------------------- topics ----

def load_topics():
    topics = []
    with open(TOPICS_FILE, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\s*\d+\.\s+(.+?)\s*$", line)
            if m:
                topics.append(m.group(1))
    return topics


def load_used():
    if os.path.exists(USED_FILE):
        with open(USED_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_used(used):
    with open(USED_FILE, "w", encoding="utf-8") as f:
        json.dump(used, f, indent=2, ensure_ascii=False)


def pick_topic(forced=None):
    topics = load_topics()
    if not topics:
        raise SystemExit("topics.md has no topics")
    if forced:
        return forced
    used = load_used()
    for t in topics:
        if t not in used:
            return t
    # everything used once -> start a fresh cycle
    save_used([])
    return topics[0]


def mark_used(topic):
    used = load_used()
    if topic not in used:
        used.append(topic)
        save_used(used)


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:48] or "history_video"

# ---------------------------------------------------------------- script ----

GENERIC_BEATS = [
    ("hook",
     "Nobody believed it could happen — but it did. This is the story of "
     "{topic}, and the ending will surprise you. Give me ninety seconds."),
    ("what",
     "So what actually happened? {topic} — let me set the scene in plain "
     "words, without the boring textbook version."),
    ("world",
     "To understand it, you have to see the world of that time. Life was "
     "very different back then — and one small decision was about to change "
     "everything."),
    ("moment1",
     "Then came the turning point. {topic_short} reached a moment where "
     "there was no going back — and the people involved had no idea how big "
     "it would become."),
    ("moment2",
     "What happened next is the part most people never hear. While everyone "
     "remembers the ending, the middle of the story is where history was "
     "really made."),
    ("myth",
     "But here is what most people get wrong about {topic_short}. The "
     "popular version skips the truth — and the real story is far more "
     "interesting."),
    ("legacy",
     "Why does it still matter today? Because {topic_short} shaped the "
     "world we live in — in ways you can still see around you right now."),
    ("close",
     "So here is the question history leaves us with: what would you have "
     "done in their place? Tell me in the comments — and remember, the past "
     "is never as simple as it looks."),
]

GENERIC_IMAGES = {
    "hook": "ancient stone monument under a dramatic sky, mysterious atmosphere, photorealistic, vertical portrait, no text",
    "what": "old parchment map and ancient artifacts on a wooden table, warm candlelight, photorealistic, vertical portrait, no text",
    "world": "historic street scene from centuries ago, people in period clothing, daily life, photorealistic, vertical portrait, no text",
    "moment1": "dramatic historic turning point scene, crowd gathered before a grand old building, golden hour light, photorealistic, vertical portrait, no text",
    "moment2": "explorer studying ancient ruins by torchlight, discovery mood, photorealistic, vertical portrait, no text",
    "myth": "museum hall with ancient artifacts in glass cases, truth versus legend atmosphere, photorealistic, vertical portrait, no text",
    "legacy": "modern city street with an ancient monument visible in the background, past meeting present, photorealistic, vertical portrait, no text",
    "close": "sunset over ancient ruins, thoughtful peaceful mood, photorealistic, vertical portrait, no text",
}


def template_script(topic):
    short = re.sub(r"^(How to|How|What Is|Why|The|Who)\s+", "", topic, flags=re.I)
    short = short.split(":")[0].strip()
    scenes = []
    for beat, text in GENERIC_BEATS:
        scenes.append({
            "narration": text.format(topic=topic, topic_short=short),
            "image": GENERIC_IMAGES[beat],
        })
    return {
        "title": topic + " 🏛️",
        "description": (
            f"{topic} — explained in simple words, with the story behind the history.\n\n"
            "Tell us in the comments: what would you have done in their place?"
        ),
        "hashtags": ["#History", "#WorldHistory", "#HistoryFacts",
                     "#LearnHistory", "#AncientHistory"],
        "scenes": scenes,
    }


def gemini_script(topic, api_key):
    """Ask the Gemini free API for an 8-scene script as JSON. Raises on failure."""
    prompt = (
        "You write short vertical history videos. Topic: " + topic + "\n"
        "Reply with ONLY a JSON object, no markdown, with keys:\n"
        '  "title": video title (max 70 chars, one history emoji at the end),\n'
        '  "description": 2-3 short lines, then a blank line, then a question for the comments,\n'
        '  "hashtags": array of 5-6 hashtags,\n'
        '  "scenes": array of exactly 8 objects {"narration": ..., "image": ...}.\n'
        "Rules: scene 1 narration is a strong HOOK (first 3 seconds). Each narration is "
        "25-35 spoken words, warm and clear, simple English. Last scene ends with a question "
        "to the comments. Each image is a photorealistic vertical photo prompt about the "
        "historical scene, ending with ', vertical portrait, no text'. "
        "Stick to widely accepted historical facts. Never invent dates, names or quotes. "
        "When a detail is uncertain or legendary, say so in the narration "
        "(for example, 'legend says')."
    )
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8, "responseMimeType": "application/json"},
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.0-flash:generateContent",
        data=body, method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    script = json.loads(text)
    assert len(script["scenes"]) == 8
    script["description"] = script["description"].rstrip()
    return script


def make_script(topic):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        try:
            print("[script] GEMINI_API_KEY found — asking Gemini free API...")
            s = gemini_script(topic, key)
            print("[script] Gemini script OK")
            return s
        except Exception as e:
            print(f"[script] Gemini failed ({e}); using template fallback")
    else:
        print("[script] no GEMINI_API_KEY — using template fallback")
    return template_script(topic)

# ------------------------------------------------------------------ voice ----

async def _edge_tts_async(text, voice, out_path):
    import edge_tts  # pip package: edge-tts (free)
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)


def tts_edge(text, out_path, voice):
    asyncio.run(_edge_tts_async(text, voice, out_path))


def tts_house(text, out_path):
    """LOCAL DEMO ONLY — uses the /opt/hatch/bin/tts CLI if present."""
    p = subprocess.run(
        ["/opt/hatch/bin/tts", "speak", "--voice", "avocado_v2:rumi",
         "--language", "en", "--speed", "126", "--format", "mp3",
         "--text-stdin", "--output", out_path],
        input=text, capture_output=True, text=True, timeout=300)
    if p.returncode != 0:
        raise RuntimeError("house tts failed: " + (p.stderr or "")[-500:])


def make_voiceover(scenes, workdir, voice):
    backend = os.environ.get("TTS_BACKEND", "edge").lower()
    paths = []
    for i, sc in enumerate(scenes, 1):
        out = os.path.join(workdir, f"vo_{i:02d}.mp3")
        if backend == "house":
            tts_house(sc["narration"], out)
        else:
            tts_edge(sc["narration"], out, voice)
        paths.append(out)
        print(f"[voice] scene {i}/{len(scenes)} done ({backend})")
    return paths

# ----------------------------------------------------------------- images ----

def download_image(prompt, seed, out_path):
    url = ("https://image.pollinations.ai/prompt/"
           + urllib.parse.quote(prompt)
           + f"?width=1080&height=1920&seed={seed}&nologo=true")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
    if len(data) < 5000:
        raise RuntimeError("image too small / not an image")
    with open(out_path, "wb") as f:
        f.write(data)


def gradient_image(out_path, seed):
    """Fallback still: a calm vertical gradient made locally with ffmpeg."""
    colors = [("0x1d4ed8", "0x0ea5e9"), ("0x065f46", "0x10b981"),
              ("0x7c2d12", "0xf59e0b"), ("0x312e81", "0x6366f1")]
    top, bottom = colors[seed % len(colors)]
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", f"gradients=s=1080x1920:c0={top}:c1={bottom}:nb_colors=2:"
               "x0=0:y0=0:x1=0:y1=1920",
         "-frames:v", "1", out_path], check=True)


def make_images(scenes, workdir, base_seed):
    paths = []
    for i, sc in enumerate(scenes, 1):
        out = os.path.join(workdir, f"img_{i:02d}.jpg")
        try:
            download_image(sc["image"], base_seed + i, out)
            print(f"[image] scene {i}/{len(scenes)} downloaded (Pollinations)")
        except Exception as e:
            print(f"[image] scene {i} download failed ({e}); gradient fallback")
            gradient_image(out, base_seed + i)
        paths.append(out)
    return paths

# ------------------------------------------------------------------ music ----

def synth_music(path, total_seconds):
    """Fresh, quiet, original music bed — pure stdlib synthesis.
    A slow I–V–vi–IV pad in C major with a soft pentatonic pluck line."""
    sr = 44100
    n = int(total_seconds * sr)
    chords = [  # (root freq, [chord freqs]) — C, G, Am, F
        (130.81, [261.63, 329.63, 392.00]),
        (98.00,  [246.94, 293.66, 392.00]),
        (110.00, [261.63, 329.63, 440.00]),
        (87.31,  [220.00, 349.23, 440.00]),
    ]
    bar = 4.0  # seconds per chord
    penta = [523.25, 587.33, 659.25, 783.99, 880.00, 783.99, 659.25, 587.33]
    samples = [0.0] * n
    for i in range(n):
        t = i / sr
        ci = int(t // bar) % len(chords)
        root, tones = chords[ci]
        ct = t - int(t // bar) * bar
        env = min(1.0, ct / 0.8) * min(1.0, max(0.0, (bar - ct) / 0.8))
        v = 0.05 * math.sin(2 * math.pi * root * t)
        for f in tones:
            v += 0.035 * math.sin(2 * math.pi * f * t)
            v += 0.012 * math.sin(2 * math.pi * f * 2 * t)
        # gentle pluck melody: one soft note every 2 seconds
        step = int(t // 2.0)
        lt = t - step * 2.0
        if lt < 1.2:
            f = penta[step % len(penta)]
            v += 0.05 * math.sin(2 * math.pi * f * t) * math.exp(-3.0 * lt)
        samples[i] = v * env
    # overall fade in/out
    fade = int(1.5 * sr)
    for i in range(min(fade, n)):
        samples[i] *= i / fade
        samples[n - 1 - i] *= i / fade
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        frames = b"".join(
            struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767 * 0.9))
            for s in samples)
        w.writeframes(frames)

# --------------------------------------------------------------- assembly ----

def ffprobe_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("command failed: " + " ".join(cmd[:3]) +
                           " ...\n" + (p.stderr or "")[-1200:])
    return p


def assemble(images, vo_paths, workdir, final_video):
    # per-scene: video segment (zoompan) + padded voice segment
    seg_videos, seg_audios, durations = [], [], []
    for i, (img, vo) in enumerate(zip(images, vo_paths), 1):
        vo_dur = ffprobe_duration(vo)
        seg_dur = vo_dur + SCENE_PAUSE
        frames = max(1, round(seg_dur * FPS))
        durations.append(seg_dur)
        vout = os.path.join(workdir, f"seg_{i:02d}.mp4")
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS),
             "-i", img,
             "-filter_complex",
             # crop the bottom 7% strip first: the free Pollinations tier
             # stamps a tiny corner attribution there; trimming it keeps the
             # frame clean (the slow zoom hides the small crop completely).
             f"[0:v]crop=iw:ih*0.93:0:0,"
             f"scale=2160:3840:force_original_aspect_ratio=increase,"
             f"crop=2160:3840,"
             f"zoompan=z='1+0.12*on/{frames}':x='iw/2-(iw/zoom/2)':"
             f"y='ih/2-(ih/zoom/2)':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},"
             f"format=yuv420p[v]",
             "-map", "[v]", "-t", f"{seg_dur:.2f}",
             "-c:v", "libx264", "-preset", "medium", "-crf", "20", vout])
        seg_videos.append(vout)
        aout = os.path.join(workdir, f"aud_{i:02d}.wav")
        run(["ffmpeg", "-y", "-v", "error", "-i", vo,
             "-af", f"apad,atrim=0:{seg_dur:.2f}",
             "-ar", "44100", "-ac", "1", aout])
        seg_audios.append(aout)
        print(f"[build] scene {i}: {seg_dur:.1f}s")

    total = sum(durations)

    # join all scene videos (video only)
    vlist = os.path.join(workdir, "vlist.txt")
    with open(vlist, "w") as f:
        for v in seg_videos:
            f.write(f"file '{v}'\n")
    joined_video = os.path.join(workdir, "joined_video.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", vlist, "-c", "copy", joined_video])

    # join all scene voice segments
    alist = os.path.join(workdir, "alist.txt")
    with open(alist, "w") as f:
        for a in seg_audios:
            f.write(f"file '{a}'\n")
    vo_full = os.path.join(workdir, "voice_full.wav")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", alist, "-c", "copy", vo_full])

    # fresh quiet music bed, mixed under the loud voice
    music = os.path.join(workdir, "music.wav")
    synth_music(music, total)
    final_audio = os.path.join(workdir, "final_audio.wav")
    run(["ffmpeg", "-y", "-v", "error", "-i", vo_full, "-i", music,
         "-filter_complex",
         "[1:a]volume=0.22[m];[0:a][m]amix=inputs=2:duration=first:"
         "normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
         "-map", "[a]", final_audio])

    # final mux — explicit stream mapping, no -shortest, no alimiter
    run(["ffmpeg", "-y", "-v", "error", "-i", joined_video, "-i", final_audio,
         "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", final_video])
    return total, vo_full

# -------------------------------------------------------------------- main ----

def main():
    ap = argparse.ArgumentParser(description="Free history video pipeline")
    ap.add_argument("--topic", default=None, help="force a topic title")
    ap.add_argument("--out", default=None, help="posting-pack output folder")
    ap.add_argument("--slug", default=None, help="MP4 file-name slug")
    args = ap.parse_args()

    topic = pick_topic(args.topic)
    slug = args.slug or slugify(topic)
    outdir = args.out or os.path.join(
        HERE, "output", f"{date.today().isoformat()}_{slug}")
    os.makedirs(outdir, exist_ok=True)
    workdir = os.path.join(outdir, "_work")
    os.makedirs(workdir, exist_ok=True)

    print(f"[topic] {topic}")
    script = make_script(topic)
    scenes = script["scenes"]
    print(f"[script] {len(scenes)} scenes, title: {script['title']}")

    voice = DEFAULT_VOICE
    vo_paths = make_voiceover(scenes, workdir, voice)
    import zlib
    base_seed = zlib.crc32(topic.encode("utf-8")) % 9000 + 100
    images = make_images(scenes, workdir, base_seed=base_seed)

    final_video = os.path.join(outdir, slug + ".mp4")
    total, _ = assemble(images, vo_paths, workdir, final_video)
    real = ffprobe_duration(final_video)
    print(f"[done] video: {final_video}  ({real:.1f}s)")

    with open(os.path.join(outdir, "title.txt"), "w", encoding="utf-8") as f:
        f.write(script["title"] + "\n")
    with open(os.path.join(outdir, "description.txt"), "w", encoding="utf-8") as f:
        f.write(script["description"].rstrip() + "\n")
    with open(os.path.join(outdir, "hashtags.txt"), "w", encoding="utf-8") as f:
        f.write(" ".join(script["hashtags"]) + "\n")
    with open(os.path.join(outdir, "script.txt"), "w", encoding="utf-8") as f:
        for i, sc in enumerate(scenes, 1):
            f.write(f"SCENE {i}\n{sc['narration']}\n\n")
    mark_used(topic)
    print(f"[pack] posting pack ready in {outdir}")


if __name__ == "__main__":
    main()
