import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import uvicorn
import json
import webbrowser  # Aggiunto per aprire automaticamente il browser
from supabase import create_client, Client

# Importa il gestore degli ordini
from ordine import GestoreOrdine, e_intento_ordine

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Verifica che le chiavi API siano presenti
if not os.getenv("OPENAI_API_KEY"):
    print("ERRORE: Chiave API di OpenAI non trovata nel file .env")
    exit(1)

# Verifica e inizializza connessione Supabase
try:
    # Ottieni credenziali Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERRORE: Credenziali Supabase non trovate nel file .env")
        exit(1)
    
    # Inizializza il client Supabase
    supabase: Client = create_client(supabase_url, supabase_key)
    print(f"Connessione a Supabase stabilita: {supabase_url}")
except Exception as e:
    print(f"ERRORE: Impossibile connettersi a Supabase: {str(e)}")
    exit(1)

# Inizializza il client OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Inizializza l'app FastAPI
app = FastAPI(title="Chatbot Pizzeria API")

# Definizione del modello per la richiesta di chat
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"

# Modello per la richiesta di login - AGGIUNTO PER DASHBOARD
class LoginRequest(BaseModel):
    username: str
    password: str

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

# Dizionario per memorizzare le conversazioni degli utenti
user_conversations = {}

# Lista di comandi per mostrare il menu
MENU_COMMANDS = ["mostra menu", "vedi menu", "menu", "il menu", "lista delle pizze", "lista pizza", "lista pizze", "mostrami il menu"]

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

# Classe per gestire il menu da Supabase
class MenuManager:
    def __init__(self, supabase_client):
        """Inizializza il gestore del menu con il client Supabase"""
        self.supabase = supabase_client
        self.menu_data = {}
        self.carica_menu()
    
    def carica_menu(self):
        """Carica i dati del menu da Supabase"""
        try:
            print("Caricamento menu da Supabase...")
            
            # Tentativo di eseguire una query di test per verificare la connessione
            self.supabase.table("menu_pizzeria").select("count").limit(1).execute()
            print("Connessione a Supabase verificata con successo")
            
            # Recupera i prodotti dal menu_pizzeria
            response = self.supabase.table("menu_pizzeria").select("*").execute()
            prodotti = response.data
            
            if not prodotti:
                print("Nessun prodotto trovato nel database Supabase")
                self.menu_data = {}
                return
                
            # Prepara la struttura del menu
            self.menu_data = {}
            
            # Organizza i prodotti per categoria
            for prodotto in prodotti:
                categoria = prodotto.get('categoria', 'Altro')
                
                # Crea la categoria se non esiste
                if categoria not in self.menu_data:
                    self.menu_data[categoria] = {}
                
                # Aggiungi il prodotto alla categoria
                nome_prodotto = prodotto.get('nome', '')
                if nome_prodotto:
                    self.menu_data[categoria][nome_prodotto] = {
                        "price": prodotto.get('prezzo', 0),
                        "description": prodotto.get('descrizione', '')
                    }
            
            # Verifica se il menu è vuoto
            if not self.menu_data or all(len(items) == 0 for items in self.menu_data.values()):
                print("Menu vuoto o formato non valido")
                self.menu_data = {}
                return
                
            print(f"Menu caricato con successo: {len(self.menu_data)} categorie")
            self._debug_print_menu_data()
            
        except Exception as e:
            print(f"Errore nel caricamento del menu da Supabase: {str(e)}")
            # In caso di errore, inizializza con un menu vuoto
            self.menu_data = {}
    
    def _debug_print_menu_data(self):
        """Stampa i dati del menu per debug"""
        print("\nDEBUG - Dati estratti dal menu:")
        for section, items in self.menu_data.items():
            print(f"Sezione: {section}")
            for item, details in items.items():
                print(f"  - {item}: €{details['price']:.2f}")
        print()
    
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
    
    def extract_price_from_text(self, text):
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

    def get_ingredienti(self, item_name):
        """
        Restituisce gli ingredienti di un prodotto se disponibili
        """
        item_name_lower = item_name.lower()
        
        for section_items in self.menu_data.values():
            for menu_item, details in section_items.items():
                if item_name_lower in menu_item.lower():
                    if details["description"]:
                        return f"La {menu_item} contiene: {details['description']}"
                    else:
                        return f"Mi dispiace, non abbiamo informazioni dettagliate sugli ingredienti della {menu_item}."
        
        return f"Mi dispiace, non abbiamo '{item_name}' nel nostro menu."
    
    def query_menu(self, query_text):
        """
        Gestisce query relative al menu usando il database locale
        """
        query_lower = query_text.lower()
        
        # Controlla se è una domanda su prezzo
        price_keywords = ["prezzo", "costa", "quanto", "costo", "euro", "€"]
        is_price_query = any(keyword in query_lower for keyword in price_keywords)
        
        # Controlla se è una domanda sugli ingredienti
        ingredient_keywords = ["ingredienti", "contiene", "allergeni", "fatto", "composto"]
        is_ingredient_query = any(keyword in query_lower for keyword in ingredient_keywords)
        
        # Estrai possibile nome prodotto
        item_name = self.extract_item_name(query_text)
        
        if is_price_query and item_name:
            # Estrai possibile prezzo menzionato
            mentioned_price = self.extract_price_from_text(query_text)
            exists, _, message = self.verify_item(item_name, mentioned_price)
            return message
        
        elif is_ingredient_query and item_name:
            return self.get_ingredienti(item_name)
        
        elif "menu" in query_lower or "lista" in query_lower:
            return self.format_menu_section()
        
        # Per altre domande generiche sul menu
        for section_name in self.menu_data.keys():
            if section_name.lower() in query_lower:
                return self.format_menu_section(section_name)
        
        # Risposta generica se non abbiamo capito la domanda
        return "Posso darle informazioni sui nostri piatti, prezzi e ingredienti. Cosa vuole sapere esattamente?"

