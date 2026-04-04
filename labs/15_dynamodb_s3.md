# Lab 15 - DynamoDB Streams, S3 e Integrazione

## Obiettivo

Creare un pipeline S3 -> Lambda -> DynamoDB che salva automaticamente i metadati dei file caricati su S3.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Completato il lab 14 (DynamoDB + Lambda CRUD)

## Scenario

Ogni volta che un file viene caricato in un bucket S3, una funzione Lambda estrae i metadati (nome, dimensione, tipo) e li salva in una tabella DynamoDB.

## Step

### Step 1 - Creare la tabella DynamoDB per i metadati

1. Vai a **DynamoDB** -> **Create table**
2. Table name: `lab15-file-metadata`
3. Partition key: `file_key` (String)
4. Impostazioni default -> **Create table**

### Step 2 - Creare il bucket S3

1. Vai a **S3** -> **Create bucket**
2. Nome: `lab15-uploads-TUONOME` (unico globalmente)
3. Region: **us-east-1**
4. Impostazioni default -> **Create bucket**

### Step 3 - Creare la funzione Lambda

1. Vai a **Lambda** -> **Create function**
2. Function name: `process-upload-metadata`
3. Runtime: **Python 3.12**, Role: `LabRole`
4. Environment variable: `TABLE_NAME` = `lab15-file-metadata`
5. Codice:

```python
import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])
s3 = boto3.client('s3')

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        size = record['s3']['object']['size']
        event_time = record['eventTime']

        # Get additional metadata from S3
        head = s3.head_object(Bucket=bucket, Key=key)
        content_type = head.get('ContentType', 'unknown')

        # Store metadata in DynamoDB
        item = {
            'file_key': key,
            'bucket': bucket,
            'size_bytes': size,
            'content_type': content_type,
            'uploaded_at': event_time,
            'processed_at': datetime.utcnow().isoformat()
        }

        table.put_item(Item=item)
        print(f"Saved metadata for: {key} ({size} bytes, {content_type})")

    return {
        'statusCode': 200,
        'body': f'Processed {len(event["Records"])} files'
    }
```

6. Clicca **Deploy**

### Step 4 - Configurare il trigger S3

1. Torna al bucket S3 `lab15-uploads-TUONOME`
2. **Properties** -> **Event notifications** -> **Create event notification**
3. Name: `upload-metadata-trigger`
4. Events: **All object create events**
5. Destination: **Lambda function** -> `process-upload-metadata`
6. Salva

### Step 5 - Testare il pipeline

1. Vai al bucket S3
2. Carica 3 file diversi (es. un .txt, un .json, un .csv)
3. Aspetta 5-10 secondi
4. Vai alla tabella DynamoDB `lab15-file-metadata`
5. Clicca **Explore table items**
6. Verifica che i 3 item siano presenti con tutti i metadati

### Step 6 - Verificare i log

1. Vai a **CloudWatch** -> **Log groups** -> `/aws/lambda/process-upload-metadata`
2. Verifica i messaggi "Saved metadata for: ..."
3. Nota la dimensione e il content type di ogni file

## Output atteso

- 3 file caricati su S3
- 3 item nella tabella DynamoDB con metadati (file_key, bucket, size_bytes, content_type, uploaded_at, processed_at)
- Log in CloudWatch che confermano il processing

## Checkpoint

- [ ] Ogni file caricato genera automaticamente un item in DynamoDB
- [ ] I metadati includono file_key, size_bytes e content_type corretti
- [ ] I log CloudWatch mostrano i dettagli di ogni file processato
- [ ] Il pipeline S3 -> Lambda -> DynamoDB funziona end-to-end

## Troubleshooting rapido

| Problema                       | Soluzione                                                           |
| ------------------------------ | ------------------------------------------------------------------- |
| Lambda non si attiva           | Verifica l'event notification S3 e che punti alla funzione corretta |
| "Access Denied" su head_object | LabRole deve avere permessi s3:GetObject e s3:HeadObject            |
| DynamoDB item non creato       | Controlla i log CloudWatch per errori nella scrittura               |
| Decimal serialization error    | Usa `default=str` in json.dumps (non necessario per put_item)       |

## Cleanup obbligatorio

1. **S3:** svuota il bucket (seleziona tutti gli oggetti -> Delete), poi elimina il bucket
2. **DynamoDB:** elimina la tabella `lab15-file-metadata`
3. **Lambda:** elimina `process-upload-metadata`
4. **CloudWatch Logs:** elimina il log group

## Parole chiave Google (screenshot/guide)

- "S3 Lambda trigger DynamoDB tutorial"
- "S3 event notification Lambda Python"
- "DynamoDB put_item Boto3 tutorial"
- "S3 head_object content type"
- "Serverless file processing pipeline AWS"
