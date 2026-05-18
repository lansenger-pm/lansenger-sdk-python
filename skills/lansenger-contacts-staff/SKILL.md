---
name: lansenger-contacts-staff
description: Lansenger staff/contacts APIs — fetch staff basic/detailed info, department ancestors, ID mapping (phone/email→staffId), org extra fields, and staff search
license: MIT
metadata:
  sdk: lansenger-sdk
  platform: lansenger
  category: contacts
  pip: pip install lansenger-sdk
---

# Lansenger Contacts & Staff API

Lansenger SDK provides staff/contacts/org APIs for looking up organization member and org information. These are org/app bot APIs (not personal bots) — they require `appToken` and optionally accept `userToken` for user-scoped access.

## API Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `fetch_staff_basic_info` | GET /v1/staffs/:staffid/fetch | appToken | Staff basic info (name, avatar, org, departments) |
| `fetch_staff_detail` | GET /v1/staffs/:staffid/infor/fetch | appToken+userToken | Full profile (email, phone, education, career, etc.) |
| `fetch_department_ancestors` | GET /v1/staffs/:staffid/departmentancestors/fetch | appToken | Ancestor department chain for a staff member |
| `fetch_staff_id_mapping` | GET /v2/staffs/id_mapping/fetch | appToken | Map phone/email/employee_id → staffId |
| `fetch_org_extra_field_ids` | GET /v1/org/:orgid/extrafieldids/fetch | appToken | Org custom field ID list |
| `search_staff` | POST /v2/staffs/search | appToken+userToken/userId | Search staff by keyword |
| `fetch_org_info` | GET /v1/org/:orgid/fetch | appToken | Organization basic info |

## SDK Method Reference

### 1. Fetch staff basic info

```python
result = await client.fetch_staff_basic_info(staff_id="staffOpenId123", user_token="userToken456")
# result.org_id, result.name, result.gender, result.avatar_url, result.departments
```

- Returns: `StaffBasicInfoResult` — orgId, orgName, name, gender, signature, avatarUrl, avatarId, status, departments
- Optional: `user_token` for user-scoped access
- `orgName` field: API sometimes returns `orgname` (lowercase n) — SDK handles this fallback

### 2. Fetch staff detail (full profile)

```python
result = await client.fetch_staff_detail(staff_id="staffOpenId123", user_token="userToken456")
# result.email, result.mobile_phone, result.employee_number, result.education, result.career
```

- Returns: `StaffDetailResult` — name, signature, avatar, org (orgId, orgName), email, phone, mobile_phone, external_phone, extra_phones, employee_number, external_id, nationality, native_place, birthdate, id_number, gender, introduction, status, avatar_id, avatar_url, login_name, duties, parties, address, education, career, login_ways, tags, extra_field_set, leaders, join_date, departments
- **Requires org or personal auth** — providing `user_token` is recommended
- Note: API field `endData` (not `endDate`) — preserved as-is per Lansenger docs typo

### 3. Fetch department ancestors for a staff member

```python
result = await client.fetch_department_ancestors(staff_id="staffOpenId123", user_token="userToken456")
# result.ancestor_groups — list of ancestor department chains
```

- Returns: `DepartmentAncestorsResult` — ancestor_groups (list of list of dicts)
- Optional: `user_token`
- Each chain: `[{"id": "...", "name": "..."}, ...]`

### 4. Map identifier to staffId

```python
result = await client.fetch_staff_id_mapping(
    org_id="orgId123",
    id_type="mobile",       # employ_id | mobile | mail | login | external_id
    id_value="13800138000",
    user_token="userToken456",
)
# result.staff_id — the mapped staff openId
```

- Returns: `StaffIdMappingResult` — staff_id
- Optional: `user_token`
- **id_type options**: `employ_id`, `mobile`, `mail`, `login`, `external_id`

### 5. Fetch org extra field IDs

```python
result = await client.fetch_org_extra_field_ids(org_id="orgId123", page=1, page_size=1000, user_token="userToken456")
# result.extra_field_ids, result.total, result.has_more
```

- Returns: `ExtraFieldIdsResult` — has_more, total, extra_field_ids
- Optional: `user_token`
- page_size max: 100000

### 6. Search staff by keyword

```python
result = await client.search_staff(
    keyword="张三",
    user_token="userToken456",     # or user_id="staffOpenId"
    recursive=True,
    sector_ids=["deptOpenId1"],    # optional scope filter
    page=1,
    page_size=50,
)
# result.staff_info, result.total, result.has_more
```

- Returns: `StaffSearchResult` — has_more, total, staff_info (list of staff dicts)
- **Auth required**: one of `user_token` or `user_id` must be provided
- `recursive=True`: search sub-departments; `sector_ids`: limit search scope to specific departments
- page_size max: 100

### 7. Fetch organization info

```python
result = await client.fetch_org_info(org_id="orgId123")
# result.org_id, result.org_name, result.icon_url, result.org_max_member_limit, result.org_order_type
```

- Returns: `OrgInfoResult` — org_id, org_name, icon_url, org_max_member_limit, org_order_type, org_days_limit, org_billing_date
- Useful for verifying org existence and getting org-level metadata

## Sync Client

All methods available on `LansengerSyncClient` with identical signatures (non-async):

```python
from lansenger_sdk import LansengerSyncClient

client = LansengerSyncClient.from_env()
result = client.fetch_staff_basic_info(staff_id="staffOpenId123")
result = client.search_staff(keyword="张三", user_token="userToken456")
result = client.fetch_org_info(org_id="orgId123")
```

## Common Patterns

### Find staffId from phone number

```python
mapping = await client.fetch_staff_id_mapping(org_id="orgId", id_type="mobile", id_value="13800138000")
if mapping.success:
    staff_id = mapping.staff_id
```

### Get full staff profile

```python
detail = await client.fetch_staff_detail(staff_id=mapping.staff_id, user_token="userToken")
if detail.success:
    print(detail.name, detail.email, detail.mobile_phone)
```

### Browse org hierarchy by department

```python
ancestors = await client.fetch_department_ancestors(staff_id="staffId")
for chain in ancestors.ancestor_groups:
    for dept in chain:
        print(dept["name"])
```