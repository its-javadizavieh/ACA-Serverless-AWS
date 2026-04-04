# ACA Serverless AWS – 72-Hour Course

> **A comprehensive, hands-on training programme on serverless computing with AWS.**  
> Suitable for cloud engineers, backend developers, and DevOps practitioners who want to master the full serverless stack – from Green IT foundations through real-world orchestration and Infrastructure as Code.

---

## 🎯 Course Overview

| Attribute | Detail |
|---|---|
| **Total Duration** | 72 hours (theory + labs) |
| **Format** | Instructor-led or self-paced |
| **Difficulty** | Intermediate (basic AWS familiarity recommended) |
| **Primary Cloud** | Amazon Web Services (AWS) |
| **IaC Tools** | AWS SAM, AWS CDK |

---

## 📚 Modules

| # | Module | Duration | Topics |
|---|--------|----------|--------|
| 1 | [Green IT & Serverless Foundations](modules/01-green-it-and-serverless-foundations/README.md) | 8 h | Sustainability, serverless concepts, AWS overview |
| 2 | [AWS Lambda Deep Dive](modules/02-aws-lambda/README.md) | 12 h | Execution model, layers, extensions, performance |
| 3 | [API Gateway & REST/HTTP APIs](modules/03-api-gateway/README.md) | 8 h | REST vs HTTP API, authorizers, CORS, throttling |
| 4 | [Event-Driven Architecture](modules/04-event-driven-architecture/README.md) | 10 h | SNS, SQS, EventBridge, fan-out patterns |
| 5 | [Data Services](modules/05-data-services/README.md) | 8 h | DynamoDB, S3, ElastiCache, data access patterns |
| 6 | [Orchestration with Step Functions](modules/06-step-functions/README.md) | 8 h | State machines, error handling, parallel workflows |
| 7 | [Infrastructure as Code](modules/07-infrastructure-as-code/README.md) | 10 h | AWS SAM, AWS CDK, CI/CD pipelines |
| 8 | [Capstone Project](modules/08-capstone-project/README.md) | 8 h | End-to-end serverless application |

---

## 🧪 Hands-On Labs

Each module contains one or more labs in its `labs/` sub-directory.  
All lab code is fully self-contained and deployable with AWS SAM or CDK.

| Lab | Module | Description |
|-----|--------|-------------|
| [Lab 01 – Carbon Footprint Calculator](labs/lab-01-carbon-footprint/README.md) | 1 | Measure and compare compute carbon emissions |
| [Lab 02 – Hello Lambda](labs/lab-02-hello-lambda/README.md) | 2 | First Lambda function: runtimes, IAM, logging |
| [Lab 03 – Lambda Layers & Dependencies](labs/lab-03-lambda-layers/README.md) | 2 | Packaging shared code as Lambda Layers |
| [Lab 04 – REST API with API Gateway](labs/lab-04-api-gateway-rest/README.md) | 3 | Build and deploy a CRUD REST API |
| [Lab 05 – Event Fan-Out with SNS & SQS](labs/lab-05-sns-sqs-fanout/README.md) | 4 | Fan-out pattern, DLQs, and message filtering |
| [Lab 06 – DynamoDB Single-Table Design](labs/lab-06-dynamodb/README.md) | 5 | Data modeling, GSIs, streams |
| [Lab 07 – Step Functions Workflow](labs/lab-07-step-functions/README.md) | 6 | Order-processing state machine |
| [Lab 08 – SAM & CDK Pipeline](labs/lab-08-iac-pipeline/README.md) | 7 | Full CI/CD pipeline with CDK Pipelines |

---

## 🔧 Prerequisites

### Knowledge
- Basic understanding of AWS (IAM, regions, console navigation)
- Familiarity with at least one programming language (Python or Node.js examples provided)
- Basic command-line / terminal usage

### Tools
```bash
# AWS CLI v2
aws --version     # >= 2.x

# AWS SAM CLI
sam --version     # >= 1.100.0

# Node.js (for CDK & JS runtimes)
node --version    # >= 18.x

# Python (for Python runtimes)
python3 --version # >= 3.11

# AWS CDK CLI
cdk --version     # >= 2.x

# Docker (for local Lambda testing)
docker --version
```

### AWS Account Setup
1. Create or use an existing AWS account.
2. Create an IAM user / role with `AdministratorAccess` (for training purposes).
3. Configure the CLI: `aws configure`
4. Verify: `aws sts get-caller-identity`

---

## 📁 Repository Structure

```
ACA-Serverless-AWS/
├── README.md                          ← You are here
├── modules/
│   ├── 01-green-it-and-serverless-foundations/
│   ├── 02-aws-lambda/
│   ├── 03-api-gateway/
│   ├── 04-event-driven-architecture/
│   ├── 05-data-services/
│   ├── 06-step-functions/
│   ├── 07-infrastructure-as-code/
│   └── 08-capstone-project/
├── labs/
│   ├── lab-01-carbon-footprint/
│   ├── lab-02-hello-lambda/
│   ├── lab-03-lambda-layers/
│   ├── lab-04-api-gateway-rest/
│   ├── lab-05-sns-sqs-fanout/
│   ├── lab-06-dynamodb/
│   ├── lab-07-step-functions/
│   └── lab-08-iac-pipeline/
└── resources/
    ├── cheatsheets/
    └── diagrams/
```

---

## 🚀 Getting Started

```bash
# 1. Clone the repository
git clone https://github.com/its-javadizavieh/ACA-Serverless-AWS.git
cd ACA-Serverless-AWS

# 2. Start with Module 1
open modules/01-green-it-and-serverless-foundations/README.md

# 3. Deploy your first lab
cd labs/lab-02-hello-lambda
sam build && sam deploy --guided
```

---

## 📜 License

This course material is provided for educational purposes.  
© ACA – Advanced Computing Academy. All rights reserved.
