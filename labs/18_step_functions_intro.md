# Lab 18 - Introduzione a Step Functions

## Obiettivo

Creare una state machine con Task, Choice e Wait usando Workflow Studio, eseguirla con input diversi e osservare l'esecuzione visuale.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Familiarita con Lambda (lezioni 06-09)

## Scenario

Creerai un workflow per processare ordini: validazione -> decisione (sconto se > 100 EUR) -> conferma. Il tutto orchestrato da Step Functions.

## Step

### Step 1 - Creare le funzioni Lambda

1. Crea `validate-order` (Python 3.12, LabRole):

```python
import json

def lambda_handler(event, context):
    order_id = event.get('order_id', 'unknown')
    total = event.get('total', 0)

    if total <= 0:
        raise ValueError(f"Invalid order total: {total}")

    return {
        'order_id': order_id,
        'total': total,
        'status': 'validated'
    }
```

2. Crea `apply-discount` (Python 3.12, LabRole):

```python
import json

def lambda_handler(event, context):
    total = event['total']
    discount = total * 0.1  # 10% discount
    new_total = round(total - discount, 2)

    return {
        'order_id': event['order_id'],
        'original_total': total,
        'discount': round(discount, 2),
        'total': new_total,
        'status': 'discounted'
    }
```

3. Crea `confirm-order` (Python 3.12, LabRole):

```python
import json

def lambda_handler(event, context):
    return {
        'order_id': event['order_id'],
        'total': event['total'],
        'status': 'confirmed',
        'message': f"Order {event['order_id']} confirmed. Total: {event['total']} EUR"
    }
```

### Step 2 - Creare la state machine con Workflow Studio

1. Vai a **Step Functions** -> **Create state machine**
2. Seleziona **Design your workflow visually**
3. Type: **Standard**

4. Costruisci il workflow:
   - Trascina un **Task** (Lambda Invoke) -> seleziona `validate-order` -> rinomina "ValidateOrder"
   - Aggiungi un **Choice** dopo ValidateOrder -> rinomina "CheckAmount"
   - Regola 1: Variable `$.total`, NumericGreaterThan `100` -> collega a un nuovo Task `apply-discount` -> rinomina "ApplyDiscount"
   - Default: collega direttamente a un Task `confirm-order` -> rinomina "ConfirmOrder"
   - Da ApplyDiscount -> collega a ConfirmOrder
   - Da ConfirmOrder -> aggiungi un **Succeed** state

5. Clicca **Next**
6. Nome: `order-processor`
7. Permissions: seleziona un ruolo esistente (`LabRole`) o lascia che ne crei uno nuovo
8. Clicca **Create state machine**

### Step 3 - Eseguire il workflow (ordine piccolo)

1. Clicca **Start execution**
2. Input:

```json
{
  "order_id": "ORD-001",
  "total": 50
}
```

3. Clicca **Start execution**
4. Osserva il flusso visuale: ValidateOrder -> CheckAmount -> ConfirmOrder (NO sconto)
5. Clicca su ogni stato per vedere input/output

### Step 4 - Eseguire il workflow (ordine grande)

1. Clicca **Start execution**
2. Input:

```json
{
  "order_id": "ORD-002",
  "total": 200
}
```

3. Osserva: ValidateOrder -> CheckAmount -> ApplyDiscount -> ConfirmOrder
4. Verifica che il totale sia stato ridotto del 10% (200 -> 180)

### Step 5 - Testare un errore

1. Clicca **Start execution**
2. Input:

```json
{
  "order_id": "ORD-003",
  "total": -10
}
```

3. Osserva: ValidateOrder FALLISCE (ValueError)
4. Lo stato diventa rosso nell'esecuzione visuale
5. Clicca sullo stato per vedere il messaggio di errore

## Output atteso

- Workflow con 3 Lambda + 1 Choice state funzionante
- Ordine < 100: percorso senza sconto
- Ordine > 100: percorso con sconto del 10%
- Ordine negativo: errore in ValidateOrder

## Checkpoint

- [ ] Il workflow visuale mostra il percorso di esecuzione corretto
- [ ] L'ordine da 50 EUR non riceve sconto (totale finale: 50)
- [ ] L'ordine da 200 EUR riceve sconto (totale finale: 180)
- [ ] L'ordine negativo genera un errore visibile nel console

## Troubleshooting rapido

| Problema                        | Soluzione                                                                      |
| ------------------------------- | ------------------------------------------------------------------------------ |
| "AccessDeniedException" al Task | Verifica che il ruolo della state machine abbia permessi lambda:InvokeFunction |
| Il Choice non funziona          | Verifica che la variabile sia `$.total` e il tipo numerico sia corretto        |
| "States.Runtime" error          | Controlla che i nomi delle funzioni Lambda siano corretti nella definizione    |
| Il workflow non parte           | Verifica che la state machine sia in stato ACTIVE                              |

## Cleanup obbligatorio

1. **Step Functions:** elimina la state machine `order-processor`
2. **Lambda:** elimina `validate-order`, `apply-discount`, `confirm-order`
3. **CloudWatch Logs:** elimina i log group delle 3 funzioni Lambda
4. **IAM:** se e' stato creato un ruolo automatico per Step Functions, eliminalo

## Parole chiave Google (screenshot/guide)

- "AWS Step Functions Workflow Studio tutorial"
- "Step Functions Choice state example"
- "Step Functions Lambda invoke tutorial"
- "Amazon States Language JSON example"
- "Step Functions visual workflow console"
