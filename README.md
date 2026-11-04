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
| `portolabs:capcut-auto-edit` | Turning a raw talking-head video into a CapCut draft in the "0827" promo style: pauses and retakes cut, subtitles, B-roll, cards, poster, logos, SFX and grading. macOS only; needs CapCut, `ffmpeg` and `mlx_whisper`. |

## Adding a skill

Add `skills/<name>/SKILL.md` with `name` and `description` frontmatter, bump `version` in `.claude-plugin/plugin.json`, and run `claude plugin validate .` before you push.
