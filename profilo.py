import os
import re
from datetime import datetime
from typing import Dict, List

def crea_comanda_txt(user_id: str, ordine: Dict) -> None:
    """
    Aggiunge i dati dell'ordine al file comanda.txt esistente
    
    Args:
        user_id: ID utente
        ordine: Dizionario dell'ordine
    """
    # Percorso del file comanda.txt esistente
    comande_path = "C:\\Users\\rubbi\\Desktop\\LAVORO\\AI\\reception_pizzeria\\comande"
    file_path = os.path.join(comande_path, "comanda.txt")
    
    # Assicurati che la directory esista
    if not os.path.exists(comande_path):
        os.makedirs(comande_path)
    
    # Usa l'ID comanda già generato in ordine.py
    comanda_id = ordine["comanda_id"]
    
    # Conteggio prodotti per tipo
    conteggio_pizze = _conta_prodotti(ordine["pizze"])
    conteggio_fritti = _conta_prodotti(ordine["fritti"])
    conteggio_bevande = _conta_prodotti(ordine["bevande"])
    
    # Costruisci il contenuto da aggiungere alla comanda
    contenuto = []
    contenuto.append("\n" + "=" * 50)  # Separatore tra comande
    contenuto.append(f"NUOVO ORDINE #{comanda_id}")
    contenuto.append("=" * 50)
    contenuto.append(f"Data: {datetime.now().strftime('%d/%m/%Y')}")
    contenuto.append(f"Ora: {datetime.now().strftime('%H:%M:%S')}")
    contenuto.append(f"Orario consegna: {ordine['orario_consegna']}")
    contenuto.append("-" * 50)
    
    # Informazioni cliente
    contenuto.append("INFORMAZIONI CLIENTE:")
    contenuto.append(f"Nome: {ordine['cliente']['nome']}")
    contenuto.append(f"Telefono: {ordine['cliente']['telefono']}")
    contenuto.append(f"Indirizzo: {ordine['cliente']['indirizzo']}")
    contenuto.append(f"Metodo pagamento: {ordine['pagamento']}")
    contenuto.append("-" * 50)
    
    # Prodotti ordinati
    contenuto.append("PRODOTTI ORDINATI:")
    
    # Pizze
    if conteggio_pizze:
        contenuto.append("\nPIZZE:")
        for pizza, (quantita, prezzo) in conteggio_pizze.items():
            contenuto.append(f"  {quantita}x {pizza:<20} {prezzo:.2f}€/cad = {quantita * prezzo:.2f}€")
    
    # Fritti
    if conteggio_fritti:
        contenuto.append("\nFRITTI:")
        for fritto, (quantita, prezzo) in conteggio_fritti.items():
            contenuto.append(f"  {quantita}x {fritto:<20} {prezzo:.2f}€/cad = {quantita * prezzo:.2f}€")
    
    # Bevande
    if conteggio_bevande:
        contenuto.append("\nBEVANDE:")
        for bevanda, (quantita, prezzo) in conteggio_bevande.items():
            contenuto.append(f"  {quantita}x {bevanda:<20} {prezzo:.2f}€/cad = {quantita * prezzo:.2f}€")
    
    contenuto.append("-" * 50)
    contenuto.append(f"TOTALE: {ordine['totale']:.2f}€")
    contenuto.append("=" * 50)
    
    # Apri il file in modalità append (a+) per aggiungere i dati
    # a+ crea il file se non esiste e lo apre in modalità append
    with open(file_path, "a+", encoding="utf-8") as f:
        f.write("\n".join(contenuto))

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

def _sanitizza_nome_file(nome: str) -> str:
    """
    Sanitizza il nome del cliente per renderlo utilizzabile come nome file
    
    Args:
        nome: Nome originale del cliente
        
    Returns:
        Nome sanitizzato utilizzabile come nome di file
    """
    # Rimuovi caratteri non validi nei nomi file
    nome_sanitizzato = re.sub(r'[\\/*?:"<>|]', '', nome)
    # Sostituisci spazi con underscore
    nome_sanitizzato = nome_sanitizzato.replace(' ', '_')
    # Limita la lunghezza massima
    if len(nome_sanitizzato) > 50:
        nome_sanitizzato = nome_sanitizzato[:50]
    # Se il nome è vuoto dopo la sanitizzazione, usa un default
    if not nome_sanitizzato:
        nome_sanitizzato = "cliente_sconosciuto"
    
    return nome_sanitizzato

