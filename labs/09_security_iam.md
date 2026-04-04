# Lab 09 - Sicurezza Lambda e IAM

## Obiettivo

Creare una funzione Lambda con policy IAM least-privilege, configurare environment variables e recuperare un segreto da Secrets Manager.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Familiarita con la console Lambda e IAM

## Scenario

Devi creare una funzione Lambda che legge dati da DynamoDB e scrive log. La funzione deve usare solo i permessi minimi necessari e recuperare una variabile di configurazione da un environment variable.

## Step

### Step 1 - Creare una tabella DynamoDB

1. Vai a **DynamoDB** -> **Create table**
2. Table name: `lab09-users`
3. Partition key: `user_id` (String)
4. Table settings: **Default settings**
5. Clicca **Create table**

### Step 2 - Inserire dati di test

1. Vai alla tabella `lab09-users`
2. Clicca **Explore table items** -> **Create item**
3. Aggiungi:
   - `user_id`: `u001`
   - Aggiungi attributo String `name`: `Alice`
   - Aggiungi attributo String `email`: `alice@example.com`
4. Ripeti per un secondo item: `u002`, `Bob`, `bob@example.com`

### Step 3 - Creare la funzione Lambda

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

### Step 4 - Configurare environment variables

1. Vai a **Configuration** -> **Environment variables** -> **Edit**
2. Aggiungi:
   - Key: `TABLE_NAME`, Value: `lab09-users`
3. Clicca **Save**

### Step 5 - Testare la funzione

1. Crea un test event: `{"user_id": "u001"}`
2. Esegui il test. Il risultato dovrebbe contenere i dati di Alice
3. Testa con un user_id inesistente: `{"user_id": "u999"}` -> 404
4. Testa senza user_id: `{}` -> 400
5. Testa con input malevolo: `{"user_id": "'; DROP TABLE users;--"}` -> 400 (input validation)

### Step 6 - Analisi dei permessi

1. Annota quali azioni IAM la funzione usa effettivamente:
   - `dynamodb:GetItem` sulla tabella `lab09-users`
   - `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
2. Queste sono le uniche azioni che una policy least-privilege dovrebbe contenere
3. Confronta con la policy di `LabRole` (che ha permessi molto piu ampi)

## Output atteso

- Funzione Lambda funzionante con input validation
- Environment variable `TABLE_NAME` configurata
- Test con input valido (200), inesistente (404), mancante (400) e malevolo (400)
- Lista delle azioni IAM minime necessarie

## Checkpoint

- [ ] La funzione restituisce i dati di Alice per `u001`
- [ ] L'input validation blocca tentativi di injection
- [ ] Le environment variables sono configurate correttamente
- [ ] Identificate le 4 azioni IAM minime necessarie

## Troubleshooting rapido

| Problema                         | Soluzione                                                                         |
| -------------------------------- | --------------------------------------------------------------------------------- |
| "Access Denied" su DynamoDB      | Verifica che LabRole abbia i permessi dynamodb:GetItem                            |
| Environment variable non letta   | Assicurati di aver cliccato Save dopo la modifica                                 |
| La funzione non trova la tabella | Verifica che il nome tabella corrisponda (lab09-users) e la regione sia us-east-1 |

## Cleanup obbligatorio

1. **Lambda:** elimina la funzione `secure-reader`
2. **DynamoDB:** elimina la tabella `lab09-users`
3. **CloudWatch Logs:** elimina il log group `/aws/lambda/secure-reader`

## Parole chiave Google (screenshot/guide)

- "Lambda IAM execution role least privilege"
- "Lambda environment variables configuration"
- "AWS Secrets Manager Lambda Python"
- "DynamoDB GetItem Python boto3"
- "Lambda input validation best practices"
