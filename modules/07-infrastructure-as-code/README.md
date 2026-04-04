# Module 7 – Infrastructure as Code

**Duration:** 10 hours  
**Lab:** [Lab 08 – SAM & CDK Pipeline](../../labs/lab-08-iac-pipeline/README.md)

---

## Learning Objectives

After completing this module you will be able to:

- Write AWS SAM templates for serverless applications.
- Build serverless applications with AWS CDK (TypeScript/Python).
- Implement CI/CD pipelines using CDK Pipelines or SAM Pipelines.
- Manage multiple environments (dev, staging, prod) with IaC.
- Apply IaC best practices: parameterisation, secrets management, drift detection.

---

## 1. Infrastructure as Code Overview

### 1.1 Why IaC?

| Manual console | IaC |
|---------------|-----|
| Hard to reproduce | Repeatable |
| No audit trail | Version controlled |
| Risky changes | Reviewed via PR |
| Environment drift | Identical environments |
| Slow onboarding | One-command setup |

### 1.2 AWS IaC Tools Comparison

| Tool | Language | Level of abstraction | Best for |
|------|----------|---------------------|----------|
| **CloudFormation** | YAML/JSON | Low (raw AWS resources) | All resources |
| **AWS SAM** | YAML (extends CFN) | Medium (serverless-specific transforms) | Serverless apps |
| **AWS CDK** | TypeScript, Python, Java, C#, Go | High (constructs, L1/L2/L3) | Any complexity |
| **Terraform** | HCL | Medium | Multi-cloud |
| **Pulumi** | General purpose languages | High | Multi-cloud |

---

## 2. AWS SAM (Serverless Application Model)

### 2.1 SAM Template Anatomy

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31   # ← SAM magic

Description: My Serverless Application

Globals:
  Function:
    Runtime: python3.12
    MemorySize: 512
    Timeout: 30
    Tracing: Active
    Environment:
      Variables:
        LOG_LEVEL: INFO

Parameters:
  StageName:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]

Resources:
  # ...

Outputs:
  ApiUrl:
    Value: !Sub https://${MyApi}.execute-api.${AWS::Region}.amazonaws.com/${StageName}/
```

### 2.2 SAM Resource Types

| SAM Type | CloudFormation Equivalent |
|----------|--------------------------|
| `AWS::Serverless::Function` | Lambda + IAM Role + event source mappings |
| `AWS::Serverless::Api` | API Gateway REST API + Stage + Deployment |
| `AWS::Serverless::HttpApi` | API Gateway HTTP API + Stage |
| `AWS::Serverless::SimpleTable` | DynamoDB table (simple key schema) |
| `AWS::Serverless::StateMachine` | Step Functions state machine |
| `AWS::Serverless::Application` | Nested SAM application from SAR |
| `AWS::Serverless::LayerVersion` | Lambda Layer |

### 2.3 Function Definition

```yaml
CreateOrderFunction:
  Type: AWS::Serverless::Function
  Properties:
    FunctionName: !Sub create-order-${StageName}
    CodeUri: src/create_order/
    Handler: app.handler
    Runtime: python3.12
    MemorySize: 1024
    Timeout: 30
    Environment:
      Variables:
        TABLE_NAME: !Ref OrdersTable
    Policies:
      - DynamoDBCrudPolicy:
          TableName: !Ref OrdersTable
    Events:
      CreateOrder:
        Type: HttpApi
        Properties:
          Path: /orders
          Method: POST
          ApiId: !Ref MyHttpApi
```

### 2.4 SAM CLI Commands

```bash
# Initialise a new project
sam init

# Build (compile, install dependencies)
sam build

# Run locally with simulated API Gateway
sam local start-api --port 3000

# Run a single function locally
sam local invoke CreateOrderFunction --event events/create-order.json

# Deploy (first time – guided)
sam deploy --guided

# Deploy (subsequent deployments)
sam deploy

# View logs
sam logs --name CreateOrderFunction --tail

# Delete stack
sam delete
```

### 2.5 SAM Local Testing

```bash
# Generate a sample event
sam local generate-event apigateway aws-proxy --method POST --body '{"name":"Widget"}' > events/create-order.json

# Invoke locally
sam local invoke CreateOrderFunction \
  --event events/create-order.json \
  --env-vars env.json
