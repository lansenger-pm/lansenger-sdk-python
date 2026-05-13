# Lansenger Groups V2 API

Lansenger SDK provides group V2 APIs for creating groups, fetching group info/members, checking membership, and updating group settings and members. These are org/app bot APIs — they require `appToken` and optionally accept `userToken`.

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `create_group` | POST /v2/groups/create | Create a new group |
| `fetch_group_info` | GET /v2/groups/:groupId/info/fetch | Group detail info |
| `fetch_group_members` | GET /v2/groups/:groupId/members/fetch | Group member list (paginated) |
| `fetch_group_list` | GET /v2/groups/fetch | Group ID list (paginated) |
| `check_is_in_group` | GET /v2/groups/:groupId/members/is_in_group | Check if staff is in group |
| `update_group_info` | POST /v2/groups/:groupId/info/update (4.28.2) | Update group settings |
| `update_group_members` | POST /v2/groups/:groupId/members/update (4.28.5) | Add/remove group members |

Note: `query_groups()` (P0) uses the older `/v2/groups/fetch` endpoint under the `groups` endpoint group. `fetch_group_list()` (P1) uses the same endpoint under the `groups_v2` endpoint group. The two methods return identical data — prefer `fetch_group_list()` for consistency.

## SDK Method Reference

### 1. Create a group

```python
result = await client.create_group(
    name="项目讨论组",
    org_id="orgId123",
    owner_id="staffOpenId",
    description="项目讨论",
    staff_id_list=["staff1", "staff2", "staff3"],  # minimum 3 members if provided
    department_id_list=["dept1"],                   # add department members
)
# result.group_id, result.total_members, result.invalid_staff, result.invalid_department
```

- Returns: `CreateGroupResult` — group_id, total_members, invalid_staff, invalid_department
- **Required**: `name` + `org_id`
- **Constraint**: minimum 3 staff members if `staff_id_list` is provided
- Optional: owner_id, description, avatar_id, apply_request_id, apply_notes, apply_global_unique_id, apply_session_unique_id

### 2. Fetch group info

```python
result = await client.fetch_group_info(group_id="groupOpenId123")
# result.name, result.description, result.owner, result.creator, result.total_members
# result.state, result.manage_mode, result.is_public, result.max_members
```

- Returns: `GroupInfoResult` — name, description, avatar_id, avatar_url, owner, creator, state, manage_mode, location_share, needs_confirm, is_public, max_members, max_history_msg_count, total_members, remind_all, send_msg_status

### 3. Fetch group members (paginated)

```python
result = await client.fetch_group_members(
    group_id="groupOpenId123",
    page_offset=0,
    page_size=100,
)
# result.total_members, result.members
```

- Returns: `GroupMemberResult` — total_members, members (list)
- Default pagination: page_offset=0, page_size=100

### 4. Fetch group list (paginated)

```python
result = await client.fetch_group_list(page_offset=0, page_size=100)
# result.total_group_ids, result.group_ids
```

- Returns: `GroupListResult` — total_group_ids, group_ids (list of group openIds)
- Use this to discover group IDs before sending messages to groups

### 5. Check if staff is in group

```python
result = await client.check_is_in_group(
    group_id="groupOpenId123",
    staff_id="staffOpenId456",  # optional — defaults to bot's own membership
)
# result.is_in_group — True/False
```

- Returns: `IsInGroupResult` — is_in_group (bool)

### 6. Update group info (4.28.2)

```python
result = await client.update_group_info(
    group_id="groupOpenId123",
    name="新群名",
    description="新描述",
    owner_id="newOwnerOpenId",          # must be existing group member
    manage_mode=1,                      # 0=all manage, 1=owner only
    remind_all=True,                    # @mention enabled/disabled
    send_msg_status=False,              # group mute enabled/disabled
    user_token="userToken",
)
# result.success
```

- Returns: `UpdateGroupResult` — success
- Only sends keys you provide — partial updates are supported
- App must have robot capability for this operation
- Optional: name, description, avatar_id, owner_id, assistant, demote_assistant, manage_mode, location_share, needs_confirm, is_public, max_members, max_history_msg_count, remind_all, send_msg_status

### 7. Update group members (4.28.5)

```python
result = await client.update_group_members(
    group_id="groupOpenId123",
    add_user_list=["staff1", "staff2"],         # add these staff
    del_user_list=["staff3"],                    # remove these staff
    add_department_id_list=["dept1"],            # add dept members (not with robot identity)
    user_token="userToken",
)
# result.total_members, result.added_staff_count, result.deleted_staff_count
# result.invalid_staff, result.invalid_department
```

- Returns: `UpdateGroupMembersResult` — total_members, added_staff_count, deleted_staff_count, invalid_staff, invalid_department
- At least one of add_user_list, del_user_list, or add_department_id_list is required
- Robot identity cannot add department members (must use user_token)

## Sync Client

```python
from lansenger_sdk import LansengerSyncClient

client = LansengerSyncClient.from_env()
result = client.create_group(name="项目讨论组", org_id="orgId123")
result = client.fetch_group_info(group_id="groupOpenId123")
result = client.fetch_group_members(group_id="groupOpenId123")
result = client.fetch_group_list()
result = client.check_is_in_group(group_id="groupOpenId123", staff_id="staffId")
result = client.update_group_info(group_id="groupId", name="新群名")
result = client.update_group_members(group_id="groupId", add_user_list=["staff1"])
```

## Common Patterns

### Create a group and send a message to it

```python
group = await client.create_group(name="项目讨论组", org_id="orgId", staff_id_list=["s1", "s2", "s3"])
if group.success:
    await client.send_text(chat_id=group.group_id, content="群已创建！", is_group=True)
```

### Browse all groups the bot is in

```python
groups = await client.fetch_group_list(page_size=100)
for gid in groups.group_ids:
    info = await client.fetch_group_info(group_id=gid)
    print(info.name, info.total_members)

### Rename a group and add new members

```python
await client.update_group_info(group_id="groupId", name="项目讨论组V2")
await client.update_group_members(group_id="groupId", add_user_list=["staff4", "staff5"])
```