# Inizializza il gestore del menu passando il client Supabase
try:
    menu_manager = MenuManager(supabase)
    print("Menu inizializzato correttamente")
except Exception as e:
    print(f"Errore durante l'inizializzazione del menu: {str(e)}")
    exit(1)

# Inizializza il gestore degli ordini passando il menu_manager
try:
    gestore_ordine = GestoreOrdine(menu_index=menu_manager)
    print("Gestore ordini inizializzato correttamente")
    # Debug - Verifica che menu_index sia stato passato correttamente
    print(f"DEBUG - menu_index.menu_data presente in gestore_ordine: {hasattr(gestore_ordine, 'menu_index') and hasattr(gestore_ordine.menu_index, 'menu_data')}")
except Exception as e:
    print(f"Errore durante l'inizializzazione del gestore ordini: {str(e)}")
    # Prova a inizializzare senza menu_manager in caso di errore
    gestore_ordine = GestoreOrdine()
    print("Gestore ordini inizializzato in modalità fallback")

# Route per servire il file login.html come pagina principale
@app.get("/")
async def get_login():
    return FileResponse("static/login.html")

# Route per servire il file index.html
@app.get("/index.html")
async def get_index():
    return FileResponse("static/index.html")

# Route per servire il file dashboard.html
@app.get("/dashboard.html") 
async def get_dashboard():
    return FileResponse("static/dashboard.html")

# API endpoint per gestire le richieste di chat
@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        user_message = request.message
        user_id = request.user_id
        
        # Debug - Informazioni sulla richiesta
        print(f"DEBUG - Richiesta ricevuta: user_id={user_id}, messaggio='{user_message}'")
        print(f"DEBUG - Conversazione esistente: {user_id in user_conversations}")
        
        # Inizializza la conversazione se è un nuovo utente
        if user_id not in user_conversations:
            # Ottieni il menu per includerlo nel messaggio di benvenuto
            menu_text = menu_manager.format_menu_section()
            welcome_with_menu = f"Buonasera, pizzeria da Mario! Ecco il nostro menu:\n\n{menu_text}\n\nChe pizza desidera ordinare?"
            
            user_conversations[user_id] = [
                {"role": "assistant", "content": welcome_with_menu}
            ]
            
            # Se è un nuovo utente, avvia automaticamente un nuovo ordine
            gestore_ordine.inizia_nuovo_ordine(user_id)
            print(f"Nuovo utente: {user_id} - Inizializzato nuovo ordine e mostrato menu")
            
            # Per un nuovo utente o messaggio vuoto, restituisci il messaggio di benvenuto
            if not user_message:
                return JSONResponse({"response": welcome_with_menu})
        
        # Aggiungi il messaggio dell'utente alla conversazione
        user_conversations[user_id].append({"role": "user", "content": user_message})
        
        # Verifica prioritariamente se è una richiesta di menu
        if any(cmd in user_message.lower() for cmd in MENU_COMMANDS):
            # Mostra il menu completo
            menu_text = menu_manager.format_menu_section()
            response_text = f"Ecco il nostro menu:\n\n{menu_text}\n\nChe pizza desidera ordinare?"
            print("Richiesta menu rilevata")
        else:
            # Se il messaggio è vuoto, fornisci un messaggio di benvenuto invece di elaborarlo
            if not user_message:
                response_text = welcome_with_menu
                print("Messaggio vuoto rilevato, inviando messaggio di benvenuto")
            else:
                # Altrimenti, gestisci con il gestore ordini
                response_text = gestore_ordine.gestisci_messaggio(user_id, user_message)
                
                # Debug - Risposta dal gestore_ordine
                print(f"DEBUG - Risposta dal gestore_ordine: '{response_text}'")
                
                # Se il gestore ordini richiede di mostrare il menu
                if response_text == "MOSTRA_MENU":
                    menu_text = menu_manager.format_menu_section()
                    response_text = f"Ecco il nostro menu:\n\n{menu_text}\n\nChe pizza desidera ordinare?"
                    print("Richiesta menu da gestore ordini")
                # Se non è un messaggio relativo all'ordine, controlla prima se è una domanda sul menu
                elif response_text == "FALLBACK":
                    print("Fallback attivato - Controllo query sul menu")
                    # Controlla se l'utente sta chiedendo informazioni sul menu
                    menu_keywords = ["carta", "prezzo", "costa", "quanto", "ingredienti", "disponibile", "offrite"]
                    is_menu_query = any(keyword in user_message.lower() for keyword in menu_keywords)
                    
                    # Gestisci le domande sul menu
                    if is_menu_query:
                        try:
                            response_text = menu_manager.query_menu(user_message)
                            print("Query sul menu elaborata")
                        except Exception as e:
                            print(f"Errore nell'elaborazione della query sul menu: {str(e)}")
                            response_text = "Mi scusi, al momento non riesco a trovare queste informazioni. Posso aiutarla con un ordine?"
                    # Altrimenti usa il fallback generico
                    else:
                        print("Utilizzo risposta generica da ChatGPT")
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