def aggiorna_profilo_cliente(user_id: str, info_cliente: Dict) -> None:
    """
    Aggiorna o crea il profilo del cliente nel database clienti
    
    Args:
        user_id: ID utente
        info_cliente: Informazioni del cliente (nome, telefono, indirizzo)
    """
    # Percorso del database clienti
    db_path = "C:\\Users\\rubbi\\Desktop\\LAVORO\\AI\\reception_pizzeria\\clienti"
    
    # Assicurati che la directory esista
    if not os.path.exists(db_path):
        os.makedirs(db_path)
    
    # Ottieni il nome sanitizzato per il file
    nome_cliente = info_cliente['nome']
    nome_file = _sanitizza_nome_file(nome_cliente)
    
    # Crea o aggiorna il file del profilo cliente
    profile_path = os.path.join(db_path, f"cliente_{nome_file}.txt")
    
    # Costruisci il contenuto del profilo
    contenuto = []
    contenuto.append(f"ID Cliente: {user_id}")
    contenuto.append(f"Nome: {info_cliente['nome']}")
    contenuto.append(f"Telefono: {info_cliente['telefono']}")
    contenuto.append(f"Indirizzo: {info_cliente['indirizzo']}")
    contenuto.append(f"Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Scrivi il contenuto nel file
    with open(profile_path, "w", encoding="utf-8") as f:
        f.write("\n".join(contenuto))

def aggiorna_file_clienti(info_cliente: Dict) -> None:
    """
    Aggiunge o aggiorna le informazioni del cliente nel file clienti.txt condiviso
    
    Args:
        info_cliente: Informazioni del cliente (nome, telefono, indirizzo)
    """
    # Percorso del file clienti.txt
    file_path = "C:\\Users\\rubbi\\Desktop\\LAVORO\\AI\\reception_pizzeria\\clienti.txt"
    
    # Raccogli i dati del cliente
    nome = info_cliente['nome']
    telefono = info_cliente['telefono']
    indirizzo = info_cliente['indirizzo']
    data_aggiornamento = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    # Verifica se il file esiste e contiene già il cliente
    clienti_esistenti = {}
    cliente_presente = False
    index_cliente = 0
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                linee = f.readlines()
                
                # Parsa le informazioni esistenti
                i = 0
                while i < len(linee):
                    if linee[i].startswith("Telefono: "):
                        tel = linee[i].strip().replace("Telefono: ", "")
                        clienti_esistenti[tel] = i - 1  # Indice della riga del nome
                    i += 1
            
            # Controlla se il cliente è già presente
            if telefono in clienti_esistenti:
                cliente_presente = True
                index_cliente = clienti_esistenti[telefono]
        except Exception as e:
            print(f"Errore nella lettura del file clienti.txt: {str(e)}")
    
    # Prepara i dati da scrivere
    if cliente_presente:
        # Aggiorna il cliente esistente
        with open(file_path, "r", encoding="utf-8") as f:
            linee = f.readlines()
        
        # Aggiorna le informazioni del cliente
        linee[index_cliente] = f"Nome: {nome}\n"
        linee[index_cliente + 1] = f"Telefono: {telefono}\n"
        linee[index_cliente + 2] = f"Indirizzo: {indirizzo}\n"
        linee[index_cliente + 3] = f"Ultimo aggiornamento: {data_aggiornamento}\n"
        
        # Riscrivi il file
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(linee)
    else:
        # Aggiungi un nuovo cliente
        with open(file_path, "a+", encoding="utf-8") as f:
            # Se il file è vuoto o non esiste, aggiungi un'intestazione
            f.seek(0)
            contenuto = f.read()
            if not contenuto:
                f.write("# ELENCO CLIENTI PIZZERIA\n")
                f.write("# Formato: Nome, Telefono, Indirizzo, Data aggiornamento\n")
                f.write("#" + "=" * 70 + "\n\n")
            else:
                # Aggiungi un separatore se ci sono già clienti
                f.write("\n" + "-" * 50 + "\n")
            
            # Aggiungi il nuovo cliente
            f.write(f"Nome: {nome}\n")
            f.write(f"Telefono: {telefono}\n")
            f.write(f"Indirizzo: {indirizzo}\n")
            f.write(f"Ultimo aggiornamento: {data_aggiornamento}\n")