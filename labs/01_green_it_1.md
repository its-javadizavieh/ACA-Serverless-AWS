# Lab 01 - Green IT: Smart Working e Smart Grid

## Obiettivo

Analizzare l'impatto ambientale delle scelte IT confrontando infrastruttura on-premise e soluzioni cloud, e identificare componenti di una smart grid gestibili con servizi AWS.

## Durata (timebox)

30 minuti

## Prerequisiti

- Accesso a Internet
- Calcolatrice (o foglio di calcolo)
- Nessun account AWS richiesto per questo lab

## Scenario

La societa FictaCorp ha 200 dipendenti, un data center on-premise con 10 rack server (consumo medio 5 kW per rack, 24/7) e un ufficio che consuma 80.000 kWh/anno. Il management vuole valutare la migrazione cloud e l'adozione dello smart working per il 60% dei dipendenti.

## Step

### Step 1 - Calcolo consumo attuale data center

1. Calcola il consumo annuo del data center:
   - 10 rack x 5 kW = 50 kW
   - 50 kW x 8.760 ore/anno = 438.000 kWh/anno
2. Applica un PUE di 1.8 (tipico on-premise):
   - 438.000 x 1.8 = 788.400 kWh/anno totali
3. Annota il risultato.

### Step 2 - Stima consumo equivalente su AWS

1. Applica il PUE di AWS (circa 1.2):
   - 438.000 x 1.2 = 525.600 kWh/anno
2. Considera che la migrazione cloud tipicamente riduce il carico IT del 30% grazie a right-sizing e auto-scaling:
   - 438.000 x 0.7 x 1.2 = 367.920 kWh/anno
3. Calcola il risparmio: 788.400 - 367.920 = 420.480 kWh/anno

### Step 3 - Impatto dello smart working

1. Con il 60% dei dipendenti in smart working, il consumo dell'ufficio si riduce stimatamente del 40%:
   - 80.000 x 0.6 = 48.000 kWh risparmiati
2. Somma il risparmio totale: 420.480 + 48.000 = 468.480 kWh/anno
3. Converti in CO2 (fattore medio UE: 0,25 kg CO2/kWh):
   - 468.480 x 0,25 = 117.120 kg CO2 = 117 tonnellate CO2/anno

### Step 4 - Componenti smart grid su AWS

1. Identifica almeno 3 servizi AWS che potrebbero essere usati in un progetto smart grid:
   - Esempio: AWS IoT Core (raccolta dati sensori), Amazon Kinesis (streaming dati real-time), Amazon S3 (storage dati storici)
2. Per ciascun servizio, scrivi una frase che descrive il suo ruolo nella smart grid.
3. Disegna uno schema semplificato su carta con: sensori -> IoT Core -> Kinesis -> S3 -> Dashboard (QuickSight)

## Output atteso

- Tabella con i consumi calcolati (on-premise vs cloud vs cloud + smart working)
- Risparmio in kWh e tonnellate CO2
- Schema di 3+ servizi AWS per smart grid con breve descrizione del ruolo

## Checkpoint

- [ ] Il risparmio calcolato e di circa 468.000 kWh/anno e ~117 t CO2/anno
- [ ] Almeno 3 servizi AWS identificati per la smart grid
- [ ] Lo schema include sensori, raccolta dati, elaborazione e visualizzazione

## Troubleshooting rapido

| Problema                      | Soluzione                                                                  |
| ----------------------------- | -------------------------------------------------------------------------- |
| Non conosco i servizi AWS IoT | Cerca "AWS IoT Core overview" nella documentazione ufficiale               |
| I calcoli non tornano         | Ricontrolla le unita di misura: kW vs kWh, ore/anno = 8.760                |
| Non so cosa sia il PUE        | Power Usage Effectiveness = energia totale facility / energia IT equipment |

## Cleanup obbligatorio

Nessuna risorsa AWS da eliminare. Questo lab e interamente basato su ricerca e calcolo.

## Parole chiave Google (screenshot/guide)

- "AWS sustainability pillars"
- "data center PUE calculator"
- "smart grid architecture IoT"
- "AWS IoT Core getting started"
- "green IT carbon footprint calculator"
