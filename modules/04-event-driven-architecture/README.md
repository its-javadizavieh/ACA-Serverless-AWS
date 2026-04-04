# Module 4 – Event-Driven Architecture

**Duration:** 10 hours  
**Lab:** [Lab 05 – Event Fan-Out with SNS & SQS](../../labs/lab-05-sns-sqs-fanout/README.md)

---

## Learning Objectives

After completing this module you will be able to:

- Explain the principles of event-driven architecture (EDA).
- Use Amazon SNS for pub/sub fan-out messaging.
- Use Amazon SQS for reliable, decoupled message queuing.
- Use Amazon EventBridge as an enterprise event bus.
- Implement common EDA patterns: fan-out, saga, event sourcing.
- Configure Dead-Letter Queues (DLQs) and error handling strategies.

---

## 1. Event-Driven Architecture Principles

### 1.1 What Is EDA?

> "An architectural paradigm where **events** are the primary means by which system components communicate and trigger actions."

**Key concepts:**
- **Event** – a record of something that happened (immutable, past-tense).
- **Event producer** – emits events (e.g., an order service).
- **Event consumer** – reacts to events (e.g., an inventory service).
- **Event broker** – routes events between producers and consumers (SNS, EventBridge, Kafka).

### 1.2 EDA vs. Request/Response

