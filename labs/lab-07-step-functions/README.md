# Lab 07 – Step Functions Workflow

**Module:** [Module 6 – Orchestration with Step Functions](../../modules/06-step-functions/README.md)  
**Duration:** ~90 minutes  
**Services:** Step Functions, Lambda, DynamoDB, SNS, CloudWatch

---

## Objective

Build an **order-processing state machine** with:

1. Order validation (Task)
2. Parallel inventory reservation (Map)
3. Payment processing with Retry/Catch
4. DynamoDB write via direct SDK integration
5. SNS notification
6. Error handling paths

---

## State Machine Diagram

```
[Start]
   │
   ▼
ValidateOrder ──(fail)──► OrderInvalid [Fail]
   │
   ▼
ReserveInventory (Map – parallel per item)
   │
   ▼
ProcessPayment ──(declined)──► ReleaseInventory ──► OrderFailed [Fail]
   │
   ▼
SaveOrderToDynamoDB (SDK integration – no Lambda)
   │
   ▼
SendConfirmationNotification
   │
   ▼
[End – Success]
```

---

## Step 1 – Deploy

```bash
cd labs/lab-07-step-functions
sam build
sam deploy --guided
# Stack name: step-functions-lab
```

---

## Step 2 – Start an Execution

```bash
STATE_MACHINE_ARN=$(aws cloudformation describe-stacks \
  --stack-name step-functions-lab \
  --query 'Stacks[0].Outputs[?OutputKey==`StateMachineArn`].OutputValue' \
  --output text)

aws stepfunctions start-execution \
  --state-machine-arn "$STATE_MACHINE_ARN" \
  --input file://events/order.json
```

---

## Step 3 – Watch the Execution

Open the AWS Step Functions console and watch the visual workflow.  
Or use the CLI:

```bash
# Get execution ARN from start-execution output, then:
aws stepfunctions describe-execution \
  --execution-arn "arn:aws:states:..."
```

---

## Step 4 – Test Payment Failure

```bash
aws stepfunctions start-execution \
  --state-machine-arn "$STATE_MACHINE_ARN" \
  --input '{"orderId":"fail-test","items":[{"productId":"p1","qty":1}],"customerId":"cust-1","total":50,"simulatePaymentFailure":true}'
```

Observe the error handling path in the console.

---

## Cleanup

```bash
sam delete --stack-name step-functions-lab
```
