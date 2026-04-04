# Module 2 – AWS Lambda Deep Dive

**Duration:** 12 hours  
**Labs:** [Lab 02 – Hello Lambda](../../labs/lab-02-hello-lambda/README.md) · [Lab 03 – Lambda Layers & Dependencies](../../labs/lab-03-lambda-layers/README.md)

---

## Learning Objectives

After completing this module you will be able to:

- Explain the Lambda execution model and lifecycle.
- Configure memory, timeout, concurrency, and environment variables.
- Use Lambda Layers to share dependencies across functions.
- Apply performance tuning techniques (power-tuning, provisioned concurrency).
- Implement observability with CloudWatch Logs, Metrics, and X-Ray tracing.
- Write Lambda functions in Python and Node.js following best practices.

---

## 1. Lambda Execution Model

### 1.1 The Invocation Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│  INIT phase (cold start)                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Download code │→ │ Start runtime │→ │ Run INIT code │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────┤
│  INVOKE phase (warm start)                              │
│  ┌──────────────────────────────────────┐               │
│  │ Execute handler() → Return response  │               │
│  └──────────────────────────────────────┘               │
├─────────────────────────────────────────────────────────┤
│  SHUTDOWN phase                                         │
│  ┌──────────────────────────┐                           │
│  │ Runtime / Extension flush │                           │
│  └──────────────────────────┘                           │
└─────────────────────────────────────────────────────────┘
```

- **Cold start**: INIT + INVOKE — happens when a new execution environment is created.
- **Warm start**: INVOKE only — reuses an existing execution environment.
- Lambda keeps environments "warm" for a few minutes of inactivity.

### 1.2 Execution Environment

Each execution environment contains:
- A Linux micro-VM (AWS Firecracker)
- The chosen runtime (Python, Node.js, Java, Go, .NET, Ruby, custom)
- Your deployment package / container image
- Ephemeral storage at `/tmp` (512 MB – 10 GB, configurable)

### 1.3 Handler Function Signature

**Python:**
```python
def handler(event: dict, context) -> dict:
    """
    event   – JSON-serialised input from the invoker / event source
    context – runtime information (function name, memory limit, request ID, …)
    """
    return {"statusCode": 200, "body": "Hello, Lambda!"}
```

**Node.js:**
```javascript
exports.handler = async (event, context) => {
  return { statusCode: 200, body: "Hello, Lambda!" };
};
```

---

## 2. Configuration

### 2.1 Memory & CPU

Lambda allocates CPU power **proportionally** to the memory setting.

| Memory (MB) | vCPU equivalent |
|-------------|-----------------|
| 128         | ~0.1            |
| 1,769       | 1               |
| 3,008       | ~1.7            |
| 10,240      | 6               |

> **Tip:** For CPU-intensive workloads, increase memory to get more CPU even if you don't need the extra RAM.

### 2.2 Timeout

- Minimum: 1 second
- Maximum: **900 seconds (15 minutes)**
- Always set the timeout as close to the expected duration as possible.

### 2.3 Environment Variables

```yaml
# In SAM template
Environment:
  Variables:
    TABLE_NAME: !Ref MyTable
    LOG_LEVEL: INFO
```

Sensitive values → use **AWS Secrets Manager** or **AWS Systems Manager Parameter Store**.

### 2.4 Concurrency

| Type | Description |
|------|-------------|
| **Unreserved concurrency** | Default; shares from the account pool |
| **Reserved concurrency** | Guarantees N instances; caps burst |
| **Provisioned concurrency** | Pre-warms N instances; eliminates cold starts |

Account default concurrent execution limit: **1,000** (soft limit, raiseable).

---

## 3. Event Sources & Invocation Types

### 3.1 Invocation Types

| Type | Description | Example triggers |
|------|-------------|-----------------|
| **Synchronous** | Caller waits for response | API Gateway, ALB, Cognito |
| **Asynchronous** | Lambda queues, returns 202 | S3, SNS, EventBridge |
| **Poll-based (stream)** | Lambda polls the source | SQS, Kinesis, DynamoDB Streams |

### 3.2 Common Event Source Payloads

**API Gateway (REST) event:**
```json
{
  "httpMethod": "GET",
  "path": "/items",
  "queryStringParameters": { "limit": "10" },
  "headers": { "Authorization": "Bearer ..." },
  "body": null
}
```

**SQS event:**
```json
{
  "Records": [
    {
      "messageId": "...",
      "body": "{\"orderId\": \"123\"}",
      "attributes": { "ApproximateReceiveCount": "1" }
    }
  ]
}
```

**S3 event:**
```json
{
  "Records": [
    {
      "s3": {
        "bucket": { "name": "my-bucket" },
        "object": { "key": "uploads/photo.jpg", "size": 102400 }
      }
    }
  ]
}
```

---

## 4. Lambda Layers

A **Layer** is a ZIP archive containing libraries, custom runtimes, or configuration that is extracted into `/opt` in the execution environment.

### 4.1 Use Cases

- Share common utility code across multiple functions.
- Separate large dependencies (e.g., `pandas`, AWS SDK v3) from your function code.
- Distribute third-party runtimes (custom runtimes).

### 4.2 Layer Limits

| Limit | Value |
|-------|-------|
| Layers per function | 5 |
| Total unzipped size (function + layers) | 250 MB |
| Layer ZIP size | 50 MB (direct upload) / 250 MB (via S3) |

### 4.3 Creating a Layer (Python)

```bash
# Create the layer package
mkdir -p layer/python
pip install requests -t layer/python
cd layer && zip -r ../requests-layer.zip python/

