# Lab 06 - Prima Funzione Lambda

## Obiettivo

Creare, testare e osservare la prima funzione Lambda nella console AWS, analizzando cold start e warm start nei log.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Browser con accesso alla console AWS

## Scenario

Crei la tua prima funzione Lambda "hello-serverless" che riceve un nome e restituisce un saluto. Osserverai la differenza tra cold start e warm start.

## Step

### Step 1 - Creare la funzione

1. Accedi alla console AWS tramite Learner Lab
2. Vai al servizio **Lambda**
3. Clicca **Create function**
4. Seleziona **Author from scratch**
5. Configurazione:
   - Function name: `hello-serverless`
   - Runtime: **Python 3.12**
   - Execution role: **Use an existing role** -> seleziona `LabRole`
6. Clicca **Create function**

### Step 2 - Scrivere il codice

1. Nell'editor inline, sostituisci il codice con:

```python
import json
import time

def lambda_handler(event, context):
    start = time.time()
    name = event.get('name', 'World')

    response = {
        'message': f'Hello, {name}!',
        'function_name': context.function_name,
        'memory_limit_mb': context.memory_limit_in_mb,
        'remaining_time_ms': context.get_remaining_time_in_millis(),
        'execution_time_ms': round((time.time() - start) * 1000, 2)
    }

    print(f"Processed request for: {name}")
    print(f"Response: {json.dumps(response)}")

    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
```

2. Clicca **Deploy**

### Step 3 - Testare la funzione

1. Clicca la tab **Test**
2. Crea un nuovo test event:
   - Event name: `test-student`
   - JSON body:
     ```json
     {
       "name": "Mario"
     }
     ```
3. Clicca **Test**
4. Osserva il risultato:
   - **Execution result:** il JSON di risposta
   - **Duration:** tempo di esecuzione
   - **Billed Duration:** arrotondato al millisecondo
   - **Init Duration:** presente SOLO al primo invoke (cold start!)

### Step 4 - Osservare cold start vs warm start

1. Clicca **Test** di nuovo immediatamente (entro 30 secondi)
2. Nota: **Init Duration** non appare piu (warm start!)
3. Aspetta 15 minuti e ripeti. Init Duration riappare (cold start)
4. Vai a **CloudWatch Logs** -> Log groups -> `/aws/lambda/hello-serverless`
5. Apri il log stream piu recente
6. Identifica le righe con `REPORT` e confronta `Init Duration` vs invocazioni senza

### Step 5 - Sperimentare con la memoria

1. Torna alla funzione Lambda
2. Vai a **Configuration** -> **General configuration** -> **Edit**
3. Cambia la memoria a **256 MB** (da 128 MB default)
4. Salva e testa di nuovo
5. Confronta la durata. Con piu memoria, la funzione potrebbe essere piu veloce

## Output atteso

- Funzione `hello-serverless` funzionante
- Screenshot o nota del risultato con `Init Duration` (cold start) e senza (warm start)
- Confronto durata con 128 MB vs 256 MB

## Checkpoint

- [ ] La funzione risponde con il messaggio "Hello, Mario!"
- [ ] Identificata la differenza tra cold start e warm start nei log
- [ ] Testata la funzione con 2 diverse configurazioni di memoria

## Troubleshooting rapido

| Problema                       | Soluzione                                                                |
| ------------------------------ | ------------------------------------------------------------------------ |
| "Access Denied" alla creazione | Verificare di aver selezionato il ruolo `LabRole`                        |
| Non vedo Init Duration         | Aspetta qualche minuto e ritesta (il container potrebbe essere gia warm) |
| CloudWatch Logs vuoto          | I log appaiono dopo qualche secondo. Aggiorna la pagina                  |
| La funzione non si deploya     | Verifica che il codice non abbia errori di sintassi Python               |

## Cleanup obbligatorio

1. Vai a **Lambda** -> funzioni
2. Seleziona `hello-serverless`
3. Clicca **Actions** -> **Delete**
4. Conferma la cancellazione
5. Vai a **CloudWatch** -> **Log groups**
6. Elimina il log group `/aws/lambda/hello-serverless`

## Parole chiave Google (screenshot/guide)

- "AWS Lambda create function console tutorial"
- "Lambda cold start vs warm start"
- "AWS Lambda Python handler tutorial"
- "CloudWatch Logs Lambda"
- "Lambda memory configuration best practice"
