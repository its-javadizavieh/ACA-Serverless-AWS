# Module 5 – Data Services

**Duration:** 8 hours  
**Lab:** [Lab 06 – DynamoDB Single-Table Design](../../labs/lab-06-dynamodb/README.md)

---

## Learning Objectives

After completing this module you will be able to:

- Apply DynamoDB single-table design for serverless applications.
- Model one-to-many and many-to-many relationships in DynamoDB.
- Use Global Secondary Indexes (GSIs) to support multiple access patterns.
- Work with DynamoDB Streams to react to data changes.
- Use Amazon S3 for object storage with Lambda event triggers.
- Choose the right data service for your serverless workload.

---

## 1. Amazon DynamoDB

### 1.1 Overview

DynamoDB is a fully managed, serverless NoSQL key-value and document database with:
- Single-digit millisecond performance at any scale.
- Automatic scaling (on-demand or provisioned with auto-scaling).
- Built-in high availability (3 AZs by default).
- Point-in-time recovery (PITR) and on-demand backups.

### 1.2 Core Data Model

| Concept | Description |
|---------|-------------|
| **Table** | Top-level container for items |
| **Item** | A collection of attributes (like a row) |
| **Attribute** | A name-value pair (like a column) |
| **Partition key (PK)** | Hash key – determines which partition stores the item |
| **Sort key (SK)** | Range key – orders items within a partition |
| **Composite key** | PK + SK combination (recommended) |

### 1.3 Capacity Modes

| Mode | Description | When to Use |
|------|-------------|-------------|
| **On-Demand** | Pay per request; auto-scales | Variable/unpredictable traffic |
| **Provisioned** | Set RCU/WCU; cheaper at steady load | Predictable traffic |
| **Provisioned + Auto Scaling** | Adjusts provisioned capacity | Gradual ramp-ups |

### 1.4 Reading Data

| Operation | Description | Cost |
|-----------|-------------|------|
| `GetItem` | Fetch a single item by PK (+ SK) | 1 RCU (strongly consistent) |
| `BatchGetItem` | Fetch up to 100 items | N RCUs |
| `Query` | Fetch items by PK + optional SK condition | Proportional to items returned |
| `Scan` | Read all items in a table | Expensive – avoid in production |

**RCU (Read Capacity Unit):** 1 strongly consistent read of up to 4 KB per second.

### 1.5 Writing Data

| Operation | Description | Cost |
|-----------|-------------|------|
| `PutItem` | Create or replace an item | 1 WCU per KB |
| `UpdateItem` | Update specific attributes | 1 WCU per KB |
| `DeleteItem` | Delete an item | 1 WCU per KB |
| `BatchWriteItem` | Up to 25 PutItem/DeleteItem | N WCUs |
| `TransactWriteItems` | Atomic multi-item write (ACID) | 2× WCUs |

**WCU (Write Capacity Unit):** 1 write of up to 1 KB per second.

---

## 2. Single-Table Design

### 2.1 Why Single-Table?

In relational databases, normalisation spreads data across many tables. In DynamoDB, **all access patterns must be served by the same table** because cross-table JOINs don't exist.

**Benefits:**
- Fewer network round-trips (get related data in one query).
- Lower cost (fewer table operations).
- Simpler operational model.

### 2.2 Generic Keys

Use generic attribute names (`PK`, `SK`) so different entity types can coexist:

```
PK              SK                   Attributes
──────────────  ───────────────────  ──────────────────────────────
CUSTOMER#c001   PROFILE              name, email, createdAt
CUSTOMER#c001   ORDER#o001           total, status, createdAt
CUSTOMER#c001   ORDER#o002           total, status, createdAt
ORDER#o001      ITEM#prod-a          qty, price
ORDER#o001      ITEM#prod-b          qty, price
PRODUCT#prod-a  METADATA             name, category, price
```

### 2.3 Access Patterns Example

For the e-commerce model above:

| Access Pattern | Operation | PK | SK Condition |
|----------------|-----------|-----|-------------|
| Get customer profile | GetItem | `CUSTOMER#{id}` | `PROFILE` |
| List all orders for a customer | Query | `CUSTOMER#{id}` | begins_with(`ORDER#`) |
| Get order details + items | Query | `ORDER#{id}` | — |
| Get a specific product | GetItem | `PRODUCT#{id}` | `METADATA` |

### 2.4 DynamoDB Condition Expressions

Prevent race conditions with conditional writes:

```python
table.put_item(
    Item={"PK": "ORDER#42", "SK": "STATUS", "status": "CREATED"},
    ConditionExpression="attribute_not_exists(PK)"  # only create if not exists
)
```

### 2.5 Update Expressions

```python
table.update_item(
    Key={"PK": "ORDER#42", "SK": "STATUS"},
    UpdateExpression="SET #s = :new_status, updatedAt = :ts",
    ConditionExpression="#s = :expected_status",
    ExpressionAttributeNames={"#s": "status"},
    ExpressionAttributeValues={
        ":new_status": "PROCESSING",
        ":expected_status": "CREATED",
        ":ts": datetime.utcnow().isoformat()
    }
)
```

---

## 3. Global Secondary Indexes (GSIs)

A GSI is an alternative index with a different partition key (and optional sort key).

### 3.1 Use Case: Query by Email

```
Table PK: CUSTOMER#{id}   SK: PROFILE
GSI1 PK:  email           SK: CUSTOMER#{id}
```

This allows:
- Main table: look up customer by ID.
- GSI1: look up customer by email (e.g., login).

### 3.2 GSI Design Principles

