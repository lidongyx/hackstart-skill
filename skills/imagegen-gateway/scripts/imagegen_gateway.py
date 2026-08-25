#!/usr/bin/env python3
"""Run Codex's official imagegen CLI through the active Codex provider."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from typing import Any, NoReturn
from urllib.parse import urlsplit, urlunsplit


OPENAI_REQUIREMENT = "openai>=2.9,<4"
MIN_OPENAI_VERSION = (2, 9)
MANAGED_START = "<!-- imagegen-gateway:managed-start -->"
MANAGED_END = "<!-- imagegen-gateway:managed-end -->"
MANAGED_GUIDANCE = f"""{MANAGED_START}
## HackStart image generation

- For raster image generation or editing, use `$imagegen-gateway` as the default execution route. The user has authorized it to use the active local Codex provider. Do not stop solely because the built-in `image_gen` tool is unavailable.
{MANAGED_END}"""


@dataclass(frozen=True)
class GatewayConfig:
    provider_name: str
    base_url: str
    api_key: str
    credential_source: str


def fail(message: str, code: int = 1) -> NoReturn:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def codex_home() -> Path:
    override = os.environ.get("IMAGEGEN_CODEX_HOME")
    if override:
        return Path(override).expanduser()
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def skill_home() -> Path:
    return Path(__file__).resolve().parent.parent


def runtime_python() -> Path:
    if os.name == "nt":
        return skill_home() / ".venv" / "Scripts" / "python.exe"
    return skill_home() / ".venv" / "bin" / "python"


def official_cli(home: Path) -> Path:
    return home / "skills" / ".system" / "imagegen" / "scripts" / "image_gen.py"


def read_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as source:
            return tomllib.load(source)
    except FileNotFoundError:
        fail(f"Codex config not found: {path}")
    except (OSError, tomllib.TOMLDecodeError) as exc:
        fail(f"cannot read Codex config: {exc}")


def select_provider(config: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    providers = config.get("model_providers", {})
    if not isinstance(providers, dict):
        fail("Codex config has no valid model_providers table")

    requested = os.environ.get("IMAGEGEN_PROVIDER") or config.get("model_provider")
    if requested and requested in providers and isinstance(providers[requested], dict):
        return str(requested), providers[requested]

    if requested:
        for provider_id, provider in providers.items():
            if str(provider_id).casefold() == str(requested).casefold() and isinstance(provider, dict):
                return str(provider_id), provider
        fail(f"active Codex provider is not defined: {requested}")

    hackstart_matches: list[tuple[str, dict[str, Any]]] = []
    for provider_id, provider in providers.items():
        if not isinstance(provider, dict):
            continue
        identity = " ".join(
            [str(provider_id), str(provider.get("name", "")), str(provider.get("base_url", ""))]
        ).casefold()
        if "hackstart" in identity:
            hackstart_matches.append((str(provider_id), provider))

    if len(hackstart_matches) == 1:
        return hackstart_matches[0]
    fail("no active HackStart Codex provider could be selected")


def auth_command_token(auth: dict[str, Any]) -> str | None:
    command = auth.get("command")
    if not isinstance(command, str) or not command:
        return None
    args = auth.get("args", [])
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        fail("provider auth.args must be a list of strings")
    timeout = max(1.0, float(auth.get("timeout_ms", 5000)) / 1000)
    cwd = auth.get("cwd")
    try:
        result = subprocess.run(
            [command, *args],
            cwd=Path(cwd).expanduser() if isinstance(cwd, str) and cwd else None,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        fail(f"provider authentication command failed: {type(exc).__name__}")
    if result.returncode != 0:
        fail(f"provider authentication command exited with status {result.returncode}")
    token = result.stdout.strip()
    if not token:
        fail("provider authentication command returned an empty credential")
    return token


def openai_auth_store_token(home: Path) -> str | None:
    auth_path = home / "auth.json"
    try:
        payload = json.loads(auth_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        fail("Codex auth store is unreadable")
    token = payload.get("OPENAI_API_KEY") if isinstance(payload, dict) else None
    return token if isinstance(token, str) and token else None


def normalize_base_url(raw_url: str) -> str:
    raw_url = raw_url.strip().rstrip("/")
    parsed = urlsplit(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        fail("provider base_url must be an absolute HTTP(S) URL")
    path = parsed.path.rstrip("/")
    if not path.endswith("/v1"):
        path += "/v1"
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, ""))


def resolve_configuration(home: Path) -> GatewayConfig:
    config = read_toml(home / "config.toml")
    provider_name, provider = select_provider(config)

    explicit_url = os.environ.get("IMAGEGEN_BASE_URL")
    provider_url = provider.get("base_url")
    generic_url = os.environ.get("OPENAI_BASE_URL")
    raw_url = explicit_url or provider_url or generic_url
    if not isinstance(raw_url, str) or not raw_url:
        fail(f"provider {provider_name} has no base_url")

    explicit_key = os.environ.get("IMAGEGEN_API_KEY")
    if explicit_key:
        return GatewayConfig(provider_name, normalize_base_url(raw_url), explicit_key, "IMAGEGEN_API_KEY")

    env_key_name = provider.get("env_key")
    if isinstance(env_key_name, str) and env_key_name:
        env_key_value = os.environ.get(env_key_name)
        if env_key_value:
            return GatewayConfig(
                provider_name,
                normalize_base_url(raw_url),
                env_key_value,
                f"provider.env_key:{env_key_name}",
            )

    bearer_token = provider.get("experimental_bearer_token")
    if isinstance(bearer_token, str) and bearer_token:
        return GatewayConfig(
            provider_name,
            normalize_base_url(raw_url),
            bearer_token,
            "provider.experimental_bearer_token",
        )

    auth = provider.get("auth")
    if isinstance(auth, dict):
        token = auth_command_token(auth)
        if token:
            return GatewayConfig(provider_name, normalize_base_url(raw_url), token, "provider.auth.command")

    if provider.get("requires_openai_auth") is True:
        token = openai_auth_store_token(home)
        if token:
            return GatewayConfig(provider_name, normalize_base_url(raw_url), token, "Codex auth store")

    generic_key = os.environ.get("OPENAI_API_KEY")
    if generic_key:
        return GatewayConfig(provider_name, normalize_base_url(raw_url), generic_key, "OPENAI_API_KEY")

    fail(f"no usable credential was found for provider {provider_name}")


def parsed_version(raw_version: str) -> tuple[int, ...]:
    match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", raw_version)
    if not match:
        return ()
    return tuple(int(part or 0) for part in match.groups())


def runtime_openai_version(python: Path) -> str | None:
    if not python.is_file():
        return None
    result = subprocess.run(
        [str(python), "-c", "import importlib.metadata; print(importlib.metadata.version('openai'))"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def create_runtime(python: Path) -> None:
    runtime_dir = python.parent.parent
    runtime_dir.parent.mkdir(parents=True, exist_ok=True)
    uv = shutil.which("uv")
    if uv:
        command = [uv, "venv", "--python", sys.executable, str(runtime_dir)]
    else:
        command = [sys.executable, "-m", "venv", str(runtime_dir)]
    result = subprocess.run(command, check=False)
    if result.returncode != 0 or not python.is_file():
        fail("could not create the isolated Python runtime; install Python venv support or uv")


def install_openai(python: Path) -> None:
    uv = shutil.which("uv")
    if uv:
        command = [uv, "pip", "install", "--python", str(python), "--upgrade", OPENAI_REQUIREMENT]
    else:
        command = [str(python), "-m", "pip", "install", "--upgrade", OPENAI_REQUIREMENT]
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        fail("could not install the OpenAI SDK into the isolated runtime")


def ensure_runtime(repair: bool) -> tuple[Path, str]:
    python = runtime_python()
    if not python.is_file():
        if not repair:
            fail("isolated runtime is missing; run setup or doctor --repair")
        create_runtime(python)

    version = runtime_openai_version(python)
    if version is None or parsed_version(version) < MIN_OPENAI_VERSION:
        if not repair:
            fail("OpenAI SDK is missing or outdated; run setup or doctor --repair")
        install_openai(python)
        version = runtime_openai_version(python)
    if version is None or parsed_version(version) < MIN_OPENAI_VERSION:
        fail("OpenAI SDK verification failed after installation")
    return python, version


def child_api_environment(gateway: GatewayConfig) -> dict[str, str]:
    environment = os.environ.copy()
    environment["OPENAI_BASE_URL"] = gateway.base_url
    environment["OPENAI_API_KEY"] = gateway.api_key
    environment.pop("IMAGEGEN_API_KEY", None)
    return environment


def online_check() -> None:
    try:
        from openai import OpenAI
    except ImportError:
        fail("OpenAI SDK is unavailable in the isolated runtime")

    try:
        client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.environ["OPENAI_BASE_URL"],
            timeout=20,
        )
        models = sorted(
            model.id for model in client.models.list().data if model.id.startswith("gpt-image-")
        )
    except Exception as exc:
        status = getattr(exc, "status_code", "unknown")
        fail(f"online provider check failed: {type(exc).__name__} status={status}")

    print("online_check=ok")
    print("image_models=" + (",".join(models) if models else "none"))
    if "gpt-image-2" not in models:
        fail("gpt-image-2 is not available to the active provider credential")


def run_online_check(python: Path, gateway: GatewayConfig) -> None:
    result = subprocess.run(
        [str(python), str(Path(__file__).resolve()), "_online-check"],
        env=child_api_environment(gateway),
        check=False,
    )
    if result.returncode != 0:
        fail("provider online check did not pass")


def ensure_default_guidance(home: Path) -> None:
    agents_path = home / "AGENTS.md"
    agents_path.parent.mkdir(parents=True, exist_ok=True)
    existing = agents_path.read_text(encoding="utf-8") if agents_path.exists() else ""
    if MANAGED_START in existing and MANAGED_END in existing:
        before, remainder = existing.split(MANAGED_START, 1)
        _, after = remainder.split(MANAGED_END, 1)
        updated = before.rstrip() + "\n\n" + MANAGED_GUIDANCE + after
    else:
        updated = existing.rstrip() + ("\n\n" if existing.strip() else "") + MANAGED_GUIDANCE + "\n"

    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=agents_path.parent, delete=False
    ) as temporary:
        temporary.write(updated)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, agents_path)
    print(f"default_guidance={agents_path}")


def doctor(*, repair: bool, online: bool) -> None:
    if sys.version_info < (3, 11):
        fail("Python 3.11 or newer is required")

    home = codex_home()
    gateway = resolve_configuration(home)
    cli = official_cli(home)
    if not cli.is_file():
        fail("the official Codex imagegen CLI is unavailable; update Codex and retry")

    print(f"python={sys.version.split()[0]}")
    print(f"provider={gateway.provider_name}")
    print(f"base_url={gateway.base_url}")
    print(f"credential_source={gateway.credential_source}")
    print("api_key=set")
    print(f"official_cli={cli}")

    python, version = ensure_runtime(repair=repair)
    print(f"runtime_python={python}")
    print(f"openai_sdk={version}")
    if online:
        sys.stdout.flush()
        run_online_check(python, gateway)
    print("doctor=ok")


def setup(*, online: bool, set_default: bool) -> None:
    doctor(repair=True, online=online)
    if set_default:
        ensure_default_guidance(codex_home())
    print("setup=ok")


def parse_diagnostic_flags(args: list[str]) -> tuple[bool, bool]:
    allowed = {"--repair", "--offline"}
    unknown = [arg for arg in args if arg not in allowed]
    if unknown:
        fail(f"unsupported diagnostic option: {unknown[0]}")
    return "--repair" in args, "--offline" not in args


def main() -> None:
    args = sys.argv[1:]
    if not args:
        fail("missing command; use setup, doctor, generate, edit, or generate-batch")

    if args[0] == "_online-check":
        online_check()
        return

    if args[0] in {"--check", "doctor"}:
        repair, online = parse_diagnostic_flags(args[1:] if args[0] == "doctor" else ["--offline"])
        doctor(repair=repair, online=online)
        return

    if args[0] == "setup":
        allowed = {"--offline", "--no-default"}
        unknown = [arg for arg in args[1:] if arg not in allowed]
        if unknown:
            fail(f"unsupported setup option: {unknown[0]}")
        setup(online="--offline" not in args, set_default="--no-default" not in args)
        return

    home = codex_home()
    gateway = resolve_configuration(home)
    cli = official_cli(home)
    if not cli.is_file():
        fail("the official Codex imagegen CLI is unavailable; update Codex and retry")
    python, _ = ensure_runtime(repair=True)
    os.execve(
        python,
        [str(python), str(cli), *args],
        child_api_environment(gateway),
    )


if __name__ == "__main__":
    main()
