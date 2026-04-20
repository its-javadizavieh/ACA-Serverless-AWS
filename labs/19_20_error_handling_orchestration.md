# Lab 19-20 - Gestione Errori, Orchestrazione e Monitoraggio Step Functions

## Obiettivo

**Parte A:** Aggiungere gestione errori (Retry e Catch) a una state machine, simulare errori transienti e permanenti, e osservare il comportamento di retry e fallback.

**Parte B:** Creare un workflow Step Functions che usa integrazioni SDK dirette (DynamoDB, S3) senza Lambda, abilitare logging e monitorare con CloudWatch.

## Durata (timebox)

60 minuti (30 + 30)

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Completato i lab 18 (Step Functions base)

---

# Parte A - Gestione Errori e Retry in Step Functions

## Scenario

Espandi il workflow di elaborazione ordini aggiungendo simulazione di errori, retry automatici e stati di fallback.

## Step

### Step 1 - Creare le funzioni Lambda

1. Crea `validate-order-v2` (Python 3.12, LabRole):

```python
import json

def lambda_handler(event, context):
    order_id = event.get('order_id', 'unknown')
    total = event.get('total', 0)

    if total <= 0:
        raise ValueError(f"Invalid total: {total}")

    return {
        'order_id': order_id,
        'total': total,
        'status': 'validated'
    }
```

2. Crea `process-payment` (Python 3.12, LabRole):

```python
import json
import random

def lambda_handler(event, context):
    order_id = event.get('order_id', 'unknown')
    total = event.get('total', 0)
    simulate_error = event.get('simulate_error', False)

    # Simulate transient failure (50% chance if simulate_error is True)
    if simulate_error and random.random() < 0.5:
        raise RuntimeError(f"Payment service temporarily unavailable for order {order_id}")

    return {
        'order_id': order_id,
        'total': total,
        'payment_id': f'PAY-{order_id}',
        'status': 'paid'
    }
```

3. Crea `handle-failure` (Python 3.12, LabRole):

```python
import json

def lambda_handler(event, context):
    error = event.get('error', {})
    order_id = event.get('order_id', 'unknown')

    print(f"FAILURE HANDLER: Order {order_id}")
    print(f"Error: {json.dumps(error)}")

    return {
        'order_id': order_id,
        'status': 'failed',
        'error_handled': True,
        'message': f'Order {order_id} failed and has been logged for review'
    }
```

### Step 2 - Creare la state machine con errori

1. Vai a **Step Functions** -> **Create state machine**
2. Seleziona **Write your workflow in code**
3. Type: **Standard**
4. Definizione ASL (sostituisci `ACCOUNT_ID` con il tuo ID account e la regione corretta):

```json
{
  "Comment": "Order processing with error handling",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:validate-order-v2",
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "ResultPath": "$.error",
          "Next": "HandleFailure"
        }
      ],
      "Next": "ProcessPayment"
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:process-payment",
      "Retry": [
        {
          "ErrorEquals": ["RuntimeError"],
          "IntervalSeconds": 2,
          "MaxAttempts": 3,
          "BackoffRate": 2.0
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "ResultPath": "$.error",
          "Next": "HandleFailure"
        }
      ],
      "Next": "OrderConfirmed"
    },
    "OrderConfirmed": {
      "Type": "Succeed"
    },
    "HandleFailure": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:handle-failure",
      "Next": "OrderFailed"
    },
    "OrderFailed": {
      "Type": "Fail",
      "Error": "OrderProcessingFailed",
      "Cause": "The order could not be processed after all retry attempts"
    }
  }
}
```

5. Nome: `order-processor-v2`
6. Ruolo: `LabRole` o ruolo generato automaticamente
7. **Create state machine**

### Step 3 - Test: ordine valido senza errori

```json
{
  "order_id": "ORD-100",
  "total": 150,
  "simulate_error": false
}
```

Risultato atteso: ValidateOrder -> ProcessPayment -> OrderConfirmed (tutto verde)

### Step 4 - Test: ordine con errori transienti

```json
{
  "order_id": "ORD-200",
  "total": 200,
  "simulate_error": true
}
```

Risultato atteso: ValidateOrder -> ProcessPayment (potrebbe fare 1-3 retry) -> OrderConfirmed O HandleFailure

### Step 5 - Test: ordine non valido

```json
{
  "order_id": "ORD-300",
  "total": -50
}
```

Risultato atteso: ValidateOrder FALLISCE -> HandleFailure -> OrderFailed

### Step 6 - Analizzare i retry

1. Nell'esecuzione con `simulate_error: true`, clicca su **ProcessPayment**
2. Nella sezione **Events**, conta quanti tentativi ha fatto
3. Osserva gli intervalli tra i retry (2s, 4s, 8s)

## Checkpoint Parte A

- [ ] Il workflow con ordine valido arriva a OrderConfirmed
- [ ] I retry sono visibili negli eventi di ProcessPayment
- [ ] L'ordine non valido attiva HandleFailure
- [ ] Il messaggio di errore e visibile nello stato OrderFailed

---

# Parte B - Orchestrazione Multi-Servizio e Monitoraggio

## Scenario

Creerai un workflow che registra un ordine in DynamoDB e salva una ricevuta in S3 usando integrazioni SDK dirette, senza funzioni Lambda intermedie.

## Step

### Step 7 - Creare le risorse

1. **DynamoDB:** crea tabella `lab20-orders` con partition key `order_id` (String)
2. **S3:** crea bucket `lab20-receipts-TUONOME` (us-east-1)

### Step 8 - Creare la state machine

1. Vai a **Step Functions** -> **Create state machine**
2. Seleziona **Write your workflow in code**
3. Type: **Standard**
4. Definizione (sostituisci `ACCOUNT_ID` e `TUONOME`):

