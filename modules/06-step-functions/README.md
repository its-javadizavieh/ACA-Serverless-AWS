# Module 6 – Orchestration with AWS Step Functions

**Duration:** 8 hours  
**Lab:** [Lab 07 – Step Functions Workflow](../../labs/lab-07-step-functions/README.md)

---

## Learning Objectives

After completing this module you will be able to:

- Explain the difference between orchestration and choreography.
- Build Standard and Express Step Functions workflows.
- Use all major state types: Task, Choice, Parallel, Map, Wait, Pass, Fail.
- Implement robust error handling with Retry and Catch.
- Integrate Step Functions with Lambda, DynamoDB, SNS, SQS, and other AWS services.
- Visualise and debug workflow executions in the AWS Console.

---

## 1. Orchestration vs. Choreography

| Aspect | Choreography (events) | Orchestration (Step Functions) |
|--------|----------------------|-------------------------------|
| Coordinator | None – services react to events | Central state machine |
| Visibility | Hard – trace across services | Built-in visual workflow |
| Error handling | Each service handles own errors | Centralised Retry/Catch |
| Coupling | Loosely coupled | Coupled to orchestrator |
| Best for | Simple fan-out, independent flows | Multi-step transactions |

> **Rule of thumb:** Use **choreography** for decoupled fan-out; use **orchestration** when you need visibility, coordination, or complex error handling across multiple steps.

---

## 2. Step Functions Concepts

### 2.1 State Machine

A **state machine** is a JSON or YAML document (Amazon States Language) that defines:
- A set of **states** (steps).
- Transitions between states.
- Input/output processing at each state.

```json
{
  "Comment": "Simple order processing workflow",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:ValidateOrder",
      "Next": "ProcessPayment"
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:ProcessPayment",
      "End": true
    }
  }
}
```

### 2.2 Workflow Types

| Feature | Standard Workflow | Express Workflow |
|---------|------------------|-----------------|
| Max duration | 1 year | 5 minutes |
| Execution rate | 2,000/s | 100,000/s |
| Pricing | Per state transition | Per duration + invocations |
| Execution history | Yes (90 days) | CloudWatch Logs only |
| Exactly-once | Yes | At-least-once |
| Best for | Long-running transactions | High-volume, short workflows |

---

## 3. State Types

### 3.1 Task State

Executes work: Lambda, AWS SDK service integration, Activity.

```json
"ValidateOrder": {
  "Type": "Task",
  "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ValidateOrder",
  "Parameters": {
    "orderId.$": "$.orderId",
    "customerId.$": "$.customerId"
  },
  "ResultPath": "$.validation",
  "TimeoutSeconds": 30,
  "Next": "CheckValidation"
}
```

### 3.2 Choice State

Routes execution based on conditions (no timeout, no retries).

```json
"CheckValidation": {
  "Type": "Choice",
  "Choices": [
    {
      "Variable": "$.validation.isValid",
      "BooleanEquals": true,
      "Next": "ProcessPayment"
    },
    {
      "Variable": "$.validation.errorCode",
      "StringEquals": "INSUFFICIENT_STOCK",
      "Next": "NotifyOutOfStock"
    }
  ],
  "Default": "OrderFailed"
}
```

### 3.3 Parallel State

Executes multiple branches simultaneously; waits for all to complete.

```json
"NotifyAllParties": {
  "Type": "Parallel",
  "Branches": [
    {
      "StartAt": "SendCustomerEmail",
      "States": {
        "SendCustomerEmail": { "Type": "Task", "Resource": "...", "End": true }
      }
    },
    {
      "StartAt": "UpdateWarehouse",
      "States": {
        "UpdateWarehouse": { "Type": "Task", "Resource": "...", "End": true }
      }
    }
  ],
  "Next": "OrderComplete"
}
```

### 3.4 Map State

Applies a workflow to each element in an array (dynamic parallelism).

```json
"ProcessOrderItems": {
  "Type": "Map",
  "ItemsPath": "$.items",
  "MaxConcurrency": 5,
  "Iterator": {
    "StartAt": "ReserveInventory",
    "States": {
      "ReserveInventory": { "Type": "Task", "Resource": "...", "End": true }
    }
  },
  "Next": "AllItemsProcessed"
}
```

### 3.5 Wait State

Pauses execution for a time duration or until a specific timestamp.

```json
"WaitForPaymentConfirmation": {
  "Type": "Wait",
  "Seconds": 300,
  "Next": "CheckPaymentStatus"
}
```

Or wait until a callback token is returned (`.waitForTaskToken`):

```json
"WaitForHumanApproval": {
  "Type": "Task",
  "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
  "Parameters": {
    "QueueUrl": "...",
    "MessageBody": {
      "taskToken.$": "$$.Task.Token",
      "orderId.$": "$.orderId"
    }
  },
  "HeartbeatSeconds": 3600,
  "Next": "ProcessApproval"
}
```

### 3.6 Pass State

Passes input to output (optionally injecting static values); useful for testing.

```json
"InjectDefaults": {
  "Type": "Pass",
  "Result": { "currency": "USD", "taxRate": 0.2 },
  "ResultPath": "$.defaults",
  "Next": "CalculateTotal"
}
```

### 3.7 Fail State

Terminates execution with an error.

```json
"OrderFailed": {
  "Type": "Fail",
  "Error": "OrderValidationError",
  "Cause": "Order failed validation checks"
}
```

---

