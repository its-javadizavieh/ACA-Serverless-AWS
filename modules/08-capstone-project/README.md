# Module 8 – Capstone Project

**Duration:** 8 hours

---

## Overview

In this capstone module you will design and deploy a **complete, production-ready serverless application** on AWS, applying every concept from the course.

**The Project: ACA ShopFlow** – A serverless e-commerce order management platform.

---

## Architecture

```
                    ┌──────────────┐
Browser / Mobile ──►│ CloudFront   │
                    │ + S3 (SPA)   │
                    └──────┬───────┘
                           │ HTTPS
                    ┌──────▼───────┐
                    │ API Gateway  │
                    │  (HTTP API)  │
                    └──┬───┬───┬───┘
              ┌────────┘   │   └──────────┐
              │            │              │
      ┌───────▼──┐  ┌──────▼──┐  ┌───────▼──┐
      │ Orders   │  │Products │  │ Users    │
      │ Lambda   │  │ Lambda  │  │ Lambda   │
      └───────┬──┘  └──────┬──┘  └───────┬──┘
              │            │              │
              └─────┬──────┘              │
                    │                     │
             ┌──────▼──────┐      ┌───────▼────┐
             │  DynamoDB   │      │  Cognito   │
             │ (orders +   │      │ User Pool  │
             │  products)  │      └────────────┘
             └──────┬──────┘
                    │ Streams
             ┌──────▼──────┐
             │  EventBridge│
             └──┬──────┬───┘
                │      │
       ┌────────▼─┐  ┌──▼──────────────────┐
       │  SNS     │  │  Step Functions       │
       │ (notify) │  │  (order workflow)     │
       └────┬─────┘  └────────────┬──────────┘
            │                     │
      ┌─────▼────┐         ┌──────▼──────┐
      │  SQS     │         │  Lambda     │
      │(email Q) │         │(fulfillment)│
      └─────┬────┘         └─────────────┘
            │
      ┌─────▼──────┐
      │  Lambda    │
      │(email send)│
      └────────────┘
```

---

## Functional Requirements

### User Stories

1. **Customer Registration & Login**
   - Users can register with email and password (Cognito User Pool).
   - Users can log in and receive a JWT token.

2. **Product Catalogue**
   - Authenticated users can browse products (GET /products).
   - Admins can add/update/delete products.
   - Products are stored in DynamoDB.

3. **Order Placement**
   - Customers can create an order (POST /orders).
   - An order triggers a Step Functions workflow:
     1. Validate product availability.
     2. Reserve inventory.
     3. Process payment (simulated).
     4. Send confirmation email (via SQS → Lambda).
     5. Update order status in DynamoDB.

4. **Order Tracking**
   - Customers can view their orders (GET /orders/{id}).
   - Order status updates in real-time (DynamoDB Streams → EventBridge).

5. **Notifications**
   - Email notifications on order status changes (SNS → SQS → Lambda).

---

## Non-Functional Requirements

| Requirement | Target |
|------------|--------|
| API P99 latency | < 500 ms |
| Availability | 99.9 % |
| Scalability | Auto-scale from 0 to 10,000 req/s |
| Security | All endpoints authenticated; secrets in Secrets Manager |
| Observability | CloudWatch Logs + X-Ray tracing |
| IaC | 100 % CDK or SAM (no manual console changes) |
| CI/CD | Automated deployment on merge to main |
| Cost | Pay-per-use; no idle servers |

---

## Project Milestones

### Milestone 1 – Foundation (1 hour)
- [ ] Create CDK or SAM project structure.
- [ ] Set up DynamoDB table with single-table design.
- [ ] Define access patterns and key schema.
- [ ] Deploy empty stack.

### Milestone 2 – Authentication (1 hour)
- [ ] Create Cognito User Pool and User Pool Client.
- [ ] Configure HTTP API JWT Authorizer.
- [ ] Test registration and login flow.

### Milestone 3 – Products API (1 hour)
- [ ] Implement `GET /products` and `GET /products/{id}`.
- [ ] Implement `POST /products` (admin only via Cognito groups).
- [ ] Write unit tests for Lambda handlers.

### Milestone 4 – Orders API & Step Functions (2 hours)
- [ ] Implement `POST /orders` → triggers Step Functions.
- [ ] Build the order workflow state machine.
- [ ] Implement inventory reservation Lambda.
- [ ] Implement simulated payment Lambda with Retry/Catch.