# =====================================================================
# AGGIUNTA PER L'INTEGRAZIONE CON LA DASHBOARD E LOGIN
# =====================================================================

# Endpoint per l'autenticazione
@app.post("/api/login")
async def login(request: LoginRequest):
    """
    Endpoint di autenticazione
    Controlla le credenziali e restituisce un token di successo o un errore
    """
    # Simulazione di autenticazione come nella demo
    if request.username == "Ciao" and request.password == "12345678":
        return {"success": True, "token": "demo-token-123456"}
    else:
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": "Credenziali non valide"}
        )

# Endpoint per ottenere le statistiche della dashboard
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """
    Ottiene le statistiche per la dashboard dalle tabelle Supabase
    """
    try:
        # Verifica se le tabelle esistono
        try:
            # Verifica tabella comande
            debug_response = supabase.table("comande").select("count").limit(1).execute()
            print(f"Debug tabella comande: {debug_response}")
            
            # Verifica tabella clienti
            clients_debug = supabase.table("clienti").select("count").limit(1).execute()
            print(f"Debug tabella clienti: {clients_debug}")
        except Exception as debug_error:
            print(f"Errore debug tabelle: {str(debug_error)}")
            return {
                "success": True,
                "data": {
                    "total_orders": 0,
                    "total_revenue": 0,
                    "avg_order": 0,
                    "top_pizza": "-",
                    "recent_orders": [],
                    "pizza_chart_data": [],
                    "sales_chart_data": []
                },
                "debug_info": f"Errore accesso tabelle: {str(debug_error)}"
            }

        # Ottieni le comande senza ordinamento (per evitare errori di sintassi)
        response = supabase.table("comande").select("*").execute()
        print(f"Risposta query comande: {len(response.data) if response.data else 0} righe")
        
        if not response.data:
            print("Nessun dato trovato nella tabella comande")
            return {
                "success": True,
                "data": {
                    "total_orders": 0,
                    "total_revenue": 0,
                    "avg_order": 0,
                    "top_pizza": "-",
                    "recent_orders": [],
                    "pizza_chart_data": [],
                    "sales_chart_data": []
                }
            }
        
        # Ottieni i dati e ordina manualmente
        orders = response.data
        
        # Ordina manualmente per data decrescente se c'è un campo 'data'
        if orders and len(orders) > 0 and 'data' in orders[0]:
            orders.sort(key=lambda x: x.get('data', ''), reverse=True)
        
        # Recupera i dati clienti
        client_info = {}
        try:
            client_response = supabase.table("clienti").select("*").execute()
            if client_response.data:
                for client in client_response.data:
                    # Usa il telefono come chiave per abbinare clienti e comande
                    telefono = client.get('telefono')
                    if telefono:
                        client_info[telefono] = client
                print(f"Recuperati {len(client_info)} clienti")
        except Exception as client_error:
            print(f"Errore nel recupero dei clienti: {str(client_error)}")
        
        # Calcola statistiche
        total_orders = len(orders)
        total_revenue = 0
        
        # Prepara i dati per i grafici e la tabella
        pizza_count = {}
        sales_by_date = {}
        
        # Elabora ogni comanda
        for order in orders:
            try:
                # Calcola il totale
                order_total = 0
                if 'totale' in order and order['totale'] is not None:
                    try:
                        order_total = float(order['totale'])
                        total_revenue += order_total
                    except (ValueError, TypeError):
                        print(f"Errore nel convertire il totale: {order.get('totale')}")
                
                # Estrai la data per il grafico vendite
                order_date = order.get('data', '')
                if order_date:
                    date_str = order_date.split('T')[0] if 'T' in order_date else order_date
                    if date_str in sales_by_date:
                        sales_by_date[date_str] += order_total
                    else:
                        sales_by_date[date_str] = order_total
                
                # Estrai le pizze/prodotti
                # Prima verifica se abbiamo 'pizze' come JSON o come stringa
                if 'pizze' in order:
                    pizze = order['pizze']
                    if isinstance(pizze, list):
                        for pizza_item in pizze:
                            if isinstance(pizza_item, dict) and 'nome' in pizza_item:
                                pizza_name = pizza_item['nome']
                                pizza_count[pizza_name] = pizza_count.get(pizza_name, 0) + 1
                    elif isinstance(pizze, str):
                        pizza_names = [p.strip() for p in pizze.split(',') if p.strip()]
                        for pizza_name in pizza_names:
                            pizza_count[pizza_name] = pizza_count.get(pizza_name, 0) + 1
                
                # Arricchisci l'ordine con info cliente
                if 'telefono_cliente' in order and order['telefono_cliente'] in client_info:
                    client = client_info[order['telefono_cliente']]
                    order['cliente'] = client.get('nome', order.get('nome_cliente', '-'))
                else:
                    order['cliente'] = order.get('nome_cliente', '-')
                
                # Formatta i campi per la dashboard
                if 'data_ordine' not in order and 'data' in order:
                    order['data_ordine'] = order['data']
                
                # Crea un campo prodotti se non esiste
                if 'prodotti' not in order:
                    prodotti = []
                    # Aggiungi pizze
                    if 'pizze' in order and order['pizze']:
                        if isinstance(order['pizze'], list):
                            for p in order['pizze']:
                                if isinstance(p, dict) and 'nome' in p:
                                    prodotti.append(p['nome'])
                        elif isinstance(order['pizze'], str):
                            prodotti.extend([p.strip() for p in order['pizze'].split(',') if p.strip()])
                    
                    # Aggiungi fritti se presenti
                    if 'fritti' in order and order['fritti']:
                        if isinstance(order['fritti'], list):
                            for f in order['fritti']:
                                if isinstance(f, dict) and 'nome' in f:
                                    prodotti.append(f['nome'])
                        elif isinstance(order['fritti'], str):
                            prodotti.extend([f.strip() for f in order['fritti'].split(',') if f.strip()])
                    
                    # Aggiungi bevande se presenti
                    if 'bevande' in order and order['bevande']:
                        if isinstance(order['bevande'], list):
                            for b in order['bevande']:
                                if isinstance(b, dict) and 'nome' in b:
                                    prodotti.append(b['nome'])
                        elif isinstance(order['bevande'], str):
                            prodotti.extend([b.strip() for b in order['bevande'].split(',') if b.strip()])
                    
                    order['prodotti'] = ', '.join(prodotti)
                
                # Aggiungi stato se non è presente
                if 'stato' not in order:
                    order['stato'] = 'Completato'  # Stato predefinito
            
            except Exception as process_error:
                print(f"Errore nell'elaborazione della comanda {order.get('comanda_id', 'unknown')}: {str(process_error)}")
        
        # Calcola la media
        avg_order = total_revenue / total_orders if total_orders > 0 else 0
        
        # Determina la pizza più venduta
        top_pizza = "-"
        if pizza_count:
            top_pizza_items = sorted(pizza_count.items(), key=lambda x: x[1], reverse=True)
            if top_pizza_items:
                top_pizza = top_pizza_items[0][0]
        
        # Dati per i grafici
        pizza_chart_data = [{"name": name, "value": count} for name, count in pizza_count.items()]
        sales_chart_data = [{"date": date, "amount": amount} for date, amount in sales_by_date.items()]
        
        # Ordini recenti
        recent_orders = orders[:min(10, len(orders))]
        
        # Invece di usare HTTPException che può causare problemi di formato,
        # restituiamo sempre una risposta JSON valida
        return {
            "success": True,
            "data": {
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "avg_order": avg_order,
                "top_pizza": top_pizza,
                "recent_orders": recent_orders,
                "pizza_chart_data": pizza_chart_data,
                "sales_chart_data": sales_chart_data
            }
        }
    
    except Exception as e:
        print(f"Errore nel recupero delle statistiche: {str(e)}")
        # Anche in caso di errore, restituisci un JSON valido
        return {
            "success": False,
            "error": str(e),
            "data": {
                "total_orders": 0,
                "total_revenue": 0,
                "avg_order": 0,
                "top_pizza": "-",
                "recent_orders": [],
                "pizza_chart_data": [],
                "sales_chart_data": []
            }
        }

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