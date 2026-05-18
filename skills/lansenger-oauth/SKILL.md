---
name: lansenger-oauth
description: Lansenger OAuth2 user authentication flow — build authorize URL, exchange code for userToken, refresh userToken, fetch user info, and the appToken/userToken hierarchy
license: MIT
metadata:
  sdk: lansenger-sdk
  platform: lansenger
  category: auth
  pip: pip install lansenger-sdk
---

# Lansenger OAuth2 & User Authentication

Lansenger uses a two-tier auth system. Understanding the hierarchy is critical before using user-level APIs.

## Authentication Hierarchy

```
┌──────────────┐    ┌──────────────────────────────┐    ┌──────────────────┐
│   appToken   │    │  OAuth2 → code → userToken    │    │   refreshToken   │
│  (bot auth)  │    │  (specific user auth)         │    │  (30-day, renew) │
└──────────────┘    └──────────────────────────────┘    └──────────────────┘
      │                        │                              │
      ▼                        ▼                              ▼
  Send messages,        Contacts, departments,         Refresh expired
  groups, streaming     user info, search              userToken
```

**Key distinction:**
- **appToken**: authenticates the **bot/app itself** — obtained via `GET /v1/apptoken/create` (auto-managed by SDK)
- **userToken**: authenticates a **specific Lansenger user** — obtained via OAuth2 code exchange
- **refreshToken**: long-lived (30 days) — used to refresh expired userToken

## OAuth2 Flow (3 Steps)

### Step 1: Build authorize URL → redirect user

```python
client = LansengerClient(
    app_id="...", app_secret="...",
    passport_url="https://passport-xxx.domain",  # REQUIRED for OAuth2
)

auth_url = client.build_authorize_url(
    redirect_uri="https://myapp.com/callback",
    scope="basic_userinfor",           # or scope=["basic_userinfor", "other_scope"]
    # state auto-generated UUID for CSRF protection
)
# Redirect user to auth_url in browser, or send as link_card
```

- `passport_url` is a **separate domain** from `api_gateway_url` — the OAuth2 authorize page lives on the passport domain
- `redirect_uri` domain must be in the app's trusted domain list on the Lansenger developer console
- Returns: full authorize URL string

### Step 2: Parse callback → exchange code for tokens

After user authorizes, Lansenger redirects to `redirect_uri?code=XXX&state=YYY`:

```python
# Parse the callback
callback = LansengerClient.parse_authorize_callback("code=XXX&state=YYY")
# or: callback = LansengerClient.parse_authorize_callback({"code": "XXX", "state": "YYY"})

# Validate state (CSRF protection)
if not LansengerClient.validate_callback_state(callback["state"], expected_state):
    raise Exception("CSRF state mismatch")

# Exchange code for userToken + refreshToken
token_result = await client.exchange_code(callback["code"], redirect_uri="https://myapp.com/callback")
# token_result.user_token, token_result.refresh_token, token_result.staff_id
```

- Code is valid for **5 minutes**, **one-time use only**
- Returns: `UserTokenResult` — userToken, refreshToken, staffId, scope, state, expires_in (7200s), refresh_expires_in (30 days)

### Step 3: Refresh expired userToken

```python
token_result = await client.refresh_user_token(refresh_token="previousRefreshToken", scope="basic_userinfor")
# token_result.user_token, token_result.refresh_token (NEW — old one invalidated)
```

- **Always use the returned refreshToken** for subsequent refreshes — the old one is invalidated
- Total validity does NOT extend — only remaining time from the original 30-day grant
- If refreshToken has expired, must re-initiate full OAuth2 flow (Step 1)

## Fetch User Info (with userToken)

```python
user_info = await client.fetch_user_info(user_token=token_result.user_token)
# user_info.staff_id, user_info.name, user_info.org_id, user_info.email, user_info.mobile_phone
```

- Returns: `UserInfoResult` — staffId, name, orgId, orgName, avatarId, avatarUrl, mobilePhone, email, employeeNumber, loginName, externalId, department
- Note: `orgName` field handles both `orgname` (lowercase) and `orgName` fallbacks

## Sync Client

```python
from lansenger_sdk import LansengerSyncClient

client = LansengerSyncClient.from_env()
# Step 1: auth_url = client.build_authorize_url(redirect_uri="...")
# Step 2: parse + exchange are async → use LansengerClient for OAuth2 steps
# Step 3: refresh is async → use LansengerClient
# fetch_user_info is async → use LansengerClient

# Note: OAuth2 exchange/refresh require async HTTP calls.
# For sync usage, the authorize URL builder and callback parsing work on SyncClient:
auth_url = client.build_authorize_url(redirect_uri="...")
callback = LansengerSyncClient.parse_authorize_callback("code=XXX&state=YYY")
```

## Configuration

```python
# OAuth2 requires passport_url — set via env or direct param
export LANSENGER_APP_ID=your_app_id
export LANSENGER_APP_SECRET=your_app_secret
export LANSENGER_PASSPORT_URL=https://passport-xxx.domain

client = LansengerClient.from_env()  # reads all env vars
```

## Common Mistakes

| Wrong | Right |
|-------|-------|
| Using appToken for user-level ops (contacts, search) | Use userToken via OAuth2 |
| Storing old refreshToken after refresh | Always store the NEW refreshToken from refresh result |
| Skipping state validation in OAuth2 callback | Always validate callback_state matches expected |
| Using passport_url as api_gateway_url | They are separate domains |
| Forgetting to set passport_url for OAuth2 | Required — raises LansengerConfigError if missing |