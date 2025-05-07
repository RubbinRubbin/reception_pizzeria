# 🍕 PizzaBot AI - Assistente Intelligente per Pizzerie
Un agente AI conversazionale che gestisce e cataloga gli ordini dei clienti per una pizzeria, offrendo un'esperienza di ordinazione naturale e intuitiva.

## 📋 Caratteristiche Principali

- 🤖 Interfaccia conversazionale basata su AI per ordinare pizze
- 📊 Sistema RAG (Retrieval Augmented Generation) per gestire il menù dinamicamente
- 👤 Profilazione clienti per esperienze personalizzate
- 🔄 Function calling per connettere l'AI a database e sistemi esterni
- 🧾 Creazione automatica di comande strutturate

## 🛠️ Tecnologie Utilizzate

- **Python 3.9+**: Linguaggio di programmazione principale
- **OpenAI API**: Integrazione con ChatGPT per l'interfaccia conversazionale
- **RAG (Retrieval Augmented Generation)**: Per memorizzare e recuperare informazioni dal menù
- **Function Calling**: Per consentire all'AI di interagire con sistemi esterni
- **Vector Database**: Per lo spazio vettoriale del menù (es. Chroma, Pinecone)

## 📁 Struttura del Progetto

```
PizzaBot-AI/
├── main.py           # Inizializzazione agente e sistema RAG 
├── ordina.py         # Gestione acquisizione ordini e dati cliente
├── profilo.py        # Organizzazione comande e profilazione clienti
├── menu/             # File di configurazione del menù
├── database/         # Database locale per test
└── requirements.txt  # Dipendenze Python
```

### Componenti Principali:

- **main.py**: Punto di ingresso dell'applicazione. Inizializza l'agente AI, carica il menù nello spazio vettoriale RAG e avvia il processo di ordinazione.

- **ordina.py**: Gestisce il dialogo di acquisizione dell'ordine, raccoglie preferenze, gestisce modifiche agli ingredienti e raccoglie i dati del cliente.

- **profilo.py**: Organizza tutte le informazioni raccolte in una comanda strutturata, aggiorna o crea il profilo cliente con preferenze e cronologia ordini.

## ⚙️ Installazione

1. Clona il repository:
   ```bash
   git clone https://github.com/username/PizzaBot-AI.git
   cd PizzaBot-AI
   ```

2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

3. Configura le variabili d'ambiente per le API di OpenAI:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

4. Personalizza il file del menù nella cartella `menu/` secondo le tue esigenze.

## 🚀 Utilizzo

Avvia l'applicazione:
```bash
python main.py
```

L'agente inizierà a interagire con l'utente, guidandolo attraverso il processo di ordinazione in linguaggio naturale.

### Esempio di interazione:

```
PizzaBot: Benvenuto alla Pizzeria AI! Cosa posso ordinare per te oggi?
Cliente: Vorrei una margherita con extra mozzarella e una bibita.
PizzaBot: Ottima scelta! Una margherita con extra mozzarella. 
         Quale bibita preferisci? Abbiamo Coca-Cola, Fanta, Sprite...
Cliente: Una Coca-Cola media.
...
```

## 📱 Roadmap Futura (v2.0)

- [ ] Sviluppo di un'applicazione web/mobile completa
- [ ] Dashboard per la gestione ordini lato pizzeria
- [ ] Interfaccia personalizzata per i clienti
- [ ] Integrazione con database cloud
- [ ] Sistema di analisi predittiva per ottimizzare inventario
- [ ] Notifiche push per aggiornamenti sullo stato dell'ordine
- [ ] Integrazione con sistemi di pagamento online

## 🤝 Contributi

I contributi sono benvenuti! Se desideri partecipare allo sviluppo:

1. Fai un fork del progetto
2. Crea un nuovo branch (`git checkout -b feature/amazing-feature`)
3. Effettua i tuoi cambiamenti e commit (`git commit -m 'Aggiunge una funzionalità incredibile'`)
4. Pusha il branch (`git push origin feature/amazing-feature`)
5. Apri una Pull Request

## 📄 Licenza

Questo progetto è distribuito con licenza MIT

---

⭐️ Se questo progetto ti è utile, mettici una stella! ⭐️
