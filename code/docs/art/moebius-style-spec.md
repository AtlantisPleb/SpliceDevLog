# Moebius-style rendering for Rovers: analysis and plan

Status: plan only. Nothing here is implemented.
Written 2026-11-11.

## 1. Source and method

- **Video:** "Moebius-style 3D Rendering" by Useless Game Dev, 491 s, uploaded
  2023-03-24. <https://www.youtube.com/watch?v=jlKNOirh66E>
- **Method:** the 720p stream was downloaded and sampled every 5 s (98 frames).
  The frames were reviewed as nine contact sheets of 12 frames each. The
  narration came from the video's English captions. Times below are accurate
  to about ±5 s.
- **Licence rule: ideas only.** This doc describes techniques in our own words.
  It contains no frames, artwork or caption text from the video. The Moebius
  pictures shown in the video belong to their publishers and are not ours to
  reuse. Every texture and asset for Rovers must be made by us.

## 2. Frame-by-frame analysis

The video is a tutorial. The creator builds a single screen-space post-process
shader step by step in Unity, tests each step on a small test room (a wall with
blocks, a sphere, a box, a window, and a tuft of grass), and ends with a demo
game.

| Time | What happens on screen | Technique step |
|---|---|---|
| 0:00–0:55 | Intro. Reference pictures of Moebius's work. Goal stated: thin black outlines, flat colour, lots of detail. | Target look |
| 0:55–1:20 | Outline is discussed. Line width should stay fixed on screen. | Screen-space line requirement |
| 1:20–2:50 | A test pattern shows how a convolution filter works. The creator uses a Sobel kernel, first horizontal then vertical, combined by taking the maximum. | Edge detection |
| 2:39–3:00 | The Sobel filter runs on the **depth buffer**, which gives outlines where objects overlap. It then runs on the **normal buffer**, which gives better edges on surface creases. | Outline from depth and normals |
| 3:03–3:13 | A small UV jitter makes lines wobble like hand drawing. The creator tries a strong jitter, rejects it, and settles on a subtle one. | Hand-drawn wobble |
| 3:26–4:06 | Surface detail is written into the normal buffer so the Sobel pass outlines it. Close-ups show the artefacts this causes, and the creator accepts them. | Detail as normal data |
| 4:15–5:38 | **Hatching.** One texture holds three independent hatch layers, one per RGB channel. Brightness thresholds decide which layers show: none above 75%, horizontal between 75% and 50%, horizontal plus vertical between 50% and 25%, all three below 25%. The hatch is screen-space. The creator notes that hatch written into normals looks poor, because the Sobel pass outlines it. | Screen-space hatch by brightness band |
| 5:57–6:37 | **Specular.** A dot product between the surface normal and the main light gives the most lit area. That area is written as a special value in the normal data, so the Sobel pass outlines it as a white shape. | Highlight shapes |
| 6:37–7:07 | **Colour.** Base colours are flat, one per object, with an optional gradient. Shading comes from the hatch, so colours are at full brightness. A post-process pass adjusts saturation and contrast. | Flat colour and grade |
| 7:07–7:23 | **Paper grain.** Grain updates about every 10 frames, not every frame, to mimic the low frame rate of old film. | Grain |
| 7:23–8:00 | **Demo.** A small lap-based racing game uses the look. Its title card, HUD and lap timer show the style in play. | Full game |

### What the analysis tells us

1. **The core is one screen-space post-process pass, not per-object work.**
   Outline, hatch and highlight all come from scene buffers. Objects don't need
   individual outline meshes.
2. **Order matters.** Depth and normals first. Outlines come from both. Shading
   bands come from the lighting term. Highlights are written as data and
   outlined by the same edge pass. Colour and grain come last.
3. **The creator keeps shading and colour apart.** Brightness is carried by the
   hatch. Colour is flat. This keeps the palette free and lets the same colours
   work at any light level.
4. **Two known weak points.** Detail written into normals gets outlined, so
   fine detail looks rough close up. Hatch in shadows is hard to make follow an
   object's curve, so the creator used screen-space hatch.

## 3. Pipeline for Rovers

Rovers is a Third Person C++ project (`Rovers/`), built on the 5.9 engine
source. The web target (Wasm) uses the mobile renderer. Nanite, Lumen and
virtual shadow maps are off there (see `docs/unreal/web-games-in-the-verse.md`).
The look must work on that renderer, so the plan does not depend on Lumen or
Nanite.

Per frame, in order:

