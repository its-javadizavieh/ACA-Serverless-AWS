# Lab 08-09 - Risorse Lambda, Monitoraggio e Sicurezza IAM

## Obiettivo

**Parte A:** Configurare memoria, timeout e concurrency di una funzione Lambda, creare un allarme CloudWatch e utilizzare Logs Insights per analizzare i log.

**Parte B:** Creare una funzione Lambda con policy IAM least-privilege, configurare environment variables e recuperare un segreto da Secrets Manager.

## Durata (timebox)

60 minuti (30 + 30)

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Familiarita con la console Lambda e IAM

---

# Parte A - Risorse Lambda e Monitoraggio

## Scenario

Creerai una funzione Lambda che simula un carico di lavoro variabile, configurerai le risorse e imposterai il monitoraggio.

## Step

### Step 1 - Creare la funzione

1. Vai a **Lambda** -> **Create function**
2. Function name: `resource-test`
3. Runtime: **Python 3.12**, Role: `LabRole`
4. Codice:

```python
import json
import time
import math

def lambda_handler(event, context):
    # Simulate CPU work
    iterations = event.get('iterations', 100000)
    start = time.time()
    result = sum(math.sqrt(i) for i in range(iterations))
    duration = round((time.time() - start) * 1000, 2)

    memory_used = context.memory_limit_in_mb
    remaining = context.get_remaining_time_in_millis()

    print(json.dumps({
        'iterations': iterations,
        'duration_ms': duration,
        'memory_mb': memory_used,
        'remaining_ms': remaining
    }))

    return {
        'statusCode': 200,
        'body': json.dumps({
            'duration_ms': duration,
            'memory_mb': memory_used,
            'result': result
        })
    }
```

5. Clicca **Deploy**

### Step 2 - Test con diverse configurazioni di memoria

1. Crea un test event con `{"iterations": 1000000}`
2. Testa con **128 MB** - annota la Duration dal REPORT
3. Vai a Configuration -> General configuration -> Edit -> cambia a **256 MB** -> Save
4. Testa di nuovo - annota la Duration
5. Ripeti con **512 MB** e **1024 MB**
6. Compila la tabella:

| Memoria | Durata (ms) | Costo stimato (MB-s) |
| ------- | ----------- | -------------------- |
| 128 MB  | ???         | = 128 x durata_s     |
| 256 MB  | ???         | = 256 x durata_s     |
| 512 MB  | ???         | = 512 x durata_s     |
| 1024 MB | ???         | = 1024 x durata_s    |

### Step 3 - Configurare Reserved Concurrency

1. Vai a Configuration -> **Concurrency**
2. Clicca **Edit**
3. Seleziona **Reserve concurrency** e imposta a **5**
4. Salva
5. Questo significa che al massimo 5 istanze della funzione possono essere in esecuzione contemporaneamente

### Step 4 - Creare un allarme CloudWatch

1. Vai a **CloudWatch** -> **Alarms** -> **Create alarm**
2. Clicca **Select metric** -> Lambda -> By Function Name
3. Seleziona **Errors** per la funzione `resource-test`
4. Condizione: **Greater than 0** per **1 valuation period** (1 minuto)
5. Notification: seleziona "In alarm" ma non configurare un SNS topic (per il lab)
6. Nome allarme: `resource-test-errors`
7. Clicca **Create alarm**

### Step 5 - Query con Logs Insights

1. Vai a **CloudWatch** -> **Logs** -> **Logs Insights**
2. Seleziona il log group `/aws/lambda/resource-test`
3. Esegui questa query:

```
filter @type = "REPORT"
| stats avg(@duration) as avgDuration, max(@duration) as maxDuration, min(@memorySize) as memorySize
| sort avgDuration desc
```

4. Osserva la durata media e massima delle invocazioni

## Checkpoint Parte A

- [ ] La durata diminuisce con l'aumento della memoria (CPU scaling)
- [ ] Il costo (MB-s) ha un punto ottimale (spesso intorno a 256-512 MB per questo tipo di task)
- [ ] L'allarme CloudWatch e in stato "OK" (nessun errore)
- [ ] La query Logs Insights restituisce i dati aggregati

---

# Parte B - Sicurezza Lambda e IAM

## Scenario

Devi creare una funzione Lambda che legge dati da DynamoDB e scrive log. La funzione deve usare solo i permessi minimi necessari e recuperare una variabile di configurazione da un environment variable.

## Step

### Step 6 - Creare una tabella DynamoDB

1. Vai a **DynamoDB** -> **Create table**
2. Table name: `lab09-users`
3. Partition key: `user_id` (String)
4. Table settings: **Default settings**
5. Clicca **Create table**

### Step 7 - Inserire dati di test

1. Vai alla tabella `lab09-users`
2. Clicca **Explore table items** -> **Create item**
3. Aggiungi:
   - `user_id`: `u001`
   - Aggiungi attributo String `name`: `Alice`
   - Aggiungi attributo String `email`: `alice@example.com`