| Aspect | Request/Response | Event-Driven |
|--------|-----------------|--------------|
| Coupling | Tight (caller knows callee) | Loose (producer doesn't know consumers) |
| Scalability | Limited by consumer capacity | Consumers scale independently |
| Availability | Caller fails if callee is down | Events buffer in broker |
| Complexity | Simple | Higher (eventual consistency) |

### 1.3 Benefits in Serverless

- **Zero-idle cost** – consumers only run when there are events.
- **Natural backpressure** – SQS queues absorb traffic spikes.
- **Independent scaling** – each consumer scales to its own throughput.
- **Resilience** – DLQs capture failed events for reprocessing.

---

## 2. Amazon SNS (Simple Notification Service)

### 2.1 Core Concepts

- **Topic** – a logical access point that acts as a communication channel.
- **Publisher** – sends a message to a topic.
- **Subscriber** – receives messages from a topic.
- **Subscription** – links a subscriber (endpoint) to a topic.

### 2.2 Supported Subscription Protocols

| Protocol | Use Case |
|----------|---------|
| Lambda | Invoke Lambda function |
| SQS | Fan-out to a queue |
| HTTP/HTTPS | Webhook |
| Email / Email-JSON | Human notification |
| SMS | Mobile text message |
| Application | Mobile push (APNs, GCM) |
| Firehose | Stream to S3/Redshift |

### 2.3 Fan-Out Pattern

```
                ┌──────────────────┐
Publisher ─────►│   SNS Topic      │
                └──┬───────┬───────┘
                   │       │
             ┌─────▼──┐  ┌─▼──────┐
             │SQS Q 1 │  │SQS Q 2 │
             └─────┬──┘  └────┬───┘
                   │          │
            ┌──────▼──┐  ┌────▼────┐
            │Lambda 1 │  │Lambda 2 │
            └─────────┘  └─────────┘
```

### 2.4 Message Filtering

Subscribers can apply a **filter policy** to receive only relevant messages.

```json
{
  "eventType": ["order.created", "order.updated"],
  "priority": [{ "numeric": [">", 5] }]
}
```

### 2.5 SNS FIFO Topics

- Strict message ordering within a message group.
- Exactly-once delivery (deduplication ID).
- Only supports SQS FIFO queues as subscribers.

### 2.6 Publishing a Message

```python
import boto3, json

sns = boto3.client("sns")

sns.publish(
    TopicArn="arn:aws:sns:us-east-1:123456789012:OrderEvents",
    Message=json.dumps({
        "orderId": "42",
        "status": "created",
        "customerId": "cust-99"
    }),
    MessageAttributes={
        "eventType": {
            "DataType": "String",
            "StringValue": "order.created"
        }
    }
)
```

---

## 3. Amazon SQS (Simple Queue Service)

### 3.1 Queue Types

| Feature | Standard Queue | FIFO Queue |
|---------|---------------|------------|
| Throughput | Nearly unlimited | 3,000 msg/s (with batching) |
| Ordering | Best-effort | Strict (per group ID) |
| Delivery | At-least-once | Exactly-once |
| Deduplication | Not guaranteed | Yes (deduplication ID) |

### 3.2 Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| Visibility Timeout | Time a consumer has to process a message | 30 s |
| Message Retention | How long messages stay in queue | 4 days (max 14) |
| Max Message Size | Maximum payload | 256 KB |
| Receive Message Wait | Long polling duration | 0 (short polling) |
| Max Receive Count | Before sending to DLQ | – |

### 3.3 Lambda Event Source Mapping

When SQS triggers Lambda, the service polls the queue and invokes Lambda in batches.

```yaml
Events:
  SQSTrigger:
    Type: SQS
    Properties:
      Queue: !GetAtt MyQueue.Arn
      BatchSize: 10
      FunctionResponseTypes:
        - ReportBatchItemFailures   # partial batch response
```

### 3.4 Partial Batch Response (ReportBatchItemFailures)

Allow Lambda to return only **failed** message IDs, so successful messages are not re-processed.

```python
def handler(event, context):
    failures = []
    for record in event["Records"]:
        try:
            process(record["body"])
        except Exception as e:
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}
```

### 3.5 Dead-Letter Queues (DLQ)

A DLQ receives messages that could not be processed successfully after `maxReceiveCount` attempts.

```yaml
MyQueue:
  Type: AWS::SQS::Queue
  Properties:
    RedrivePolicy:
      deadLetterTargetArn: !GetAtt MyDLQ.Arn
      maxReceiveCount: 3

MyDLQ:
  Type: AWS::SQS::Queue
  Properties:
    MessageRetentionPeriod: 1209600  # 14 days
```

---

## 4. Amazon EventBridge

### 4.1 Overview

EventBridge is a **serverless event bus** that connects AWS services, SaaS applications, and your own applications.

**Three types of event buses:**
1. **Default event bus** – receives events from AWS services.
2. **Custom event bus** – receives events from your applications.
3. **Partner event bus** – receives events from SaaS partners (Zendesk, Shopify, etc.).

### 4.2 Event Structure

```json
{
  "version": "0",
  "id": "uuid",
  "source": "com.myapp.orders",
  "detail-type": "Order Created",
  "time": "2024-01-15T10:00:00Z",
  "account": "123456789012",
  "region": "us-east-1",
  "detail": {
    "orderId": "42",
    "customerId": "cust-99",
    "total": 99.99
  }
}
```

### 4.3 Event Rules & Patterns

Rules match events based on patterns and route them to targets.

```json
{
  "source": ["com.myapp.orders"],
  "detail-type": ["Order Created"],
  "detail": {
    "total": [{ "numeric": [">=", 100] }]
  }
}
```

### 4.4 Targets

EventBridge rules can route events to:
- Lambda, Step Functions, SQS, SNS
- API Gateway, EventBridge API Destinations (any HTTP endpoint)
- Kinesis Data Streams, Firehose
- ECS tasks, CodeBuild, CodePipeline

### 4.5 Sending Events

```python
import boto3, json
from datetime import datetime

events = boto3.client("events")

events.put_events(
    Entries=[{
        "Source": "com.myapp.orders",
        "DetailType": "Order Created",
        "Detail": json.dumps({"orderId": "42", "total": 150.00}),
        "EventBusName": "my-app-bus"
    }]
)
```

### 4.6 EventBridge Pipes

Connect event sources directly to targets with optional enrichment and filtering:

```
SQS Queue ──► [filter] ──► [enrich with Lambda] ──► [transform] ──► Step Functions
```

---

## 5. EDA Patterns

### 5.1 Event Fan-Out

One event triggers multiple independent consumers simultaneously.

**Use case:** Order placed → notify warehouse + update CRM + send confirmation email.

### 5.2 Saga Pattern (Choreography-based)

Distributed transactions across microservices using compensating events.

```
OrderService          InventoryService        PaymentService
     │                      │                      │
     │── OrderCreated ──────►│                      │
     │                      │── InventoryReserved ─►│
     │                      │                      │── PaymentCharged
     │                      │                      │
     │◄── if payment fails ─ CompensateInventory ◄──│
```

### 5.3 Event Sourcing

Store all state changes as a sequence of immutable events.

```
Events: [Created, ItemAdded, ItemRemoved, Checkout, PaymentConfirmed]
Current state = replay of all events
```

### 5.4 CQRS (Command Query Responsibility Segregation)

Separate read and write models, often combined with event sourcing.

```
Commands (writes) ──► Write Model ──► Events ──► Read Model
Queries (reads)   ◄── Read Model (optimised for read patterns)
```

---

## 6. Hands-On: Lab 05

➡️ [Lab 05 – Event Fan-Out with SNS & SQS](../../labs/lab-05-sns-sqs-fanout/README.md)

**What you'll build:**
- An SNS topic (`OrderEvents`) with two SQS queue subscribers.
- Lambda consumers for each queue (email notification + warehouse update).
- Message filtering so each consumer receives only relevant event types.
- A DLQ on each SQS queue with a CloudWatch alarm.
- An EventBridge rule that routes high-value orders (> $100) to a VIP queue.

---

## 7. Key Takeaways

- SNS is for **pub/sub fan-out**; SQS is for **reliable queuing**.
- EventBridge is the recommended event bus for complex routing and SaaS integration.
- Always configure DLQs to capture failed messages.
- Use **partial batch response** with SQS + Lambda to avoid reprocessing successful messages.
- FIFO queues and topics guarantee ordering and exactly-once delivery at the cost of throughput.

---

## 📖 Further Reading

- [SNS Developer Guide](https://docs.aws.amazon.com/sns/latest/dg/welcome.html)
- [SQS Developer Guide](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html)
- [EventBridge User Guide](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html)
- [AWS re:Invent – Event-Driven Architectures](https://www.youtube.com/watch?v=NrkVBtb1V5E)

---

*Previous Module → [Module 3: API Gateway](../03-api-gateway/README.md)*  
*Next Module → [Module 5: Data Services](../05-data-services/README.md)*
