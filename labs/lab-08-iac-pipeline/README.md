# Lab 08 – SAM & CDK Pipeline

**Module:** [Module 7 – Infrastructure as Code](../../modules/07-infrastructure-as-code/README.md)  
**Duration:** ~90 minutes  
**Services:** Lambda, DynamoDB, API Gateway, CodePipeline / GitHub Actions, CDK

---

## Objective

Build a serverless application with AWS CDK and set up a GitHub Actions CI/CD pipeline that automatically deploys on every push to `main`.

---

## Directory Structure

```
lab-08-iac-pipeline/
├── README.md
├── bin/
│   └── app.ts                     ← CDK App entry point
├── lib/
│   ├── api-stack.ts               ← Lambda + API Gateway + DynamoDB stack
│   └── pipeline-stack.ts          ← CI/CD concept (SAM approach)
├── src/
│   └── handlers/
│       ├── items.py               ← Lambda handler
│       └── requirements.txt
├── test/
│   └── api-stack.test.ts          ← CDK unit tests
├── .github/
│   └── workflows/
│       └── deploy.yml             ← GitHub Actions pipeline
├── cdk.json
├── package.json
└── tsconfig.json
```

---

## Prerequisites

```bash
node --version   # >= 18.x
npm --version    # >= 9.x
cdk --version    # >= 2.x (npm install -g aws-cdk)
```

---

## Step 1 – Install Dependencies

```bash
cd labs/lab-08-iac-pipeline
npm install
```

---

## Step 2 – Bootstrap CDK (first time only)

```bash
cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/$(aws configure get region)
```

---

## Step 3 – Run CDK Unit Tests

```bash
npm test
```

---

## Step 4 – Synthesise and Review

```bash
# Generate CloudFormation template
cdk synth

# Compare with what's deployed (nothing yet)
cdk diff
```

---

## Step 5 – Deploy

```bash
cdk deploy --all --require-approval never
```

---

## Step 6 – Test the API

```bash
API_URL=$(aws cloudformation describe-stacks \
  --stack-name ItemsApiStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

# Create an item
curl -X POST "$API_URL/items" \
  -H "Content-Type: application/json" \
  -d '{"name": "CDK Widget", "price": 9.99}'

# List items
curl "$API_URL/items"
```

---

## Step 7 – GitHub Actions Pipeline

Push to your GitHub repo and watch the pipeline deploy automatically.  
The pipeline in `.github/workflows/deploy.yml`:

1. Runs CDK unit tests.
2. Synthesises the CDK app.
3. Deploys to AWS using OIDC (no stored AWS credentials).

---

## Cleanup

```bash
cdk destroy --all
```
