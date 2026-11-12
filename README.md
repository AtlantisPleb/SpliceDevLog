# Rovers devlog: how we record it

Goal: win **Glass Box**, "Best dev log showing how you built your game
(Unreal Engine or UEFN)". The jam build window is 2026-11-12 to 2026-11-15.

A judge should be able to read the log and see, step by step, how the game was
built: what we tried, what broke, why it broke, how we fixed it, and what it
looked like at each point. Failures are the most valuable part, so we keep them.

## Layout

```
docs/devlog/
  README.md               this process
  TEMPLATE.md             copy this for each entry
  entries/NNNN-slug.md    one file per entry, numbered in order
  media/NNNN/             images and clips for that entry
tools/devlog/shot.sh      renders a screenshot from the open editor
tools/ue/                 the editor scripts the entries refer to
```

## When to write an entry

- **One entry per working session**, plus one whenever something visible
  changes: a new feature, a new look, or a bug fixed after a hunt.
- During the jam, at least **one entry per day**.
- Write it the same day, while the details are fresh. A rough entry now beats a
  polished one later.

## What every entry has

1. **Goal:** what we set out to do, in one or two lines.
2. **Before and after images:** at fixed camera positions, so they can be compared.
3. **Steps:** what we did, in order, with times.
4. **What broke:** each failure with its symptom, its cause, and the fix. Keep
   the "before" images for these.
5. **Tools and AI:** what we used, including AI agents, and what they did. The
   jam allows any AI tools, so showing this workflow honestly is a strength.
6. **Numbers:** anything measurable, such as iteration time or frame time.
7. **Next:** what's still wrong and what comes next.

## Capturing media

**Screenshots.** With the editor open, run:

```sh
tools/devlog/shot.sh 0002 hero 450 -800 190 -4 119
```

- The arguments are: entry, name, camera X Y Z, pitch, yaw.
- The editor renders the frame itself (`HighResShot`, 1920x1080), so it doesn't
  matter which window is in front.
- Reuse the same named cameras in every entry so progress lines up. The
  standard set is below.

| Name | X | Y | Z | Pitch | Yaw |
|---|---|---|---|---|---|
| hero | 450 | -800 | 190 | -4 | 119 |
| close | 260 | -330 | 230 | -3 | 122 |
| low | 230 | -400 | 55 | 14 | 121 |
| wide | 1500 | -2700 | 520 | -9 | 118 |
| side | -950 | -520 | 240 | -4 | 29 |

**Failures.** When something looks wrong, take the shot before you fix it. Name
it `before_N_what.png`.

**Clips.** For motion (play mode, camera moves, effect toggles), record 10–30 s
with macOS screen recording (Cmd-Shift-5). Crop the clip to the viewport and
save it in `media/NNNN/`. Keep the raw clips: the 30–60 s submission video is
cut from them.

**Before you add any image, check it.**

- Crop to the viewport.
- No terminals, browser tabs, emails, or other personal windows in frame.
- Only our own work: no frames or art from reference videos or Pinterest.

## End-of-session checklist

- [ ] Standard camera shots taken for this entry
- [ ] Every failure from the session has a cause and a fix written down
- [ ] Scripts the entry refers to are saved under `tools/`
- [ ] Entry added to the index below
- [ ] Committed with `dv commit`

## Publishing

The devlog is public at <https://github.com/AtlantisPleb/SpliceDevLog>. This
folder in the game repo is the source; the GitHub repo is a published copy.

- **Write every image and file link as an absolute GitHub URL:**
  - images: `https://raw.githubusercontent.com/AtlantisPleb/SpliceDevLog/main/media/NNNN/name.png`
  - files: `https://github.com/AtlantisPleb/SpliceDevLog/blob/main/...`

  Then they render both on GitHub and in the Diversion viewer, which can't
  resolve relative image paths.
- **To publish,** run `tools/devlog/publish.sh "message"`. It copies the
  entries, the media and the referenced scripts into the GitHub repo, then
  commits and pushes. Images only show up in Diversion after this has been run.

## Submission

On the last day:

1. Read the entries in order and write a short summary at the top of the index.
2. Cut the 30–60 s gameplay video from the clips.
3. Export the log, either as this folder or as one long page, for the dev log
   link.

## Index

| # | Date | Title |
|---|---|---|
| [0001](https://github.com/AtlantisPleb/SpliceDevLog/blob/main/entries/0001-moebius-mars.md) | 2026-11-12 | A robot on Mars, in a Moebius style |
| [0002](https://github.com/AtlantisPleb/SpliceDevLog/blob/main/entries/0002-splice-mine-graybox.md) | 2026-11-12 | Splice gray box, step 1: the mine |
