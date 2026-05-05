# Lab 10 - Introduzione ad API Gateway

## Obiettivo

Creare un REST API con API Gateway, integrare Lambda con proxy integration e testare l'endpoint con CORS configurato.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Familiarita con Lambda (lezioni 06-09)

## Scenario

Creerai un API REST con un endpoint `/hello` che invoca una funzione Lambda e restituisce un saluto personalizzato.

## Step

### Step 1 - Creare la funzione Lambda

1. Vai a **Lambda** -> **Create function**
2. Function name: `api-hello`
3. Runtime: **Python 3.12**, Role: `LabRole`
4. Codice:

```python
import json

def lambda_handler(event, context):
    # Get name from query string or default
    params = event.get('queryStringParameters') or {}
    name = params.get('name', 'World')

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': f'Hello, {name}!',
            'method': event.get('httpMethod'),
            'path': event.get('path')
        })
    }
```

5. Clicca **Deploy**

### Step 2 - Creare il REST API

1. Vai a **API Gateway**
2. Clicca **Create API** -> **REST API** -> **Build**
3. Protocol: **REST**, Create new API: **New API**
4. API name: `student-api`
5. Endpoint type: **Regional**
6. Clicca **Create API**

### Step 3 - Creare la risorsa e il metodo

1. Nel pannello Resources, seleziona la root `/`
2. Clicca **Create Resource**
3. Resource name: `hello` (il path sara `/hello`)
4. Clicca **Create Resource**
5. Seleziona la risorsa `/hello`
6. Clicca **Create Method** -> seleziona **GET**
7. Integration type: **Lambda Function**
8. Attiva **Lambda Proxy Integration**
9. Lambda function: `api-hello`
10. Clicca **Create Method**

### Step 4 - Testare nel console

1. Seleziona il metodo GET su `/hello`
2. Clicca **Test** (icona del fulmine)
3. In Query Strings, scrivi: `name=Mario`
4. Clicca **Test**
5. Verifica il risultato: status 200, body con `"Hello, Mario!"`

### Step 5 - Deploy dell'API

1. Clicca **Deploy API**
2. Stage: **[New Stage]**
3. Stage name: `dev`
4. Clicca **Deploy**
5. Copia l'**Invoke URL** (es. `https://abc123.execute-api.us-east-1.amazonaws.com/dev`)
6. Apri nel browser: `<invoke-url>/hello?name=Student`
7. Dovresti vedere il JSON di risposta

### Step 6 - Configurare CORS (metodo OPTIONS)

1. Torna a Resources, seleziona `/hello`
2. Clicca **Enable CORS** (nel menu Actions o pulsante dedicato)
3. Verifica che sia selezionato `GET`
4. Clicca **Save**
5. Rideploya l'API allo stage `dev`

## Output atteso

- API Gateway REST API con endpoint `/hello`
- Risposta JSON: `{"message": "Hello, Mario!", "method": "GET", "path": "/hello"}`
- Invoke URL funzionante nel browser

## Checkpoint

- [ ] Il test nella console API Gateway restituisce 200 con il messaggio corretto
- [ ] L'invoke URL funziona nel browser
- [ ] I query parameter vengono passati correttamente a Lambda
- [ ] Le CORS headers sono presenti nella risposta

## Troubleshooting rapido

| Problema                  | Soluzione                                                                         |
| ------------------------- | --------------------------------------------------------------------------------- |
| 502 Bad Gateway           | Verifica che la risposta Lambda contenga `statusCode` e `body` (non solo il JSON) |
| 403 Forbidden             | L'API non e' stata deployata. Clicca Deploy API                                    |
| CORS error nel browser    | Verifica che la Lambda restituisca `Access-Control-Allow-Origin: *` nelle headers |
| 500 Internal Server Error | Controlla i log CloudWatch della funzione Lambda per dettagli                     |

## Cleanup obbligatorio

1. **API Gateway:** vai a APIs -> seleziona `student-api` -> Delete API
2. **Lambda:** elimina la funzione `api-hello`
3. **CloudWatch Logs:** elimina il log group `/aws/lambda/api-hello`

## Parole chiave Google (screenshot/guide)

- "AWS API Gateway REST API create tutorial"
- "API Gateway Lambda proxy integration"
- "API Gateway deploy stage console"
- "API Gateway CORS configuration"
- "API Gateway test endpoint browser"
