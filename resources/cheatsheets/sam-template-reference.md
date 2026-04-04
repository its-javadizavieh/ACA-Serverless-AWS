# SAM Template Quick Reference

## Minimal Serverless Function

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Runtime: python3.12
    MemorySize: 512
    Timeout: 30
    Tracing: Active

Resources:
  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/my_function/
      Handler: app.handler
```

## HTTP API + Lambda

```yaml
  MyApi:
    Type: AWS::Serverless::HttpApi
    Properties:
      CorsConfiguration:
        AllowOrigins: ["*"]
        AllowMethods: [GET, POST, PUT, DELETE]
        AllowHeaders: [Content-Type, Authorization]

  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: app.handler
      Events:
        GetItems:
          Type: HttpApi
          Properties:
            ApiId: !Ref MyApi
            Path: /items
            Method: GET
```

## DynamoDB + Lambda (with policy)

```yaml
  MyTable:
    Type: AWS::DynamoDB::Table
    Properties:
      BillingMode: PAY_PER_REQUEST
      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE
      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK
          AttributeType: S

  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: app.handler
      Environment:
        Variables:
          TABLE_NAME: !Ref MyTable
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref MyTable
```

## SNS + SQS Fan-Out

```yaml
  MyTopic:
    Type: AWS::SNS::Topic

  MyQueue:
    Type: AWS::SQS::Queue
    Properties:
      RedrivePolicy:
        deadLetterTargetArn: !GetAtt MyDLQ.Arn
        maxReceiveCount: 3

  MyDLQ:
    Type: AWS::SQS::Queue

  MySubscription:
    Type: AWS::SNS::Subscription
    Properties:
      TopicArn: !Ref MyTopic
      Protocol: sqs
      Endpoint: !GetAtt MyQueue.Arn
      RawMessageDelivery: true

  MyConsumer:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: app.handler
      Events:
        Queue:
          Type: SQS
          Properties:
            Queue: !GetAtt MyQueue.Arn
            BatchSize: 10
            FunctionResponseTypes:
              - ReportBatchItemFailures
```

## Step Functions State Machine

```yaml
  MyStateMachine:
    Type: AWS::Serverless::StateMachine
    Properties:
      DefinitionUri: statemachine/workflow.json
      DefinitionSubstitutions:
        MyFunctionArn: !GetAtt MyFunction.Arn
      Policies:
        - LambdaInvokePolicy:
            FunctionName: !Ref MyFunction
      Type: STANDARD
      Tracing:
        Enabled: true
```

## Lambda Layer

```yaml
  MyLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      ContentUri: src/layer/
      CompatibleRuntimes:
        - python3.12
      RetentionPolicy: Delete
    Metadata:
      BuildMethod: python3.12
```

## Common SAM Policy Templates

```yaml
Policies:
  - DynamoDBCrudPolicy:          # Read + Write
      TableName: !Ref MyTable
  - DynamoDBReadPolicy:          # Read only
      TableName: !Ref MyTable
  - SNSPublishMessagePolicy:     # SNS publish
      TopicName: !GetAtt MyTopic.TopicName
  - SQSSendMessagePolicy:        # SQS send
      QueueName: !GetAtt MyQueue.QueueName
  - S3ReadPolicy:                # S3 read
      BucketName: !Ref MyBucket
  - S3CrudPolicy:                # S3 read + write
      BucketName: !Ref MyBucket
  - StepFunctionsExecutionPolicy: # Start SF execution
      StateMachineName: !GetAtt MyStateMachine.Name
```
