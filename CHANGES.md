# CHANGES.md — finance v1 → history v2

What changed when the finance system (`~/workspace/finance_assistant/`)
was adapted into this history pipeline. Everything not listed here is
identical to v1 (same video build, same QC, same free services).

## Removed

- **Finance disclaimer deleted everywhere.** The education-only /
  not-financial-advice disclaimer sentence is gone from `pipeline.py`
  (both the template description and the Gemini-script post-processing
  that appended it) and from the README. No replacement disclaimer was
  added — history videos do not need one.
- **Featured finance script deleted.** The built-in 8-scene Emergency Fund
  script (`FEATURED_SCRIPTS`) was finance-only, so it was removed. Every
  history topic now uses the generic template or a Gemini script.
- **Finance topic list replaced.** The 34 finance topics are gone; the
  30 history topics from `history_vault/topics.md` are the pool now.
- **Finance branding not carried over.** The v1 `branding/` images, the
  finance sample video and the QR images were not copied. The
  `history_vault/branding/` v2 logo/banner (made for a rename) was
  deliberately NOT used anywhere.

## Renamed / reworded

- **Channel name locked to "The Money Guide"** in README and SETUP. The
  "Past History Vault" rename was cancelled on 2026-10-24 — nothing here
  renames, deletes or rebrands any channel, page or account.
- **Topics header rewritten.** The history topics file said "Past History
  Vault"; it now says "The Money Guide — History Video Topics". The 30
  topic titles themselves are unchanged.
- **Title emoji:** `💰` → `🏛️` for template titles.
- **Hashtags:** finance tags → `#History #WorldHistory #HistoryFacts
  #LearnHistory #AncientHistory` (template fallback).
- **Voice env var:** `FINANCE_TTS_VOICE` → `HISTORY_TTS_VOICE`. The voice
  itself is unchanged (`en-US-ChristopherNeural`).
- **Fallback slug:** `finance_video` → `history_video`.
- **Workflow identity:** job name "Daily Finance Video" → "Daily History
  Video"; git commit identity `finance-assistant` → `history-assistant`.
- **Docstrings / descriptions:** "finance" → "history" throughout.

## Rewritten for history

- **Template story beats (8 scenes):** money habits (hook / what / why /
  steps / mistake / close) → history beats (hook / what happened / world
  of that time / turning point / hidden middle / myth vs fact / legacy /
  closing question).
- **Template image prompts:** money/daily-life photos → historic scenes
  (monuments, parchment maps, period streets, ruins, museums, past-meets-
  present). Still photorealistic, vertical portrait, no text.
- **Gemini script prompt:** finance-education prompt → history prompt.
  New accuracy rules: stick to widely accepted historical facts; never
  invent dates, names or quotes; uncertain or legendary details must be
  labelled in the narration (e.g. "legend says"). The old finance rules
  ("never promise profits", "no personalised financial advice") are gone
  with the finance topic.
- **README / SETUP rewritten** for history and for the owner's real state:
  GitHub account and `GEMINI_API_KEY` secret already exist, repo name is
  `history-videos`, and posting is the same video on YouTube + TikTok +
  Facebook as "The Money Guide".

## Schedule change (and why)

- **Cron:** `30 3 * * *` (03:30 UTC) → `0 12 * * *` (**12:00 UTC =
  17:00 PKT**). Reason: the channel's publish slot is 01:00 AM PKT
  (20:00 UTC). A 12:00 UTC run leaves the posting pack ready the same
  evening, ~8 hours before the slot, so the owner can download and
  schedule in time. Still one run per day, still free-tier pace.
  Manual runs (`workflow_dispatch`) unchanged.

## Unchanged mechanics (kept exactly from v1)

- 8 scenes, voiceover per scene + 0.4s pause, 1080×1920 30fps, slow
  zoompan (`1+0.12*on/N`, centred), bottom-7% Pollinations attribution
  crop, ffmpeg concat, explicit `-map 0:v:0 -map 1:a:0`, no `-shortest`,
  no `alimiter`, loudnorm mix (voice loud, music at 0.22), fresh stdlib
  synthesized music bed, Pollinations images with local gradient fallback,
  edge-tts voiceover, template fallback when Gemini fails or no key is
  set, `used_topics.json` cycle (fresh empty list for v2), artifact
  upload with 30-day retention, `qc_check.py` copied unchanged.

## Secrets & safety

- The Gemini key comes **only** from the GitHub Actions secret
  `GEMINI_API_KEY` (`${{ secrets.GEMINI_API_KEY }}` in `daily.yml`).
  No key value, password, credential or personal data appears in any file
  in this folder. Verified by searching the folder for key-like values
  before delivery (see verification below).
