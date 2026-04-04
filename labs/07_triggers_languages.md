# Lab 07 - Trigger Lambda e Linguaggi

## Obiettivo

Configurare Lambda con trigger S3 (asincrono) e trigger EventBridge schedulato, osservando i diversi modelli di invocazione.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Familiarita con la console Lambda (lab precedente)

## Scenario

Creerai due funzioni Lambda con trigger diversi: una attivata dal caricamento di un file su S3, l'altra eseguita su una schedulazione temporale.

## Step

### Step 1 - Creare un bucket S3

1. Vai al servizio **S3**
2. Clicca **Create bucket**
3. Nome: `lab07-trigger-TUONOME` (sostituisci TUONOME con il tuo nome, i nomi S3 devono essere unici)
4. Region: **us-east-1**
5. Lascia le altre impostazioni di default
6. Clicca **Create bucket**

### Step 2 - Creare la funzione Lambda per S3

1. Vai a **Lambda** -> **Create function**
2. Function name: `process-s3-upload`
3. Runtime: **Python 3.12**
4. Execution role: `LabRole`
5. Codice:

```python
import json

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        size = record['s3']['object']['size']
        print(f"File uploaded: s3://{bucket}/{key} (size: {size} bytes)")

    return {'statusCode': 200, 'body': f'Processed {len(event["Records"])} files'}
```

6. Clicca **Deploy**

### Step 3 - Configurare il trigger S3

1. Torna al bucket S3 `lab07-trigger-TUONOME`
2. Vai a **Properties** -> scorri fino a **Event notifications**
3. Clicca **Create event notification**
4. Nome: `upload-trigger`
5. Events: seleziona **All object create events**
6. Destination: **Lambda function** -> seleziona `process-s3-upload`
7. Salva

### Step 4 - Testare il trigger S3

1. Torna al bucket S3
2. Clicca **Upload** -> carica un file qualsiasi (es. un file .txt)
3. Vai a **CloudWatch** -> **Log groups** -> `/aws/lambda/process-s3-upload`
4. Apri il log stream piu recente
5. Verifica che il messaggio contenga il nome del file caricato

### Step 5 - Creare una funzione schedulata

1. Vai a **Lambda** -> **Create function**
2. Function name: `scheduled-task`
3. Runtime: **Python 3.12**
4. Execution role: `LabRole`
5. Codice:

```python
import json
from datetime import datetime

def lambda_handler(event, context):
    now = datetime.utcnow().isoformat()
    print(f"Scheduled execution at {now}")
    print(f"Event source: {json.dumps(event)}")
    return {'statusCode': 200, 'body': f'Executed at {now}'}
```

6. Clicca **Deploy**

### Step 6 - Configurare il trigger EventBridge

1. Nella pagina della funzione `scheduled-task`, clicca **Add trigger**
2. Seleziona **EventBridge (CloudWatch Events)**
3. Seleziona **Create a new rule**
4. Rule name: `every-5-min-rule`
5. Schedule expression: `rate(5 minutes)`
6. Clicca **Add**
7. Aspetta 5-10 minuti e controlla i log in CloudWatch

## Output atteso

- Funzione `process-s3-upload` attivata dal caricamento file su S3
- Funzione `scheduled-task` eseguita automaticamente ogni 5 minuti
- Log in CloudWatch che mostrano l'evento S3 e l'evento schedulato

## Checkpoint

- [ ] Il log di `process-s3-upload` mostra il nome del file caricato
- [ ] Il log di `scheduled-task` mostra almeno 1 esecuzione schedulata
- [ ] Identificata la differenza: S3 invia dettagli del file, EventBridge invia dettagli della regola

## Troubleshooting rapido

| Problema                         | Soluzione                                                                          |
| -------------------------------- | ---------------------------------------------------------------------------------- |
| S3 non triggera Lambda           | Verifica che l'event notification sia configurata e punti alla funzione corretta   |
| "Unable to validate destination" | LabRole deve avere i permessi per Lambda. Se l'errore persiste, ricrea la funzione |
| EventBridge non esegue           | Aspetta almeno 5 minuti, controlla che la regola sia in stato "Enabled"            |
| Non vedo i log                   | I log appaiono dopo 10-30 secondi. Aggiorna la pagina di CloudWatch                |

## Cleanup obbligatorio

1. **Lambda:** elimina le funzioni `process-s3-upload` e `scheduled-task`
2. **S3:** svuota e elimina il bucket `lab07-trigger-TUONOME`
3. **EventBridge:** vai a EventBridge -> Rules -> elimina `every-5-min-rule`
4. **CloudWatch:** elimina i log group `/aws/lambda/process-s3-upload` e `/aws/lambda/scheduled-task`

## Parole chiave Google (screenshot/guide)

- "AWS Lambda S3 trigger tutorial"
- "Lambda EventBridge schedule rule"
- "S3 event notification Lambda configuration"
- "CloudWatch Logs Lambda tutorial"
- "AWS Lambda event source types"
