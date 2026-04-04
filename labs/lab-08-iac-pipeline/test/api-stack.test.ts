import * as cdk from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { ItemsApiStack } from "../lib/api-stack";

describe("ItemsApiStack", () => {
  let app: cdk.App;
  let stack: ItemsApiStack;
  let template: Template;

  beforeEach(() => {
    app = new cdk.App({ context: { stageName: "test" } });
    stack = new ItemsApiStack(app, "TestStack", {
      stageName: "test",
    });
    template = Template.fromStack(stack);
  });

  test("creates a DynamoDB table with PAY_PER_REQUEST billing", () => {
    template.hasResourceProperties("AWS::DynamoDB::Table", {
      BillingMode: "PAY_PER_REQUEST",
      TableName: "items-test",
    });
  });

  test("DynamoDB table has composite key (PK + SK)", () => {
    template.hasResourceProperties("AWS::DynamoDB::Table", {
      KeySchema: [
        { AttributeName: "PK", KeyType: "HASH" },
        { AttributeName: "SK", KeyType: "RANGE" },
      ],
    });
  });

  test("creates a Lambda function with Python 3.12 runtime", () => {
    template.hasResourceProperties("AWS::Lambda::Function", {
      Runtime: "python3.12",
      MemorySize: 512,
      FunctionName: "items-api-test",
    });
  });

  test("Lambda function has X-Ray tracing enabled", () => {
    template.hasResourceProperties("AWS::Lambda::Function", {
      TracingConfig: { Mode: "Active" },
    });
  });

  test("Lambda function has TABLE_NAME environment variable", () => {
    template.hasResourceProperties("AWS::Lambda::Function", {
      Environment: {
        Variables: Match.objectLike({
          LOG_LEVEL: "INFO",
        }),
      },
    });
  });

  test("creates an HTTP API", () => {
    template.resourceCountIs("AWS::ApiGatewayV2::Api", 1);
    template.hasResourceProperties("AWS::ApiGatewayV2::Api", {
      ProtocolType: "HTTP",
    });
  });

  test("dev stack uses DESTROY removal policy for DynamoDB", () => {
    // Table should NOT have DeletionPolicy: Retain in dev/test
    const tables = template.findResources("AWS::DynamoDB::Table");
    const tableEntries = Object.values(tables);
    expect(tableEntries.length).toBe(1);
    // DESTROY = no DeletionPolicy attribute (default behaviour)
    const table = tableEntries[0] as { DeletionPolicy?: string };
    expect(table.DeletionPolicy).not.toBe("Retain");
  });

  test("prod stack uses RETAIN removal policy for DynamoDB", () => {
    const prodApp = new cdk.App({ context: { stageName: "prod" } });
    const prodStack = new ItemsApiStack(prodApp, "ProdStack", { stageName: "prod" });
    const prodTemplate = Template.fromStack(prodStack);

    const tables = prodTemplate.findResources("AWS::DynamoDB::Table");
    const tableEntries = Object.values(tables);
    const table = tableEntries[0] as { DeletionPolicy?: string };
    expect(table.DeletionPolicy).toBe("Retain");
  });

  test("outputs API URL and table name", () => {
    template.hasOutput("ApiUrl", {});
    template.hasOutput("TableName", {});
  });
});
