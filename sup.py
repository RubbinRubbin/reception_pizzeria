from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json
from datetime import datetime

# Carica le variabili d'ambiente dal file .env
load_dotenv()

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

# Modelli per le richieste
class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str

# Inizializza l'app API
app = FastAPI(title="Supabase Bridge API")

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, limita agli host consentiti
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Endpoint per il chatbot
@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Endpoint per il chatbot
    Riceve un messaggio e restituisce una risposta
    """
    message = request.message
    
    # Logica del chatbot (mantenuta uguale alla versione demo)
    response = ""
    if "menu" in message.lower():
        response = "## PIZZE CLASSICHE\n\n**Margherita** - €6.50\nPomodoro, mozzarella, basilico\n\n**Marinara** - €5.50\nPomodoro, aglio, origano\n\n**Napoli** - €7.50\nPomodoro, mozzarella, acciughe, origano\n\n---\n\n## PIZZE SPECIALI\n\n**Quattro Stagioni** - €9.00\nPomodoro, mozzarella, prosciutto, funghi, carciofi, olive\n\n**Diavola** - €8.50\nPomodoro, mozzarella, salame piccante"
    elif "margherita" in message.lower() and "prezzo" in message.lower():
        response = "La Margherita costa €6.50"
    elif "consegn" in message.lower():
        response = "Sì, effettuiamo consegne a domicilio tutti i giorni dalle 18:30 alle 22:30. È possibile ordinare chiamando il nostro numero o utilizzando l'app."
    elif "vegetarian" in message.lower():
        response = "Abbiamo diverse opzioni vegetariane nel nostro menu, tra cui la Margherita, la Quattro Formaggi, e la Ortolana con verdure di stagione."
    else:
        response = "Grazie per il suo messaggio. Come posso aiutarla con la nostra pizzeria?"
    
    return {"response": response}

# Endpoint per ottenere le statistiche della dashboard
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """
    Ottiene le statistiche per la dashboard dalle tabelle Supabase
    """
    try:
        # Ottieni le comande dalla vista vista_comande_dashboard
        response = supabase.table("vista_comande_dashboard").select("*").order("data_ordine", {"ascending": False}).execute()
        
        if not response.data:
            # Nessun dato trovato
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
        
        orders = response.data
        
        # Calcola statistiche
        total_orders = len(orders)
        total_revenue = sum(order.get('totale', 0) for order in orders)
        avg_order = total_revenue / total_orders if total_orders > 0 else 0
        
        # Conta le pizze più vendute
        pizza_count = {}
        for order in orders:
            products = order.get('prodotti', '')
            if isinstance(products, str):
                pizzas = products.split(',')
                for pizza in pizzas:
                    pizza = pizza.strip()
                    if pizza:
                        pizza_count[pizza] = pizza_count.get(pizza, 0) + 1
        
        # Trova la pizza più venduta
        top_pizza = "-"
        if pizza_count:
            top_pizza_items = sorted(pizza_count.items(), key=lambda x: x[1], reverse=True)
            if top_pizza_items:
                top_pizza = top_pizza_items[0][0]
        
        # Prepara dati per il grafico pizza
        pizza_chart_data = [{"name": pizza, "value": count} for pizza, count in pizza_count.items()]
        
        # Prepara dati per il grafico di vendite
        sales_by_date = {}
        for order in orders:
            date = order.get('data_ordine', '')
            if isinstance(date, str) and date:
                date = date.split('T')[0]  # Estrai solo la data (YYYY-MM-DD)
                sales_by_date[date] = sales_by_date.get(date, 0) + order.get('totale', 0)
        
        sales_chart_data = [{"date": date, "amount": amount} for date, amount in sales_by_date.items()]
        
        # Prepara l'elenco degli ordini recenti
        recent_orders = orders[:10]  # Prendi i primi 10 ordini
        
        # Ottieni informazioni aggiuntive dai clienti se necessario
        client_info = {}
        try:
            client_response = supabase.table("clienti").select("*").execute()
            if client_response.data:
                for client in client_response.data:
                    client_id = client.get('id')
                    if client_id:
                        client_info[client_id] = client
        except Exception as client_error:
            print(f"Errore nel recupero dei dati cliente: {str(client_error)}")
        
        # Restituisci i dati completi
        return {
            "success": True,
            "data": {
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "avg_order": avg_order,
                "top_pizza": top_pizza,
                "recent_orders": recent_orders,
                "pizza_chart_data": pizza_chart_data,
                "sales_chart_data": sales_chart_data,
                "client_info": client_info  # Informazioni aggiuntive sui clienti
            }
        }
    
    except Exception as e:
        print(f"Errore nel recupero delle statistiche: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore del server: {str(e)}")

# Se eseguito direttamente
if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  SUPABASE BRIDGE API SERVER")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=5000)