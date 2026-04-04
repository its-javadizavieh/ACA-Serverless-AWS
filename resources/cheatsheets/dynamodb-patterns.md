# DynamoDB Design Patterns Cheat Sheet

## Key Design Principles

1. **Understand your access patterns FIRST** – design the table around queries, not entities.
2. **Use composite keys** (PK + SK) for hierarchical data.
3. **Use generic attribute names** (PK, SK) to allow multiple entity types in one table.
4. **Use GSIs for additional access patterns** – but only when needed (cost/write amplification).
5. **Avoid Scan** – always query with a known PK.

---

## Common Key Patterns

### User + Orders (One-to-Many)

```
Entity   PK               SK               Attributes
──────── ──────────────── ──────────────── ────────────────────────
User     USER#{userId}    PROFILE          name, email
Order    USER#{userId}    ORDER#{orderId}  total, status, createdAt
```

**Access patterns:**
- Get user profile: `GetItem(PK=USER#{id}, SK=PROFILE)`
- List user's orders: `Query(PK=USER#{id}, SK begins_with ORDER#)`

---

### Product Catalogue + Reviews (One-to-Many)

```
Entity   PK                   SK                    Attributes
──────── ──────────────────── ───────────────────── ────────────────
Product  PRODUCT#{productId}  METADATA              name, price, stock
Review   PRODUCT#{productId}  REVIEW#{reviewId}     rating, text, userId
```

**Access patterns:**
- Get product: `GetItem(PK=PRODUCT#{id}, SK=METADATA)`
- List reviews: `Query(PK=PRODUCT#{id}, SK begins_with REVIEW#)`
- Get specific review: `GetItem(PK=PRODUCT#{id}, SK=REVIEW#{id})`

---

### Many-to-Many (Teams + Members)

```
Entity        PK              SK              Attributes
────────────  ──────────────  ──────────────  ────────────────
Team          TEAM#{teamId}   METADATA        name, createdAt
User          USER#{userId}   METADATA        name, email
Membership    TEAM#{teamId}   USER#{userId}   role, joinedAt
Membership    USER#{userId}   TEAM#{teamId}   role, joinedAt
```

**Access patterns:**
- List team members: `Query(PK=TEAM#{id}, SK begins_with USER#)`
- List user's teams: `Query(PK=USER#{id}, SK begins_with TEAM#)`

---

### Hierarchical Data (Org / Dept / Employee)

```
PK               SK                       Entity
──────────────── ──────────────────────── ──────────
ORG#acme         ORG                      Organisation
ORG#acme         DEPT#engineering         Department
ORG#acme         DEPT#sales               Department
DEPT#engineering EMP#alice                Employee
DEPT#engineering EMP#bob                  Employee
```

---

## GSI Patterns

### Sparse GSI (index only active records)

```yaml
# Only items with GSI1PK attribute will appear in the index
# Use this to index only "active" or "flagged" records
GlobalSecondaryIndexes:
  - IndexName: ActiveOrders
    KeySchema:
      - AttributeName: GSI1PK   # e.g. "ACTIVE" (only set on active orders)
        KeyType: HASH
      - AttributeName: createdAt
        KeyType: RANGE
```

### Inverted Index (swap PK and SK)

Useful for querying child → parent relationships:

```
Main table:  PK=USER#{id}  SK=ORDER#{id}  → user's orders
GSI:         PK=ORDER#{id} SK=USER#{id}   → order's users (reverse lookup)
```

---

## Useful Python Snippets

### Query with begins_with

```python
from boto3.dynamodb.conditions import Key

results = table.query(
    KeyConditionExpression=(
        Key("PK").eq("USER#alice") & Key("SK").begins_with("ORDER#")
    )
)
```

### Paginate large results

```python
items = []
kwargs = {"KeyConditionExpression": Key("PK").eq("USER#alice")}
while True:
    response = table.query(**kwargs)
    items.extend(response["Items"])
    if "LastEvaluatedKey" not in response:
        break
    kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
```

### Conditional write (optimistic locking)

```python
try:
    table.update_item(
        Key={"PK": "ORDER#42", "SK": "METADATA"},
        UpdateExpression="SET #s = :new",
        ConditionExpression="#s = :expected",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":new": "SHIPPED", ":expected": "CONFIRMED"},
    )
except table.meta.client.exceptions.ConditionalCheckFailedException:
    # Another process changed the status first
    raise
```

### Atomic counter

```python
response = table.update_item(
    Key={"PK": "PRODUCT#widget", "SK": "METADATA"},
    UpdateExpression="ADD stock :delta",
    ConditionExpression="stock > :zero",        # prevent negative stock
    ExpressionAttributeValues={":delta": -1, ":zero": 0},
    ReturnValues="UPDATED_NEW",
)
```
