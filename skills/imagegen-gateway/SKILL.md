---
name: imagegen-gateway
description: "Generate or edit raster images through the user's active HackStart provider, defaulting to gpt-image-2.5-flare. Use when the user asks for an image and wants the configured third-party image API used without handling credentials manually."
---

# HackStart Image Generation Gateway

Use the user's active Codex provider and the official bundled image CLI. The default
model is `gpt-image-2.5-flare`; keep explicit user model overrides. Never display,
copy, or log API credentials.

## Simple use

For an ordinary request such as “生成一张赛博朋克城市夜景”, call the gateway directly
and save the image to a sensible output path. Do not ask the user to provide API keys or
CLI flags unless the request needs them. The shortest CLI form is:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/imagegen-gateway/scripts/imagegen_gateway.py" \
  quick "生成一张赛博朋克城市夜景"
```

`quick` uses `gpt-image-2.5-flare` and overwrites the default output file. For a custom
path or advanced options, use the underlying commands:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/imagegen-gateway/scripts/imagegen_gateway.py" \
  generate --prompt "<prompt>" --out "<output path>"
```

## First use and repair

Locate Python 3.11 or newer, then run setup once:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/imagegen-gateway/scripts/imagegen_gateway.py" setup
```

On Windows, use `py -3` or `python` and the equivalent `%USERPROFILE%\.codex` path.
Setup reads the active provider from the user's local Codex configuration, creates an
isolated runtime, installs the OpenAI SDK, performs a zero-cost model-list check, and
adds an idempotent global preference for this skill. It never prints the credential.

If setup has already run, generate directly. The gateway injects
`--model gpt-image-2.5-flare` when no `--model` is supplied:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/imagegen-gateway/scripts/imagegen_gateway.py" \
  generate --prompt "<prompt>" --out "<output path>"
```

The launcher accepts the official CLI's `generate`, `edit`, and `generate-batch`
arguments unchanged and automatically repairs a missing or outdated isolated runtime
before a paid request. Use `--model` to override the default when needed.

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
checks list models and do not generate an image or incur image-generation charges. Setup
requires `gpt-image-2.5-flare` to be available.
