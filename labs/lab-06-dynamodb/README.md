# Lab 06 – DynamoDB Single-Table Design

**Module:** [Module 5 – Data Services](../../modules/05-data-services/README.md)  
**Duration:** ~90 minutes  
**Services:** DynamoDB, Lambda, S3

---

## Objective

Design a DynamoDB single-table for customers and orders, implement CRUD operations, and add a DynamoDB Streams consumer.

---

## Data Model

```
Entity      PK                    SK                    Attributes
──────────  ────────────────────  ───────────────────── ──────────────────────────
Customer    CUSTOMER#{customerId} PROFILE               name, email, createdAt
Order       CUSTOMER#{customerId} ORDER#{orderId}        total, status, createdAt
Order       ORDER#{orderId}       METADATA              customerId, total, status

GSI1: GSI1PK = status, SK = createdAt  (list orders by status)
```

---

## Directory Structure

```
lab-06-dynamodb/
├── README.md
├── template.yaml
├── src/
│   └── orders/
│       ├── app.py           ← CRUD Lambda
│       └── requirements.txt
└── events/
    ├── create_customer.json
    ├── create_order.json
    └── list_orders.json
```

---

## Step 1 – Deploy

```bash
cd labs/lab-06-dynamodb
sam build
sam deploy --guided
# Stack name: dynamodb-lab
```

---

## Step 2 – Create a Customer

```bash
aws lambda invoke \
  --function-name orders-manager \
  --payload file://events/create_customer.json \
  --cli-binary-format raw-in-base64-out \
  response.json && cat response.json
```

---

## Step 3 – Create Orders for the Customer

```bash
aws lambda invoke \
  --function-name orders-manager \
  --payload file://events/create_order.json \
  --cli-binary-format raw-in-base64-out \
  response.json && cat response.json
```

---

## Step 4 – List Orders by Customer

```bash
aws lambda invoke \
  --function-name orders-manager \
  --payload file://events/list_orders.json \
  --cli-binary-format raw-in-base64-out \
  response.json && cat response.json
```

---

## Step 5 – Explore with the Console

1. Open the DynamoDB console → your table.
2. Look at the **Explore items** tab.
3. Run a **PartiQL** query: `SELECT * FROM "orders-lab" WHERE PK = 'CUSTOMER#cust-001'`

---

## Step 6 – DynamoDB Streams

Check CloudWatch Logs for the stream consumer:

```bash
aws logs tail /aws/lambda/orders-stream-consumer --since 5m
```

Every time an order is created or updated, the stream consumer logs the change.

---

## Cleanup

```bash
sam delete --stack-name dynamodb-lab
```