### Milestone 5 – Notifications (1 hour)
- [ ] Configure DynamoDB Streams → EventBridge rule.
- [ ] Set up SNS topic and SQS email queue.
- [ ] Implement email notification Lambda.

### Milestone 6 – Frontend & CI/CD (1.5 hours)
- [ ] Deploy a simple React/HTML static site to S3 + CloudFront.
- [ ] Configure GitHub Actions / CodePipeline for automated deployment.
- [ ] Add staging and production environments.

### Milestone 7 – Observability & Cleanup (0.5 hours)
- [ ] Enable X-Ray tracing on all Lambda functions and API Gateway.
- [ ] Create a CloudWatch Dashboard.
- [ ] Configure CloudWatch Alarms for error rates.
- [ ] Verify and clean up resources (tag all with `Project: shopflow`).

---

## DynamoDB Single-Table Design

```
Entity      PK                   SK                    Attributes
──────────  ───────────────────  ─────────────────────  ──────────────────────
User        USER#{userId}        PROFILE               email, name, createdAt
Product     PRODUCT#{productId}  METADATA              name, price, stock, category
Order       ORDER#{orderId}      METADATA              customerId, total, status, createdAt
Order Item  ORDER#{orderId}      ITEM#{productId}      qty, price
```

**GSIs:**
- `GSI1`: `GSI1PK = CUSTOMER#{customerId}`, `SK` → list orders by customer
- `GSI2`: `GSI2PK = STATUS#{status}`, `SK = createdAt` → list orders by status

---

## Step Functions – Order Workflow

```json
{
  "Comment": "ACA ShopFlow Order Processing",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:ValidateOrderFunction",
      "Retry": [{ "ErrorEquals": ["States.ALL"], "MaxAttempts": 2 }],
      "Catch": [{ "ErrorEquals": ["ValidationError"], "Next": "OrderInvalid" }],
      "Next": "ReserveInventory"
    },
    "ReserveInventory": {
      "Type": "Map",
      "ItemsPath": "$.items",
      "MaxConcurrency": 5,
      "Iterator": {
        "StartAt": "ReserveItem",
        "States": {
          "ReserveItem": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:ReserveInventoryFunction",
            "End": true
          }
        }
      },
      "Next": "ProcessPayment"
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:ProcessPaymentFunction",
      "Retry": [{ "ErrorEquals": ["TransientError"], "MaxAttempts": 3, "IntervalSeconds": 2 }],
      "Catch": [{ "ErrorEquals": ["PaymentDeclinedException"], "Next": "ReleaseInventory" }],
      "Next": "SaveOrder"
    },
    "SaveOrder": {
      "Type": "Task",
      "Resource": "arn:aws:states:::dynamodb:putItem",
      "Parameters": {
        "TableName": "${TableName}",
        "Item": {
          "PK": { "S.$": "States.Format('ORDER#{}', $.orderId)" },
          "SK": { "S": "METADATA" },
          "status": { "S": "CONFIRMED" }
        }
      },
      "Next": "SendConfirmation"
    },
    "SendConfirmation": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "${OrderEventsTopic}",
        "Message.$": "States.JsonToString($)",
        "MessageAttributes": {
          "eventType": { "DataType": "String", "StringValue": "order.confirmed" }
        }
      },
      "End": true
    },
    "ReleaseInventory": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:ReleaseInventoryFunction",
      "Next": "OrderFailed"
    },
    "OrderInvalid": { "Type": "Fail", "Error": "OrderInvalid" },
    "OrderFailed": { "Type": "Fail", "Error": "PaymentFailed" }
  }
}
```

---

## Evaluation Criteria

| Criterion | Weight |
|-----------|--------|
| All milestones completed | 40 % |
| Code quality (clean, documented, tested) | 20 % |
| Security (least-privilege IAM, no secrets in code) | 15 % |
| IaC completeness (no manual resources) | 15 % |
| Observability (tracing, alarms) | 10 % |

---

## Delivery

- Push your code to a GitHub repository.
- Share the deployed API Gateway URL.
- Include a short `ARCHITECTURE.md` describing your design decisions.
- Demonstrate a full order flow (register → browse → order → track).

---

*Previous Module → [Module 7: Infrastructure as Code](../07-infrastructure-as-code/README.md)*
