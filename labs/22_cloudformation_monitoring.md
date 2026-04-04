# Lab 22 - CloudFormation, Deploy Automatizzato e Monitoraggio CloudWatch

## Obiettivo

Deployare un'applicazione SAM, esplorare lo stack CloudFormation, creare allarmi CloudWatch e analizzare i log con Logs Insights.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Terminale con SAM CLI (Cloud9 consigliato)
- Completato il lab 21 (SAM base)

## Scenario

Aggiungi monitoraggio alla tua applicazione SAM: allarmi su errori Lambda, analisi dei log con Logs Insights e un dashboard CloudWatch.

## Step

### Step 1 - Deployare l'applicazione SAM

Se non hai gia l'app dal lab 21, inizializzala:

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

### Step 2 - Generare traffico di test

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

### Step 3 - Esplorare lo stack CloudFormation

1. Vai a **CloudFormation** -> Stacks -> `monitored-api-lab22`
2. Tab **Resources:** osserva tutte le risorse create da SAM (Lambda, API Gateway, IAM Role, ecc.)
3. Tab **Template:** confronta il template SAM originale con le risorse generate
4. Tab **Events:** vedi l'ordine di creazione delle risorse

### Step 4 - Analizzare i log con Logs Insights

1. Vai a **CloudWatch** -> **Logs Insights**
2. Seleziona il log group della Lambda (es. `/aws/lambda/monitored-api-lab22-ProcessFunction-XXXX`)
3. Esegui queste query:

**Top invocazioni piu lente:**

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

### Step 5 - Creare un allarme CloudWatch

1. Vai a **CloudWatch** -> **Alarms** -> **Create alarm**
2. Seleziona metrica: **Lambda** -> **By Function Name** -> `Errors` per la tua funzione
3. Configura:
   - Statistic: Sum
   - Period: 5 minutes
   - Threshold: Greater than 2
4. Actions: Skip (niente SNS per questo lab)
5. Nome: `lab22-lambda-errors`
6. **Create alarm**

### Step 6 - Creare un dashboard

1. Vai a **CloudWatch** -> **Dashboards** -> **Create dashboard**
2. Nome: `lab22-serverless`
3. Aggiungi widget:
   - **Line graph:** Lambda Invocations (per la tua funzione)
   - **Line graph:** Lambda Errors
   - **Number:** Lambda Duration (Average)
4. Salva il dashboard

## Output atteso

- Stack CloudFormation con tutte le risorse SAM visibili
- Logs Insights mostra invocazioni lente, errori, e cold starts
- Allarme CloudWatch configurato per errori Lambda
- Dashboard con metriche Lambda

## Checkpoint

- [ ] Lo stack CloudFormation mostra tutte le risorse create
- [ ] Logs Insights restituisce risultati per le query eseguite
- [ ] L'allarme `lab22-lambda-errors` e in stato OK o ALARM
- [ ] Il dashboard `lab22-serverless` visualizza le metriche Lambda

## Troubleshooting rapido

| Problema                     | Soluzione                                                                       |
| ---------------------------- | ------------------------------------------------------------------------------- |
| Logs Insights vuoto          | Aspetta 1-2 minuti dopo aver generato traffico; seleziona il log group corretto |
| Nessuna metrica Lambda       | Le metriche appaiono dopo la prima invocazione; aspetta qualche minuto          |
| Stack deploy fallisce        | Controlla CloudFormation Events per il messaggio di errore specifico            |
| Allarme in INSUFFICIENT_DATA | La metrica non ha ancora dati; genera qualche invocazione                       |

## Cleanup obbligatorio

```bash
sam delete --stack-name monitored-api-lab22 --no-prompts
```

Inoltre:

1. **CloudWatch Alarms:** elimina `lab22-lambda-errors`
2. **CloudWatch Dashboards:** elimina `lab22-serverless`
3. **CloudWatch Logs:** elimina eventuali log group residui

## Parole chiave Google (screenshot/guide)

- "CloudFormation stack resources tab"
- "CloudWatch Logs Insights Lambda tutorial"
- "CloudWatch alarm Lambda errors"
- "CloudWatch dashboard serverless"
- "SAM deploy CloudFormation stack"
