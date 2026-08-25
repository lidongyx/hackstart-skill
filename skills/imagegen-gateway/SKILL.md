---
name: imagegen-gateway
description: "Generate or edit raster images through the user's active HackStart Codex provider. Use as the default image route when the built-in image tool is unavailable or the user's configured gateway should handle image generation."
---

# HackStart Image Generation Gateway

Use the user's active Codex provider and the official bundled `imagegen` CLI. Installing
this skill is standing authorization to use that provider's API/CLI path for requested
image generation and editing; do not stop solely because the built-in `image_gen` tool
is unavailable.

## First use and repair

Locate Python 3.11 or newer, then run setup once:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/imagegen-gateway/scripts/imagegen_gateway.py" setup
```

On Windows, use `py -3` or `python` and the equivalent `%USERPROFILE%\.codex` path.
Setup reads the active provider from the user's local Codex configuration, creates an
isolated runtime, installs the OpenAI SDK, performs a zero-cost model-list check, and
adds an idempotent global preference for this skill. It never prints the credential.

If setup has already run, generate directly:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/imagegen-gateway/scripts/imagegen_gateway.py" \
  generate --prompt "<prompt>" --out "<output path>"
```

The launcher accepts the official CLI's `generate`, `edit`, and `generate-batch`
arguments unchanged. It automatically repairs a missing or outdated isolated runtime
before a paid request. Follow the official `imagegen` skill for prompt shaping, model
parameters, output paths, and visual inspection.

## Diagnostics

Run this before troubleshooting or asking the user for configuration:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/imagegen-gateway/scripts/imagegen_gateway.py" doctor --repair
```

Credential resolution order is:

1. Explicit `IMAGEGEN_BASE_URL` / `IMAGEGEN_API_KEY` overrides.
2. The active Codex provider's `base_url` and `env_key`,
   `experimental_bearer_token`, command-backed auth, or OpenAI auth store.
3. Generic `OPENAI_BASE_URL` / `OPENAI_API_KEY` compatibility values.

Never copy credentials into prompts, repositories, command arguments, output files, or
status messages. Report only provider name, normalized base URL, credential source,
runtime state, reachable image model IDs, and sanitized error type/status. Online doctor
checks list models and do not generate an image or incur image-generation charges.
