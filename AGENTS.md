# AGENTS.md — lansenger-sdk-python

Python SDK for the Lansenger Smart Bot API. Published to PyPI as `lansenger-sdk`.

## How to run

- Install dev: `pip install -e .[dev]` (or `pip install -e .` plus `pytest`, `build`, `twine`)
- Tests: `python3 -m pytest -q`
- Build: `python3 -m build`
- Publish: `python3 -m twine upload dist/lansenger_sdk-<version>*`

## Tech stack

Python 3.10+, httpx (async + sync wrapper), dataclasses, setuptools build backend.

## Layout

- `src/lansenger_sdk/` — SDK source (`client.py` async, `sync_client.py` sync, `config.py`, `chats.py`, `models.py`, `auth.py`)
- `tests/` — pytest suite
- `pyproject.toml` — version + packaging

## Release rules — CRITICAL

### Version numbers live in MULTIPLE places — update ALL of them together

Before tagging/publishing a release, every one of these must hold the same version:

| File | Symbol |
|------|--------|
| `pyproject.toml` | `version = "x.y.z"` |
| `src/lansenger_sdk/__init__.py` | `__version__ = "x.y.z"` |
| `CHANGELOG.md` | `## [x.y.z] - <date>` |

PyPI does not allow re-uploading a version. If a version was already uploaded with a
mistake, bump to the next patch (e.g. 1.7.1 → 1.7.2) — do not try to overwrite.

### NEVER publish without a full green test run

`python3 -m pytest -q` MUST pass (0 failures) before `twine upload`. No exceptions —
not "the failure is just a version string", not "I'll fix it in the next release".
A red test run means the release is not ready.

### Pass-through (external token) mode

`LansengerClient` / `LansengerSyncClient` support two init modes:
- **Standard**: `app_id` + `app_secret` (SDK auto-refreshes appToken)
- **Pass-through**: `app_token` (+ optional `user_token`); `app_id`/`app_secret` default to `""`

`app_id`/`app_secret` are optional (default `""`). `LansengerConfig.create()` raises
`LansengerConfigError` only when neither `app_id`/`app_secret` nor `app_token` is given.
Keep the constructors and `LansengerConfig` in sync — do not re-introduce a required
positional `app_id`/`app_secret`.

## Current status

v1.7.2 released. Pass-through init bug fixed (app_id/app_secret now optional).
