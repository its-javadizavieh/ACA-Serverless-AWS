# Lab 21 - Introduzione a SAM

## Obiettivo

Inizializzare un progetto SAM, definire una funzione Lambda e una tabella DynamoDB nel template, testare localmente e fare il deploy su AWS.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Terminale con AWS SAM CLI installato (Cloud9 lo ha pre-installato)
- Docker installato (per test locali)

## Scenario

Creerai un'API serverless che salva e recupera ordini, usando SAM per definire l'infrastruttura e deployare tutto con un singolo comando.

## Step

### Step 1 - Inizializzare il progetto SAM

```bash
sam init --runtime python3.12 --name order-api --app-template hello-world --no-tracing --no-application-insights
cd order-api
```

### Step 2 - Modificare il template SAM

Sostituisci il contenuto di `template.yaml`:

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31
Description: Order API - SAM Lab 21

Globals:
  Function:
    Runtime: python3.12
    Timeout: 10
    MemorySize: 128
    Environment:
      Variables:
        TABLE_NAME: !Ref OrdersTable

Resources:
  CreateOrderFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.create_order
      CodeUri: src/
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref OrdersTable
      Events:
        CreateOrder:
          Type: Api
          Properties:
            Path: /orders
            Method: post

  GetOrderFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.get_order
      CodeUri: src/
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref OrdersTable
      Events:
        GetOrder:
          Type: Api
          Properties:
            Path: /orders/{order_id}
            Method: get

  OrdersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: sam-lab21-orders
      AttributeDefinitions:
        - AttributeName: order_id
          AttributeType: S
      KeySchema:
        - AttributeName: order_id
          KeyType: HASH
      BillingMode: PAY_PER_REQUEST

Outputs:
  ApiUrl:
    Description: API endpoint URL
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/"
```

### Step 3 - Creare il codice Lambda

Crea la directory `src/` e il file `src/app.py`:

```python
import json
import os
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def create_order(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        order_id = str(uuid.uuid4())[:8]

        item = {
            'order_id': order_id,
            'customer': body.get('customer', 'unknown'),
            'total': str(body.get('total', 0)),
            'status': 'created'
        }

        table.put_item(Item=item)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Order created', 'order': item})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_order(event, context):
    try:
        order_id = event['pathParameters']['order_id']

        response = table.get_item(Key={'order_id': order_id})
        item = response.get('Item')

        if not item:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Order not found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({'order': item})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### Step 4 - Validare il template

```bash
sam validate
```

Output atteso: `template.yaml is a valid SAM Template`

### Step 5 - Build

```bash
sam build
```

### Step 6 - Test locale (opzionale, richiede Docker)

```bash
sam local invoke CreateOrderFunction --event events/create_order.json
```

Crea `events/create_order.json`:

```json
{
  "body": "{\"customer\": \"Alice\", \"total\": 99.99}",
  "httpMethod": "POST",
  "path": "/orders"
}
```

### Step 7 - Deploy su AWS

```bash
sam deploy --guided
```

Risposte suggerite:

- Stack name: `order-api-lab21`
- Region: `us-east-1`
- Confirm changes: `Y`
- Allow SAM CLI IAM role creation: `Y`
- CreateOrderFunction may not have authorization: `Y`
- GetOrderFunction may not have authorization: `Y`
- Save arguments: `Y`

### Step 8 - Testare l'API live

1. Copia l'URL API dall'output del deploy
2. Crea un ordine:

```bash
curl -X POST https://XXXXXXX.execute-api.us-east-1.amazonaws.com/Prod/orders \
  -H "Content-Type: application/json" \
  -d '{"customer": "Bob", "total": 150}'
```

3. Recupera l'ordine (usa l'order_id dalla risposta):

```bash
curl https://XXXXXXX.execute-api.us-east-1.amazonaws.com/Prod/orders/ORDER_ID
```

## Output atteso

- Progetto SAM con 2 Lambda + 1 DynamoDB + 1 API Gateway
- Deploy riuscito con URL API funzionante
- POST crea ordini, GET li recupera

## Checkpoint

- [ ] `sam validate` conferma template valido
- [ ] `sam build` completa senza errori
- [ ] `sam deploy` crea lo stack CloudFormation con successo
- [ ] POST `/orders` restituisce 200 con l'ordine creato
- [ ] GET `/orders/{id}` restituisce l'ordine corretto

## Troubleshooting rapido

| Problema                              | Soluzione                                                         |
| ------------------------------------- | ----------------------------------------------------------------- |
| "sam: command not found"              | In Cloud9 e pre-installato. Altrimenti: `pip install aws-sam-cli` |
| "No AWS credentials"                  | Esegui `aws configure` o verifica che il Learner Lab sia attivo   |
| Deploy fallisce su IAM                | Seleziona `Y` per "Allow SAM CLI IAM role creation"               |
| 403 Forbidden sull'API                | L'API non ha autorizzazione configurata (atteso per questo lab)   |
| "Table not found" durante test locale | SAM local non crea DynamoDB; testa direttamente dopo il deploy    |

## Cleanup obbligatorio

```bash
sam delete --stack-name order-api-lab21 --no-prompts
```

Questo elimina: Lambda functions, API Gateway, DynamoDB table, IAM roles, S3 deployment bucket.

Verifica nella console CloudFormation che lo stack sia stato eliminato.

## Parole chiave Google (screenshot/guide)

- "AWS SAM init tutorial python"
- "SAM deploy guided example"
- "SAM template DynamoDB example"
- "SAM local invoke tutorial"
- "SAM CLI commands reference"
