# Lab 12 - Versioni, Stage e Monitoraggio API

## Obiettivo

Configurare un'API con stage multipli, stage variables, logging e monitoraggio CloudWatch.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Familiarita con API Gateway e Lambda (lab 10-11)

## Scenario

Hai un'API gia funzionante. La deploy su due stage (dev e prod) con configurazioni diverse e imposti il monitoraggio completo.

## Step

### Step 1 - Creare la funzione Lambda

1. Vai a **Lambda** -> **Create function**
2. Function name: `stage-demo`
3. Runtime: **Python 3.12**, Role: `LabRole`
4. Codice:

```python
import json
import os

def lambda_handler(event, context):
    stage = event.get('requestContext', {}).get('stage', 'unknown')

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': f'Hello from {stage} stage!',
            'stage': stage,
            'function_version': context.function_version
        })
    }
```

5. Clicca **Deploy**

### Step 2 - Creare l'API con stage multipli

1. Vai a **API Gateway** -> **Create API** -> **REST API** -> **Build**
2. API name: `multi-stage-api`
3. Crea risorsa `/status` con metodo **GET** -> Lambda proxy -> `stage-demo`
4. **Deploy API** -> Stage: `dev`
5. **Deploy API** nuovamente -> Stage: `prod`

### Step 3 - Configurare stage variables

1. Vai a **Stages** -> seleziona `dev`
2. Tab **Stage Variables** -> **Add Stage Variable**
3. Name: `environment`, Value: `development`
4. Ripeti per lo stage `prod`: Name: `environment`, Value: `production`

### Step 4 - Abilitare i log di accesso

1. Vai a **Stages** -> seleziona `dev`
2. Tab **Logs/Tracing**
3. Abilita **CloudWatch Logs**: seleziona **INFO**
4. Abilita **Access Logging**
5. Per il formato JSON, inserisci:

```
{"requestId":"$context.requestId","ip":"$context.identity.sourceIp","method":"$context.httpMethod","status":"$context.status","latency":"$context.responseLatency"}
```

6. Per l'ARN del log group, crea prima un log group in CloudWatch:
   - Vai a **CloudWatch** -> **Log groups** -> **Create log group**
   - Nome: `api-access-logs-dev`
   - Copia l'ARN e incollalo nel campo
7. Salva le modifiche

### Step 5 - Testare e generare traffico

1. Apri gli invoke URL dei due stage nel browser:
   - `https://<api-id>.execute-api.us-east-1.amazonaws.com/dev/status`
   - `https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/status`
2. Verifica che la risposta contenga lo stage corretto
3. Fai almeno 5 richieste per generare dati nei log

### Step 6 - Analizzare i log

1. Vai a **CloudWatch** -> **Logs** -> **Logs Insights**
2. Seleziona il log group `api-access-logs-dev`
3. Esegui la query:

```
fields @timestamp, @message
| parse @message '"status":"*"' as status
| stats count() by status
```

4. Osserva la distribuzione degli status code

## Output atteso

- Due stage funzionanti (dev, prod) con risposte diverse
- Log di accesso in formato JSON nel log group
- Query Logs Insights con distribuzione status code

## Checkpoint

- [ ] L'endpoint dev restituisce `"stage": "dev"`
- [ ] L'endpoint prod restituisce `"stage": "prod"`
- [ ] I log di accesso sono visibili in CloudWatch
- [ ] La query Logs Insights restituisce risultati

## Troubleshooting rapido

| Problema                                   | Soluzione                                                                                      |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| Lo stage mostra "unknown"                  | Verifica di usare Lambda proxy integration (requestContext.stage viene passato solo con proxy) |
| Log di accesso vuoti                       | I log possono impiegare 1-2 minuti ad apparire. Verifica l'ARN del log group                   |
| Errore nel salvare le impostazioni del log | Verifica che il log group esista e che l'ARN sia corretto                                      |

## Cleanup obbligatorio

1. **API Gateway:** elimina `multi-stage-api`
2. **Lambda:** elimina `stage-demo`
3. **CloudWatch Logs:** elimina `api-access-logs-dev` e i log group delle funzioni Lambda
4. **CloudWatch:** elimina eventuali dashboard create

## Parole chiave Google (screenshot/guide)

- "API Gateway multiple stages tutorial"
- "API Gateway stage variables"
- "API Gateway access logging CloudWatch"
- "CloudWatch Logs Insights API Gateway"
- "API Gateway canary deployment"