## 4. Error Handling

### 4.1 Retry

Automatically retry a failed Task state with exponential backoff.

```json
"ProcessPayment": {
  "Type": "Task",
  "Resource": "...",
  "Retry": [
    {
      "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException"],
      "IntervalSeconds": 2,
      "MaxAttempts": 3,
      "BackoffRate": 2,
      "JitterStrategy": "FULL"
    },
    {
      "ErrorEquals": ["States.ALL"],
      "IntervalSeconds": 5,
      "MaxAttempts": 2
    }
  ],
  "Next": "OrderComplete"
}
```

### 4.2 Catch

Handle specific errors and transition to a recovery path.

```json
"ProcessPayment": {
  "Type": "Task",
  "Resource": "...",
  "Retry": [...],
  "Catch": [
    {
      "ErrorEquals": ["PaymentDeclinedException"],
      "ResultPath": "$.error",
      "Next": "NotifyPaymentFailed"
    },
    {
      "ErrorEquals": ["States.ALL"],
      "ResultPath": "$.error",
      "Next": "OrderFailed"
    }
  ],
  "Next": "OrderComplete"
}
```

### 4.3 Reserved Error Names

| Error Name | Description |
|-----------|-------------|
| `States.ALL` | Matches any error |
| `States.Timeout` | Task exceeded TimeoutSeconds |
| `States.TaskFailed` | Task threw an error |
| `States.Permissions` | Insufficient IAM permissions |
| `States.HeartbeatTimeout` | Activity heartbeat timed out |

---

## 5. AWS SDK Integrations

Step Functions can directly call 200+ AWS APIs without a Lambda function.

### 5.1 Optimistic Integration (DynamoDB Put)

```json
"SaveOrderToDynamo": {
  "Type": "Task",
  "Resource": "arn:aws:states:::dynamodb:putItem",
  "Parameters": {
    "TableName": "Orders",
    "Item": {
      "PK": { "S.$": "States.Format('ORDER#{}', $.orderId)" },
      "SK": { "S": "METADATA" },
      "status": { "S": "CREATED" }
    }
  },
  "Next": "ProcessPayment"
}
```

### 5.2 Sending SNS Notification

```json
"SendNotification": {
  "Type": "Task",
  "Resource": "arn:aws:states:::sns:publish",
  "Parameters": {
    "TopicArn": "arn:aws:sns:...:OrderEvents",
    "Message.$": "States.JsonToString($.order)"
  },
  "Next": "Done"
}
```

---

## 6. Input/Output Processing

### 6.1 Key Fields

| Field | Description |
|-------|-------------|
| `InputPath` | Select portion of state input to pass to task (`$` = all) |
| `Parameters` | Construct a new JSON input for the task |
| `ResultSelector` | Transform the raw task result |
| `ResultPath` | Where to place the task result (`$.result` merges; `null` discards) |
| `OutputPath` | Select portion of state output to pass to next state |

### 6.2 Intrinsic Functions

| Function | Example |
|----------|---------|
| `States.Format` | `States.Format('ORDER#{}', $.orderId)` |
| `States.StringToJson` | Parse a JSON string |
| `States.JsonToString` | Stringify a JSON object |
| `States.Array` | Build an array: `States.Array($.a, $.b)` |
| `States.MathAdd` | `States.MathAdd($.price, $.tax)` |
| `States.UUID` | Generate a UUID v4 |

---

## 7. Monitoring & Debugging

### 7.1 Execution History

View every state transition in the AWS Console:
- Input/output at each step.
- Error details and retry attempts.
- Duration of each state.

### 7.2 CloudWatch Metrics

| Metric | Description |
|--------|-------------|
| `ExecutionsStarted` | Number of started executions |
| `ExecutionsSucceeded` | Successful completions |
| `ExecutionsFailed` | Failed executions |
| `ExecutionThrottled` | Throttled starts |
| `ExecutionTime` | Total execution duration |

### 7.3 X-Ray Tracing

Enable tracing for end-to-end visibility across Lambda, DynamoDB, and other services.

---

## 8. Hands-On: Lab 07

➡️ [Lab 07 – Step Functions Workflow](../../labs/lab-07-step-functions/README.md)

**What you'll build:**  
An order-processing state machine with:
- Parallel product validation (Map state).
- Payment processing with Retry/Catch.
- Human approval step (`.waitForTaskToken` via SQS).
- DynamoDB direct SDK integration (no Lambda for DB writes).
- CloudWatch alarm on failed executions.

---

## 9. Key Takeaways

- Use Step Functions when you need visibility, coordination, or error handling across multiple steps.
- Standard workflows are for long-running, exactly-once transactions; Express for high-throughput short workflows.
- SDK integrations eliminate Lambda functions for simple AWS API calls.
- `.waitForTaskToken` enables human-in-the-loop and external callback patterns.
- Use `ResultPath` carefully to avoid overwriting your workflow state.

---

## 📖 Further Reading

- [Step Functions Developer Guide](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html)
- [Amazon States Language Specification](https://states-language.net/)
- [Step Functions Workshop](https://catalog.workshops.aws/stepfunctions/en-US)
- [Serverless Land Step Functions Patterns](https://serverlessland.com/patterns?services=step-functions)

---

*Previous Module → [Module 5: Data Services](../05-data-services/README.md)*  
*Next Module → [Module 7: Infrastructure as Code](../07-infrastructure-as-code/README.md)*
