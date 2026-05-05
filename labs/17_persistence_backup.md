# Lab 17 - Persistenza Dati, TTL e Backup

## Obiettivo

Configurare TTL in DynamoDB, creare un backup on-demand, configurare una lifecycle policy S3 e verificare il PITR.

## Durata (timebox)

30 minuti

## Prerequisiti

- Account AWS Academy Learner Lab attivo
- Completato i lab 14-16 (DynamoDB e S3)

## Scenario

Gestisci una tabella di sessioni utente con scadenza automatica (TTL) e configuri backup e lifecycle per la protezione dei dati.

## Step

### Step 1 - Creare la tabella con dati di sessione

1. Vai a **DynamoDB** -> **Create table**
2. Table name: `lab17-sessions`
3. Partition key: `session_id` (String)
4. Impostazioni default -> **Create table**

### Step 2 - Abilitare TTL

1. Vai alla tabella `lab17-sessions`
2. Clicca **Additional settings** (o tab **TTL**)
3. Clicca **Enable TTL** (o **Turn on**)
4. TTL attribute: `expires_at`
5. Conferma

### Step 3 - Inserire dati con TTL

1. Vai a **Lambda** -> **Create function**
2. Function name: `insert-sessions`
3. Runtime: **Python 3.12**, Role: `LabRole`
4. Codice:

```python
import json
import time
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('lab17-sessions')

def lambda_handler(event, context):
    now = int(time.time())

    sessions = [
        {
            'session_id': 'sess-001',
            'user_id': 'alice',
            'created_at': now,
            'expires_at': now + 60  # Scade tra 60 secondi
        },
        {
            'session_id': 'sess-002',
            'user_id': 'bob',
            'created_at': now,
            'expires_at': now + 3600  # Scade tra 1 ora
        },
        {
            'session_id': 'sess-003',
            'user_id': 'charlie',
            'created_at': now,
            'expires_at': now + 86400  # Scade tra 24 ore
        }
    ]

    for session in sessions:
        table.put_item(Item=session)
        print(f"Created session {session['session_id']}, expires in {session['expires_at'] - now}s")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Created {len(sessions)} sessions',
            'current_epoch': now
        })
    }
```

5. Deploy e testa la funzione (nessun input necessario)

### Step 4 - Osservare TTL in azione

1. Vai a DynamoDB -> `lab17-sessions` -> **Explore table items**
2. Verifica i 3 item con i loro `expires_at`
3. Aspetta 1-2 minuti (nota: DynamoDB puo' impiegare fino a 48 ore per eliminare gli item, ma in pratica e molto piu' veloce)
4. `sess-001` dovrebbe scomparire presto (TTL 60 secondi)
5. `sess-002` e `sess-003` rimarranno

### Step 5 - Creare un backup on-demand

1. Vai a `lab17-sessions` -> **Backups**
2. Clicca **Create backup**
3. Nome: `sessions-backup-test`
4. Tipo: **DynamoDB** (backup completo)
5. Clicca **Create backup**
6. Verifica lo stato: AVAILABLE

### Step 6 - Abilitare PITR

1. Nella stessa sezione **Backups**
2. Trova **Point-in-time recovery**
3. Clicca **Enable** (o **Edit** -> Enable)
4. Conferma
5. Ora puoi ripristinare la tabella a qualsiasi momento degli ultimi 35 giorni

### Step 7 - Configurare lifecycle S3

1. Crea un bucket S3: `lab17-lifecycle-TUONOME`
2. Carica alcuni file di test
3. Vai a **Management** -> **Create lifecycle rule**
4. Rule name: `archive-old-files`
5. Apply to all objects
6. Transitions:
   - Transition to **Standard-IA** after **30 days**
   - Transition to **Glacier Flexible Retrieval** after **90 days**
7. Expiration: **Delete** after **365 days**
8. Clicca **Create rule**

## Output atteso

- 3 sessioni create con TTL diversi
- `sess-001` eliminata automaticamente (o in attesa di eliminazione TTL)
- Backup on-demand in stato AVAILABLE
- PITR abilitato sulla tabella
- Lifecycle rule configurata nel bucket S3

## Checkpoint

- [ ] TTL abilitato sull'attributo `expires_at`
- [ ] Le sessioni hanno timestamp `expires_at` corretti
- [ ] Backup on-demand creato con successo
- [ ] PITR abilitato e funzionante
- [ ] Lifecycle rule S3 mostra 3 transizioni configurate

## Troubleshooting rapido

| Problema                      | Soluzione                                                                                                                      |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| TTL non elimina l'item        | L'eliminazione TTL puo' impiegare fino a 48 ore. Non e' immediata                                                                |
| Backup in stato CREATING      | Il backup puo' richiedere qualche minuto per tabelle grandi                                                                     |
| PITR non disponibile          | Verifica che la tabella sia in stato ACTIVE prima di abilitare                                                                 |
| Lifecycle rule non si applica | Le regole si applicano ai nuovi oggetti e a quelli esistenti, ma le transizioni avvengono dopo il numero di giorni specificato |

## Cleanup obbligatorio

1. **DynamoDB Backups:** elimina il backup `sessions-backup-test`
2. **DynamoDB:** disabilita PITR, poi elimina la tabella `lab17-sessions`
3. **Lambda:** elimina `insert-sessions`
4. **S3:** rimuovi la lifecycle rule, svuota e elimina il bucket `lab17-lifecycle-TUONOME`
5. **CloudWatch Logs:** elimina i log group

## Parole chiave Google (screenshot/guide)

- "DynamoDB TTL enable tutorial"
- "DynamoDB on-demand backup console"
- "DynamoDB point-in-time recovery"
- "S3 lifecycle policy create tutorial"
- "S3 storage class transition"