- GSIs replicate data → additional storage and write cost.
- GSIs can have **sparse** data (only items with the GSI PK attribute).
- Use sparse GSIs as filters (e.g., only ACTIVE orders appear in the GSI).

### 3.3 SAM/CloudFormation GSI Definition

```yaml
MyTable:
  Type: AWS::DynamoDB::Table
  Properties:
    BillingMode: PAY_PER_REQUEST
    KeySchema:
      - AttributeName: PK
        KeyType: HASH
      - AttributeName: SK
        KeyType: RANGE
    AttributeDefinitions:
      - AttributeName: PK
        AttributeType: S
      - AttributeName: SK
        AttributeType: S
      - AttributeName: GSI1PK
        AttributeType: S
    GlobalSecondaryIndexes:
      - IndexName: GSI1
        KeySchema:
          - AttributeName: GSI1PK
            KeyType: HASH
          - AttributeName: SK
            KeyType: RANGE
        Projection:
          ProjectionType: ALL
```

---

## 4. DynamoDB Streams & Change Data Capture

### 4.1 Overview

DynamoDB Streams captures a time-ordered log of item modifications. Lambda can poll the stream to react to changes.

**Stream view types:**
| View | What is captured |
|------|-----------------|
| `KEYS_ONLY` | Only PK and SK |
| `NEW_IMAGE` | Item after modification |
| `OLD_IMAGE` | Item before modification |
| `NEW_AND_OLD_IMAGES` | Both (most information) |

### 4.2 Lambda Integration

```yaml
Events:
  Stream:
    Type: DynamoDB
    Properties:
      Stream: !GetAtt MyTable.StreamArn
      StartingPosition: TRIM_HORIZON
      BatchSize: 100
      FunctionResponseTypes:
        - ReportBatchItemFailures
```

### 4.3 Processing Stream Records

```python
def handler(event, context):
    for record in event["Records"]:
        event_name = record["eventName"]  # INSERT, MODIFY, REMOVE
        if event_name == "INSERT":
            new_item = record["dynamodb"]["NewImage"]
            # Deserialize DynamoDB JSON
            item = {k: list(v.values())[0] for k, v in new_item.items()}
            print(f"New item created: {item}")
```

---

## 5. Amazon S3 for Serverless Applications

### 5.1 Common Serverless Patterns

| Pattern | Description |
|---------|-------------|
| **Static website hosting** | S3 + CloudFront for SPAs |
| **File upload trigger** | S3 event → Lambda → process file |
| **Data lake** | S3 as raw data store, Lambda for ETL |
| **Large payload workaround** | Store payloads > 256 KB in S3; pass S3 key in event |

### 5.2 S3 Event Notifications

```yaml
MyBucket:
  Type: AWS::S3::Bucket
  Properties:
    NotificationConfiguration:
      LambdaConfigurations:
        - Event: s3:ObjectCreated:*
          Filter:
            S3Key:
              Rules:
                - Name: prefix
                  Value: uploads/
                - Name: suffix
                  Value: .jpg
          Function: !GetAtt ProcessImageFunction.Arn
```

### 5.3 Pre-Signed URLs

Allow clients to upload/download files directly to/from S3 without going through Lambda:

```python
import boto3

s3 = boto3.client("s3")

def generate_upload_url(bucket, key, expiry=300):
    """Generate a pre-signed URL for direct upload to S3."""
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key, "ContentType": "image/jpeg"},
        ExpiresIn=expiry
    )

def generate_download_url(bucket, key, expiry=3600):
    """Generate a pre-signed URL for direct download from S3."""
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expiry
    )
```

### 5.4 S3 Best Practices

- Enable **server-side encryption** (SSE-S3 or SSE-KMS).
- Enable **versioning** for important buckets.
- Configure **lifecycle rules** to transition old objects to cheaper storage classes.
- Block public access unless hosting a public static site.
- Use **S3 Transfer Acceleration** for global uploads.

---

## 6. Choosing the Right Data Service

| Requirement | Recommended Service |
|------------|---------------------|
| Key-value / document store at scale | DynamoDB |
| Relational data with SQL | Aurora Serverless v2 |
| Full-text search | OpenSearch Serverless |
| Time-series data | Timestream |
| In-memory caching | ElastiCache (Redis/Memcached) |
| Object / file storage | S3 |
| Blob storage in Lambda | `/tmp` (up to 10 GB) |

---

## 7. Hands-On: Lab 06

➡️ [Lab 06 – DynamoDB Single-Table Design](../../labs/lab-06-dynamodb/README.md)

**What you'll build:**
- A DynamoDB table with a single-table design for customers and orders.
- Lambda functions for CRUD operations using the `boto3` resource API.
- A GSI for querying orders by status.
- DynamoDB Streams → Lambda to update an orders-by-status view.
- S3 integration: export order history to S3 as JSON.

---

## 8. Key Takeaways

- Design your DynamoDB table around **access patterns**, not entity types.
- Single-table design enables efficient, low-latency queries.
- GSIs allow querying data by attributes other than the primary key.
- Use DynamoDB Streams to trigger downstream processes on data changes.
- S3 pre-signed URLs are the serverless way to handle large file uploads.

---

## 📖 Further Reading

- [DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)
- [Alex DeBrie – The DynamoDB Book](https://www.dynamodbbook.com/)
- [DynamoDB Design Patterns – re:Invent](https://www.youtube.com/watch?v=HaEPXoXVf2k)
- [Amazon S3 Developer Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)

---

*Previous Module → [Module 4: Event-Driven Architecture](../04-event-driven-architecture/README.md)*  
*Next Module → [Module 6: Step Functions](../06-step-functions/README.md)*
