# Lab 15-16 - DynamoDB Streams, S3, Trigger e GSI

## Obiettivo

**Parte A:** Creare un pipeline S3 -> Lambda -> DynamoDB che salva automaticamente i metadati dei file caricati su S3.

**Parte B:** Creare un pipeline S3 -> Lambda che importa dati CSV in DynamoDB con filtro prefix/suffix, e creare un GSI per query ottimizzate.

## Durata (timebox)

60 minuti (30 + 30)

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Completato il lab 14 (DynamoDB + Lambda CRUD)

---

# Parte A - DynamoDB Streams, S3 e Integrazione

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

## Checkpoint Parte A

- [ ] Ogni file caricato genera automaticamente un item in DynamoDB
- [ ] I metadati includono file_key, size_bytes e content_type corretti
- [ ] I log CloudWatch mostrano i dettagli di ogni file processato
- [ ] Il pipeline S3 -> Lambda -> DynamoDB funziona end-to-end

---

# Parte B - S3 Trigger, Import CSV e GSI

## Scenario

Un'azienda riceve file CSV con dati di prodotti. I file vengono caricati in S3 e una funzione Lambda li importa automaticamente in DynamoDB. Un GSI permette di cercare i prodotti per categoria.

## Step

### Step 7 - Creare la tabella DynamoDB con GSI

1. Vai a **DynamoDB** -> **Create table**
2. Table name: `lab16-products`
3. Partition key: `product_id` (String)
4. Clicca su **Customize settings**
5. In **Secondary indexes** -> **Create global index**
   - Partition key: `category` (String)
   - Sort key: `price` (Number)
   - Index name: `category-price-index`
   - Projection: **All**
6. Clicca **Create index**, poi **Create table**

### Step 8 - Creare il bucket S3

1. Vai a **S3** -> **Create bucket**
2. Nome: `lab16-csv-import-TUONOME`
3. Region: **us-east-1** -> **Create bucket**
4. Crea una "cartella" (prefix): clicca **Create folder** -> nome: `imports`

### Step 9 - Preparare il file CSV

Crea un file `products.csv` sul tuo computer con questo contenuto:

```csv
product_id,category,name,price,stock
P001,Electronics,Laptop,999.99,50
P002,Electronics,Mouse,29.99,200
P003,Books,Python Cookbook,45.00,100
P004,Electronics,Keyboard,79.99,150
P005,Books,AWS in Action,55.00,75
P006,Clothing,T-Shirt,19.99,300
```

### Step 10 - Creare la funzione Lambda

1. Vai a **Lambda** -> **Create function**
2. Function name: `csv-importer`
3. Runtime: **Python 3.12**, Role: `LabRole`
4. Timeout: **30 seconds** (Configuration -> General -> Edit)
5. Environment variable: `TABLE_NAME` = `lab16-products`
6. Codice:

```python
import csv
import io
import json
import os
import boto3
from decimal import Decimal

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']

    print(f"Processing: s3://{bucket}/{key}")

    obj = s3.get_object(Bucket=bucket, Key=key)
    content = obj['Body'].read().decode('utf-8')

    reader = csv.DictReader(io.StringIO(content))
    count = 0

    with table.batch_writer() as batch:
        for row in reader:
            item = {
                'product_id': row['product_id'],
                'category': row['category'],
                'name': row['name'],
                'price': Decimal(row['price']),
                'stock': int(row['stock'])
            }
            batch.put_item(Item=item)
            count += 1

    print(f"Imported {count} products")
    return {'statusCode': 200, 'body': f'Imported {count} products'}
```

7. Clicca **Deploy**

### Step 11 - Configurare il trigger con filtro

1. Vai al bucket S3 -> **Properties** -> **Event notifications**
2. **Create event notification**
3. Name: `csv-import-trigger`
4. Prefix: `imports/`
5. Suffix: `.csv`
6. Events: **All object create events**
7. Destination: **Lambda function** -> `csv-importer`
8. Salva

### Step 12 - Testare il pipeline

1. Vai al bucket S3
2. Naviga nella cartella `imports/`
3. Carica il file `products.csv`
4. Aspetta 10 secondi
5. Vai a DynamoDB -> `lab16-products` -> **Explore table items**
6. Verifica che i 6 prodotti siano stati importati

### Step 13 - Query con GSI

1. In **Explore table items**, clicca su **Query**
2. Seleziona l'indice: `category-price-index`
3. Partition key: `Electronics`
4. Esegui la query
5. Risultato: 3 prodotti (Laptop, Mouse, Keyboard) ordinati per prezzo
6. Prova con Partition key: `Books`
7. Risultato: 2 prodotti ordinati per prezzo

## Checkpoint Parte B

- [ ] Il caricamento di un CSV in `imports/` attiva la Lambda
- [ ] I 6 prodotti sono presenti nella tabella DynamoDB
- [ ] La query sul GSI `category-price-index` restituisce prodotti per categoria
- [ ] Un file caricato fuori da `imports/` NON attiva la Lambda

---

## Output atteso

**Parte A:**

- 3 file caricati su S3
- 3 item nella tabella DynamoDB con metadati (file_key, bucket, size_bytes, content_type, uploaded_at, processed_at)
- Log in CloudWatch che confermano il processing

**Parte B:**

- CSV importato automaticamente: 6 prodotti in DynamoDB
- Il trigger si attiva solo per file `.csv` nella cartella `imports/`
- Query GSI per categoria restituisce prodotti ordinati per prezzo

## Troubleshooting rapido

| Problema                       | Soluzione                                                           |
| ------------------------------ | ------------------------------------------------------------------- |
| Lambda non si attiva           | Verifica l'event notification S3 e che punti alla funzione corretta |
| "Access Denied" su head_object | LabRole deve avere permessi s3:GetObject e s3:HeadObject            |
| DynamoDB item non creato       | Controlla i log CloudWatch per errori nella scrittura               |
| Decimal serialization error    | Usa `default=str` in json.dumps (non necessario per put_item)       |
| Errore prefix/suffix           | Verifica prefix (`imports/`) e suffix (`.csv`) nel trigger S3       |
| GSI non disponibile            | L'indice potrebbe richiedere qualche minuto per diventare ACTIVE    |
| Timeout Lambda                 | Aumenta il timeout a 30 secondi per file CSV grandi                 |

## Cleanup obbligatorio

1. **S3:** svuota e elimina i bucket `lab15-uploads-TUONOME` e `lab16-csv-import-TUONOME`
2. **DynamoDB:** elimina le tabelle `lab15-file-metadata` e `lab16-products` (il GSI si elimina automaticamente)
3. **Lambda:** elimina `process-upload-metadata` e `csv-importer`
4. **CloudWatch Logs:** elimina i log group correlati

## Parole chiave Google (screenshot/guide)

- "S3 Lambda trigger DynamoDB tutorial"
- "S3 event notification Lambda Python"
- "DynamoDB put_item Boto3 tutorial"
- "S3 head_object content type"
- "Serverless file processing pipeline AWS"
- "S3 event notification prefix suffix filter"
- "Lambda CSV import DynamoDB Python"
- "DynamoDB Global Secondary Index create"
- "DynamoDB GSI query Boto3"
- "S3 Lambda trigger avoid infinite loop"
