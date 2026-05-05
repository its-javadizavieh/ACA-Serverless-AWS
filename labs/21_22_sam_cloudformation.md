# Lab 21-22 - SAM, CloudFormation e Monitoraggio

## Obiettivo

**Parte A:** Inizializzare un progetto SAM, definire una funzione Lambda e una tabella DynamoDB nel template, testare localmente e fare il deploy su AWS.

**Parte B:** Deployare un'applicazione SAM, esplorare lo stack CloudFormation, creare allarmi CloudWatch e analizzare i log con Logs Insights.

## Durata (timebox)

60 minuti (30 + 30)

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Terminale con AWS SAM CLI installato (Cloud9 lo ha pre-installato)
- Docker installato (per test locali)

---

# Parte A - Introduzione a SAM

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

## Checkpoint Parte A

- [ ] `sam validate` conferma template valido
- [ ] `sam build` completa senza errori
- [ ] `sam deploy` crea lo stack CloudFormation con successo
- [ ] POST `/orders` restituisce 200 con l'ordine creato
- [ ] GET `/orders/{id}` restituisce l'ordine corretto

---

# Parte B - CloudFormation, Deploy Automatizzato e Monitoraggio CloudWatch

## Scenario

Aggiungi monitoraggio alla tua applicazione SAM: allarmi su errori Lambda, analisi dei log con Logs Insights e un dashboard CloudWatch.

## Step

### Step 9 - Deployare l'applicazione SAM

Se non hai gia' l'app dal lab 21, inizializzala:

```bash
sam init --runtime python3.12 --name monitored-api --app-template hello-world --no-tracing --no-application-insights
cd monitored-api
```

Aggiorna `template.yaml` con una funzione che genera errori controllabili:

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31
Description: Monitored API - Lab 22

Resources:
  ProcessFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.handler
      Runtime: python3.12
      Timeout: 10
      MemorySize: 128
      Events:
        Process:
          Type: Api
          Properties:
            Path: /process
            Method: post

Outputs:
  ApiUrl:
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/"
```

Crea `src/app.py` (o `hello_world/app.py` a seconda del template):

```python
import json
import time
import random

def handler(event, context):
    body = json.loads(event.get('body', '{}'))
    action = body.get('action', 'fast')

    if action == 'error':
        raise ValueError("Simulated error for monitoring test")
    elif action == 'slow':
        time.sleep(3)
    elif action == 'random':
        if random.random() < 0.3:
            raise RuntimeError("Random failure")

    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'ok', 'action': action})
    }
```

Build e deploy:

```bash
sam build
sam deploy --guided --stack-name monitored-api-lab22
```

### Step 10 - Generare traffico di test

Usa l'URL API dall'output del deploy:

```bash
API_URL="https://XXXXXXX.execute-api.us-east-1.amazonaws.com/Prod"

# Richieste normali
for i in {1..10}; do
  curl -s -X POST "$API_URL/process" -H "Content-Type: application/json" -d '{"action": "fast"}' &
done
wait

# Richieste lente
for i in {1..3}; do
  curl -s -X POST "$API_URL/process" -H "Content-Type: application/json" -d '{"action": "slow"}' &
done
wait

# Richieste con errore
for i in {1..5}; do
  curl -s -X POST "$API_URL/process" -H "Content-Type: application/json" -d '{"action": "error"}' &
done
wait
```

### Step 11 - Esplorare lo stack CloudFormation

1. Vai a **CloudFormation** -> Stacks -> `monitored-api-lab22`
2. Tab **Resources:** osserva tutte le risorse create da SAM (Lambda, API Gateway, IAM Role, ecc.)
3. Tab **Template:** confronta il template SAM originale con le risorse generate
4. Tab **Events:** vedi l'ordine di creazione delle risorse

### Step 12 - Analizzare i log con Logs Insights

1. Vai a **CloudWatch** -> **Logs Insights**
2. Seleziona il log group della Lambda (es. `/aws/lambda/monitored-api-lab22-ProcessFunction-XXXX`)
3. Esegui queste query:

**Top invocazioni piu' lente:**

```
filter @type = "REPORT"
| sort @duration desc
| limit 10
```

**Conteggio errori vs successi:**

```
filter @type = "REPORT"
| stats count() as total,
  sum(@duration > 1000) as slow,
  count(@initDuration) as coldStarts
