# Lab 08 - Risorse Lambda e Monitoraggio

## Obiettivo

Configurare memoria, timeout e concurrency di una funzione Lambda, creare un allarme CloudWatch e utilizzare Logs Insights per analizzare i log.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Familiarita con la console Lambda

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

## Output atteso

- Tabella con durata e costo per 4 configurazioni di memoria
- Reserved concurrency impostata a 5
- Allarme CloudWatch creato per errori Lambda
- Screenshot della query Logs Insights con risultati

## Checkpoint

- [ ] La durata diminuisce con l'aumento della memoria (CPU scaling)
- [ ] Il costo (MB-s) ha un punto ottimale (spesso intorno a 256-512 MB per questo tipo di task)
- [ ] L'allarme CloudWatch e in stato "OK" (nessun errore)
- [ ] La query Logs Insights restituisce i dati aggregati

## Troubleshooting rapido

| Problema                            | Soluzione                                                                               |
| ----------------------------------- | --------------------------------------------------------------------------------------- |
| La durata non cambia con la memoria | Il carico potrebbe essere I/O-bound. Aumenta `iterations` per un carico CPU-bound       |
| Non posso creare l'allarme          | Verifica di avere i permessi CloudWatch. Usa LabRole                                    |
| Logs Insights non mostra risultati  | Assicurati di aver selezionato il log group corretto e un intervallo temporale adeguato |

## Cleanup obbligatorio

1. **Lambda:** elimina la funzione `resource-test`
2. **CloudWatch Alarms:** elimina l'allarme `resource-test-errors`
3. **CloudWatch Logs:** elimina il log group `/aws/lambda/resource-test`

## Parole chiave Google (screenshot/guide)

- "AWS Lambda memory CPU relationship"
- "Lambda reserved concurrency tutorial"
- "CloudWatch alarm Lambda errors"
- "CloudWatch Logs Insights query examples"
- "Lambda Power Tuning open source"
