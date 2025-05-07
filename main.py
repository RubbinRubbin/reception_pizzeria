import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import uvicorn
import json
import webbrowser  # Aggiunto per aprire automaticamente il browser

# Import LlamaIndex components
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.settings import Settings
from llama_index.llms.openai import OpenAI as LlamaOpenAI

# Importa il gestore degli ordini
from ordine import GestoreOrdine, e_intento_ordine

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Verifica che la chiave API sia presente
if not os.getenv("OPENAI_API_KEY"):
    print("ERRORE: Chiave API di OpenAI non trovata nel file .env")
    exit(1)

# Inizializza il client OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Inizializza l'app FastAPI
app = FastAPI(title="Chatbot Pizzeria API")

# Definizione del modello per la richiesta di chat
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"

# Configurazione per servire file statici
app.mount("/static", StaticFiles(directory="static"), name="static")

# Definizione del system prompt direttamente nel file main.py
SYSTEM_PROMPT = """Obiettivo
Voglio un chatbot che prenda ordinazioni per la Pizzeria da Mario, rispondendo come un autentico cameriere italiano al telefono. Deve essere efficiente e naturale nella gestione degli ordini.
Formato di Risposta
Sei Mario, addetto alle ordinazioni della Pizzeria da Mario. Gestisci la conversazione guidando il cliente attraverso l'ordine in modo naturale, chiedendo prima il tipo di pizza, poi eventuali modifiche, bevande, e infine i dettagli di consegna o ritiro.
Conferma sempre l'ordine completo alla fine e fornisci un tempo di attesa stimato.
Avvertenze
Assicurati che le risposte siano brevi e dirette, evitando formalismi eccessivi o spiegazioni non richieste. Non usare mai un tono robotico o artificiale.
Non confermare ogni singolo messaggio del cliente e non scusarti inutilmente. Concentrati sull'efficienza.
Contesto
La Pizzeria da Mario è un ristorante italiano autentico. I clienti si aspettano un servizio rapido e un tono colloquiale tipico di una pizzeria italiana.
Il chatbot dovrebbe usare occasionalmente espressioni italiane tipiche di una pizzeria e mantenere un tono cordiale ma diretto, come un cameriere telefonico italiano che è occupato ma amichevole.
Evita giri di parole e vai subito al punto, guidando la conversazione verso il completamento dell'ordine in modo efficiente e naturale."""

