# Free History Video Assistant — for "The Money Guide"

An automatic system that makes **one finished history video every day**,
using only free services — no paid tools, no computer needed. It runs in
the cloud on GitHub Actions and can be managed entirely from an Android
phone. The finished video is posted by the channel owner on YouTube,
TikTok and Facebook, always under the name **"The Money Guide"**.

## What it does, every day, by itself

1. **Picks a topic** from `topics.md` (30 history topics).
   Used topics are logged in `used_topics.json`, so nothing repeats.
2. **Writes the script** — with a free Google Gemini API key it writes a
   fresh script; without a key it uses a built-in template. Either way the
   video has a strong hook in the first 3 seconds and ends with a question
   for comments. Scripts stick to widely accepted historical facts, and
   legends are flagged as legends ("legend says").
3. **Records the voiceover** with edge-tts (free Microsoft voice,
   `en-US-ChristopherNeural`).
4. **Creates one image per scene** with the free Pollinations image API
   (with an automatic local fallback image if a download ever fails).
5. **Adds a fresh, quiet, original music bed** — synthesized by the code
   itself, so it is different every run and 100% licence-free.
6. **Builds the video** with ffmpeg: vertical 1080×1920 (perfect for
   YouTube Shorts, TikTok and Facebook Reels), slow zoom on every scene,
   loud clear voice over quiet music.
7. **Saves a posting pack**: the MP4 plus `title.txt`, `description.txt`,
   `hashtags.txt` and `script.txt`.

## What is free (and where)

| Part            | Service                        | Cost            |
|-----------------|--------------------------------|-----------------|
| Running the system | GitHub Actions              | Free tier       |
| Script writing  | Google Gemini API (free tier) or built-in template | Free |
| Voiceover       | edge-tts (Microsoft voices)    | Free            |
| Images          | Pollinations image API         | Free            |
| Music           | Synthesized by the pipeline    | Free            |
| Video assembly  | ffmpeg (open source)           | Free            |

## Known limits — please read

- **TikTok needs one manual tap.** TikTok does not allow outside tools to
  post directly without a long approval process. The video arrives finished;
  posting it on TikTok is one manual upload from the phone. YouTube and
  Facebook can be connected for automatic posting later.
- **Free quotas exist.** Gemini's free tier, GitHub Actions minutes and
  Pollinations are generous for one video per day, but they are not
  unlimited. One video a day is the safe, designed pace.
- **This is v2.** It produces the video and the posting pack. Connecting
  YouTube/Facebook auto-upload comes in the next step, once those accounts
  are connected by the channel owner. (The channel name stays
  "The Money Guide" everywhere — no rename.)
- **History, told honestly.** Scripts never invent dates, names or quotes,
  and uncertain or legendary details are labelled as such.
- **Free images have small print.** Pollinations' free tier stamps a tiny
  attribution in the bottom corner of each image; the pipeline trims the
  bottom strip of every frame to remove it (invisible under the slow zoom).
  The free image service can also be slow at busy times — if a download
  fails, the pipeline uses a local fallback image so the day's video is
  still produced.

## Files

- `pipeline.py` — the whole pipeline (one file, standard library + edge-tts)
- `topics.md` — the topic list (add your own lines any time)
- `used_topics.json` — created automatically; the topic memory
- `requirements.txt` — the one Python package needed (`edge-tts`)
- `.github/workflows/daily.yml` — the daily schedule on GitHub Actions
- `SETUP.md` — phone-only setup guide (simple English)
- `qc_check.py` — optional local tool that proves the narration is audible
  in the finished video (needs numpy)
- `CHANGES.md` — what changed vs the finance v1 system

## Run it locally (optional)

```bash
pip install -r requirements.txt
python3 pipeline.py                      # today's topic
python3 pipeline.py --topic "Some Title" # a chosen topic
```

Output appears in `output/<date>_<slug>/`.
