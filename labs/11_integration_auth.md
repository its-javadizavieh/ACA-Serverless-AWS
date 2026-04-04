# Lab 11 - Integrazione Avanzata e Autenticazione

## Obiettivo

Costruire un'API CRUD multi-risorsa con API Gateway e Lambda, implementare un Lambda authorizer per proteggere l'API.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Completato il lab 10 (familiarita con API Gateway e Lambda proxy)

## Scenario

Creerai un'API completa per gestire utenti (CRUD) con una tabella DynamoDB e proteggerai l'API con un Lambda authorizer che valida un token.

## Step

### Step 1 - Creare la tabella DynamoDB

1. Vai a **DynamoDB** -> **Create table**
2. Table name: `lab11-users`
3. Partition key: `user_id` (String)
4. Impostazioni default -> **Create table**

### Step 2 - Creare la funzione CRUD

1. Vai a **Lambda** -> **Create function**
2. Function name: `crud-users`
3. Runtime: **Python 3.12**, Role: `LabRole`
4. Codice:

```python
import json
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('lab11-users')

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*'
}

def lambda_handler(event, context):
    method = event['httpMethod']
    path_params = event.get('pathParameters') or {}

    try:
        if method == 'GET' and 'id' in path_params:
            return get_user(path_params['id'])
        elif method == 'GET':
            return list_users()
        elif method == 'POST':
            body = json.loads(event.get('body', '{}'))
            return create_user(body)
        elif method == 'DELETE' and 'id' in path_params:
            return delete_user(path_params['id'])
        else:
            return response(405, {'error': 'Method not allowed'})
    except Exception as e:
        return response(500, {'error': str(e)})

def get_user(user_id):
    result = table.get_item(Key={'user_id': user_id})
    item = result.get('Item')
    if not item:
        return response(404, {'error': 'User not found'})
    return response(200, item)

def list_users():
    result = table.scan(Limit=50)
    return response(200, {'users': result.get('Items', [])})

def create_user(body):
    if 'name' not in body:
        return response(400, {'error': 'name is required'})
    item = {
        'user_id': str(uuid.uuid4())[:8],
        'name': body['name'],
        'email': body.get('email', '')
    }
    table.put_item(Item=item)
    return response(201, item)

def delete_user(user_id):
    table.delete_item(Key={'user_id': user_id})
    return response(200, {'message': f'User {user_id} deleted'})

def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body)
    }
```

5. Clicca **Deploy**

### Step 3 - Creare il Lambda authorizer

1. Vai a **Lambda** -> **Create function**
2. Function name: `simple-authorizer`
3. Runtime: **Python 3.12**, Role: `LabRole`
4. Codice:

```python
def lambda_handler(event, context):
    token = event.get('authorizationToken', '')
    method_arn = event.get('methodArn', '')

    if token == 'Bearer my-secret-token-2025':
        effect = 'Allow'
    else:
        effect = 'Deny'

    return {
        'principalId': 'user',
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': method_arn
            }]
        }
    }
```

5. Clicca **Deploy**

### Step 4 - Creare l'API Gateway

1. Vai a **API Gateway** -> **Create API** -> **REST API** -> **Build**
2. API name: `crud-api`
3. Crea la risorsa `/users`
4. Crea la risorsa figlio `/users/{id}`
5. Su `/users`: crea metodi **GET** e **POST** con Lambda proxy -> `crud-users`
6. Su `/users/{id}`: crea metodi **GET** e **DELETE** con Lambda proxy -> `crud-users`

### Step 5 - Configurare l'authorizer

1. Nel menu laterale, clicca **Authorizers**
2. Clicca **Create New Authorizer**
3. Name: `token-auth`
4. Type: **Lambda**
5. Lambda function: `simple-authorizer`
6. Token source: `Authorization`
7. Clicca **Create** (conferma il permesso)
8. (Opzionale) Assegna l'authorizer ai metodi POST e DELETE

### Step 6 - Deploy e test

1. Clicca **Deploy API** -> Stage: `dev`
2. Usa l'invoke URL per testare:
   - `GET /dev/users` -> lista vuota
   - `POST /dev/users` con body `{"name": "Alice"}` e header `Authorization: Bearer my-secret-token-2025`
   - `GET /dev/users` -> lista con Alice

## Output atteso

- API CRUD funzionante con GET, POST, DELETE
- Lambda authorizer che valida il token
- Richieste senza token rifiutate (403)

## Checkpoint

- [ ] GET /users restituisce la lista (vuota o con utenti)
- [ ] POST /users crea un nuovo utente
- [ ] GET /users/{id} restituisce un utente specifico
- [ ] DELETE /users/{id} elimina un utente
- [ ] Il Lambda authorizer blocca le richieste senza token valido

## Troubleshooting rapido

| Problema                         | Soluzione                                                                       |
| -------------------------------- | ------------------------------------------------------------------------------- |
| 502 Bad Gateway                  | Verifica il formato di risposta Lambda (statusCode + body obbligatori)          |
| 403 Forbidden (senza authorizer) | Rideploya l'API dopo ogni modifica                                              |
| 401/403 con authorizer           | Verifica che il token nell'header sia esattamente `Bearer my-secret-token-2025` |
| DynamoDB Access Denied           | Verifica che LabRole abbia permessi DynamoDB                                    |

## Cleanup obbligatorio

1. **API Gateway:** elimina `crud-api`
2. **Lambda:** elimina `crud-users` e `simple-authorizer`
3. **DynamoDB:** elimina la tabella `lab11-users`
4. **CloudWatch Logs:** elimina i log group di entrambe le funzioni Lambda

## Parole chiave Google (screenshot/guide)

- "API Gateway CRUD Lambda DynamoDB tutorial"
- "Lambda authorizer API Gateway Python"
- "API Gateway path parameters Lambda proxy"
- "REST API multi-resource tutorial"
- "API Gateway authorizer token validation"
