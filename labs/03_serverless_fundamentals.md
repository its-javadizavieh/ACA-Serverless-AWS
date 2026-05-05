# Lab 03 - Fondamenti Serverless e Confronto Architetturale

## Obiettivo

Disegnare diagrammi architetturali per le tre principali architetture (monolite, microservizi, serverless) e confrontare i costi stimati.

## Durata (timebox)

30 minuti

## Prerequisiti

- Accesso a Internet
- AWS Pricing Calculator: https://calculator.aws/
- Nessun account AWS richiesto

## Scenario

La startup QuickOrder vuole lanciare un servizio di food delivery. Il sistema deve gestire: registrazione utenti, catalogo ristoranti, gestione ordini, pagamenti. Il traffico previsto e 500 ordini/giorno normali, con picchi di 3.000 ordini/ora durante il weekend sera.

## Step

### Step 1 - Diagramma architettura monolitica

1. Disegna un'architettura monolitica con:
   - 2 istanze EC2 dietro un Application Load Balancer
   - Un database RDS MySQL
   - Tutti i moduli (utenti, catalogo, ordini, pagamenti) nella stessa applicazione
2. Annota: tipo istanza (es. t3.medium), dimensione RDS (db.t3.small)

### Step 2 - Diagramma architettura microservizi

1. Disegna l'architettura a microservizi:
   - 4 servizi separati (utenti, catalogo, ordini, pagamenti) su ECS Fargate
   - Ogni servizio con il proprio database (DynamoDB o RDS)
   - API Gateway o ALB come entry point
2. Annota: numero task Fargate per servizio, tipo database

### Step 3 - Diagramma architettura serverless

1. Disegna l'architettura serverless:
   - API Gateway come entry point
   - 4 Lambda functions (una per dominio)
   - DynamoDB per i dati
   - S3 per asset statici (immagini menu)
   - SNS per notifiche ordine
2. Annota: nessun server da gestire, scaling automatico

### Step 4 - Stima costi con AWS Pricing Calculator

1. Apri https://calculator.aws/
2. Stima il costo mensile per ciascuna architettura:
   - Monolite: 2x t3.medium EC2 (24/7) + 1x db.t3.small RDS
   - Microservizi: 4 task Fargate (0.25 vCPU, 0.5 GB) + 4 tabelle DynamoDB
   - Serverless: API Gateway + Lambda (500 ordini/giorno = ~15.000/mese, 200ms media, 256 MB) + DynamoDB on-demand
3. Compila una tabella comparativa con costo mensile stimato per ciascuna architettura

## Output atteso

- 3 diagrammi architetturali (monolite, microservizi, serverless)
- Tabella comparativa con costi mensili stimati
- Nota su quale architettura e piu' adatta al caso d'uso e perche'

## Checkpoint

- [ ] Tutti e 3 i diagrammi sono completi con i servizi AWS corretti
- [ ] I costi sono stimati con il Pricing Calculator
- [ ] La scelta architetturale e giustificata rispetto al pattern di traffico (spiky/variabile)

## Troubleshooting rapido

| Problema                           | Soluzione                                                              |
| ---------------------------------- | ---------------------------------------------------------------------- |
| Non so usare il Pricing Calculator | Cerca "AWS Pricing Calculator tutorial" su YouTube                     |
| Non conosco i tipi di istanza      | Usa t3.micro o t3.small per le stime di base                           |
| Non so cosa sia Fargate            | E un servizio di container serverless, alternativa a EC2 per container |

## Cleanup obbligatorio

Nessuna risorsa AWS da eliminare. Lab basato su calcolo e diagrammi.

## Parole chiave Google (screenshot/guide)

- "AWS serverless architecture diagram example"
- "AWS Pricing Calculator tutorial"
- "monolith vs microservices vs serverless comparison"
- "AWS Lambda pricing example"
- "ECS Fargate pricing"
