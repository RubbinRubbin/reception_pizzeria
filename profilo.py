import os
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

def crea_comanda_txt(user_id: str, ordine: Dict) -> None:
    """
    Salva i dati dell'ordine nel database Supabase con formato ordinato per la stampa
    
    Args:
        user_id: ID utente
        ordine: Dizionario dell'ordine
    """
    # Ottieni l'ID comanda
    comanda_id = ordine["comanda_id"]
    
    # Prepara i prodotti in formato JSONB per il database
    pizze_json = _prepara_prodotti_json(ordine["pizze"])
    fritti_json = _prepara_prodotti_json(ordine["fritti"])
    bevande_json = _prepara_prodotti_json(ordine["bevande"])
    
    # Prepara i dati della comanda per il database
    comanda_data = {
        "comanda_id": comanda_id,
        "user_id": user_id,
        "data": datetime.now().strftime('%Y-%m-%d'),
        "ora": datetime.now().strftime('%H:%M:%S'),
        "orario_consegna": ordine['orario_consegna'],
        "nome_cliente": ordine['cliente']['nome'],
        "telefono_cliente": ordine['cliente']['telefono'],
        "indirizzo_cliente": ordine['cliente']['indirizzo'],
        "metodo_pagamento": ordine['pagamento'],
        "totale": ordine['totale'],
        "pizze": pizze_json,
        "fritti": fritti_json,
        "bevande": bevande_json
    }
    
    # Salva la comanda nella tabella "comande"
    response = supabase.table("comande").insert(comanda_data).execute()

def _prepara_prodotti_json(prodotti: List[Dict]) -> List[Dict]:
    """
    Prepara i prodotti in formato JSON per il database
    
    Args:
        prodotti: Lista di prodotti
        
    Returns:
        Lista di dizionari con formato adatto per JSON
    """
    # Utilizza _conta_prodotti per raggruppare e contare
    conteggio = _conta_prodotti(prodotti)
    
    # Converte in formato JSON per il database
    risultato = []
    for nome, (quantita, prezzo) in conteggio.items():
        risultato.append({
            "nome": nome,
            "prezzo": prezzo,
            "quantita": quantita
        })
    
    # Ordina per nome prodotto per avere un formato consistente
    return sorted(risultato, key=lambda x: x["nome"])

def formatta_comanda_per_stampa(comanda_id: str) -> str:
    """
    Formatta una comanda per la stampa
    
    Args:
        comanda_id: ID della comanda da formattare
        
    Returns:
        String con la comanda formattata pronta per la stampa
    """
    # Recupera i dati della comanda
    response = supabase.table("comande").select("*").eq("comanda_id", comanda_id).execute()
    
    if not response.data or len(response.data) == 0:
        return "Comanda non trovata."
    
    comanda = response.data[0]
    
    # Costruisci il contenuto formattato
    contenuto = []
    contenuto.append("=" * 50)
    contenuto.append(f"ORDINE #{comanda['comanda_id']}")
    contenuto.append("=" * 50)
    contenuto.append(f"Data: {comanda['data']}")
    contenuto.append(f"Ora: {comanda['ora']}")
    contenuto.append(f"Orario consegna: {comanda['orario_consegna']}")
    contenuto.append("-" * 50)
    
    # Informazioni cliente
    contenuto.append("INFORMAZIONI CLIENTE:")
    contenuto.append(f"Nome: {comanda['nome_cliente']}")
    contenuto.append(f"Telefono: {comanda['telefono_cliente']}")
    contenuto.append(f"Indirizzo: {comanda['indirizzo_cliente']}")
    contenuto.append(f"Metodo pagamento: {comanda['metodo_pagamento']}")
    contenuto.append("-" * 50)
    
    # Prodotti ordinati
    contenuto.append("PRODOTTI ORDINATI:")
    
    # Pizze
    pizze = comanda.get("pizze", [])
    if pizze:
        contenuto.append("\nPIZZE:")
        for pizza in pizze:
            prezzo = float(pizza["prezzo"]) if isinstance(pizza["prezzo"], str) else pizza["prezzo"]
            quantita = int(pizza["quantita"])
            contenuto.append(f"  {quantita}x {pizza['nome']:<20} {prezzo:.2f}€/cad = {quantita * prezzo:.2f}€")
    
    # Fritti
    fritti = comanda.get("fritti", [])
    if fritti:
        contenuto.append("\nFRITTI:")
        for fritto in fritti:
            prezzo = float(fritto["prezzo"]) if isinstance(fritto["prezzo"], str) else fritto["prezzo"]
            quantita = int(fritto["quantita"])
            contenuto.append(f"  {quantita}x {fritto['nome']:<20} {prezzo:.2f}€/cad = {quantita * prezzo:.2f}€")
    
    # Bevande
    bevande = comanda.get("bevande", [])
    if bevande:
        contenuto.append("\nBEVANDE:")
        for bevanda in bevande:
            prezzo = float(bevanda["prezzo"]) if isinstance(bevanda["prezzo"], str) else bevanda["prezzo"]
            quantita = int(bevanda["quantita"])
            contenuto.append(f"  {quantita}x {bevanda['nome']:<20} {prezzo:.2f}€/cad = {quantita * prezzo:.2f}€")
    
    contenuto.append("-" * 50)
    contenuto.append(f"TOTALE: {float(comanda['totale']):.2f}€")
    contenuto.append("=" * 50)
    
    return "\n".join(contenuto)

