---
name: lansenger-departments
description: Lansenger department APIs — navigate org hierarchy, fetch department detail/children, and list department staff
license: MIT
metadata:
  sdk: lansenger-sdk
  platform: lansenger
  category: org_structure
  pip: pip install lansenger-sdk
---

# Lansenger Departments API

Lansenger SDK provides department APIs for navigating the org hierarchy — department detail, child departments, and staff listing. These are org/app bot APIs requiring `appToken`, optionally accepting `userToken`.

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `fetch_department_detail` | GET /v1/departments/:deptId/fetch | Department detail info |
| `fetch_department_children` | GET /v1/departments/:deptId/children/fetch | Child departments |
| `fetch_department_staffs` | GET /v1/departments/:deptId/staffs/fetch | Department staff list (paginated) |

## SDK Method Reference

### 1. Fetch department detail

```python
result = await client.fetch_department_detail(
    department_id="524288-0",  # root department ID format
    tag_id="tagId123",         # optional tag filter
)
# result.id, result.name, result.parent_id, result.has_children, result.normal_members
# result.order, result.external_id, result.tags, result.leaders, result.emails
```

- Returns: `DepartmentDetailResult` — id, name, external_id, parent_id, order, has_children, normal_members, inactive_members, frozen_members, deleted_members, tags, ancestor_departments, leaders, emails, phones, addresses, introductions, dept_type
- Root department ID is typically `"524288-0"` — start here to browse the org tree

### 2. Fetch child departments

```python
result = await client.fetch_department_children(department_id="parentDeptId")
# result.departments — list of child department dicts
```

- Returns: `DepartmentChildrenResult` — departments (list of dicts with id, name, etc.)

### 3. Fetch department staff list (paginated)

```python
result = await client.fetch_department_staffs(
    department_id="deptId123",
    page=1,
    page_size=100,
)
# result.staffs, result.total, result.has_more
```

- Returns: `DepartmentStaffsResult` — has_more, total, staffs (list of staff dicts)
- Default pagination: page=1, page_size=100

## Sync Client

```python
from lansenger_sdk import LansengerSyncClient

client = LansengerSyncClient.from_env()
result = client.fetch_department_detail(department_id="524288-0")
result = client.fetch_department_children(department_id="deptId")
result = client.fetch_department_staffs(department_id="deptId", page=1)
```

## Common Patterns

### Walk the org tree from root

```python
root = await client.fetch_department_detail(department_id="524288-0")
if root.has_children:
    children = await client.fetch_department_children(department_id="524288-0")
    for dept in children.departments:
        print(dept["id"], dept["name"])
        # Recurse into each child department...
```

### Get all staff in a department

```python
page = 1
all_staff = []
while True:
    result = await client.fetch_department_staffs(department_id="deptId", page=page, page_size=100)
    all_staff.extend(result.staffs or [])
    if not result.has_more:
        break
    page += 1
```

### Combine with contacts: find department → get staff → get profile

```python
staffs = await client.fetch_department_staffs(department_id="deptId")
for s in (staffs.staffs or []):
    detail = await client.fetch_staff_basic_info(staff_id=s["staffId"])
    print(detail.name, detail.org_name)
```