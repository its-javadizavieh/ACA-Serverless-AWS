# Lab 12-13 - Versioni, Stage, Caching e Monitoraggio API

## Obiettivo

**Parte A:** Configurare un'API con stage multipli, stage variables, logging e monitoraggio CloudWatch.

**Parte B:** Abilitare il caching di API Gateway, verificare cache hit/miss con CloudWatch, abilitare X-Ray tracing e prepararsi alla verifica intermedia.

## Durata (timebox)

60 minuti (30 + 30)

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Familiarita con API Gateway, Lambda e CloudWatch (lab 10-11)

---

# Parte A - Versioni, Stage e Monitoraggio API

## Scenario

Hai un'API gia' funzionante. La deploy su due stage (dev e prod) con configurazioni diverse e imposti il monitoraggio completo.

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

## Checkpoint Parte A

- [ ] L'endpoint dev restituisce `"stage": "dev"`
- [ ] L'endpoint prod restituisce `"stage": "prod"`
- [ ] I log di accesso sono visibili in CloudWatch
- [ ] La query Logs Insights restituisce risultati

---

# Parte B - Caching, Monitoraggio Avanzato e Revisione

## Scenario

Hai un'API REST con un endpoint GET. Abiliterai il caching per ridurre le invocazioni Lambda e configurerai X-Ray per il tracing distribuito.

## Step

### Step 7 - Creare l'infrastruttura per il caching

1. Crea una funzione Lambda `cache-demo` (Python 3.12, LabRole):

```python
import json
import time

def lambda_handler(event, context):
    # Simulate some processing time
    time.sleep(0.5)

    params = event.get('queryStringParameters') or {}
    category = params.get('category', 'all')

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'category': category,
            'items': ['item1', 'item2', 'item3'],
            'timestamp': time.time()
        })
    }
```

2. Crea un REST API `cache-test-api` con risorsa `/products` e metodo GET -> Lambda proxy -> `cache-demo`
3. Deploy allo stage `dev`

### Step 8 - Abilitare il caching

1. Vai a **Stages** -> `dev`
2. Tab **Settings** (o **Cache Settings**)
3. Abilita **Enable API cache**
4. Cache capacity: **0.5 GB** (minimo)
5. Cache TTL: **60** secondi
6. Salva le modifiche (il provisioning del cache richiede qualche minuto)

### Step 9 - Testare cache hit vs cache miss

1. Apri l'invoke URL nel browser: `/dev/products?category=electronics`
2. Nota il `timestamp` nella risposta
3. Ricarica la pagina entro 60 secondi
4. Se il `timestamp` e identico -> **cache hit** (Lambda non invocata)
5. Aspetta 60 secondi e ricarica -> `timestamp` cambia -> **cache miss** (TTL scaduto)
6. Prova con un parametro diverso: `/dev/products?category=books` -> cache miss (chiave diversa)

### Step 10 - Verificare le metriche

1. Vai a **CloudWatch** -> **Metrics** -> **ApiGateway**
2. Cerca le metriche per `cache-test-api`:
   - **CacheHitCount**: richieste servite dalla cache
   - **CacheMissCount**: richieste inviate a Lambda
3. Confronta i conteggi con le richieste che hai fatto

### Step 11 - Abilitare X-Ray

1. Vai a **Stages** -> `dev` -> **Logs/Tracing**
2. Abilita **X-Ray Tracing**
3. Vai alla funzione Lambda `cache-demo` -> **Configuration** -> **Monitoring and operations tools**
4. Abilita **Active tracing** (X-Ray)
5. Fai alcune richieste all'API
6. Vai a **X-Ray** -> **Service Map**
7. Osserva il flusso: API Gateway -> Lambda e i tempi di risposta

## Checkpoint Parte B

- [ ] Il timestamp non cambia tra richieste successive (cache hit)
- [ ] Il timestamp cambia dopo il TTL (cache miss)
- [ ] Le metriche CacheHitCount/CacheMissCount sono visibili
- [ ] X-Ray mostra il Service Map con i tempi

---

## Output atteso

**Parte A:**

- Due stage funzionanti (dev, prod) con risposte diverse
- Log di accesso in formato JSON nel log group
- Query Logs Insights con distribuzione status code

**Parte B:**

- Cache funzionante con timestamp identico per cache hit
- Metriche CacheHitCount e CacheMissCount in CloudWatch
- Service Map in X-Ray con flusso API Gateway -> Lambda

## Troubleshooting rapido

| Problema                                   | Soluzione                                                                                      |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| Lo stage mostra "unknown"                  | Verifica di usare Lambda proxy integration (requestContext.stage viene passato solo con proxy) |
| Log di accesso vuoti                       | I log possono impiegare 1-2 minuti ad apparire. Verifica l'ARN del log group                   |
| Errore nel salvare le impostazioni del log | Verifica che il log group esista e che l'ARN sia corretto                                      |
| Il cache non sembra funzionare             | Il provisioning del cache richiede 1-4 minuti. Aspetta e riprova                               |
| CacheHitCount sempre 0                     | Verifica di usare gli stessi query parameters nelle richieste successive                       |
| X-Ray Service Map vuoto                    | Le tracce appaiono dopo 1-2 minuti. Genera almeno 5 richieste                                  |
| Errore abilitando X-Ray                    | Verifica che LabRole abbia permessi xray:PutTraceSegments                                      |

## Cleanup obbligatorio

1. **API Gateway:** disabilita il caching prima di eliminare (per evitare costi), poi elimina `cache-test-api` e `multi-stage-api`
2. **Lambda:** elimina `stage-demo` e `cache-demo`
3. **CloudWatch Logs:** elimina `api-access-logs-dev` e i log group delle funzioni Lambda
4. **CloudWatch:** elimina eventuali dashboard create
5. **X-Ray:** non richiede cleanup (le tracce scadono automaticamente dopo 30 giorni)

## Parole chiave Google (screenshot/guide)

- "API Gateway multiple stages tutorial"
- "API Gateway stage variables"
- "API Gateway access logging CloudWatch"
- "CloudWatch Logs Insights API Gateway"
- "API Gateway canary deployment"
- "API Gateway caching REST API tutorial"
- "API Gateway cache hit miss CloudWatch"
- "AWS X-Ray API Gateway Lambda tracing"
- "X-Ray Service Map tutorial"
- "API Gateway cache invalidation"
