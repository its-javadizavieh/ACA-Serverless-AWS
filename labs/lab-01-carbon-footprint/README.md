# Lab 01 – Carbon Footprint Calculator

**Module:** [Module 1 – Green IT & Serverless Foundations](../../modules/01-green-it-and-serverless-foundations/README.md)  
**Duration:** ~45 minutes  
**Services:** AWS Lambda, CloudWatch

---

## Objective

Build a Lambda function that compares the estimated CO₂ emissions of running a compute workload as:

1. AWS Lambda (pay-per-ms)
2. Amazon EC2 t3.micro (24/7)
3. Amazon EC2 m5.large (24/7)

---

## Prerequisites

- AWS CLI configured with sufficient permissions
- AWS SAM CLI installed
- Python 3.11+

---

## Directory Structure

```
lab-01-carbon-footprint/
├── README.md
├── template.yaml           ← SAM template
├── src/
│   └── calculator/
│       ├── app.py          ← Lambda handler
│       └── requirements.txt
└── events/
    └── calculate.json      ← Test event
```

---

## Step 1 – Deploy the Function

```bash
cd labs/lab-01-carbon-footprint
sam build
sam deploy --guided
```

When prompted:
- Stack name: `carbon-footprint-lab`
- AWS Region: pick a green region (`eu-west-1` recommended)
- Accept defaults for the rest

---

## Step 2 – Test the Function

```bash
# Via SAM local
sam local invoke CarbonCalculatorFunction \
  --event events/calculate.json

# Via AWS CLI (after deployment)
aws lambda invoke \
  --function-name carbon-footprint-calculator \
  --payload file://events/calculate.json \
  --cli-binary-format raw-in-base64-out \
  output.json && cat output.json
```

---

## Step 3 – Review the Results

The function outputs a comparison table:

```json
{
  "statusCode": 200,
  "body": {
    "workload": {
      "invocationsPerDay": 10000,
      "avgDurationMs": 200,
      "memorySizeMB": 512
    },
    "comparison": {
      "lambda": {
        "monthlyComputeGbSeconds": 1000.0,
        "estimatedCO2Grams": 120.0,
        "estimatedMonthlyCostUSD": 1.67
      },
      "ec2_t3micro": {
        "monthlyComputeHours": 720,
        "estimatedCO2Grams": 8640.0,
        "estimatedMonthlyCostUSD": 7.59
      },
      "ec2_m5large": {
        "monthlyComputeHours": 720,
        "estimatedCO2Grams": 30240.0,
        "estimatedMonthlyCostUSD": 69.12
      }
    },
    "summary": "Lambda emits ~72x less CO2 than an EC2 m5.large for this workload."
  }
}
```

---

## Step 4 – Experiment

Try changing the invocation parameters in `events/calculate.json`:

```json
{
  "invocationsPerDay": 100000,
  "avgDurationMs": 500,
  "memorySizeMB": 1024
}
```

At what invocation rate does EC2 become more cost-effective?  
Does the CO₂ comparison change at higher scale? Why?

---

## Cleanup

```bash
sam delete --stack-name carbon-footprint-lab
```
