# Lab 14 - Fondamenti DynamoDB e Lambda

## Obiettivo

Creare una tabella DynamoDB con chiave composta, inserire dati, eseguire Query e Scan, e integrare con una funzione Lambda CRUD.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Familiarita con la console Lambda e Python (Boto3)

## Scenario

Creerai una tabella per gestire ordini con chiave composta (customer_id + order_date) e una funzione Lambda per le operazioni CRUD.

## Step

### Step 1 - Creare la tabella DynamoDB

1. Vai a **DynamoDB** -> **Create table**
2. Table name: `lab14-orders`
3. Partition key: `customer_id` (String)
4. Sort key: `order_date` (String)
5. Table settings: **Default settings** (on-demand)
6. Clicca **Create table**

### Step 2 - Inserire dati dalla console

1. Vai alla tabella `lab14-orders` -> **Explore table items**
2. Clicca **Create item** e inserisci:

| customer_id | order_date | product  | quantity | total  |
| ----------- | ---------- | -------- | -------- | ------ |
| C001        | 2025-01-15 | Laptop   | 1        | 999.99 |
| C001        | 2025-02-20 | Mouse    | 2        | 49.98  |
| C001        | 2025-03-10 | Keyboard | 1        | 79.99  |
| C002        | 2025-01-22 | Monitor  | 1        | 349.99 |
| C002        | 2025-03-05 | Webcam   | 1        | 89.99  |

3. Per ogni item, aggiungi gli attributi `product` (String), `quantity` (Number), `total` (Number)

### Step 3 - Creare la funzione Lambda CRUD

1. Vai a **Lambda** -> **Create function**
2. Function name: `orders-crud`
3. Runtime: **Python 3.12**, Role: `LabRole`
4. Aggiungi environment variable: `TABLE_NAME` = `lab14-orders`
5. Codice:

```python
import json
import os
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    action = event.get('action', '')

    try:
        if action == 'get':
            return get_order(event)
        elif action == 'query':
            return query_orders(event)
        elif action == 'create':
            return create_order(event)
        elif action == 'scan':
            return scan_orders()
        else:
            return response(400, {'error': f'Unknown action: {action}'})
    except Exception as e:
        return response(500, {'error': str(e)})

def get_order(event):
    result = table.get_item(Key={
        'customer_id': event['customer_id'],
        'order_date': event['order_date']
    })
    item = result.get('Item')
    if not item:
        return response(404, {'error': 'Order not found'})
    return response(200, item)

def query_orders(event):
    customer_id = event['customer_id']
    prefix = event.get('date_prefix', '')

    if prefix:
        result = table.query(
            KeyConditionExpression=Key('customer_id').eq(customer_id) &
                                   Key('order_date').begins_with(prefix)
        )
    else:
        result = table.query(
            KeyConditionExpression=Key('customer_id').eq(customer_id)
        )
    return response(200, {'orders': result['Items'], 'count': result['Count']})

def create_order(event):
    item = event['item']
    table.put_item(Item=item)
    return response(201, {'message': 'Order created', 'item': item})

def scan_orders():
    result = table.scan(Limit=50)
    return response(200, {'orders': result['Items'], 'count': result['Count']})

def response(status_code, body):
    return {
        'statusCode': status_code,
        'body': json.dumps(body, default=str)
    }
```

6. Clicca **Deploy**

### Step 4 - Testare le operazioni

1. **GetItem** - Crea test event:

```json
{
  "action": "get",
  "customer_id": "C001",
  "order_date": "2025-01-15"
}
```

Risultato atteso: dati del Laptop

2. **Query** - Ordini C001 di gennaio 2025:

```json
{
  "action": "query",
  "customer_id": "C001",
  "date_prefix": "2025-01"
}
```

Risultato atteso: 1 ordine (2025-01-15)

3. **Query** - Tutti gli ordini di C001:

```json
{
  "action": "query",
  "customer_id": "C001"
}
```

Risultato atteso: 3 ordini

4. **Scan** - Tutti gli ordini:

```json
{
  "action": "scan"
}
```

Risultato atteso: 5 ordini

### Step 5 - Creare un nuovo ordine

```json
{
  "action": "create",
  "item": {
    "customer_id": "C003",
    "order_date": "2025-04-01",
    "product": "Headphones",
    "quantity": 1,
    "total": 59.99
  }
}
```

Verifica nella console DynamoDB che l'item sia stato creato.

## Output atteso

- Tabella con chiave composta funzionante
- Query per customer_id con filtro date funzionante
- Lambda CRUD completa con get, query, create, scan

## Checkpoint

- [ ] GetItem restituisce un singolo ordine con tutti gli attributi
- [ ] Query per customer_id restituisce solo gli ordini del cliente specificato
- [ ] Query con date_prefix filtra correttamente per mese
- [ ] Scan restituisce tutti gli ordini (max 50)
- [ ] Create aggiunge un nuovo ordine visibile nella console

## Troubleshooting rapido

| Problema                                                          | Soluzione                                                                       |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| "ValidationException: The provided key does not match the schema" | Verifica di includere ENTRAMBE le chiavi (customer_id E order_date) nel GetItem |
| "Decimal is not JSON serializable"                                | Usa `default=str` in json.dumps (gia incluso nel codice)                        |
| Query restituisce 0 risultati                                     | Verifica che il customer_id sia esattamente uguale (case-sensitive)             |
| Environment variable non trovata                                  | Verifica `TABLE_NAME` nella configurazione Lambda                               |

## Cleanup obbligatorio

1. **DynamoDB:** elimina la tabella `lab14-orders`
2. **Lambda:** elimina la funzione `orders-crud`
3. **CloudWatch Logs:** elimina il log group `/aws/lambda/orders-crud`

## Parole chiave Google (screenshot/guide)

- "DynamoDB create table console tutorial"
- "DynamoDB composite key query"
- "Boto3 DynamoDB query KeyConditionExpression"
- "Lambda DynamoDB CRUD Python tutorial"
- "DynamoDB on-demand vs provisioned capacity"