def aggiorna_profilo_cliente(user_id: str, info_cliente: Dict) -> None:
    """
    Aggiorna o crea il profilo del cliente nel database Supabase
    
    Args:
        user_id: ID utente
        info_cliente: Informazioni del cliente (nome, telefono, indirizzo)
    """
    # Prepara i dati del cliente
    cliente_data = {
        "user_id": user_id,
        "nome": info_cliente['nome'],
        "telefono": info_cliente['telefono'],
        "indirizzo": info_cliente['indirizzo'],
        "ultimo_aggiornamento": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Verifica se il cliente esiste già (usando il telefono come chiave)
    response = supabase.table("clienti").select("*").eq("telefono", info_cliente['telefono']).execute()
    
    if response.data and len(response.data) > 0:
        # Cliente esistente, aggiorna i dati
        cliente_id = response.data[0]['id']  # Assumiamo che 'id' sia la chiave primaria
        supabase.table("clienti").update(cliente_data).eq("id", cliente_id).execute()
    else:
        # Nuovo cliente, inserisci i dati
        supabase.table("clienti").insert(cliente_data).execute()

def aggiorna_file_clienti(info_cliente: Dict) -> None:
    """
    Questa funzione non fa nulla - mantenuta solo per compatibilità con ordine.py
    Tutti i dati del cliente vengono gestiti in aggiorna_profilo_cliente
    
    Args:
        info_cliente: Informazioni del cliente (nome, telefono, indirizzo)
    """
    # Non fa nulla - i dati sono già salvati in Supabase
    pass

def _conta_prodotti(prodotti: List[Dict]) -> Dict[str, tuple]:
    """
    Conta i prodotti raggruppandoli per nome
    
    Args:
        prodotti: Lista di prodotti
        
    Returns:
        Dizionario con conteggio e prezzo per ogni prodotto
    """
    conteggio = {}
    for prodotto in prodotti:
        nome = prodotto["nome"]
        prezzo = prodotto["prezzo"]
        
        if nome in conteggio:
            conteggio[nome] = (conteggio[nome][0] + 1, prezzo)
        else:
            conteggio[nome] = (1, prezzo)
    
    return conteggio

def cerca_comande_cliente(telefono: str) -> List[Dict]:
    """
    Cerca tutte le comande di un cliente utilizzando il numero di telefono
    
    Args:
        telefono: Numero di telefono del cliente
        
    Returns:
        Lista delle comande del cliente
    """
    response = supabase.table("comande").select("*").eq("telefono_cliente", telefono).order("data", desc=True).execute()
    return response.data

# ===== FUNZIONI PER LA DASHBOARD =====

def ottieni_comande_dashboard(filtro: str = "tutte") -> List[Dict]:
    """
    Ottiene le comande formattate per la dashboard
    
    Args:
        filtro: Filtro da applicare ('tutte', 'oggi', 'in_corso', 'completate', 'future')
        
    Returns:
        Lista di comande formattate per la dashboard
    """
    # Determina gli stati delle comande per il filtro e l'ordinamento
    oggi = date.today().strftime('%Y-%m-%d')
    ora = datetime.now().strftime('%H:%M:%S')
    
    # Query base per recuperare le comande
    query = supabase.table("comande").select("*")
    
    # Applica i filtri
    if filtro == "oggi":
        query = query.eq("data", oggi)
    elif filtro == "in_corso":
        query = query.eq("data", oggi).lt("orario_consegna", (datetime.now() + timedelta(hours=2)).strftime('%H:%M:%S'))
    elif filtro == "completate":
        query = query.eq("data", oggi).lt("ora", ora)
    elif filtro == "future":
        query = query.gt("data", oggi)
    
    # Ordina per data e ora
    query = query.order("data", desc=True).order("ora", desc=True)
    
    # Esegui la query
    response = query.execute()
    
    if not response.data:
        return []
    
    # Arricchisci i dati per la dashboard
    comande_formattate = []
    for comanda in response.data:
        # Determina lo stato della comanda
        data_comanda = comanda.get('data', '')
        ora_comanda = comanda.get('ora', '')
        orario_consegna = comanda.get('orario_consegna', '')
        
        if data_comanda == oggi and orario_consegna > ora:
            stato = "in_corso"
        elif data_comanda == oggi and orario_consegna <= ora:
            stato = "completato"
        elif data_comanda > oggi:
            stato = "futuro"
        else:
            stato = "storico"
        
        # Aggiungi il campo stato
        comanda['stato'] = stato
        
        # Calcola il totale delle pizze, fritti e bevande
        comanda['num_pizze'] = len(comanda.get('pizze', []))
        comanda['num_fritti'] = len(comanda.get('fritti', []))
        comanda['num_bevande'] = len(comanda.get('bevande', []))
        
        # Aggiungi il totale dei prodotti
        comanda['num_prodotti'] = comanda['num_pizze'] + comanda['num_fritti'] + comanda['num_bevande']
        
        # Aggiungi la comanda formattata alla lista
        comande_formattate.append(comanda)
    
    return comande_formattate

def ottieni_dettaglio_comanda_dashboard(comanda_id: str) -> Dict:
    """
    Ottiene i dettagli formattati di una singola comanda per la dashboard
    
    Args:
        comanda_id: ID della comanda
        
    Returns:
        Dizionario con dettagli formattati della comanda
    """
    response = supabase.table("comande").select("*").eq("comanda_id", comanda_id).execute()
    
    if not response.data or len(response.data) == 0:
        return {"errore": "Comanda non trovata"}
    
    comanda = response.data[0]
    
    # Formato HTML per la stampa
    html_formattato = f"""
    <div class="comanda-container">
        <div class="comanda-header">
            <h2>ORDINE #{comanda['comanda_id']}</h2>
            <div class="comanda-info">
                <p><strong>Data:</strong> {comanda['data']}</p>
                <p><strong>Ora:</strong> {comanda['ora']}</p>
                <p><strong>Consegna:</strong> {comanda['orario_consegna']}</p>
            </div>
        </div>
        
        <div class="cliente-info">
            <h3>INFORMAZIONI CLIENTE</h3>
            <p><strong>Nome:</strong> {comanda['nome_cliente']}</p>
            <p><strong>Telefono:</strong> {comanda['telefono_cliente']}</p>
            <p><strong>Indirizzo:</strong> {comanda['indirizzo_cliente']}</p>
            <p><strong>Metodo pagamento:</strong> {comanda['metodo_pagamento']}</p>
        </div>
        
        <div class="prodotti-ordinati">
            <h3>PRODOTTI ORDINATI</h3>
    """
    
    # Aggiungi le pizze
    pizze = comanda.get("pizze", [])
    if pizze:
        html_formattato += "<div class='categoria-prodotti'><h4>PIZZE</h4><ul>"
        for pizza in pizze:
            prezzo = float(pizza["prezzo"]) if isinstance(pizza["prezzo"], str) else pizza["prezzo"]
            quantita = int(pizza["quantita"])
            html_formattato += f"<li>{quantita}x {pizza['nome']} - {prezzo:.2f}€/cad = {quantita * prezzo:.2f}€</li>"
        html_formattato += "</ul></div>"
    
    # Aggiungi i fritti
    fritti = comanda.get("fritti", [])
    if fritti:
        html_formattato += "<div class='categoria-prodotti'><h4>FRITTI</h4><ul>"
        for fritto in fritti:
            prezzo = float(fritto["prezzo"]) if isinstance(fritto["prezzo"], str) else fritto["prezzo"]
            quantita = int(fritto["quantita"])
            html_formattato += f"<li>{quantita}x {fritto['nome']} - {prezzo:.2f}€/cad = {quantita * prezzo:.2f}€</li>"
        html_formattato += "</ul></div>"
    
    # Aggiungi le bevande
    bevande = comanda.get("bevande", [])
    if bevande:
        html_formattato += "<div class='categoria-prodotti'><h4>BEVANDE</h4><ul>"
        for bevanda in bevande:
            prezzo = float(bevanda["prezzo"]) if isinstance(bevanda["prezzo"], str) else bevanda["prezzo"]
            quantita = int(bevanda["quantita"])
            html_formattato += f"<li>{quantita}x {bevanda['nome']} - {prezzo:.2f}€/cad = {quantita * prezzo:.2f}€</li>"
        html_formattato += "</ul></div>"
    
    # Chiusura e totale
    html_formattato += f"""
        </div>
        
        <div class="comanda-footer">
            <h3>TOTALE: {float(comanda['totale']):.2f}€</h3>
        </div>
    </div>
    """
    
    # Aggiungi sia la versione HTML che i dati originali
    return {
        "dati": comanda,
        "html": html_formattato,
        "testo": formatta_comanda_per_stampa(comanda_id)
    }

def ottieni_statistiche_giornaliere() -> Dict:
    """
    Ottiene le statistiche giornaliere per la dashboard
    
    Returns:
        Dizionario con statistiche giornaliere
    """
    oggi = date.today().strftime('%Y-%m-%d')
    
    # Statistiche comande di oggi
    response_oggi = supabase.table("comande").select("*").eq("data", oggi).execute()
    comande_oggi = response_oggi.data if response_oggi.data else []
    
    # Statistiche ultime 24 ore
    ieri = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    response_24h = supabase.table("comande").select("*").gte("timestamp_creazione", ieri).execute()
    comande_24h = response_24h.data if response_24h.data else []
    
    # Calcolo statistiche
    totale_oggi = sum(float(c['totale']) for c in comande_oggi)
    num_comande_oggi = len(comande_oggi)
    
    totale_24h = sum(float(c['totale']) for c in comande_24h)
    num_comande_24h = len(comande_24h)
    
    # Calcolo prodotti più venduti oggi
    prodotti_conteggio = {}
    
    for comanda in comande_oggi:
        # Conta pizze
        for pizza in comanda.get('pizze', []):
            nome = pizza.get('nome', '')
            quantita = int(pizza.get('quantita', 0))
            if nome in prodotti_conteggio:
                prodotti_conteggio[nome] += quantita
            else:
                prodotti_conteggio[nome] = quantita
        
        # Conta fritti
        for fritto in comanda.get('fritti', []):
            nome = fritto.get('nome', '')
            quantita = int(fritto.get('quantita', 0))
            if nome in prodotti_conteggio:
                prodotti_conteggio[nome] += quantita
            else:
                prodotti_conteggio[nome] = quantita
        
        # Conta bevande
        for bevanda in comanda.get('bevande', []):
            nome = bevanda.get('nome', '')
            quantita = int(bevanda.get('quantita', 0))
            if nome in prodotti_conteggio:
                prodotti_conteggio[nome] += quantita
            else:
                prodotti_conteggio[nome] = quantita
    
    # Ordina per quantità
    prodotti_ordinati = sorted(
        [{"nome": k, "quantita": v} for k, v in prodotti_conteggio.items()],
        key=lambda x: x["quantita"],
        reverse=True
    )
    
    return {
        "totale_oggi": totale_oggi,
        "num_comande_oggi": num_comande_oggi,
        "totale_24h": totale_24h,
        "num_comande_24h": num_comande_24h,
        "prodotti_piu_venduti": prodotti_ordinati[:5]  # Top 5 prodotti
    }