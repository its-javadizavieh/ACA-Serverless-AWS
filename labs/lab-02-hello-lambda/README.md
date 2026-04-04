# Lab 02 – Hello Lambda

**Module:** [Module 2 – AWS Lambda Deep Dive](../../modules/02-aws-lambda/README.md)  
**Duration:** ~60 minutes  
**Services:** AWS Lambda, CloudWatch Logs, AWS CLI

---

## Objective

Build and deploy your first Lambda function from scratch. You will:

- Write a Python Lambda handler.
- Explore the execution context (`context` object).
- Configure environment variables and memory.
- Invoke the function via the AWS CLI and the Lambda Console.
- Inspect CloudWatch Logs.
- Observe cold starts vs warm starts.

---

## Directory Structure

```
lab-02-hello-lambda/
├── README.md
├── template.yaml
├── src/
│   └── hello/
│       ├── app.py
│       └── requirements.txt
└── events/
    ├── hello.json
    └── echo.json
```

---

## Step 1 – Review the Code

Open `src/hello/app.py` and read through the handler.  
Notice how the function:
1. Reads an environment variable (`GREETING`).
2. Uses the `context` object to log the request ID.
3. Returns a structured JSON response.

---

## Step 2 – Build and Deploy

```bash
cd labs/lab-02-hello-lambda
sam build
sam deploy --guided
```

Use these values when prompted:
- Stack name: `hello-lambda-lab`
- Region: your nearest region
- Allow SAM to create IAM roles: `Y`

---

## Step 3 – Invoke via CLI

```bash
# Synchronous invocation
aws lambda invoke \
  --function-name hello-world \
  --payload file://events/hello.json \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

Expected output:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Hello, Lambda Learner! 👋",
    "requestId": "...",
    "functionName": "hello-world",
    "memoryLimitMB": "256",
    "remainingTimeMs": 29900
  }
}
```

---

## Step 4 – Explore Cold vs Warm Starts

Run the function 5 times in quick succession:

```bash
for i in {1..5}; do
  aws lambda invoke \
    --function-name hello-world \
    --payload '{}' \
    --cli-binary-format raw-in-base64-out \
    /dev/null 2>&1
done
```

Then check CloudWatch Logs:

```bash
aws logs tail /aws/lambda/hello-world --follow
```

Look for `Init Duration` in the REPORT lines — it only appears on cold starts.

---

## Step 5 – Update Memory and Observe

Update the memory in `template.yaml` from `256` to `1024`, then redeploy:

```bash
sam deploy
```

Re-run the function. Does the duration change?

---

## Bonus – Node.js Version

The template includes an optional Node.js version of the same function (`HelloWorldNodeFunction`). Compare the cold start times between Python and Node.js runtimes.

---

## Cleanup

```bash
sam delete --stack-name hello-lambda-lab
```
