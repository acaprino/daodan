---
description: >
  Detect the 24 catalogued patterns and edit them out without inventing content; --score adds a self-assessed quality score.
  TRIGGER WHEN: the user asks to humanize prose/text, remove AI-sounding copy, or rewrite articles/blog posts/documentation for natural voice.
  DO NOT TRIGGER WHEN: cleaning up source code (use /clean-code:clean-code) or translating text.
argument-hint: "<file or text> [--register docs|business|personal] [--score]"
---

# Humanize Text

Remove AI writing traces from prose, articles, blog posts, documentation or any other non-code text, with the `text-humanizer` agent.

**This is for text and prose. For source code readability, use `/clean-code:clean-code`.**

## Step 1: Read the arguments

From `$ARGUMENTS`:
- **Input:** a file path, or inline text. With neither, ask the user for the text and wait.
- `--register docs|business|personal`: optional. Without it, the agent infers the register.
- `--score`: optional. Adds the quality score.

## Step 2: Run the text-humanizer agent

Dispatch the `text-humanizer` agent in its own isolated context, with this brief filled in:

```
Humanize the text below following the anti-ai-writing-patterns skill: ground rules first,
then register, language and patterns.

Input: <the file path, or the inline text>
File handling: if a path is given, read it; do not write or edit any file.
Register: <docs | business | personal | infer>
Score: <yes | no>
Reply format: report
```

## Step 3: Show the report

Show the agent's report as it came back: the final text, Changes, Open points, and the score when `--score` was given.

## Step 4: Offer to write (file input only)

When the input was a file, ask:

```
Humanized version ready.

1. Overwrite the original file
2. Write to a new file ([filename].humanized.[ext])
3. Only show the result
```

Write only after the user picks 1 or 2, and write only the body inside the **Final text** fence of the report, exactly as it stands: never the fence lines, the headings or the other sections.

## When to use what

- `/clean-code:clean-code`: source code readability (naming, comments, structure)
- `/text-humanizer:humanize-text`: prose and text (this command)

$ARGUMENTS
