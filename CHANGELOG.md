# Changelog

All notable changes to the Lansenger Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.6.6] - 2026-06-10

### Fixed

- **sync_client**: `from_store()` now auto-loads user token from credential store and registers it with `UserTokenManager`.
- **sync_client**: `set_user_tokens()` fixed TypeError — now directly calls async client instead of going through `_ephemeral_call` wrapper.
- **sync_client**: `get_user_token()` now uses persistent async client for token management, raising `LansengerAuthError` when no token is available.

### Added

- **sync_client**: `_async_client_for_tokens` instance preserved across method calls for consistent token management.

## [1.6.5] - 2026-06-10

### Added

- **auth**: `UserTokenManager` now persists `staff_id` in credential store and restores it from cache.
- **auth**: `get_token()` passes `staff_id` to `save_user_token()` and `set_tokens()`.

## [1.6.4] - 2026-06-10

### Added

- **config**: `redirect_uri` field added to `LansengerConfig`, resolvable via `LANSENGER_REDIRECT_URI` env var.
- **oauth**: `build_authorize_url()` now validates that `redirect_uri` is set (from params, config, or env), raising a clear error if missing.
- **persistence**: `redirect_uri` persisted in `CredentialStore` (`save_credentials`/`load_credentials`).
- **client/ sync_client**: `from_store()` now passes `redirect_uri` from stored credentials to config.

## [1.6.3] - 2026-06-09

### Fixed

- **constants**: `MEDIA_TYPE_AUDIO` changed from 4 to 3 to match OpenAPI 4.5.1 (`VIDEO=1, IMAGE=2, AUDIO=3`). `MEDIA_TYPE_FILE` removed (no FILE type in 4.5.1). `guess_media_type()` now correctly returns `MEDIA_TYPE_AUDIO` for audio extensions and `MEDIA_TYPE_IMAGE` for unknown types.
- **media**: `download_media()` now accepts optional `user_token` parameter (OpenAPI 4.5.2).
- **media**: `upload_app_media()` now accepts optional `context` parameter (OpenAPI 4.5.4).
- **calendars**: `add_schedule_attendees()` and `delete_schedule_attendees()` now accept `operation_type` and `current_time` parameters required for recurring schedules (OpenAPI 4.23.16/18).
- **config**: `http_timeout=0` no longer incorrectly overwritten to 30.0 by `or 30.0` fallback.
- **api_utils**: `except Exception` narrowed to `except (json.JSONDecodeError, UnicodeDecodeError)` to avoid silently swallowing programming errors.
- **oauth**: `quote(safe='')` changed to `quote()` — no longer over-encodes URL-safe characters.
- **oauth**: Removed duplicate `aclose()` in `except` block (already handled by `finally`).
- **contacts**: `search_staff()` now validates that at least one of `user_token` or `user_id` is provided (OpenAPI 4.1.16 v2).
- **models**: `GroupCreateInfo.org_id` type changed from `int` to `str` for consistency with `groups.py`.
- **auth**: `TokenManager` now reads `app_token_expiry` from profile-level data instead of top-level state (multi-profile stores).
- **auth**: `UserTokenManager.get_token()` added `asyncio.Lock` to prevent concurrent refresh race conditions.
- **\_\_init\_\_** : `MEDIA_TYPE_AUDIO` correctly exported; duplicate `__all__` entries removed.

## [1.6.2] - 2026-06-09

### Fixed

- **auth**: `UserTokenManager` now loads `refresh_token` from cache independently of `user_token` expiry — no longer lost on restart.
- **auth**: `refresh_token` expiry is checked before calling the API, providing a clear error instead of confusing API error.

## [1.6.1] - 2026-06-09

### Changed

- **CLI**: `id_type` parameter values aligned with SDK (`employ_id, mobile, mail, login, external_id`).
- **api_utils**: Extracted shared API utilities (`do_get`, `do_post`, `parse_api_response`) into `api_utils.py` to eliminate code duplication across 6 modules.

## [1.6.0] - 2026-06-06

### Added

- Token management fixes: `refreshToken` preserved on refresh, `expiry` margin subtracted in persistence, `refreshExpiresIn` persisted.
- API response field names aligned with OpenAPI specification.

## [1.5.1] - 2026-05-30

### Added

- `UserTokenManager` for automatic `userToken` refresh.
- `ChatMessageInfo.plain_text()` helper.
- `schedule_list` optional params, `statusList` field name fix.
- `ChatMessagesResult.retryable` attribute.

### Fixed

- `exchange_code` `expires_in` fix.
- `ephemeral_call` encoding_key/callback_token fix.

## [1.5.0] - 2026-05-25

### Added

- `UserTokenManager` class for automatic user token refresh with file persistence.
- `ChatMessageInfo.plain_text()` method for extracting plain text from messages.

## [1.4.1] - 2026-05-20

### Added

- `cover_image` parameter to `send_text()` and `send_file()`.

## [1.4.0] - 2026-05-15

### Added

- 5 new API endpoints.
- Separation of `upload_media` (4.5.1 core platform) and `upload_app_media` (4.5.4 app bot).

### Fixed

- Various bug fixes across modules.

## [1.3.2] - 2026-05-10

### Fixed

- CLI credential resolution from store.
- `dataEncrypt` without key no longer raises.
- `save_credentials` properly handles `encoding_key` and `callback_token`.

## [1.3.1] - 2026-05-08

### Added

- `encoding_key` and `callback_token` persisted in `CredentialStore`.
- Convenience methods: `from_store`, `parse_callback`, `verify_callback`.

## [1.3.0] - 2026-05-05

### Added

- Callback encryption/decryption and signature verification (OpenAPI 4.10).

## [1.2.0] - 2026-05-01

### Added

- Multi-profile `CredentialStore` with `from_store` classmethod.
- Profile switching support.

## [1.1.0] - 2026-04-25

### Added

- `url_helpers.py` unifying URL construction across all modules using `build_api_url()`.
- Calendar and todo endpoints added to `API_ENDPOINTS` constants.
- Group chat support for all send methods.
- Chat fetch APIs: `fetch_chat_list`, `fetch_chat_messages`.

### Fixed

- `ChatStaffInfo`, `ChatGroupInfo`, `ChatListResult`, `ChatMessageInfo`, `ChatMessagesResult` `to_dict()` methods.
- Media `create` endpoint path.

## [1.0.3] - 2026-04-20

### Added

- `send_oacard` method.
- `pad_card_link`, `pad_link` support in card methods.

## [1.0.1] - 2026-04-18

### Changed

- Project URLs updated.
- README.pypi.md added for PyPI display.

## [1.0.0] - 2026-04-15

### Added

- Initial release with P0+P1+P2 API coverage.
- `LansengerClient` (async) and `LansengerSyncClient` (sync) interfaces.
- `TokenManager` for app token lifecycle.
- `CredentialStore` for file-based credential persistence.
- Structured dataclass models for all callback event types.
- Support for: messages, groups, staff, departments, media, calendars, todos, streaming, reminders, OAuth2, callbacks.
- 5-language READMEs.
