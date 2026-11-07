# portolabs-skill

Claude Code skills for the Portolabs team, packaged as one plugin (`portolabs`) in its own marketplace.

## Install

In Claude Code:

```
/plugin marketplace add portolabs-id/portolabs-skill
/plugin install portolabs@portolabs
```

The repo is private, so your GitHub login (`gh auth login`) must have access to `portolabs-id`. Run `/plugin marketplace update portolabs` to pull new versions.

## Skills

| Skill | Use it for |
|---|---|
| `portolabs:classmate-import` | Turning a Google Drive folder of MP4s into a Classmate with ordered lessons grouped into modules, through Chrome and the Strapi admin. |
| `portolabs:capcut-auto-edit` | Turning a raw talking-head video into a CapCut draft with pauses and retakes cut. Style `della` (default, the "0827" promo: subtitles, B-roll, cards, poster, logos, SFX, grading) or `minimal` (`/portolabs:capcut-auto-edit minimal`: moody grade, kinetic captions with a lime keyword, strike, alert cards, words behind the head, REC frame, glitch). macOS only; needs CapCut, `ffmpeg` and `mlx_whisper`, plus `npx` for minimal. |
| `portolabs:capcut-asmr-edit` | Turning a long raw process video (laptop/PC service, cleaning, repair) into several short satisfying reels over a background song, as one CapCut project with a timeline per reel. macOS only; needs CapCut and `ffmpeg`, and `capcut-auto-edit` next to it. |
| `portolabs:explainer-reel` | Turning a topic into a 30–90 s vertical explainer reel in the clean grid style: trend research, hooks and script approved first, then ElevenLabs voice, real logos and screenshots, HyperFrames motion, delivered as a CapCut draft. macOS only; needs CapCut, `ffmpeg`, `uv`, Node 22+, Chrome, an ElevenLabs key, and `capcut-auto-edit` next to it. |
| `portolabs:capcut-webinar-edit` | Cutting a 1–2 hour webinar recording into lesson videos (one topic each, material only, Portolabs intro and outro) as landscape CapCut drafts, ready for `classmate-import`. macOS only; needs CapCut, `ffmpeg` and `mlx_whisper`, and `capcut-auto-edit` and `capcut-asmr-edit` next to it. |

## Adding a skill

Add `skills/<name>/SKILL.md` with `name` and `description` frontmatter, bump `version` in `.claude-plugin/plugin.json`, and run `claude plugin validate .` before you push.