4. Ripeti per un secondo item: `u002`, `Bob`, `bob@example.com`

### Step 8 - Creare la funzione Lambda

1. Vai a **Lambda** -> **Create function**
2. Function name: `secure-reader`
3. Runtime: **Python 3.12**, Role: `LabRole`
4. Codice:

```python
import json
import os
import boto3

TABLE_NAME = os.environ.get('TABLE_NAME', 'lab09-users')
REGION = os.environ.get('AWS_REGION', 'us-east-1')

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    user_id = event.get('user_id')

    if not user_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'user_id is required'})
        }

    # Input validation: only allow alphanumeric + hyphens
    if not all(c.isalnum() or c == '-' for c in user_id):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid user_id format'})
        }

    try:
        response = table.get_item(Key={'user_id': user_id})
        item = response.get('Item')

        if not item:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'User not found'})
            }

        print(json.dumps({
            'action': 'get_user',
            'user_id': user_id,
            'status': 'success'
        }))

        return {
            'statusCode': 200,
            'body': json.dumps(item)
        }
    except Exception as e:
        print(json.dumps({
            'action': 'get_user',
            'user_id': user_id,
            'status': 'error',
            'error': str(e)
        }))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
```

5. Clicca **Deploy**

### Step 9 - Configurare environment variables

1. Vai a **Configuration** -> **Environment variables** -> **Edit**
2. Aggiungi:
   - Key: `TABLE_NAME`, Value: `lab09-users`
3. Clicca **Save**

### Step 10 - Testare la funzione

1. Crea un test event: `{"user_id": "u001"}`
2. Esegui il test. Il risultato dovrebbe contenere i dati di Alice
3. Testa con un user_id inesistente: `{"user_id": "u999"}` -> 404
4. Testa senza user_id: `{}` -> 400
5. Testa con input malevolo: `{"user_id": "'; DROP TABLE users;--"}` -> 400 (input validation)

### Step 11 - Analisi dei permessi

1. Annota quali azioni IAM la funzione usa effettivamente:
   - `dynamodb:GetItem` sulla tabella `lab09-users`
   - `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
2. Queste sono le uniche azioni che una policy least-privilege dovrebbe contenere
3. Confronta con la policy di `LabRole` (che ha permessi molto piu ampi)

## Checkpoint Parte B

- [ ] La funzione restituisce i dati di Alice per `u001`
- [ ] L'input validation blocca tentativi di injection
- [ ] Le environment variables sono configurate correttamente
- [ ] Identificate le 4 azioni IAM minime necessarie

---

## Output atteso

**Parte A:**
- Tabella con durata e costo per 4 configurazioni di memoria
- Reserved concurrency impostata a 5
- Allarme CloudWatch creato per errori Lambda
- Screenshot della query Logs Insights con risultati

**Parte B:**
- Funzione Lambda funzionante con input validation
- Environment variable `TABLE_NAME` configurata
- Test con input valido (200), inesistente (404), mancante (400) e malevolo (400)
- Lista delle azioni IAM minime necessarie

## Troubleshooting rapido

| Problema                            | Soluzione                                                                               |
| ----------------------------------- | --------------------------------------------------------------------------------------- |
| La durata non cambia con la memoria | Il carico potrebbe essere I/O-bound. Aumenta `iterations` per un carico CPU-bound       |
| Non posso creare l'allarme          | Verifica di avere i permessi CloudWatch. Usa LabRole                                    |
| Logs Insights non mostra risultati  | Assicurati di aver selezionato il log group corretto e un intervallo temporale adeguato |
| "Access Denied" su DynamoDB         | Verifica che LabRole abbia i permessi dynamodb:GetItem                                  |
| Environment variable non letta      | Assicurati di aver cliccato Save dopo la modifica                                       |
| La funzione non trova la tabella    | Verifica che il nome tabella corrisponda (lab09-users) e la regione sia us-east-1       |

## Cleanup obbligatorio

1. **Lambda:** elimina le funzioni `resource-test` e `secure-reader`
2. **DynamoDB:** elimina la tabella `lab09-users`
3. **CloudWatch Alarms:** elimina l'allarme `resource-test-errors`
4. **CloudWatch Logs:** elimina i log group `/aws/lambda/resource-test` e `/aws/lambda/secure-reader`

## Parole chiave Google (screenshot/guide)

- "AWS Lambda memory CPU relationship"
- "Lambda reserved concurrency tutorial"
- "CloudWatch alarm Lambda errors"
- "CloudWatch Logs Insights query examples"
- "Lambda Power Tuning open source"
- "Lambda IAM execution role least privilege"
- "Lambda environment variables configuration"
- "AWS Secrets Manager Lambda Python"
- "DynamoDB GetItem Python boto3"
- "Lambda input validation best practices"