1. **Scene buffers:** depth, world normal, flat base colour, and a light
   term (the dot product of normal and main light).
2. **Edge pass:** Sobel on depth and on normals. Take the maximum. Apply a
   subtle screen-space UV wobble. Output: line mask.
3. **Band pass:** map the light term to four bands. Band 0 is no hatch. Bands
   1 to 3 add hatch layers from the RGB channels of our own hatch texture.
   Output: hatch mask. Hatch is screen-space.
4. **Highlight pass:** threshold the light term above a fixed level. Mark the
   result in a data channel so the edge pass outlines it.
5. **Compose:** flat colour, then hatch, then lines, then the grade (saturation
   and contrast), then paper grain. Grain changes every 10 frames.

### Unreal 5.9 implementation options (to verify in the editor)

- **Custom post-process material** on a Post Process Volume, reading
  `SceneTexture` nodes for depth and world normal. Our first choice. The exact
  inputs available on the mobile forward renderer in 5.9 are **unverified**.
  Confirm this before M1.
- **Custom depth or stencil** on selected meshes, if the depth and normal
  buffers give weak outlines on characters. Fallback only.
- **Lighting for the look:** unlit or custom flat materials on world and
  character meshes, so engine lighting doesn't add its own shading. Lumen and
  global illumination are turned off for this look.
- **Hatch texture:** we make a new RGB texture with three hatch layers. It is
  not the video's texture.
- **Grain:** a noise texture whose time input is quantized to every 10 frames.

### Rovers milestones

Each milestone has an acceptance check, verified by a screenshot in the editor
and, where possible, a headless capture (see the `run` skill).

| # | Milestone | Acceptance |
|---|---|---|
| M0 | This spec, reviewed and agreed | Owner sign-off on the decisions in section 5 |
| M1 | Outline post-process on the Third Person map | Line width is constant in pixels from near to far. A flat floor with uniform normals draws no line. Works at 1280x720 and 1920x1080. |
| M2 | Flat colour material set | No engine lighting shading on world or character meshes. Colours match the agreed palette. |
| M3 | Hatch by brightness band | Hatch density steps at the band thresholds. No hatch under full light. Hatch layers come from our own texture. |
| M4 | Highlight shapes | Lit areas above the threshold get a white outlined shape. Nothing outside the threshold changes. |
| M5 | Grade and paper grain | Saturation and contrast are adjustable from one place. Grain changes every 10 frames and not every frame. |
| M6 | Web build check | The Wasm build of Rovers runs the look. Frame time is measured against the bars in `web-games-in-the-verse.md` section 6. Any feature the mobile renderer lacks is listed with its fallback. |

## 4. Risks

- **Buffers on the mobile renderer.** Depth or normal input may not be
  available on the mobile forward path in 5.9. If not, the edge pass needs a
  different source, such as custom depth. This is the main technical risk, and
  M1 checks it first.
- **Edge aliasing at distance.** Sobel on a sub-pixel detail flickers. Mitigate
  with a depth-scaled threshold, and check it in the far-camera shot.
- **Hatch shimmer.** Screen-space hatch crawls when the camera moves. Mitigate
  by keeping hatch scale fixed to pixels and using a low-amplitude wobble.
- **Overdraw on the web.** Several full-screen passes cost frame time on phones.
  Measure after M1 and combine passes if needed.
- **Detail in normals.** Fine surface detail outlined by the edge pass looks
  rough close up. Keep surface detail out of the normal buffer unless it helps
  the look.

## 5. Decisions for the owner

| # | Decision | Recommendation |
|---|---|---|
| A1 | Scope: whole game or the Rovers test map first? | Test map first (M1 to M5), then the whole game |
| A2 | Characters: same hatch and outline as the world? | Yes, same pass. Check at M3. |
| A3 | Palette: who sets it? | We agree a palette at M2 from our own concept art |
| A4 | Grain on or off by default on phones? | Off on phones if M6 frame time is tight |
| A5 | Is a wobble of the outlines a must? | Yes, but subtle. The video shows it is easy to overdo. |

## Sources

- Video: Useless Game Dev, "Moebius-style 3D Rendering", 2023-03-24.
  <https://www.youtube.com/watch?v=jlKNOirh66E> (analysed from a 720p stream
  sampled every 5 s, plus captions; no frames are reproduced here).
- `docs/unreal/web-games-in-the-verse.md` (renderer limits and performance
  bars).
- `Rovers/` (Third Person C++ project, created 2026-11-11).
