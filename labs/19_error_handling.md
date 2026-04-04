# Lab 19 - Gestione Errori e Retry in Step Functions

## Obiettivo

Aggiungere gestione errori (Retry e Catch) a una state machine, simulare errori transienti e permanenti, e osservare il comportamento di retry e fallback.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Completato il lab 18 (Step Functions base)

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

## Output atteso

- Ordine valido: workflow completato con successo
- Ordine con errori transienti: retry visibili, successo o fallback
- Ordine non valido: fallback a HandleFailure -> OrderFailed

## Checkpoint

- [ ] Il workflow con ordine valido arriva a OrderConfirmed
- [ ] I retry sono visibili negli eventi di ProcessPayment
- [ ] L'ordine non valido attiva HandleFailure
- [ ] Il messaggio di errore e visibile nello stato OrderFailed

## Troubleshooting rapido

| Problema                          | Soluzione                                                                 |
| --------------------------------- | ------------------------------------------------------------------------- |
| "AccessDeniedException"           | Verifica che il ruolo della state machine abbia lambda:InvokeFunction     |
| I retry non funzionano            | Verifica che ErrorEquals corrisponda al tipo di errore lanciato da Lambda |
| HandleFailure non riceve l'errore | Verifica ResultPath: "$.error" nel Catch                                  |
| ARN Lambda non valido             | Correggi ACCOUNT_ID e la regione nella definizione ASL                    |

## Cleanup obbligatorio

1. **Step Functions:** elimina `order-processor-v2`
2. **Lambda:** elimina `validate-order-v2`, `process-payment`, `handle-failure`
3. **CloudWatch Logs:** elimina i log group delle funzioni Lambda
4. **IAM:** elimina eventuali ruoli creati automaticamente per Step Functions

## Parole chiave Google (screenshot/guide)

- "Step Functions Retry Catch example"
- "Step Functions error handling tutorial"
- "Amazon States Language Retry BackoffRate"
- "Step Functions Catch ResultPath"
- "Step Functions execution history events"
