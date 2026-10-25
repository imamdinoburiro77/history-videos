# Setup Guide — Phone Only, Short Steps

You need only an **Android phone**. The GitHub account and the Gemini key
secret are already done — so this is just: upload the files, run once.

## Step 1 — Upload these files to your repo

Your repo is **`history-videos`** on GitHub.

1. Open the repo on GitHub in your phone browser.
2. Tap **Add file → Upload files**.
3. Upload all the files from this folder, **including** the `.github`
   folder (it holds the daily schedule). If the phone browser makes
   folders difficult, upload the files one by one, and create the workflow
   file at the path `.github/workflows/daily.yml` using
   **Add file → Create new file**.

## Step 2 — Check the Gemini key secret (already done?)

1. In your repo, open **Settings → Secrets and variables → Actions**.
2. You should see a secret named **`GEMINI_API_KEY`**.
3. If it is missing, tap **New repository secret**, name it
   `GEMINI_API_KEY`, paste the key, tap **Add secret**.
   **Never share the key with anyone, and never paste it in a chat.**

## Step 3 — Run it once to test

1. Open the **Actions** tab in your repo. If GitHub asks, allow the
   workflows to run.
2. Tap **Daily History Video → Run workflow**.
3. Wait a few minutes. When it finishes, open the run and download the
   **posting-pack** file at the bottom of the page. Inside it: your video,
   its title, description and hashtags.

From now on it runs **every day by itself at 12:00 UTC (17:00 PKT)**.
Each day's posting pack appears in the Actions tab, ready to download.

## Step 4 — Post the video (one manual step a day)

Download the posting pack and post the **same video** on all three, always
as **"The Money Guide"**:

1. **YouTube** — upload the MP4, paste the title, description and
   hashtags from the pack.
2. **TikTok** — upload from the phone (TikTok always needs this manual tap).
3. **Facebook** — post the same video on the page.

## Later: connect YouTube and Facebook

When you want automatic posting, the YouTube channel and Facebook page can
be connected. That is a separate short setup, and it must be done by you,
because the accounts belong to you.

---

**Problems?** Open the failed run in the Actions tab — the red step shows
exactly what went wrong. The most common issue is a missing or wrong
`GEMINI_API_KEY` secret; the video then simply uses the template script,
so a video is still produced.
