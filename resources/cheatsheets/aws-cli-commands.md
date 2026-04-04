# AWS Serverless Cheat Sheet

## AWS Lambda

```bash
# Deploy with SAM
sam build && sam deploy --guided

# Invoke function
aws lambda invoke --function-name MY_FN --payload '{}' --cli-binary-format raw-in-base64-out out.json

# View logs
aws logs tail /aws/lambda/MY_FN --follow

# Update function code
aws lambda update-function-code --function-name MY_FN --zip-file fileb://function.zip

# Get function configuration
aws lambda get-function-configuration --function-name MY_FN

# List functions
aws lambda list-functions --query 'Functions[*].[FunctionName,Runtime,MemorySize]' --output table

# Put a concurrency reservation
aws lambda put-function-concurrency --function-name MY_FN --reserved-concurrent-executions 10
```

## Amazon DynamoDB

```bash
# Put item
aws dynamodb put-item --table-name MY_TABLE \
  --item '{"PK":{"S":"USER#1"},"SK":{"S":"PROFILE"},"name":{"S":"Alice"}}'

# Get item
aws dynamodb get-item --table-name MY_TABLE \
  --key '{"PK":{"S":"USER#1"},"SK":{"S":"PROFILE"}}'

# Query
aws dynamodb query --table-name MY_TABLE \
  --key-condition-expression "PK = :pk" \
  --expression-attribute-values '{":pk":{"S":"USER#1"}}'

# Scan (avoid in production)
aws dynamodb scan --table-name MY_TABLE --filter-expression "begins_with(PK, :prefix)" \
  --expression-attribute-values '{":prefix":{"S":"USER#"}}'

# Describe table
aws dynamodb describe-table --table-name MY_TABLE --query 'Table.{Status:TableStatus,ItemCount:ItemCount}'
```

## Amazon API Gateway

```bash
# List APIs (HTTP)
aws apigatewayv2 list-apis --query 'Items[*].[Name,ApiId,ApiEndpoint]' --output table

# List APIs (REST)
aws apigateway get-rest-apis --query 'items[*].[name,id]' --output table

# Get stage URL (HTTP API)
aws apigatewayv2 get-api --api-id API_ID --query 'ApiEndpoint'

# Test invoke (REST API)
aws apigateway test-invoke-method --rest-api-id API_ID --resource-id RES_ID --http-method GET
```

## Amazon SNS & SQS

```bash
# Publish to SNS
aws sns publish --topic-arn TOPIC_ARN \
  --message '{"orderId":"42"}' \
  --message-attributes '{"eventType":{"DataType":"String","StringValue":"order.created"}}'

# Send to SQS
aws sqs send-message --queue-url QUEUE_URL --message-body '{"orderId":"42"}'

# Receive from SQS
aws sqs receive-message --queue-url QUEUE_URL --max-number-of-messages 10

# Get queue attributes (message count etc.)
aws sqs get-queue-attributes --queue-url QUEUE_URL \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible

# Purge queue (all messages)
aws sqs purge-queue --queue-url QUEUE_URL
```

## AWS Step Functions

```bash
# Start execution
aws stepfunctions start-execution \
  --state-machine-arn STATE_MACHINE_ARN \
  --input '{"orderId":"42"}'

# List executions
aws stepfunctions list-executions --state-machine-arn STATE_MACHINE_ARN \
  --status-filter RUNNING --output table

# Describe execution
aws stepfunctions describe-execution --execution-arn EXECUTION_ARN

# Get execution history
aws stepfunctions get-execution-history --execution-arn EXECUTION_ARN \
  --query 'events[*].[type,timestamp]' --output table
```

## AWS CloudFormation / SAM

```bash
# List stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[*].[StackName,StackStatus]' --output table

# Get stack outputs
aws cloudformation describe-stacks --stack-name MY_STACK \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' --output table

# Detect drift
aws cloudformation detect-stack-drift --stack-name MY_STACK

# Delete stack
aws cloudformation delete-stack --stack-name MY_STACK
```

## AWS CDK

```bash
# Bootstrap
cdk bootstrap aws://ACCOUNT_ID/REGION

# Diff
cdk diff

# Deploy
cdk deploy --all --require-approval never

# Synth
cdk synth

# Destroy
cdk destroy --all
```

## SAM CLI

```bash
# Init new project
sam init

# Build
sam build

# Local invoke
sam local invoke FunctionName --event events/test.json

# Local API
sam local start-api --port 3000

# Deploy (guided)
sam deploy --guided

# Deploy (subsequent)
sam deploy

# Logs
sam logs --name FunctionName --tail

# Delete
sam delete
```

## Useful AWS CLI Shortcuts

```bash
# Get current account ID
aws sts get-caller-identity --query Account --output text

# Get current region
aws configure get region

# Set profile
export AWS_PROFILE=my-profile

# Enable JSON output
export AWS_DEFAULT_OUTPUT=json
```