```

**Messaggi di errore:**

```
filter @message like /ERROR/
| fields @timestamp, @message
| sort @timestamp desc
| limit 10
```

### Step 13 - Creare un allarme CloudWatch

1. Vai a **CloudWatch** -> **Alarms** -> **Create alarm**
2. Seleziona metrica: **Lambda** -> **By Function Name** -> `Errors` per la tua funzione
3. Configura:
   - Statistic: Sum
   - Period: 5 minutes
   - Threshold: Greater than 2
4. Actions: Skip (niente SNS per questo lab)
5. Nome: `lab22-lambda-errors`
6. **Create alarm**

### Step 14 - Creare un dashboard

1. Vai a **CloudWatch** -> **Dashboards** -> **Create dashboard**
2. Nome: `lab22-serverless`
3. Aggiungi widget:
   - **Line graph:** Lambda Invocations (per la tua funzione)
   - **Line graph:** Lambda Errors
   - **Number:** Lambda Duration (Average)
4. Salva il dashboard

## Checkpoint Parte B

- [ ] Lo stack CloudFormation mostra tutte le risorse create
- [ ] Logs Insights restituisce risultati per le query eseguite
- [ ] L'allarme `lab22-lambda-errors` e in stato OK o ALARM
- [ ] Il dashboard `lab22-serverless` visualizza le metriche Lambda

---

## Output atteso

**Parte A:**
- Progetto SAM con 2 Lambda + 1 DynamoDB + 1 API Gateway
- Deploy riuscito con URL API funzionante
- POST crea ordini, GET li recupera

**Parte B:**
- Stack CloudFormation con tutte le risorse SAM visibili
- Logs Insights mostra invocazioni lente, errori, e cold starts
- Allarme CloudWatch configurato per errori Lambda
- Dashboard con metriche Lambda

## Troubleshooting rapido

| Problema                              | Soluzione                                                                       |
| ------------------------------------- | ------------------------------------------------------------------------------- |
| "sam: command not found"              | In Cloud9 e pre-installato. Altrimenti: `pip install aws-sam-cli`               |
| "No AWS credentials"                  | Esegui `aws configure` o verifica che il Learner Lab sia attivo                 |
| Deploy fallisce su IAM                | Seleziona `Y` per "Allow SAM CLI IAM role creation"                             |
| 403 Forbidden sull'API                | L'API non ha autorizzazione configurata (atteso per questo lab)                 |
| "Table not found" durante test locale | SAM local non crea DynamoDB; testa direttamente dopo il deploy                  |
| Logs Insights vuoto                   | Aspetta 1-2 minuti dopo aver generato traffico; seleziona il log group corretto |
| Nessuna metrica Lambda                | Le metriche appaiono dopo la prima invocazione; aspetta qualche minuto          |
| Stack deploy fallisce                 | Controlla CloudFormation Events per il messaggio di errore specifico            |
| Allarme in INSUFFICIENT_DATA          | La metrica non ha ancora dati; genera qualche invocazione                       |

## Cleanup obbligatorio

```bash
sam delete --stack-name order-api-lab21 --no-prompts
sam delete --stack-name monitored-api-lab22 --no-prompts
```

Inoltre:

1. **CloudWatch Alarms:** elimina `lab22-lambda-errors`
2. **CloudWatch Dashboards:** elimina `lab22-serverless`
3. **CloudWatch Logs:** elimina eventuali log group residui

Verifica nella console CloudFormation che gli stack siano stati eliminati.

## Parole chiave Google (screenshot/guide)

- "AWS SAM init tutorial python"
- "SAM deploy guided example"
- "SAM template DynamoDB example"
- "SAM local invoke tutorial"
- "SAM CLI commands reference"
- "CloudFormation stack resources tab"
- "CloudWatch Logs Insights Lambda tutorial"
- "CloudWatch alarm Lambda errors"
- "CloudWatch dashboard serverless"
- "SAM deploy CloudFormation stack"
