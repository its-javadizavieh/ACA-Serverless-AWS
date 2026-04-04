# Lab 05 - Limitazioni Serverless e Best Practice

## Obiettivo

Analizzare una Lambda function mal progettata, identificare le violazioni delle best practice e proporre miglioramenti concreti.

## Durata (timebox)

30 minuti

## Prerequisiti

- Conoscenza base di Python (o Node.js)
- Nessun account AWS richiesto

## Scenario

Un collega ha scritto una Lambda function per elaborare ordini e-commerce. Il codice funziona ma viola diverse best practice. Devi fare una code review e proporre miglioramenti.

## Step

### Step 1 - Analizza il codice

Ecco il codice della funzione (Python):

```python
import boto3
import json
import os
import pandas  # unused
import numpy   # unused

DB_PASSWORD = "SuperSecret123!"  # hardcoded credential

def lambda_handler(event, context):
    # Initialize DynamoDB client inside handler
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('orders')

    # No input validation
    order_id = event['body']['order_id']
    amount = event['body']['amount']

    # Write to DynamoDB
    table.put_item(Item={
        'order_id': order_id,
        'amount': amount,
        'db_password': DB_PASSWORD  # storing password in DB!
    })

    # Connect to RDS with hardcoded password
    import pymysql
    conn = pymysql.connect(
        host='mydb.cluster-xxx.us-east-1.rds.amazonaws.com',
        user='admin',
        password=DB_PASSWORD,
        database='orders'
    )

    # No error handling
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO orders VALUES ('{order_id}', {amount})")
    conn.commit()
    conn.close()

    return {'statusCode': 200, 'body': 'OK'}
```

### Step 2 - Identifica i problemi

1. Crea una tabella con le colonne: Problema | Categoria | Livello di rischio (Alto/Medio/Basso)
2. Identifica almeno 8 problemi nel codice
3. Categorie suggerite: Sicurezza, Performance, Design, Manutenibilita

### Step 3 - Proponi le soluzioni

Per ogni problema identificato, scrivi la soluzione corretta:

1. Come eliminare le credenziali hardcoded?
2. Come inizializzare il client DynamoDB in modo efficiente?
3. Come validare gli input?
4. Come gestire gli errori?
5. Come ridurre la dimensione del pacchetto?
6. Come evitare SQL injection?

### Step 4 - Crea la checklist

Scrivi una checklist di 10 best practice serverless che userai come riferimento nel resto del corso:

1. [ ] Mai credenziali nel codice
2. [ ] Inizializzare client SDK fuori dall'handler
3. [ ] Validare tutti gli input
4. [ ] ...continua fino a 10

## Output atteso

- Tabella con almeno 8 problemi identificati, categorizzati e con livello di rischio
- Soluzione proposta per ciascun problema
- Checklist di 10 best practice serverless

## Checkpoint

- [ ] Identificati almeno: credenziali hardcoded, dipendenze inutili, client nel handler, nessuna validazione input, SQL injection, nessun error handling, password scritta in DynamoDB, nessun logging
- [ ] Soluzioni corrette: Secrets Manager, init fuori handler, parametrized queries, try/except, rimuovere pandas/numpy
- [ ] Checklist completa con 10 punti

## Troubleshooting rapido

| Problema                         | Soluzione                                                                                        |
| -------------------------------- | ------------------------------------------------------------------------------------------------ |
| Non conosco Secrets Manager      | E un servizio AWS per gestire credenziali in modo sicuro. Cerca "AWS Secrets Manager tutorial"   |
| Non so cosa sia SQL injection    | E un attacco che sfrutta input non validati nelle query SQL. Usa query parametrizzate            |
| Non capisco "init fuori handler" | Sposta `dynamodb = boto3.resource('dynamodb')` PRIMA della funzione handler, a livello di modulo |

## Cleanup obbligatorio

Nessuna risorsa AWS da eliminare. Lab basato su code review.

## Parole chiave Google (screenshot/guide)

- "AWS Lambda best practices Python"
- "AWS Secrets Manager Lambda integration"
- "SQL injection prevention Python"
- "Lambda handler best practices cold start"
- "boto3 client initialization Lambda"
