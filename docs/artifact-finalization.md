# Screenshots & GIF Checklist

Use this list when you want polished visuals for GitHub or a slide deck.

## Screenshots (PNG)

Save under `assets/screenshots/`:

1. `01-home-overview.png` — Home page with the role menu visible.
2. `02-submit-trip-flow.png` — Submit page after **Load Demo Values**.
3. `03-contributions-map-timeline.png` — Contributions page with KPI cards + map + timeline.
4. `04-qa-analyst-queue.png` — Analyst queue after **Run QA**, flags visible.
5. `05-analyst-exports.png` — Exports page with QA summary loaded (or downloads ready).
6. `06-access-denied-banner.png` — Home page showing the friendly message when an angler hits an analyst-only URL.

## GIF (optional but nice)

Save as `assets/gif/portal-end-to-end.gif` (about 45–75 seconds):

1. Load demo values → submit trip/catch/tag  
2. Switch to analyst → run QA → tap one action  
3. Open exports → load QA summary  
4. Switch back to angler → load contributions  

## Recording tips

- Same browser zoom every time (100% works well).
- Hide bookmarks/personal clutter if you can.
- Pause ~1 second after each big step so viewers can read it.

## Hook these into README

After files exist, README should link to:

- `assets/screenshots/01-home-overview.png`
- `assets/screenshots/02-submit-trip-flow.png`
- `assets/screenshots/03-contributions-map-timeline.png`
- `assets/screenshots/04-qa-analyst-queue.png`
- `assets/screenshots/05-analyst-exports.png`
- `assets/screenshots/06-access-denied-banner.png`
- `assets/gif/portal-end-to-end.gif`

## FFmpeg on Mac

If you see `command not found: ffmpeg`:

- Install: `brew install ffmpeg`
- Or call it directly: `/opt/homebrew/bin/ffmpeg`

Your screen recording might live at `assets/Source/portal-demo.mp4` (capital **S** in `Source` on some machines).

Example conversion (smaller file):

`ffmpeg -y -i "assets/Source/portal-demo.mp4" -vf "fps=10,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5" -loop 0 "assets/gif/portal-end-to-end.gif"`
