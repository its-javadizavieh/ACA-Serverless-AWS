# Lab 05 – Event Fan-Out with SNS & SQS

**Module:** [Module 4 – Event-Driven Architecture](../../modules/04-event-driven-architecture/README.md)  
**Duration:** ~90 minutes  
**Services:** SNS, SQS, Lambda, CloudWatch

---

## Objective

Implement the **fan-out** pattern:

```
Publisher Lambda ──► SNS Topic ──┬──► SQS Email Queue ──► Email Consumer Lambda
                                  └──► SQS Warehouse Queue ──► Warehouse Consumer Lambda
```

Also configure:
- Message filtering (warehouse only gets `order.created` events).
- Dead-Letter Queues on both SQS queues.
- CloudWatch Alarms on DLQ message count.

---

## Directory Structure

```
lab-05-sns-sqs-fanout/
├── README.md
├── template.yaml
├── src/
│   ├── publisher/
│   │   └── app.py           ← Publishes order events to SNS
│   ├── email_consumer/
│   │   └── app.py           ← Processes email notifications
│   └── warehouse_consumer/
│       └── app.py           ← Processes warehouse updates
└── events/
    └── publish.json         ← Test event for publisher
```

---

## Step 1 – Deploy

```bash
cd labs/lab-05-sns-sqs-fanout
sam build
sam deploy --guided
# Stack name: sns-sqs-fanout-lab
```

---

## Step 2 – Publish an Event

```bash
aws lambda invoke \
  --function-name order-event-publisher \
  --payload file://events/publish.json \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

---

## Step 3 – Verify Fan-Out

Check that both consumer Lambdas were invoked:

```bash
# Check email consumer logs
aws logs tail /aws/lambda/email-notification-consumer --since 5m

# Check warehouse consumer logs
aws logs tail /aws/lambda/warehouse-update-consumer --since 5m
```

---

## Step 4 – Test Message Filtering

Publish an event with `eventType = order.cancelled`. According to the filter policy on the warehouse queue, only the email consumer should receive it:

```bash
aws lambda invoke \
  --function-name order-event-publisher \
  --payload '{"orderId":"99","eventType":"order.cancelled","email":"test@example.com"}' \
  --cli-binary-format raw-in-base64-out \
  /dev/null
```

Verify only the email consumer logs show activity.

---

## Step 5 – Trigger the DLQ

Temporarily break the email consumer (introduce an error) and redeploy.  
Publish events, then check the DLQ:

```bash
aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name email-dlq --query QueueUrl --output text) \
  --attribute-names ApproximateNumberOfMessages
```

---

## Cleanup

```bash
sam delete --stack-name sns-sqs-fanout-lab
```