```

`env.json`:
```json
{
  "CreateOrderFunction": {
    "TABLE_NAME": "orders-local",
    "LOG_LEVEL": "DEBUG"
  }
}
```

---

## 3. AWS CDK (Cloud Development Kit)

### 3.1 Core Concepts

| Concept | Description |
|---------|-------------|
| **App** | Root CDK program; contains one or more stacks |
| **Stack** | A CloudFormation stack (unit of deployment) |
| **Construct** | Reusable building block (L1, L2, L3) |
| **L1 construct** | Direct CloudFormation resource (1:1 mapping) |
| **L2 construct** | Higher-level abstraction with sensible defaults |
| **L3 construct (Pattern)** | Pre-built architecture pattern |

### 3.2 CDK Project Structure (TypeScript)

```
my-serverless-app/
├── bin/
│   └── app.ts               ← CDK App entry point
├── lib/
│   ├── api-stack.ts          ← API Gateway + Lambda stack
│   ├── data-stack.ts         ← DynamoDB stack
│   └── pipeline-stack.ts     ← CI/CD pipeline
├── src/
│   └── handlers/             ← Lambda function code
├── test/
│   └── api-stack.test.ts     ← CDK unit tests
├── cdk.json
└── package.json
```

### 3.3 Lambda Function (CDK TypeScript)

```typescript
import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as apigw from "aws-cdk-lib/aws-apigatewayv2";
import { HttpLambdaIntegration } from "aws-cdk-lib/aws-apigatewayv2-integrations";
import { Construct } from "constructs";

export class ApiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // DynamoDB table
    const ordersTable = new dynamodb.Table(this, "OrdersTable", {
      partitionKey: { name: "PK", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "SK", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,  // dev only
    });

    // Lambda function
    const createOrderFn = new lambda.Function(this, "CreateOrderFunction", {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "app.handler",
      code: lambda.Code.fromAsset("src/handlers/create_order"),
      environment: {
        TABLE_NAME: ordersTable.tableName,
        LOG_LEVEL: "INFO",
      },
      tracing: lambda.Tracing.ACTIVE,
      memorySize: 1024,
      timeout: cdk.Duration.seconds(30),
    });

    // Grant Lambda access to DynamoDB
    ordersTable.grantReadWriteData(createOrderFn);

    // HTTP API
    const api = new apigw.HttpApi(this, "OrdersApi", {
      corsPreflight: {
        allowHeaders: ["Content-Type", "Authorization"],
        allowMethods: [apigw.CorsHttpMethod.ANY],
        allowOrigins: ["*"],
      },
    });

    api.addRoutes({
      path: "/orders",
      methods: [apigw.HttpMethod.POST],
      integration: new HttpLambdaIntegration("CreateOrderIntegration", createOrderFn),
    });

    new cdk.CfnOutput(this, "ApiUrl", { value: api.url! });
  }
}
```

### 3.4 CDK CLI Commands

```bash
# Bootstrap CDK (first time per account/region)
cdk bootstrap aws://ACCOUNT_ID/REGION

# Synthesise CloudFormation template
cdk synth

# Show diff against deployed stack
cdk diff

# Deploy
cdk deploy

# Deploy all stacks
cdk deploy --all

# Destroy
cdk destroy
```

### 3.5 CDK Unit Tests

```typescript
import { Template } from "aws-cdk-lib/assertions";
import * as cdk from "aws-cdk-lib";
import { ApiStack } from "../lib/api-stack";

test("Lambda function created with correct runtime", () => {
  const app = new cdk.App();
  const stack = new ApiStack(app, "TestStack");
  const template = Template.fromStack(stack);

  template.hasResourceProperties("AWS::Lambda::Function", {
    Runtime: "python3.12",
    MemorySize: 1024,
  });
});

test("DynamoDB table uses PAY_PER_REQUEST billing", () => {
  const app = new cdk.App();
  const stack = new ApiStack(app, "TestStack");
  const template = Template.fromStack(stack);

  template.hasResourceProperties("AWS::DynamoDB::Table", {
    BillingMode: "PAY_PER_REQUEST",
  });
});
```

---

## 4. CI/CD Pipelines

### 4.1 SAM Pipelines

SAM Pipelines generates a complete CI/CD pipeline configuration.

```bash
# Generate pipeline
sam pipeline init --bootstrap

