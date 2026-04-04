# Lab 03 – Lambda Layers & Dependencies

**Module:** [Module 2 – AWS Lambda Deep Dive](../../modules/02-aws-lambda/README.md)  
**Duration:** ~60 minutes  
**Services:** AWS Lambda, Lambda Layers

---

## Objective

Create a shared utilities Lambda Layer containing common helper code, publish it, and attach it to multiple Lambda functions.

---

## Directory Structure

```
lab-03-lambda-layers/
├── README.md
├── template.yaml
├── src/
│   ├── layer/
│   │   └── python/
│   │       └── utils/
│   │           ├── __init__.py
│   │           ├── response.py    ← HTTP response helpers
│   │           └── logging.py     ← Structured logging helper
│   └── consumer/
│       ├── app.py                 ← Lambda using the layer
│       └── requirements.txt
└── events/
    └── invoke.json
```

---

## What the Layer Contains

- `utils.response` – helpers to build consistent HTTP responses.
- `utils.logging` – structured JSON logger with request ID injection.

---

## Step 1 – Review the Layer Code

Look at `src/layer/python/utils/response.py` and `utils/logging.py`.  
These will be available to any Lambda function that attaches the layer at `/opt/python/utils/`.

---

## Step 2 – Build and Deploy

```bash
cd labs/lab-03-lambda-layers
sam build
sam deploy --guided
# Stack name: lambda-layers-lab
```

---

## Step 3 – Invoke the Consumer Function

```bash
aws lambda invoke \
  --function-name layer-consumer \
  --payload file://events/invoke.json \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

---

## Step 4 – Inspect the Layer

```bash
# List published layer versions
aws lambda list-layer-versions --layer-name aca-utils-layer

# See what the consumer function's layers look like
aws lambda get-function-configuration --function-name layer-consumer \
  --query 'Layers'
```

---

## Step 5 – Extend the Layer

Add a new function to `utils/response.py` (e.g., `not_found(message)`), redeploy, and verify the consumer can use it without any code change.

---

## Cleanup

```bash
sam delete --stack-name lambda-layers-lab
```
