# 🍕 Chatbot Pizzeria - Sistema di ordinazione con AI

Un sistema completo per la gestione delle ordinazioni di una pizzeria, che combina un'interfaccia conversazionale AI per i clienti e una dashboard amministrativa per il personale della pizzeria.

## 📋 Panoramica

Questo progetto rappresenta un'evoluzione dalle semplici applicazioni basate su chatbot a una soluzione completa per la gestione di una pizzeria:

- **Versione 1.0**: Chatbot semplice che utilizzava RAG (Retrieval Augmented Generation) su file di testo per il menu
- **Versione 2.0** (attuale): Sistema completo con database, frontend moderno, dashboard amministrativa e gestione ordini

## 🌟 Funzionalità principali

### 🤖 Interfaccia cliente
- **Assistente conversazionale**: Interagisce con i clienti in modo naturale, guidando l'esperienza di ordinazione
- **Visualizzazione menu**: Mostra automaticamente il menu all'inizio della conversazione o su richiesta
- **Processo di ordinazione guidato**: Accompagna il cliente nella scelta di pizze, fritti, bevande
- **Raccolta informazioni di consegna**: Gestisce indirizzo, telefono e modalità di pagamento
- **Conferma ordine**: Fornisce un riepilogo completo dell'ordine e tempo di attesa stimato

### 📊 Dashboard amministrativa
- **Login sicuro**: Protezione dell'area amministrativa con autenticazione
- **Statistiche in tempo reale**: Visualizzazione di ordini totali, fatturato, ordine medio
- **Grafici interattivi**: Analisi delle vendite per tipo di pizza e andamento temporale
- **Lista ordini**: Tabella degli ordini recenti con dettagli completi
- **Stampa comande**: Possibilità di stampare le comande per la cucina

### 🔄 Backend intelligente
- **Estrazione menu da database**: Il menu viene caricato direttamente da Supabase
- **Gestione conversazionale**: Mantiene il contesto della conversazione per un'esperienza fluida
- **Riconoscimento delle intenzioni**: Identifica automaticamente le richieste del cliente
- **Persistenza dati**: Salvataggio completo di ordini e profili cliente su Supabase

## 🔧 Architettura e componenti

### 🧩 Struttura del progetto
- **`main.py`**: Server FastAPI principale, gestisce richieste API e integrazione OpenAI
- **`ordine.py`**: Gestisce il flusso di ordinazione e la logica conversazionale
- **`profilo.py`**: Gestisce i dati dei clienti e la formattazione delle comande
- **`sup.py`**: Modulo di sicurezza che centralizza tutte le interazioni con Supabase
- **Frontend**:
  - `index.html`: Interfaccia conversazionale per il cliente
  - `login.html`: Pagina di accesso per l'area amministrativa
  - `dashboard.html`: Dashboard per visualizzare statistiche e gestire ordini

### 🗄️ Database (Supabase)
- **`menu_pizzeria`**: Contiene tutti i prodotti disponibili con categorie, prezzi e descrizioni
- **`comande`**: Archivio degli ordini completati con dettagli e stato
- **`clienti`**: Informazioni dei clienti per consegne future

### 🔌 Integrazione
- **OpenAI**: Per la gestione delle conversazioni naturali
- **Supabase**: Database sicuro per la persistenza dei dati
- **FastAPI**: Backend veloce e scalabile
- **Chart.js**: Visualizzazione dei dati nella dashboard

## 📦 Installazione

### Prerequisiti
- Python 3.9+
- Account Supabase
- Chiave API OpenAI

### Configurazione
1. Clona il repository:
   ```bash
   git clone https://github.com/yourusername/chatbot-pizzeria.git
   cd chatbot-pizzeria
   ```

2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

3. Crea un file `.env` nella directory principale con:
   ```
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4o-mini
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

4. Configura il database Supabase:
   - Crea una tabella `menu_pizzeria` con campi: nome, prezzo, descrizione, categoria
   - Crea una tabella `comande` per gli ordini
   - Crea una tabella `clienti` per i dati cliente

### Avvio
Avvia il server con:
```bash
python main.py
```
L'applicazione sarà disponibile su `http://localhost:5000`

## 📱 Guida all'uso

### Per i clienti
1. Apri l'applicazione nel browser
2. Inizia a conversare con il chatbot
3. Il menu verrà mostrato automaticamente all'inizio
4. Segui il flusso guidato per ordinare:
   - Scegli le pizze
   - Aggiungi eventuali fritti
   - Aggiungi bevande
   - Fornisci i dati per la consegna
   - Conferma l'ordine

### Per l'amministrazione pizzeria
1. Accedi alla dashboard usando:
   - Username: `Ciao`
   - Password: `12345678`
2. Visualizza le statistiche in tempo reale
3. Controlla gli ordini recenti
4. Stampa le comande cliccando sul pulsante di stampa
5. Esci con il pulsante Logout

## 🔍 Dettagli tecnici

### Ciclo di vita di un ordine
1. Il cliente avvia la conversazione
2. L'agente mostra automaticamente il menu
3. `ordine.py` gestisce il flusso conversazionale
4. I dati vengono raccolti e validati in tempo reale
5. L'ordine completato viene salvato su Supabase
6. Il personale visualizza e processa l'ordine dalla dashboard

### Gestione del contesto
- Ogni sessione utente mantiene un ID univoco
- La conversazione viene memorizzata per mantenere il contesto
- Il sistema ricorda le scelte precedenti e guida verso i passaggi successivi

### Sicurezza
- Tutte le interazioni con il database sono centralizzate in `sup.py`
- L'autenticazione protegge l'accesso alla dashboard
- Non vengono memorizzate informazioni sensibili dei clienti oltre quelle necessarie per la consegna

## 🚀 Casi d'uso

### Pizzeria con elevato volume di ordini telefonici
Il sistema riduce il carico di lavoro del personale gestendo automaticamente gli ordini più semplici, liberando i dipendenti per attività a maggior valore aggiunto.

### Pizzerie con servizio di consegna
Il sistema raccoglie automaticamente tutti i dati necessari per la consegna, riducendo gli errori e migliorando l'efficienza.

### Pizzerie con analisi dei dati
La dashboard fornisce statistiche in tempo reale che aiutano a ottimizzare il menu, gestire l'inventario e pianificare le promozioni.

## 🔮 Sviluppi futuri

- **Integrazione con sistemi POS**: Collegamento diretto con sistemi di cassa esistenti
- **Gestione multi-lingua**: Supporto per clienti internazionali
- **App mobile dedicata**: Versione nativa per iOS e Android
- **Gestione inventario**: Monitoraggio automatico delle scorte
- **Sistema di fidelizzazione**: Programma punti e coupon per clienti abituali
- **Previsioni di domanda**: Utilizzo di ML per prevedere picchi di ordini

## 📄 Licenza

Questo progetto è rilasciato sotto la licenza MIT.