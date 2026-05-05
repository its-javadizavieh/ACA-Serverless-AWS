# Lab 04 - Casi d'Uso Serverless e Analisi Economica

## Obiettivo

Calcolare i costi dettagliati per tre scenari reali confrontando architettura tradizionale e serverless, e identificare il punto di break-even.

## Durata (timebox)

30 minuti

## Prerequisiti

- Accesso a Internet
- AWS Pricing Calculator: [https://calculator.aws/](https://calculator.aws/)
- Google DOC

## Scenario

Devi aiutare tre aziende a scegliere tra architettura tradizionale e serverless. Per ciascuna, calcola i costi mensili e la raccomandazione.

## Step

### Step 1 - Scenario A: Blog con traffico basso

1. Un blog riceve 10.000 visite/giorno, ogni visita genera 3 API call
2. **Architettura EC2:** 1x t3.micro (24/7) + 1x RDS db.t3.micro
   - EC2: ≈$8.50/mese, RDS: ≈$15/mese = **$23.50/mese**
3. **Architettura serverless:** API Gateway HTTP + Lambda (50ms, 128 MB) + DynamoDB on-demand
   - 900.000 richieste/mese
   - API Gateway: $0.90, Lambda: ≈$0.10, DynamoDB: ≈$0.50 = **≈$1.50/mese**
4. Annota il risparmio percentuale

### Step 2 - Scenario B: E-commerce ad alto traffico costante

1. Un e-commerce riceve 1.000.000 di richieste API/ora (costanti, 24/7)
2. **Architettura EC2:** cluster di 10x c5.large con ALB
   - EC2: ≈$620/mese, ALB: ≈$20/mese = **≈$640/mese**
3. **Architettura serverless:** API Gateway + Lambda (200ms, 512 MB)
   - 720 milioni richieste/mese
   - API Gateway: $720, Lambda: ≈$1.200 = **≈$1.920/mese**
4. In questo caso, EC2 e piu' conveniente. Annota perche'

### Step 3 - Scenario C: Applicazione stagionale

1. Un servizio di prenotazione vacanze: 50.000 req/ora in estate (4 mesi), 500 req/ora in inverno (8 mesi)
2. Calcola il costo annuale per entrambe le architetture
3. EC2: devi pagare per il picco estivo tutto l'anno (o gestire ASG)
4. Serverless: paga solo per l'uso effettivo
5. Identifica il risparmio annuale

### Step 4 - Break-even point

1. Crea uno scenario di riferimento con questi parametri:
   - **EC2:** 1x t3.medium, Linux, On-Demand, 730 ore/mese
   - **API Gateway:** HTTP API, 1.000.000 richieste/mese
   - **Lambda:** 1.000.000 richieste/mese, 200 ms, 256 MB
   - **DynamoDB:** on-demand, 1.000.000 read e 1.000.000 write al mese
2. Calcola il **costo per singola invocazione** scomponendolo in parti:
   - API Gateway: $1.00 / 1.000.000 = **$0.000001**
   - Lambda request charge: $0.20 / 1.000.000 = **$0.0000002**
   - Lambda compute: 0.2 s x 0.25 GB x $0.0000166667 = **$0.000000833335**
   - DynamoDB write: $1.25 / 1.000.000 = **$0.00000125**
   - DynamoDB read: $0.25 / 1.000.000 = **$0.00000025**
3. Somma i componenti:
   - $0.000001 + $0.0000002 + $0.000000833335 + $0.00000125 + $0.00000025 = **$0.000003533335 ≈ $0.0000035** per invocazione
4. Calcola il break-even con il valore semplificato del lab:
   - $30 / $0.0000035 = **≈8.571.428 invocazioni/mese**
5. Se usi il valore EC2 reale spesso mostrato dal Calculator in us-east-1, circa **$30.37/mese**, ottieni:
   - $30.37 / $0.0000035 = **≈8.677.143 invocazioni/mese**
6. Conclusione da annotare:
   - Il break-even e **intorno a 8.5-8.7 milioni di invocazioni al mese**
   - Sotto questa soglia, serverless e piu' conveniente
   - Sopra questa soglia, conviene iniziare a valutare EC2 o container always-on

## Output atteso

- Tabella con costi mensili per i 3 scenari (EC2 vs Serverless)
- Break-even point calcolato con i passaggi esplicitati
- Raccomandazione motivata per ogni scenario

## Checkpoint

- [ ] Scenario A: serverless e significativamente piu' economico (≈94% risparmio)
- [ ] Scenario B: EC2 e piu' conveniente per traffico costante e alto
- [ ] Scenario C: serverless vince grazie al pattern stagionale
- [ ] Break-even: circa 8,5-8,7 milioni di invocazioni/mese con passaggi corretti

## Troubleshooting rapido

| Problema                        | Soluzione                                                                         |
| ------------------------------- | --------------------------------------------------------------------------------- |
| Non so calcolare i costi Lambda | Usa: (richieste x $0.20/1M) + (richieste x durata_s x GB_RAM x $0.0000166667)     |
| I numeri non tornano            | Verifica le unita': millisecondi vs secondi, MB vs GB                              |
| Non so cosa sia il break-even   | E il punto in cui due opzioni costano uguale. Sotto: una conviene. Sopra: l'altra |
| Lambda a $0.00 nel Calculator   | Verifica free tier e configurazione; per il lab usa comunque il calcolo unitario  |

## Cleanup obbligatorio

Nessuna risorsa AWS da eliminare. Lab basato su calcoli con il Pricing Calculator.

## Parole chiave Google (screenshot/guide)

- "AWS Lambda cost calculator"
- "serverless vs EC2 break even point"
- "AWS Pricing Calculator tutorial"
- "API Gateway HTTP API vs REST API pricing"
- "DynamoDB on-demand vs provisioned pricing"
