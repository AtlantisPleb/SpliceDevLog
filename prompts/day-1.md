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

```text
So I want you to keep going, do as much of the brief as you can, but also evolve the party scene to have a network of rooms you have to explore to find the one blue piece, not a bunch of them. If you fight and win any of the other characters, they drop robot pieces that go into your inventory.

This is so that you can sell them later for battery juice when we include battery juice. But for now, make sure it feels like a party scene with the lighting, a cyberpunk party with a DJ and a main stage and different imperial robots patrolling, and raiders are relaxed and dancing in place. But make it so that there's several rooms to explore and reasons to explore them, like batteries to pick up. Have it so that your robot is following you around and it's always next to you.

Before you prompt it to do something, you can see it moving from the main character to the activity it's set to do. And let's change the main character to a cylinder
```
Result: the night zone redesign and steps 11–12 ([build note 0006](../entries/0006-party-rooms-boss-ending.md)).

Words in [brackets] replace a session id or an internal name.

```text
review [the prototype session] and write a doc about why your version is so different (and worse) than that world. make a doc w gap analysis and plan to close the gaps, like make your version exactly like that one, and do it
```
Result: the gap list, and the `Rovers` look and world rebuilt outdoors.

```text
So we're gonna continue this, but we're gonna build in [our tools] and then build an exporter to Unreal Engine. Eventually we're gonna want that to be a two-way thing, like import any Unreal Engine project to us, two-way. For now, I want an exporter. so using the current version of Splice in [our tools] as the base. figure out what is the minimal exporter needed to export it to Unreal Engine. remember we have the Unreal Engine source code on this computer, so you can look at that. First, write a specification for it.
```
Result: the specification, then the exporter and the Unreal bridge
([build note 0007](../entries/0007-prototype-bridge-to-unreal.md)).
