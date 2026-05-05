# Lab 02 - Green IT, Economia Circolare e Intro Serverless

## Obiettivo

Classificare apparecchiature IT secondo le categorie RAEE, e disegnare il primo schema di un'applicazione serverless event-driven su AWS.

## Durata (timebox)

30 minuti

## Prerequisiti

- Accesso a Internet
- Conoscenza base dei servizi AWS (dalla lezione precedente)
- Nessun account AWS richiesto

## Scenario

Il reparto IT della societa EcoTech deve dismettere 150 dispositivi (laptop, monitor, server, stampanti, smartphone aziendali). Contemporaneamente, il CTO ha chiesto un POC (Proof of Concept) per valutare l'adozione di architetture serverless.

## Step

### Step 1 - Classificazione RAEE

1. Crea una tabella con le colonne: Dispositivo | Categoria RAEE | Azione consigliata
2. Classifica i seguenti dispositivi:
   - 50 laptop (funzionanti)
   - 30 monitor LCD (non funzionanti)
   - 20 server rack (obsoleti ma funzionanti)
   - 30 stampanti laser (miste)
   - 20 smartphone aziendali (funzionanti)
3. Per ogni categoria, specifica l'azione: donazione, riciclo certificato, o refurbishment
4. Indica quale normativa si applica (Direttiva EU 2012/19/EU)

### Step 2 - Schema serverless event-driven

1. Disegna su carta (o digitalmente) un'architettura serverless con questi componenti:
   - **Evento:** un utente carica un file CSV su Amazon S3
   - **Trigger:** S3 Event Notification
   - **Compute:** AWS Lambda legge il CSV e trasforma i dati
   - **Storage:** Lambda scrive i dati trasformati in Amazon DynamoDB
   - **Notifica:** Lambda invia un messaggio su Amazon SNS
2. Per ogni componente, scrivi una frase che descriva il suo ruolo
3. Identifica quali componenti sono serverless e perche'

### Step 3 - Confronto costi idle vs serverless

1. Calcola il costo annuo di un server EC2 t3.medium sempre acceso:
   - Prezzo on-demand us-east-1: circa $0.0416/ora
   - Costo annuo: $0.0416 x 8.760 ore = $364.42
2. Stima il costo Lambda equivalente (supponendo 100.000 invocazioni/mese, 500ms ciascuna, 256 MB RAM):
   - 100.000 x 0.5s = 50.000 GB-secondo/mese (con 256 MB = 12.500 GB-s)
   - Costo: circa $0.21/mese = $2.52/anno
3. Annota il rapporto di risparmio e collegalo ai principi Green IT

## Output atteso

- Tabella RAEE con 5 categorie di dispositivi, classificazione e azioni
- Schema architetturale serverless con almeno 4 servizi AWS collegati
- Calcolo comparativo EC2 vs Lambda con il rapporto di risparmio

## Checkpoint

- [ ] Tutti i 150 dispositivi sono classificati secondo le categorie RAEE
- [ ] Lo schema serverless include S3, Lambda, DynamoDB e SNS
- [ ] Il calcolo mostra un risparmio di circa il 99% con Lambda vs EC2 always-on
- [ ] La connessione tra serverless e Green IT e esplicitata

## Troubleshooting rapido

| Problema                      | Soluzione                                                                                                            |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Non conosco le categorie RAEE | Cerca "RAEE categorie Italia" oppure vedi Allegato VII della Direttiva 2012/19/EU                                    |
| Non so stimare i costi Lambda | Usa il calcolatore ufficiale: https://aws.amazon.com/lambda/pricing/                                                 |
| Non so cosa sia un S3 Event   | Verra approfondito nella lezione 16, per ora basta sapere che S3 puo' notificare Lambda quando un file viene caricato |

## Cleanup obbligatorio

Nessuna risorsa AWS da eliminare. Lab basato su ricerca, calcolo e disegno architetturale.

## Parole chiave Google (screenshot/guide)

- "RAEE categorie Italia normativa"
- "AWS serverless architecture diagram"
- "AWS Lambda pricing calculator"
- "S3 event notification Lambda"
- "NIST 800-88 data sanitization guidelines"
