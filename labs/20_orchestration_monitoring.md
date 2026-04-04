# Lab 20 - Orchestrazione Multi-Servizio e Monitoraggio

## Obiettivo

Creare un workflow Step Functions che usa integrazioni SDK dirette (DynamoDB, S3) senza Lambda, abilitare logging e monitorare con CloudWatch.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Completato i lab 18-19 (Step Functions base e gestione errori)

## Scenario

Creerai un workflow che registra un ordine in DynamoDB e salva una ricevuta in S3 usando integrazioni SDK dirette, senza funzioni Lambda intermedie.

## Step

### Step 1 - Creare le risorse

1. **DynamoDB:** crea tabella `lab20-orders` con partition key `order_id` (String)
2. **S3:** crea bucket `lab20-receipts-TUONOME` (us-east-1)

### Step 2 - Creare la state machine

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

### Step 3 - Eseguire il workflow

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

### Step 4 - Verificare i risultati

1. **DynamoDB:** vai a `lab20-orders` -> Explore table items
2. Verifica che l'ordine `ORD-500` sia presente con tutti gli attributi
3. **S3:** vai al bucket `lab20-receipts-TUONOME`
4. Naviga nella cartella `receipts/`
5. Scarica `ORD-500.json` e verifica il contenuto

### Step 5 - Eseguire un secondo ordine

```json
{
  "order_id": "ORD-501",
  "customer": "Bob",
  "total": 49.99
}
```

Verifica che anche questo ordine appaia in DynamoDB e S3.

### Step 6 - Analizzare i log e le metriche

1. Vai a **CloudWatch** -> **Log groups** -> `step-functions-lab20`
2. Osserva i log: vedrai ogni transizione di stato con input e output
3. Vai a **CloudWatch** -> **Metrics** -> **States**
4. Cerca le metriche per `direct-integration-demo`:
   - ExecutionsSucceeded
   - ExecutionTime

## Output atteso

- 2 ordini salvati in DynamoDB (ORD-500 e ORD-501)
- 2 ricevute JSON in S3 (`receipts/ORD-500.json` e `receipts/ORD-501.json`)
- 0 funzioni Lambda utilizzate
- Log dettagliati in CloudWatch

## Checkpoint

- [ ] Il workflow usa DynamoDB PutItem direttamente (nessuna Lambda)
- [ ] Il workflow usa S3 PutObject direttamente (nessuna Lambda)
- [ ] Gli ordini sono presenti in DynamoDB
- [ ] Le ricevute sono presenti in S3
- [ ] I log CloudWatch mostrano le transizioni di stato

## Troubleshooting rapido

| Problema                            | Soluzione                                                                                         |
| ----------------------------------- | ------------------------------------------------------------------------------------------------- |
| "AccessDeniedException" su DynamoDB | Verifica che il ruolo della state machine abbia permessi dynamodb:PutItem                         |
| "AccessDeniedException" su S3       | Verifica che il ruolo abbia permessi s3:PutObject                                                 |
| Errore "States.Format"              | Controlla la sintassi: `States.Format('{}', $.total)` (le virgolette JSON devono essere corrette) |
| Log vuoti                           | Verifica che il logging sia abilitato e il log group sia corretto                                 |

## Cleanup obbligatorio

1. **Step Functions:** elimina `direct-integration-demo`
2. **DynamoDB:** elimina `lab20-orders`
3. **S3:** svuota e elimina `lab20-receipts-TUONOME`
4. **CloudWatch Logs:** elimina `step-functions-lab20` e altri log group correlati
5. **IAM:** elimina eventuali ruoli creati automaticamente

## Parole chiave Google (screenshot/guide)

- "Step Functions DynamoDB direct integration"
- "Step Functions S3 putObject integration"
- "Step Functions SDK service integrations"
- "Step Functions CloudWatch logging"
- "Step Functions execution monitoring"
