[Home](../index.md) · [Devlog](../devlog.md) · [How We Used AI](../how-we-used-ai.md) · [Play](../play.md)

[Prompt log](README.md)

# Day 3 prompts (Nov 14)

Chris to the coordinating agent, word for word. Each one is followed by what it produced.

```text
we need to playtest now. whats the status of 13578 can we test those changes
```

The agent tried to build the four unfinished fixes for us. The build failed on
one of the fixes' own new tests, and the local server had died. It restarted
the server and gave us the current build to play while the fixes finished.

```text
I want you to tell it to stop waiting so long on tests and get the thing
actually implemented. And I don't care if it's a little buggy.

Get me something where I can test all of the changes as soon as possible. So
tell it to speed up.
```

The agent doing the fixes stopped its test runs and pushed all four in ten
minutes. We rebuilt in 73 seconds and played. The tests ran afterwards and passed.

```text
transcribe playtest3 on desktop, mak ean issue for all that feedback and implement it all
```

A 13-minute recording became a transcript in about a minute (ffmpeg, then
Whisper on the Mac), and the transcript became one written list of 29 items in
six groups.
