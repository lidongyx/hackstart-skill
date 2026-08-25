# HackStart Skills Repository

## Purpose

- This repository collects independently installable HackStart Codex skills.
- Put each skill under `skills/<skill-name>/` with a required `SKILL.md`.
- Keep shared user-facing installation prompts under `docs/`.

## Safety

- Never commit API keys, bearer tokens, provider configuration, auth stores, generated images, or local virtual environments.
- Diagnostics may report provider name, normalized base URL, credential source, SDK version, and available model IDs, but never credential values.
- Installation checks must not submit paid image-generation requests.

## Validation

- Validate a skill with the Codex `skill-creator` `quick_validate.py` helper.
- Run Python syntax checks for scripts and `git diff --check` before committing.
- For environment tests, use a task-specific temporary Codex home and fake credentials; do not repurpose `HOME` or `CODEX_HOME`.

## Git

- The default branch is `main`.
- Keep changes scoped to the requested skill and its documentation.
- Do not commit `.DS_Store`, `.venv`, `__pycache__`, or generated output.