```json
{
  "Comment": "Direct SDK integration workflow",
  "StartAt": "SaveOrder",
  "States": {
    "SaveOrder": {
      "Type": "Task",
      "Resource": "arn:aws:states:::dynamodb:putItem",
      "Parameters": {
        "TableName": "lab20-orders",
        "Item": {
          "order_id": { "S.$": "$.order_id" },
          "customer": { "S.$": "$.customer" },
          "total": { "N.$": "States.Format('{}', $.total)" },
          "status": { "S": "confirmed" }
        }
      },
      "ResultPath": "$.dynamoResult",
      "Next": "SaveReceipt"
    },
    "SaveReceipt": {
      "Type": "Task",
      "Resource": "arn:aws:states:::s3:putObject",
      "Parameters": {
        "Bucket": "lab20-receipts-TUONOME",
        "Key.$": "States.Format('receipts/{}.json', $.order_id)",
        "Body": {
          "order_id.$": "$.order_id",
          "customer.$": "$.customer",
          "total.$": "$.total",
          "status": "confirmed"
        }
      },
      "ResultPath": "$.s3Result",
      "Next": "OrderComplete"
    },
    "OrderComplete": {
      "Type": "Succeed"
    }
  }
}
```

5. Nome: `direct-integration-demo`
6. Ruolo: seleziona `LabRole` (deve avere permessi DynamoDB e S3)
7. **Logging:** abilita ALL, seleziona o crea un log group `step-functions-lab20`
8. **Create state machine**

### Step 9 - Eseguire il workflow

1. Clicca **Start execution**
2. Input:

```json
{
  "order_id": "ORD-500",
  "customer": "Alice",
  "total": 199.99
}
```

3. Osserva l'esecuzione visuale
4. Verifica che entrambi gli stati siano verdi (successo)

### Step 10 - Verificare i risultati

1. **DynamoDB:** vai a `lab20-orders` -> Explore table items
2. Verifica che l'ordine `ORD-500` sia presente con tutti gli attributi
3. **S3:** vai al bucket `lab20-receipts-TUONOME`
4. Naviga nella cartella `receipts/`
5. Scarica `ORD-500.json` e verifica il contenuto

### Step 11 - Eseguire un secondo ordine

```json
{
  "order_id": "ORD-501",
  "customer": "Bob",
  "total": 49.99
}
```

Verifica che anche questo ordine appaia in DynamoDB e S3.

### Step 12 - Analizzare i log e le metriche

1. Vai a **CloudWatch** -> **Log groups** -> `step-functions-lab20`
2. Osserva i log: vedrai ogni transizione di stato con input e output
3. Vai a **CloudWatch** -> **Metrics** -> **States**
4. Cerca le metriche per `direct-integration-demo`:
   - ExecutionsSucceeded
   - ExecutionTime

## Checkpoint Parte B

- [ ] Il workflow usa DynamoDB PutItem direttamente (nessuna Lambda)
- [ ] Il workflow usa S3 PutObject direttamente (nessuna Lambda)
- [ ] Gli ordini sono presenti in DynamoDB
- [ ] Le ricevute sono presenti in S3
- [ ] I log CloudWatch mostrano le transizioni di stato

---

## Output atteso

**Parte A:**
- Ordine valido: workflow completato con successo
- Ordine con errori transienti: retry visibili, successo o fallback
- Ordine non valido: fallback a HandleFailure -> OrderFailed

**Parte B:**
- 2 ordini salvati in DynamoDB (ORD-500 e ORD-501)
- 2 ricevute JSON in S3 (`receipts/ORD-500.json` e `receipts/ORD-501.json`)
- 0 funzioni Lambda utilizzate
- Log dettagliati in CloudWatch

## Troubleshooting rapido

| Problema                            | Soluzione                                                                                         |
| ----------------------------------- | ------------------------------------------------------------------------------------------------- |
| "AccessDeniedException"             | Verifica che il ruolo della state machine abbia lambda:InvokeFunction                             |
| I retry non funzionano              | Verifica che ErrorEquals corrisponda al tipo di errore lanciato da Lambda                         |
| HandleFailure non riceve l'errore   | Verifica ResultPath: "$.error" nel Catch                                                          |
| ARN Lambda non valido               | Correggi ACCOUNT_ID e la regione nella definizione ASL                                            |
| "AccessDeniedException" su DynamoDB | Verifica che il ruolo della state machine abbia permessi dynamodb:PutItem                         |
| "AccessDeniedException" su S3       | Verifica che il ruolo abbia permessi s3:PutObject                                                 |
| Errore "States.Format"              | Controlla la sintassi: `States.Format('{}', $.total)` (le virgolette JSON devono essere corrette) |
| Log vuoti                           | Verifica che il logging sia abilitato e il log group sia corretto                                 |

## Cleanup obbligatorio

1. **Step Functions:** elimina `order-processor-v2` e `direct-integration-demo`
2. **Lambda:** elimina `validate-order-v2`, `process-payment`, `handle-failure`
3. **DynamoDB:** elimina `lab20-orders`
4. **S3:** svuota e elimina `lab20-receipts-TUONOME`
5. **CloudWatch Logs:** elimina `step-functions-lab20` e i log group delle funzioni Lambda
6. **IAM:** elimina eventuali ruoli creati automaticamente per Step Functions

## Parole chiave Google (screenshot/guide)

- "Step Functions Retry Catch example"
- "Step Functions error handling tutorial"
- "Amazon States Language Retry BackoffRate"
- "Step Functions Catch ResultPath"
- "Step Functions execution history events"
- "Step Functions DynamoDB direct integration"
- "Step Functions S3 putObject integration"
- "Step Functions SDK service integrations"
- "Step Functions CloudWatch logging"
- "Step Functions execution monitoring"
