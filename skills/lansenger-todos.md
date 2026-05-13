# Lansenger Unified Todo (4.33)

Lansenger SDK provides unified todo/task APIs for creating, updating, querying, and managing todo tasks. These are org/app bot APIs — they require `appToken` and optionally accept `userToken`.

## Todo Status & Type Codes

| Code | Meaning |
|------|---------|
| 11 | 待阅 (pending-read) |
| 12 | 已阅 (read) |
| 21 | 待办 (pending-do) |
| 22 | 已办 (done) |

| Code | Type |
|------|------|
| 1 | 通知 (notification) |
| 2 | 审批 (approval) |

Constants available: `TODO_TODO_STATUS_PENDING_READ`, `TODO_TODO_STATUS_READ`, `TODO_TODO_STATUS_PENDING_DO`, `TODO_TODO_STATUS_DONE`, `TODO_TYPE_NOTIFICATION`, `TODO_TYPE_APPROVAL`

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `create_todo_task` | POST /xtra/task/unified/v1/todotask/create | Create a todo task |
| `update_todo_task` | POST /xtra/task/unified/v1/todotask/info/update | Update todo content |
| `update_todo_task_status` | POST /xtra/task/unified/v1/todotask/status/update | Update todo status |
| `delete_todo_task` | POST /xtra/task/unified/v1/sender/todotask/delete | Delete (sender only) |
| `fetch_todo_task_list` | POST /xtra/task/unified/v1/todotask/list/fetch | Query all todos |
| `fetch_todo_task_by_source_id` | POST /xtra/task/unified/v1/todotask/info/fetchbysourceid | Query by sourceId |
| `fetch_todo_task_by_id` | POST /xtra/task/unified/v1/todotask/info/fetch | Query by todotaskId |
| `fetch_todo_task_status_counts` | POST /xtra/task/unified/v1/todotask/status/countList/fetch | Status count stats |
| `update_executor_status` | POST /xtra/task/unified/v1/todotask/executor/status/update | Update executor status |
| `add_executors` | POST /xtra/task/unified/v1/todotask/executor/create | Add executors |
| `delete_executors` | POST /xtra/task/unified/v1/todotask/executor/delete | Delete executors |
| `fetch_executor_list` | POST /xtra/task/unified/v1/todotask/executor/list/fetch | Get executor list |

Note: Todo endpoints use `/xtra/task/unified/v1/` path prefix (not standard `/v1/` or `/v2/`).

## SDK Method Reference

### 1. Create a todo task

```python
from lansenger_sdk import TODO_TYPE_NOTIFICATION, TODO_TODO_STATUS_PENDING_DO

result = await client.create_todo_task(
    title="请审批报销单",
    link="https://app.example.com/approval/123",
    pc_link="https://pc.app.example.com/approval/123",
    executor_ids=["staffOpenId1", "staffOpenId2"],
    org_id="orgId123",
    type=TODO_TYPE_APPROVAL,               # 1=通知, 2=审批
    source_id="approval-123",              # optional dedup key
    desc="报销金额500元",
)
# result.todotask_id — created task ID
```

- Returns: `TodoTaskCreateResult` — todotask_id
- **Required**: title, link, pc_link, executor_ids, org_id
- Optional: type (default 1), source_id, desc, sender_id

### 2. Update todo task content

```python
result = await client.update_todo_task(
    todotask_id="taskOpenId",
    title="审批已更新",
    link="https://app.example.com/approval/123",
    pc_link="https://pc.app.example.com/approval/123",
    org_id="orgId123",
    desc="更新内容",
)
# result.todotask_id
```

- Returns: `TodoTaskCreateResult` — todotask_id
- **Required**: todotask_id, title, org_id

### 3. Update todo task status

```python
from lansenger_sdk import TODO_TODO_STATUS_DONE

result = await client.update_todo_task_status(
    todotask_id="taskOpenId",
    status=TODO_TODO_STATUS_DONE,          # "22"
    org_id="orgId123",
    staff_id="executorOpenId",             # optional: which executor
)
```

