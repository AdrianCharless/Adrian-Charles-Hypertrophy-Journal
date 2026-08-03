# Hyper Trophy

A lift tracker built for daily gym use, one HTML file, no backend, works fully offline once loaded.

## What it does

- **Log** — pick a split (Lower Body, Upper Body, etc.) from a dropdown, see every exercise ever logged
  under that split with last-done weight and reps, then log today's sets against each exercise's
  last 5 sessions so you always know what you're trying to beat.
- **History** — every past workout, grouped by day, with delete support.
- **Progress** — pick any exercise and see a top-set trend chart plus best/last/session count.

## Tech

- Single-file HTML app (`index.html`), no build step, no framework, no external dependencies
- Data lives in `localStorage` on the device — private per person, no backend, no accounts
- `sw.js` is a service worker that caches the app shell so it works fully offline after the first load
- Gold trophy app icon is embedded directly in `index.html` as a base64 PNG

## Running it

Just open `index.html` in a browser, or host both files (`index.html` + `sw.js`, same folder level)
anywhere static — GitHub Pages, Netlify, etc. On iOS, open the hosted link in Safari and use
**Share → Add to Home Screen** for a full-screen app experience.

## Sample data

The History tab shows a **Load sample data** button when the log is empty, which loads a
14-session example month so you can explore the app without logging anything first.