# Menu Indexing with LlamaIndex
class MenuIndex:
    def __init__(self, menu_path):
        """Inizializza l'indice del menu con il percorso del file menu"""
        self.menu_path = menu_path
        self.index = None
        self.menu_data = {}  # Dizionario per memorizzare i dati del menu strutturati
        self._extract_menu_data()  # Prima estraiamo i dati strutturati
        self._initialize_index()  # Poi inizializziamo l'indice
        
        # Assicuriamoci che ci siano sempre prodotti disponibili
        self.ensure_basic_menu()
        
        # Debug: stampa i dati estratti dal menu per verificare
        self._debug_print_menu_data()
    
    def ensure_basic_menu(self):
        """Assicura che ci siano prodotti base nel menu anche se il caricamento fallisce"""
        if not self.menu_data or all(len(items) == 0 for items in self.menu_data.values()):
            print("Utilizzo menu di base di fallback...")
            self.menu_data = {
                "Pizze Classiche": {
                    "Margherita": {"price": 6.00, "description": "Pomodoro, mozzarella, basilico"},
                    "Diavola": {"price": 7.50, "description": "Pomodoro, mozzarella, salame piccante"},
                    "Quattro Stagioni": {"price": 8.00, "description": "Pomodoro, mozzarella, prosciutto, funghi, carciofi, olive"},
                    "Napoletana": {"price": 7.00, "description": "Pomodoro, mozzarella, acciughe, origano, capperi"},
                    "Marinara": {"price": 5.00, "description": "Pomodoro, aglio, origano"},
                    "Capricciosa": {"price": 8.50, "description": "Pomodoro, mozzarella, prosciutto, funghi, carciofi, olive"}
                },
                "Fritti": {
                    "Patatine": {"price": 3.50, "description": "Patatine fritte"},
                    "Crocchette": {"price": 4.00, "description": "Crocchette di patate"},
                    "Supplì": {"price": 2.00, "description": "Supplì di riso"},
                    "Arancini": {"price": 2.50, "description": "Arancini siciliani"}
                },
                "Bevande": {
                    "Acqua": {"price": 2.00, "description": "Acqua naturale/frizzante 0.5L"},
                    "Coca Cola": {"price": 3.00, "description": "Coca Cola 0.33L"},
                    "Birra": {"price": 4.00, "description": "Birra alla spina 0.4L"},
                    "Fanta": {"price": 3.00, "description": "Fanta 0.33L"},
                    "Sprite": {"price": 3.00, "description": "Sprite 0.33L"}
                }
            }
            return True
        return False
    
    def _debug_print_menu_data(self):
        """Stampa i dati del menu per debug"""
        print("\nDEBUG - Dati estratti dal menu:")
        for section, items in self.menu_data.items():
            print(f"Sezione: {section}")
            for item, details in items.items():
                print(f"  - {item}: €{details['price']:.2f}")
        print()
    
    def _initialize_index(self):
        """Crea un indice dal file del menu - aggiornato per usare Settings"""
        try:
            # Verifica se il file menu esiste
            if not os.path.exists(self.menu_path):
                print(f"ERRORE: File menu non trovato in {self.menu_path}")
                return
            
            # Carica il documento
            documents = SimpleDirectoryReader(input_files=[self.menu_path]).load_data()
            
            # Inizializza LLM con la nuova API
            llm = LlamaOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.2)
            
            # Configura impostazioni globali
            Settings.llm = llm
            
            # Crea l'indice
            self.index = VectorStoreIndex.from_documents(documents)
            print(f"Indice del menu creato con successo da {self.menu_path}")
        except Exception as e:
            print(f"Errore nell'inizializzazione dell'indice del menu: {str(e)}")
    
    def _extract_menu_data(self):
        """Estrae i dati strutturati dal file menu"""
        try:
            if not os.path.exists(self.menu_path):
                print(f"ERRORE: File menu non trovato in {self.menu_path}")
                return
                
            with open(self.menu_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Estrai le sezioni del menu
            sections = content.split('---')
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                
                # Estrai il titolo della sezione
                section_title = None
                if '##' in section:
                    section_parts = section.split('\n', 1)
                    section_title = section_parts[0].replace('#', '').strip()
                    section_content = section_parts[1] if len(section_parts) > 1 else ""
                else:
                    section_content = section
                
                # Estrai gli elementi del menu
                if section_title:
                    self.menu_data[section_title] = {}
                    
                    # Divide in singoli elementi del menu
                    items = section_content.strip().split('\n\n')
                    for item in items:
                        item = item.strip()
                        if not item:
                            continue
                            
                        # Estrai nome e prezzo
                        name_price_match = re.search(r'\*\*(.*?)\*\*\s*-\s*€\s*([\d.,]+)', item)
                        if name_price_match:
                            name = name_price_match.group(1).strip()
                            price_str = name_price_match.group(2).strip().replace(',', '.')
                            price = float(price_str)
                            
                            # Estrai descrizione
                            description = item.split('\n', 1)[1].strip() if '\n' in item else ""
                            
                            # Aggiungi al dizionario
                            self.menu_data[section_title][name] = {
                                "price": price,
                                "description": description
                            }
            
            print(f"Dati del menu estratti: {len(self.menu_data)} sezioni")
            # Assicuriamoci di avere sempre prodotti disponibili
            self.ensure_basic_menu()
        except Exception as e:
            print(f"Errore nell'estrazione dei dati del menu: {str(e)}")
            # In caso di errore, utilizziamo il menu di fallback
            self.ensure_basic_menu()
    
    def query(self, query_text):
        """Interroga l'indice del menu"""
        # Prima controlla se è una domanda sul prezzo
        price_keywords = ["prezzo", "costa", "quanto", "costo", "euro", "€"]
        is_price_query = any(keyword in query_text.lower() for keyword in price_keywords)
        
        if is_price_query:
            # Estrai il possibile nome della pizza
            pizza_name = self.extract_item_name(query_text)
            if pizza_name:
                exists, _, message = self.verify_item(pizza_name)
                if exists:
                    return message
        
        # Usa l'indice per query generali se non è una query di prezzo o non abbiamo trovato il prodotto
        if not self.index:
            return "Le informazioni sul menu non sono disponibili al momento."
        
        try:
            query_engine = self.index.as_query_engine()
            response = query_engine.query(query_text)
            return str(response)
        except Exception as e:
            print(f"Errore nella ricerca sul menu: {str(e)}")
            return "Mi dispiace, non riesco a trovare queste informazioni nel menu al momento."
    
    def extract_item_name(self, text):
        """
        Estrae possibili nomi di prodotti dal testo
        """
        # Crea un set di tutti i prodotti del menu
        all_items = set()
        for section in self.menu_data.values():
            for item in section.keys():
                all_items.add(item.lower())
                # Aggiungi anche la prima parola del nome come possibile match
                words = item.split()
                if words:
                    all_items.add(words[0].lower())
        
        # Normalizza il testo per la ricerca
        text_lower = text.lower()
        
        # Cerca menzioni di prodotti nel testo
        for item in all_items:
            if item in text_lower:
                return item
        
        # Se non abbiamo trovato un match esatto, cerca parole che potrebbero essere nomi di prodotti
        words = text_lower.replace(',', ' ').replace('.', ' ').split()
        for word in words:
            if len(word) > 3 and word not in ["pizza", "vorrei", "voglio", "ordinare", "anche", "solo", "senza", "euro", "grazie"]:
                # Cerca somiglianze
                for item in all_items:
                    if word in item or any(w in item for w in words if len(w) > 3):
                        return item
        
        return None
    
    def verify_item(self, item_name, mentioned_price=None):
        """
        Verifica se un elemento esiste nel menu e se il prezzo è corretto
        Restituisce: (esiste, prezzo_corretto, messaggio)
        """
        # Normalizza il nome dell'elemento per la ricerca
        item_name_lower = item_name.lower()
        
        # Cerca in tutte le sezioni
        for section_title, items in self.menu_data.items():
            for menu_item, details in items.items():
                if item_name_lower in menu_item.lower():
                    # Se il prezzo è menzionato, verifica
                    if mentioned_price is not None:
                        try:
                            mentioned_price_float = float(mentioned_price)
                            actual_price = details["price"]
                            
                            if abs(mentioned_price_float - actual_price) < 0.01:
                                return (True, True, f"La {menu_item} costa €{actual_price:.2f}")
                            else:
                                return (True, False, f"La {menu_item} costa €{actual_price:.2f}")
                        except (ValueError, TypeError):
                            return (True, False, f"La {menu_item} costa €{details['price']:.2f}")
                    else:
                        return (True, True, f"La {menu_item} costa €{details['price']:.2f}")
        
        # Se non trova corrispondenze esatte, prova a ottenere alternative simili
        alternatives = []
        for section_title, items in self.menu_data.items():
            for menu_item in items.keys():
                # Verifica somiglianza parziale
                if any(word in menu_item.lower() for word in item_name_lower.split() if len(word) > 3):
                    alternatives.append(menu_item)
        
        if alternatives:
            alternative_text = ", ".join(alternatives[:3])
            return (False, False, f"'{item_name}'? Non ce l'abbiamo. Forse intende: {alternative_text}?")
        
        return (False, False, f"Mi dispiace, non abbiamo '{item_name}' in menu.")
    
    def format_menu_section(self, section_name=None):
        """
        Formatta una sezione del menu per la visualizzazione
        Se section_name è None, restituisce tutto il menu
        """
        if not self.menu_data:
            return "Menu non disponibile."
            
        result = []
        
        # Se è specificata una sezione
        if section_name:
            for title, items in self.menu_data.items():
                if section_name.lower() in title.lower():
                    result.append(f"## {title}")
                    for item, details in items.items():
                        result.append(f"**{item}** - €{details['price']:.2f}")
                        if details["description"]:
                            result.append(f"{details['description']}")
                        result.append("")
                    break
            
            if not result:
                return f"Sezione '{section_name}' non trovata nel menu."
        else:
            # Restituisce tutto il menu
            for title, items in self.menu_data.items():
                result.append(f"## {title}")
                for item, details in items.items():
                    result.append(f"**{item}** - €{details['price']:.2f}")
                    if details["description"]:
                        result.append(f"{details['description']}")
                    result.append("")
                result.append("---")
        
        return "\n".join(result)

def extract_price_from_text(text):
    """
    Estrae un possibile prezzo dal testo
    """
    try:
        # Cerca pattern comuni per i prezzi
        price_patterns = [
            r'(\d+[.,]?\d*)\s*euro',  # 5 euro, 5.50 euro
            r'(\d+[.,]?\d*)\s*€',     # 5 €, 5.50 €
            r'€\s*(\d+[.,]?\d*)',     # € 5, € 5.50
            r'costa\s*(\d+[.,]?\d*)',  # costa 5, costa 5.50
            r'prezzo\s*(\d+[.,]?\d*)', # prezzo 5, prezzo 5.50
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text.lower())
            if match:
                # Normalizza il formato del prezzo
                price_str = match.group(1).replace(',', '.')
                return float(price_str)
                
        # Se non trova un pattern, restituisce None
        return None
    except Exception as e:
        print(f"Errore nell'estrazione del prezzo: {str(e)}")
        return None

def get_chatgpt_response(message, conversation_history, system_instruction=None):
    """
    Invia un messaggio a ChatGPT con un'istruzione di sistema specifica o quella definita in SYSTEM_PROMPT
    """
    try:
        # Usa il SYSTEM_PROMPT definito nel file se non viene specificata un'istruzione specifica
        if system_instruction is None:
            system_instruction = SYSTEM_PROMPT
        
        # Prepara i messaggi per l'API di OpenAI con l'istruzione specifica
        messages = [
            {"role": "system", "content": system_instruction}
        ]
        
        # Aggiungi la cronologia della conversazione
        messages.extend(conversation_history)
        
        # Aggiungi il messaggio corrente dell'utente
        messages.append({"role": "user", "content": message})
        
        # Chiama l'API di OpenAI
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
        temperature = float(os.getenv("TEMPERATURE", "0.5"))
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Estrai la risposta
        reply = response.choices[0].message.content
        
        return reply
        
    except Exception as e:
        print(f"\nErrore nella chiamata all'API: {str(e)}")
        return f"Mi scusi, si è verificato un errore di sistema. Può ripetere?"

# Inizializza l'indice del menu
menu_file_path = "C:\\Users\\rubbi\\Desktop\\LAVORO\\AI\\reception_pizzeria\\menu.txt"
try:
    menu_index = MenuIndex(menu_file_path)
    print("Menu inizializzato correttamente")
except Exception as e:
    print(f"Errore durante l'inizializzazione del menu: {str(e)}")
    # Crea un indice di menu di fallback
    menu_index = MenuIndex(None)  # Inizializza con None, farà usare il menu di base
    menu_index.ensure_basic_menu()  # Forza l'uso del menu di base

# Inizializza il gestore degli ordini
gestore_ordine = GestoreOrdine(menu_index)

# Dizionario per memorizzare le conversazioni degli utenti
user_conversations = {}

# Lista di comandi per mostrare il menu
MENU_COMMANDS = ["mostra menu", "vedi menu", "menu", "il menu", "lista delle pizze", "lista pizza", "lista pizze", "mostrami il menu"]

# Route per servire il file index.html
@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

# API endpoint per gestire le richieste di chat
@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        user_message = request.message
        user_id = request.user_id
        
        # Debug
        print(f"\nRichiesta chat - Messaggio: '{user_message}', User ID: {user_id}")
        
        # Inizializza la conversazione se è un nuovo utente
        if user_id not in user_conversations:
            # Ottieni il menu per includerlo nel messaggio di benvenuto
            menu_text = menu_index.format_menu_section()
            welcome_with_menu = f"Buonasera, pizzeria da Mario! Ecco il nostro menu:\n\n{menu_text}\n\nChe pizza desidera ordinare?"
            
            user_conversations[user_id] = [
                {"role": "assistant", "content": welcome_with_menu}
            ]
            
            # Se è un nuovo utente, avvia automaticamente un nuovo ordine
            gestore_ordine.inizia_nuovo_ordine(user_id)
            print(f"Nuovo utente: {user_id} - Inizializzato nuovo ordine e mostrato menu")
        
        # Aggiungi il messaggio dell'utente alla conversazione
        user_conversations[user_id].append({"role": "user", "content": user_message})
        
        # Verifica prioritariamente se è una richiesta di menu
        if any(cmd in user_message.lower() for cmd in MENU_COMMANDS):
            # Mostra il menu completo
            menu_text = menu_index.format_menu_section()
            response_text = f"Ecco il nostro menu:\n\n{menu_text}\n\nChe pizza desidera ordinare?"
            print("Richiesta menu rilevata")
        else:
            # Altrimenti, gestisci con il gestore ordini
            response_text = gestore_ordine.gestisci_messaggio(user_id, user_message)
            
            # Se il gestore ordini richiede di mostrare il menu
            if response_text == "MOSTRA_MENU":
                menu_text = menu_index.format_menu_section()
                response_text = f"Ecco il nostro menu:\n\n{menu_text}\n\nChe pizza desidera ordinare?"
                print("Richiesta menu da gestore ordini")
            # Se non è un messaggio relativo all'ordine, fallback su risposte generiche
            elif response_text == "FALLBACK":
                print("Fallback attivato - Controllo query sul menu")
                # Controlla se l'utente sta chiedendo informazioni sul menu
                menu_keywords = ["carta", "prezzo", "costa", "quanto", "ingredienti", "disponibile", "offrite"]
                is_menu_query = any(keyword in user_message.lower() for keyword in menu_keywords)
                
                # Gestisci le domande sul menu
                if is_menu_query:
                    try:
                        # Estrai possibile prezzo menzionato
                        mentioned_price = extract_price_from_text(user_message)
                        
                        # Controlla se è una domanda sul prezzo di un prodotto specifico
                        item_name = menu_index.extract_item_name(user_message)
                        
                        if item_name:
                            # Verifica l'elemento nel menu
                            exists, price_correct, message = menu_index.verify_item(item_name, mentioned_price)
                            response_text = message
                            print(f"Query sul menu - Prodotto trovato: {item_name}")
                        else:
                            # Usa RAG per domande più generiche sul menu
                            response_text = menu_index.query(user_message)
                            print("Query sul menu - Ricerca generica")
                    except Exception as e:
                        print(f"\nErrore nella gestione della query sul menu: {str(e)}")
                        response_text = "Non ho capito bene. Vuole ordinare qualcosa?"
                
                # Gestisci altre conversazioni generiche
                else:
                    print("Utilizzo risposta generica da ChatGPT")
                    # Usa il SYSTEM_PROMPT definito nel file
                    response_text = get_chatgpt_response(user_message, user_conversations[user_id][:-1])
        
        # Aggiungi la risposta alla cronologia
        user_conversations[user_id].append({"role": "assistant", "content": response_text})
        
        # Limita la lunghezza della cronologia
        if len(user_conversations[user_id]) > 10:
            user_conversations[user_id] = user_conversations[user_id][-10:]
        
        # Debug
        print(f"Risposta: '{response_text[:100]}...'")
        
        # Restituisci la risposta come JSON
        return JSONResponse({"response": response_text})
        
    except Exception as e:
        print(f"Errore nella gestione della richiesta: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"response": "Mi scusi, si è verificato un errore. Può riprovare?"}
        )

# Funzione per aprire il browser
def open_browser():
    webbrowser.open("http://localhost:5000")

# Avvia l'app quando viene eseguito questo file
if __name__ == "__main__":
    print("=" * 60)
    print("  SERVER CHATBOT PIZZERIA CON FASTAPI")
    print("  Apertura automatica del browser...")
    print("=" * 60)
    
    # Apri automaticamente il browser dopo un breve ritardo
    import threading
    threading.Timer(1.5, open_browser).start()
    
    # Avvia il server FastAPI con uvicorn
    # Rimuovi l'opzione reload per evitare l'avviso
    uvicorn.run(app, host="127.0.0.1", port=5000)