- Returns: `TodoTaskCreateResult` — todotask_id
- **Required**: todotask_id, status, org_id
- Valid statuses: "11"(待阅), "12"(已阅), "21"(待办), "22"(已办)

### 4. Delete a todo task (sender only)

```python
result = await client.delete_todo_task(
    todotask_id="taskOpenId",
    org_id="orgId123",
)
```

- Returns: `TodoTaskCreateResult` — todotask_id
- **Required**: todotask_id, org_id
- Only the sender (creator) can delete a todo task

### 5. Fetch todo task list

```python
result = await client.fetch_todo_task_list(
    org_id="orgId123",
    staff_id="staffOpenId",               # optional: filter by executor
    app_ids=["appId1"],                   # optional: filter by app
    status_list=["21", "22"],             # optional: filter by status
)
# result.total, result.todotask_list
```

- Returns: `TodoTaskListResult` — total, todotask_list

### 6. Fetch todo by sourceId

```python
result = await client.fetch_todo_task_by_source_id(
    source_id="approval-123",
    org_id="orgId123",
)
# result.todotask_id, result.title, result.status, result.executor_ids
```

- Returns: `TodoTaskInfoResult` — todotask_id, source_id, title, desc, status, type, link, pc_link, sender_id, executor_ids, create_time, app_id

### 7. Fetch todo by todotaskId

```python
result = await client.fetch_todo_task_by_id(
    todotask_id="taskOpenId",
    org_id="orgId123",
)
# result.todotask_id, result.title, result.status
```

- Returns: `TodoTaskInfoResult` (same fields as above)

### 8. Fetch status counts

```python
result = await client.fetch_todo_task_status_counts(
    staff_id="staffOpenId",
    org_id="orgId123",
    app_id="appId1",                      # optional: filter by app
)
# result.status_counts — list of {status, count} dicts
```

- Returns: `TodoTaskStatusCountResult` — status_counts

### 9-12. Executor management

```python
# Update executor status
result = await client.update_executor_status(
    executor_status_list=[{"executorId": "staffId", "todotaskId": "taskId", "status": "22"}],
    org_id="orgId123",
)

# Add executors
result = await client.add_executors(
    executor_ids=["staffOpenId3", "staffOpenId4"],
    org_id="orgId123",
    todotask_id="taskOpenId",
)

# Delete executors
result = await client.delete_executors(
    executor_ids=["staffOpenId3"],
    org_id="orgId123",
    todotask_id="taskOpenId",
)

# Fetch executor list
result = await client.fetch_executor_list(
    todotask_id="taskOpenId",
    org_id="orgId123",
    status_list=["21"],                   # optional: filter by executor status
)
# result.total, result.executor_list
```

## Sync Client

```python
from lansenger_sdk import LansengerSyncClient, TODO_TODO_STATUS_DONE

client = LansengerSyncClient.from_env()
result = client.create_todo_task(title="审批", link="l", pc_link="p", executor_ids=["s1"], org_id="o")
result = client.fetch_todo_task_list(org_id="orgId123")
result = client.update_todo_task_status(todotask_id="t1", status=TODO_TODO_STATUS_DONE, org_id="o1")
```

## Common Patterns

### Create a todo and notify the executor

```python
todo = await client.create_todo_task(
    title="请审批报销单", link="https://app.com/a/1", pc_link="https://pc.app.com/a/1",
    executor_ids=["staff1"], org_id="org1", type=TODO_TYPE_APPROVAL,
)
if todo.success:
    await client.send_text(chat_id="staff1", content=f"您有一条新的待办任务：请审批报销单")
```

### Batch query all pending todos for a user

```python
counts = await client.fetch_todo_task_status_counts(staff_id="staffId", org_id="orgId")
for item in counts.status_counts:
    print(f"Status {item.get('status')}: {item.get('count')} tasks")
```