# Publish the layer
aws lambda publish-layer-version \
  --layer-name requests-layer \
  --zip-file fileb://../requests-layer.zip \
  --compatible-runtimes python3.11 python3.12
```

---

## 5. Lambda Extensions

Extensions run as a separate process alongside your function handler.

- **Internal extensions** – run inside the runtime process.
- **External extensions** – run as a standalone process; can run during INIT and SHUTDOWN.

**Common uses:**
- Sending logs/metrics to third-party observability platforms (Datadog, New Relic).
- Fetching secrets at startup.
- Profiling and monitoring.

---

## 6. Performance Best Practices

### 6.1 Reducing Cold Start Duration

1. **Choose a lightweight runtime** – Python / Node.js cold starts < 500 ms; Java can be > 2 s.
2. **Minimise deployment package size** – only include required dependencies.
3. **Initialise SDK clients outside the handler:**

```python
import boto3

# ✅ Created once per execution environment (outside handler)
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def handler(event, context):
    # table is already warm
    response = table.get_item(Key={"pk": event["pk"]})
    return response.get("Item")
```

4. **Use Provisioned Concurrency** for latency-sensitive workloads.
5. **Use SnapStart** (Java 11+, Python 3.12+) to restore from a snapshot.

### 6.2 AWS Lambda Power Tuning

Use the [AWS Lambda Power Tuning](https://github.com/alexcasalboni/aws-lambda-power-tuning) Step Functions state machine to find the optimal memory setting.

```bash
# Deploy via SAM
sam deploy -g --template-url https://s3.amazonaws.com/...

# Run via AWS Console or CLI
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:... \
  --input '{"lambdaARN": "...", "num": 10, "payload": {}, "powerValues": [128,256,512,1024,2048,3008]}'
```

---

## 7. Observability

### 7.1 CloudWatch Logs

Every Lambda invocation produces structured log output:

```
START RequestId: abc123 Version: $LATEST
[INFO] Processing order: 42
END RequestId: abc123
REPORT RequestId: abc123  Duration: 45.23 ms  Billed Duration: 46 ms  Memory Size: 512 MB  Max Memory Used: 78 MB
```

Enable **structured JSON logging** for easier querying:

```python
import json, logging, os

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

def handler(event, context):
    logger.info(json.dumps({"action": "start", "requestId": context.aws_request_id}))
```

### 7.2 X-Ray Tracing

Enable active tracing in SAM:

```yaml
MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    Tracing: Active
```

Add the X-Ray SDK:

```python
from aws_xray_sdk.core import xray_recorder, patch_all

patch_all()  # Instruments boto3, requests, etc.
```

### 7.3 Lambda Insights

Enable the CloudWatch Lambda Insights extension for enhanced metrics (CPU, memory, disk, network):

```yaml
Layers:
  - !Sub arn:aws:lambda:${AWS::Region}:580247275435:layer:LambdaInsightsExtension:38
```

---

## 8. IAM & Security

### 8.1 Execution Role

Every Lambda function needs an **IAM execution role** that grants it access to other AWS services.

```yaml
# SAM auto-creates a basic execution role; add additional policies:
Policies:
  - DynamoDBCrudPolicy:
      TableName: !Ref MyTable
  - S3ReadPolicy:
      BucketName: !Ref MyBucket
```

### 8.2 Resource-Based Policy

Control which services can **invoke** your function:

```bash
aws lambda add-permission \
  --function-name my-function \
  --statement-id allow-s3 \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::my-bucket
```

### 8.3 VPC Access

Lambda functions can run inside a VPC to access private resources (RDS, ElastiCache):

```yaml
VpcConfig:
  SecurityGroupIds: [!Ref LambdaSG]
  SubnetIds: [!Ref PrivateSubnet1, !Ref PrivateSubnet2]
```

> **Note:** VPC-attached functions have slightly higher cold start times. Prefer non-VPC when possible.

---

## 9. Hands-On Labs

### Lab 02 – Hello Lambda
➡️ [Lab 02 – Hello Lambda](../../labs/lab-02-hello-lambda/README.md)

Build your first Lambda function, configure environment variables, set up CloudWatch Logs, and invoke it via the CLI and console.

### Lab 03 – Lambda Layers & Dependencies
➡️ [Lab 03 – Lambda Layers & Dependencies](../../labs/lab-03-lambda-layers/README.md)

Create a shared utilities layer, publish it, and attach it to multiple functions.

---

## 10. Key Takeaways

- Lambda execution environments are reused; initialise resources outside the handler.
- Memory setting controls both RAM and CPU allocation.
- Layers enable code reuse and smaller deployment packages.
- Use structured logging + X-Ray for full observability.
- Always follow least-privilege IAM policies.

---

## 📖 Further Reading

- [Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [Lambda Operator Guide](https://docs.aws.amazon.com/lambda/latest/operatorguide/intro.html)
- [AWS Lambda Power Tuning](https://github.com/alexcasalboni/aws-lambda-power-tuning)
- [Lambda SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)

---

*Previous Module → [Module 1](../01-green-it-and-serverless-foundations/README.md)*  
*Next Module → [Module 3: API Gateway](../03-api-gateway/README.md)*
