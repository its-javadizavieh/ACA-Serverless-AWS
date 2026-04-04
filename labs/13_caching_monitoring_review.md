# Lab 13 - Caching, Monitoraggio Avanzato e Revisione

## Obiettivo

Abilitare il caching di API Gateway, verificare cache hit/miss con CloudWatch, abilitare X-Ray tracing e prepararsi alla verifica intermedia.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Familiarita con API Gateway, Lambda e CloudWatch (lab 10-12)

## Scenario

Hai un'API REST con un endpoint GET. Abiliterai il caching per ridurre le invocazioni Lambda e configurerai X-Ray per il tracing distribuito.

## Step

### Step 1 - Creare l'infrastruttura

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

### Step 2 - Abilitare il caching

1. Vai a **Stages** -> `dev`
2. Tab **Settings** (o **Cache Settings**)
3. Abilita **Enable API cache**
4. Cache capacity: **0.5 GB** (minimo)
5. Cache TTL: **60** secondi
6. Salva le modifiche (il provisioning del cache richiede qualche minuto)

### Step 3 - Testare cache hit vs cache miss

1. Apri l'invoke URL nel browser: `/dev/products?category=electronics`
2. Nota il `timestamp` nella risposta
3. Ricarica la pagina entro 60 secondi
4. Se il `timestamp` e identico -> **cache hit** (Lambda non invocata)
5. Aspetta 60 secondi e ricarica -> `timestamp` cambia -> **cache miss** (TTL scaduto)
6. Prova con un parametro diverso: `/dev/products?category=books` -> cache miss (chiave diversa)

### Step 4 - Verificare le metriche

1. Vai a **CloudWatch** -> **Metrics** -> **ApiGateway**
2. Cerca le metriche per `cache-test-api`:
   - **CacheHitCount**: richieste servite dalla cache
   - **CacheMissCount**: richieste inviate a Lambda
3. Confronta i conteggi con le richieste che hai fatto

### Step 5 - Abilitare X-Ray

1. Vai a **Stages** -> `dev` -> **Logs/Tracing**
2. Abilita **X-Ray Tracing**
3. Vai alla funzione Lambda `cache-demo` -> **Configuration** -> **Monitoring and operations tools**
4. Abilita **Active tracing** (X-Ray)
5. Fai alcune richieste all'API
6. Vai a **X-Ray** -> **Service Map**
7. Osserva il flusso: API Gateway -> Lambda e i tempi di risposta

## Output atteso

- Cache funzionante con timestamp identico per cache hit
- Metriche CacheHitCount e CacheMissCount in CloudWatch
- Service Map in X-Ray con flusso API Gateway -> Lambda

## Checkpoint

- [ ] Il timestamp non cambia tra richieste successive (cache hit)
- [ ] Il timestamp cambia dopo il TTL (cache miss)
- [ ] Le metriche CacheHitCount/CacheMissCount sono visibili
- [ ] X-Ray mostra il Service Map con i tempi

## Troubleshooting rapido

| Problema                       | Soluzione                                                                |
| ------------------------------ | ------------------------------------------------------------------------ |
| Il cache non sembra funzionare | Il provisioning del cache richiede 1-4 minuti. Aspetta e riprova         |
| CacheHitCount sempre 0         | Verifica di usare gli stessi query parameters nelle richieste successive |
| X-Ray Service Map vuoto        | Le tracce appaiono dopo 1-2 minuti. Genera almeno 5 richieste            |
| Errore abilitando X-Ray        | Verifica che LabRole abbia permessi xray:PutTraceSegments                |

## Cleanup obbligatorio

1. **API Gateway:** disabilita il caching prima di eliminare (per evitare costi), poi elimina `cache-test-api`
2. **Lambda:** elimina `cache-demo`
3. **CloudWatch Logs:** elimina i log group correlati
4. **X-Ray:** non richiede cleanup (le tracce scadono automaticamente dopo 30 giorni)

## Parole chiave Google (screenshot/guide)

- "API Gateway caching REST API tutorial"
- "API Gateway cache hit miss CloudWatch"
- "AWS X-Ray API Gateway Lambda tracing"
- "X-Ray Service Map tutorial"
- "API Gateway cache invalidation"
