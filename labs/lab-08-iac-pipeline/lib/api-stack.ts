import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as apigwv2 from "aws-cdk-lib/aws-apigatewayv2";
import { HttpLambdaIntegration } from "aws-cdk-lib/aws-apigatewayv2-integrations";
import * as logs from "aws-cdk-lib/aws-logs";
import { Construct } from "constructs";

export interface ItemsApiStackProps extends cdk.StackProps {
  stageName: string;
}

export class ItemsApiStack extends cdk.Stack {
  public readonly apiUrl: string;

  constructor(scope: Construct, id: string, props: ItemsApiStackProps) {
    super(scope, id, props);

    const { stageName } = props;

    // ── DynamoDB Table ────────────────────────────────────────────────────
    const itemsTable = new dynamodb.Table(this, "ItemsTable", {
      tableName: `items-${stageName}`,
      partitionKey: { name: "PK", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "SK", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: stageName === "prod",
      removalPolicy:
        stageName === "prod"
          ? cdk.RemovalPolicy.RETAIN
          : cdk.RemovalPolicy.DESTROY,
    });

    // ── Lambda Function ───────────────────────────────────────────────────
    const logGroup = new logs.LogGroup(this, "ItemsFunctionLogs", {
      logGroupName: `/aws/lambda/items-api-${stageName}`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const itemsFunction = new lambda.Function(this, "ItemsFunction", {
      functionName: `items-api-${stageName}`,
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "items.handler",
      code: lambda.Code.fromAsset("src/handlers"),
      memorySize: 512,
      timeout: cdk.Duration.seconds(30),
      tracing: lambda.Tracing.ACTIVE,
      logGroup,
      environment: {
        TABLE_NAME: itemsTable.tableName,
        LOG_LEVEL: stageName === "prod" ? "WARNING" : "INFO",
      },
    });

    // Grant DynamoDB permissions
    itemsTable.grantReadWriteData(itemsFunction);

    // ── HTTP API ──────────────────────────────────────────────────────────
    const api = new apigwv2.HttpApi(this, "ItemsApi", {
      apiName: `items-api-${stageName}`,
      description: `Items API – ${stageName}`,
      corsPreflight: {
        allowHeaders: ["Content-Type", "Authorization"],
        allowMethods: [apigwv2.CorsHttpMethod.ANY],
        allowOrigins: ["*"],
        maxAge: cdk.Duration.seconds(600),
      },
    });

    const integration = new HttpLambdaIntegration("ItemsIntegration", itemsFunction);

    api.addRoutes({ path: "/items", methods: [apigwv2.HttpMethod.GET], integration });
    api.addRoutes({ path: "/items", methods: [apigwv2.HttpMethod.POST], integration });
    api.addRoutes({ path: "/items/{id}", methods: [apigwv2.HttpMethod.GET], integration });
    api.addRoutes({ path: "/items/{id}", methods: [apigwv2.HttpMethod.PUT], integration });
    api.addRoutes({ path: "/items/{id}", methods: [apigwv2.HttpMethod.DELETE], integration });

    this.apiUrl = api.url!;

    // ── Outputs ───────────────────────────────────────────────────────────
    new cdk.CfnOutput(this, "ApiUrl", {
      description: "HTTP API endpoint URL",
      value: this.apiUrl,
      exportName: `ItemsApiUrl-${stageName}`,
    });

    new cdk.CfnOutput(this, "TableName", {
      description: "DynamoDB table name",
      value: itemsTable.tableName,
    });

    new cdk.CfnOutput(this, "FunctionName", {
      description: "Lambda function name",
      value: itemsFunction.functionName,
    });
  }
}
