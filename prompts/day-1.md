[Prompt log](README.md)

# Day 1 prompts (Nov 12)

## Kiki's gray box build prompt

From "Splice: Jam Pitch & Gray Box Plan". This is the start of the prompt; the
full text, steps 1–7, is in the plan.

```text
You are helping me build a game jam gray box in Unreal Engine 5.9. Use
Blueprints only, no C++. Use only basic shapes (cubes, cylinders, spheres)
and simple colored materials. No art, no sound, no polish.

RULES
- Do ONE step at a time. After each step, stop, tell me exactly what to test
in the editor, and wait for me to say "next".
- Name every asset exactly as written below.
- Put everything in the folder /Game/Splice/.
- If something fails, tell me in plain words and fix it before moving on.
- Keep it simple. If there is an easy way and a clever way, choose the easy
way.

THE GAME IN ONE SENTENCE
The player picks up robot parts in a mine, builds a Digger bot at their
rover, and the bot drills through a blocked tunnel to reach the exit.
```

## To Claude Code

```text
create a process for devlog we need to record -- we want to win this aweard -- Best dev log showing how you built your game (Unreal Engine or UEFN) - make a system for this and make our first entry
```
Result: this devlog's process and build note 0001.

```text
We are going to sleep, so do it all in one go.  And let me see it with the post-process shader on, too.
```
Result:
- gray box steps 2–7, built overnight in one pass instead of stopping after
  each step;
- the scripted playtest;
- the Moebius look turned on in the mine.

See [Day 1](../days/day-1.md).
