[Home](index.md) · [Devlog](devlog.md) · [How We Used AI](how-we-used-ai.md) · [Play](play.md)

# How We Used AI

## Tools

| Tool | What we used it for | Example |
|---|---|---|
| **Claude Code** (Claude Opus 5.5) | The build agent. It writes and runs editor scripts, writes the Blueprint logic, playtests, takes and checks screenshots, and keeps this log. | Built Kiki's 7-step gray box overnight and played it through by script ([Day 1](days/day-1.md)) |
| **Unreal Editor MCP server** (UE 5.9) | Lets the agent drive the open editor: run Python, edit Blueprint graphs as text, and build UMG widgets | The Digger's logic is written as text in [`BP_Bot.dsl`](https://github.com/AtlantisPleb/SpliceDevLog/blob/main/code/tools/ue/splice_dsl/BP_Bot.dsl) and applied live |
| **Claude** (chat) | Kiki's pitch and the gray box plan, including the step-by-step build prompt | [prompts/day-1.md](prompts/day-1.md) |
| **ffmpeg** | Turning screen recordings into clips and GIFs | Day 1 clip |

## What AI made vs. what we made by hand

| AI made | We made by hand |
|---|---|
| Level geometry and layout scripts (`tools/ue/splice_step1_level.py`) | The game idea, the pitch and the world (Kiki) |
| All Blueprint logic, written as Blueprint Graph DSL | The gray box plan, with its steps and tests (Kiki) |
| The three UI widgets (HUD, Edit Bay, End screen) | The art direction: the Moebius references and the palette |
| The Moebius post-process shader (HLSL), from our written spec | Concept sketches in a notebook (Day 0) |
| The scripted playtest and screenshots | Every decision about scope, and what to cut |
| Drafts of this devlog | Final review of each devlog entry |

## Art sources

| Asset | Source |
|---|---|
| All level and prop shapes (mine, rover, parts, bot, rubble) | Unreal Engine basic shapes (cube, sphere, cylinder, cone), shipped with the engine |
| Player character | Unreal Engine Third Person template mannequin (Epic Games, engine content) |
| Materials (flat colours) | Made in script by us and the agent; no textures |
| Moebius look | Our own post-process shader, written from [our spec](https://github.com/AtlantisPleb/SpliceDevLog/blob/main/code/docs/art/moebius-style-spec.md). No frames or art from the reference video are used. |
| Concept sketches | Handmade by the team (Day 0) |
| AI-generated images | None so far |

## Prompt log

We save the key prompts for each day in [`/prompts`](prompts/README.md):
- [Day 0](prompts/day-0.md)
- [Day 1](prompts/day-1.md)