# Creates:
# - .aws-sam/pipeline/pipelineconfig.toml
# - codepipeline.yaml (or GitHub Actions / GitLab CI)
```

### 4.2 GitHub Actions with SAM

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/GitHubActionsDeployRole
          aws-region: us-east-1

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install SAM CLI
        run: pip install aws-sam-cli

      - name: Build
        run: sam build

      - name: Deploy to Production
        run: |
          sam deploy \
            --stack-name my-app-prod \
            --parameter-overrides StageName=prod \
            --no-confirm-changeset \
            --no-fail-on-empty-changeset
```

### 4.3 CDK Pipelines

CDK Pipelines creates a self-mutating pipeline that deploys itself before deploying your application.

```typescript
import * as pipelines from "aws-cdk-lib/pipelines";

export class PipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const pipeline = new pipelines.CodePipeline(this, "Pipeline", {
      synth: new pipelines.ShellStep("Synth", {
        input: pipelines.CodePipelineSource.connection(
          "my-org/my-repo", "main",
          { connectionArn: "arn:aws:codestar-connections:..." }
        ),
        commands: ["npm ci", "npm run build", "npx cdk synth"],
      }),
    });

    // Add deployment stages
    pipeline.addStage(new AppStage(this, "Dev", {
      env: { account: "123456789012", region: "us-east-1" },
    }));

    pipeline.addStage(new AppStage(this, "Prod", {
      env: { account: "987654321098", region: "us-east-1" },
    }), {
      pre: [new pipelines.ManualApprovalStep("Approve Prod Deployment")],
    });
  }
}
```

---

## 5. Multi-Environment Management

### 5.1 Environment Strategy

```
Environments:
  dev     ← Developer feature branches
  staging ← Pre-production integration testing
  prod    ← Production traffic
```

### 5.2 SAM Parameters for Environments

```yaml
# samconfig.toml
[dev.deploy.parameters]
stack_name = "my-app-dev"
parameter_overrides = "StageName=dev TableName=orders-dev"
confirm_changeset = true

[prod.deploy.parameters]
stack_name = "my-app-prod"
parameter_overrides = "StageName=prod TableName=orders-prod"
confirm_changeset = false
```

### 5.3 CDK Context & Environment Variables

```typescript
// cdk.json
{
  "context": {
    "dev": { "memorySize": 512, "minCapacity": 0 },
    "prod": { "memorySize": 1024, "minCapacity": 2 }
  }
}

// In stack
const env = this.node.tryGetContext(stageName);
const fn = new lambda.Function(this, "Fn", {
  memorySize: env.memorySize,
});
```

---

## 6. IaC Best Practices

1. **Version control everything** – IaC code lives in the same repo as application code.
2. **Use parameters / context** – avoid hardcoded values.
3. **Never store secrets in IaC** – use Secrets Manager or SSM Parameter Store.
4. **Review changes before deploying** – `sam deploy --confirm-changeset` or `cdk diff`.
5. **Enable termination protection** on production stacks.
6. **Tag all resources** for cost allocation.
7. **Test your IaC** – CDK snapshot tests, `cfn-lint` for CFN/SAM.
8. **Enable drift detection** – CloudFormation drift detection identifies manual changes.

---

## 7. Hands-On: Lab 08

➡️ [Lab 08 – SAM & CDK Pipeline](../../labs/lab-08-iac-pipeline/README.md)

**What you'll build:**
- A full SAM-based serverless application with Lambda, HTTP API, and DynamoDB.
- A GitHub Actions CI/CD pipeline that:
  - Runs unit tests.
  - Deploys to `dev` on every push to a feature branch.
  - Deploys to `prod` on merge to `main` with a manual approval gate.
- A CDK unit test suite validating the infrastructure.

---

## 8. Key Takeaways

- SAM is the fastest way to build and deploy serverless applications; built on CloudFormation.
- CDK is more powerful for complex multi-service architectures; supports unit testing.
- CDK Pipelines creates self-mutating pipelines that evolve with your infrastructure code.
- Use `samconfig.toml` or CDK context to manage multiple environments cleanly.
- Always use `cdk diff` / `--confirm-changeset` before deploying to production.

---

## 📖 Further Reading

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)
- [AWS CDK Developer Guide](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
- [CDK Patterns](https://cdkpatterns.com/)
- [Serverless Land](https://serverlessland.com/)
- [AWS Pipeline Workshop](https://catalog.workshops.aws/cdkpipelines/en-US)

---

*Previous Module → [Module 6: Step Functions](../06-step-functions/README.md)*  
*Next Module → [Module 8: Capstone Project](../08-capstone-project/README.md)*
