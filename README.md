# Hyper Trophy

A lift tracker built for daily gym use. No app store, no account required, no backend server.
Open it in Safari, add it to your home screen, and it behaves like a native app, including offline.

## Features

**Log**
- Pick a split (Lower Body, Upper Body, etc.) from a dropdown built from your own history, or add a new one
- Selecting a split shows every exercise you've ever logged under it, with the most recent weight and
  reps for each, even exercises you skipped last time but did the session before
- "Use these exercises" pre-loads that full list into today's session so you're filling in numbers,
  not re-typing exercise names
- Picking an exercise in the set-entry sheet shows your last 5 sessions for it, so you always know
  what you're trying to beat before you log today's sets

**History**
- Every past workout, grouped by day, with the split and full exercise/set breakdown
- Delete any workout individually
- **Backup** section: export your full log to a JSON file, or import one back in (adds anything not
  already present, safe to import over existing data)

**Progress**
- Pick any exercise and see a top-set trend chart, best/last top set, and total sessions logged

## Tech

- `index.html` — the app itself: HTML, CSS, and JavaScript in one file, no framework, no build step
- `sw.js` — a service worker that caches the app shell so it keeps working with no signal after the
  first successful load; uses a network-first strategy so updates show up immediately when you're online
- `icon.png` — the home screen icon, shipped as a real file (not embedded) since iOS Safari is
  unreliable about generating home screen icons from inline data URIs
- Data lives in the browser's `localStorage`, private to each device, nothing is sent to a server

## Live

Hosted at **https://hypertrophygymlog.netlify.app/**

**Installing on iPhone**
1. Open that link in **Safari** (must be Safari, not an in-app browser or another browser)
2. Tap the Share icon → **Add to Home Screen** → **Add**
3. Launch it from the home screen icon from then on

## Sample data

The History tab shows a **Load sample data** button whenever the log is empty, loading a 14-session
example month so you can explore the app before logging anything of your own.

## Data & backups

There's no cloud sync, everything is local to the device it was logged on. Use **Export data** in the
History tab's Backup section periodically, and especially before switching phones or resetting one, since
clearing Safari's site data or a factory reset wipes local logs with no way to recover them otherwise.
