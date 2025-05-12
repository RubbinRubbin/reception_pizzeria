import re
from datetime import datetime, timedelta
from collections import Counter

# Importazioni da profilo.py
from profilo import crea_comanda_txt, aggiorna_profilo_cliente, aggiorna_file_clienti

class GestoreOrdine:
    """
    Classe per gestire la raccolta e l'elaborazione dei dati degli ordini
    """
    
    # Contatore statico per gli ID delle comande
    _contatore_id_comanda = 0
    
    @classmethod
    def _genera_id_comanda(cls):
        """
        Genera un nuovo ID comanda incrementando il contatore statico
        
        Returns:
            Stringa con l'ID numerico nel formato "000001"
        """
        cls._contatore_id_comanda += 1
        return f"{cls._contatore_id_comanda:06d}"
    
    def __init__(self, menu_index):
        """
        Inizializza un nuovo gestore ordini
        
        Args:
            menu_index: L'istanza MenuIndex per accedere alle informazioni sui prodotti
        """
        self.menu_index = menu_index
        self.ordini_attivi = {}  # user_id -> ordine
        self.orari_prenotati = {}  # slot_orario -> conteggio prenotazioni
        
        # Inizializzazione degli orari prenotati
        # In una versione più completa, potrebbe recuperare questi dati da Supabase
        self._inizializza_orari_prenotati()
    
    def _inizializza_orari_prenotati(self):
        """
        Inizializza il dizionario degli orari prenotati
        In una implementazione completa, potrebbe recuperare questi dati da Supabase
        """
        self.orari_prenotati = {}
    
    def _genera_orari_disponibili(self):
        """
        Genera una lista di orari disponibili per la consegna
        
        Returns:
            Lista di stringhe con gli orari disponibili
        """
        orari_disponibili = []
        
        # Inizia dalle 19:00 come richiesto
        ora_inizio = datetime.now().replace(hour=19, minute=0, second=0, microsecond=0)
        
        # Genera slot di 15 minuti fino alle 23:00 (ultimo orario di consegna)
        ora_corrente = ora_inizio
        ora_fine = ora_inizio.replace(hour=23, minute=0)
        
        while ora_corrente <= ora_fine:
            # Formatta l'orario come stringa (es. "19:00")
            slot_orario = f"{ora_corrente.hour:02d}:{ora_corrente.minute:02d}"
            
            # Controlla quanti ordini sono già prenotati per questo slot
            conteggio = self.orari_prenotati.get(slot_orario, 0)
            
            # Se ci sono meno di 2 prenotazioni, lo slot è disponibile
            if conteggio < 2:
                orari_disponibili.append(slot_orario)
            
            # Passa al prossimo slot di 15 minuti
            ora_corrente += timedelta(minutes=15)
        
        return orari_disponibili
    
    def _genera_menu_pizze(self):
        """
        Genera una rappresentazione testuale del menu delle pizze
        
        Returns:
            Stringa contenente il menu delle pizze
        """
        menu_text = "🍕 MENU PIZZE 🍕\n"
        
        # Categorie di pizze da cercare nel menu
        categorie_pizze = ["Pizze Classiche", "Pizze Speciali", "Pizze Bianche"]
        
        for section_title, items in self.menu_index.menu_data.items():
            if any(categoria in section_title for categoria in categorie_pizze):
                menu_text += f"\n{section_title}:\n"
                for item_name, details in items.items():
                    menu_text += f"- {item_name}: €{details['price']:.2f}\n"
        
        return menu_text
    
    def _genera_menu_fritti(self):
        """
        Genera una rappresentazione testuale del menu dei fritti
        
        Returns:
            Stringa contenente il menu dei fritti
        """
        menu_text = "🍟 MENU FRITTI 🍟\n"
        
        # Categorie di fritti da cercare nel menu
        categorie_fritti = ["Fritti", "Antipasti"]
        
        for section_title, items in self.menu_index.menu_data.items():
            if any(categoria in section_title for categoria in categorie_fritti):
                menu_text += f"\n{section_title}:\n"
                for item_name, details in items.items():
                    menu_text += f"- {item_name}: €{details['price']:.2f}\n"
        
        return menu_text
    
    def _genera_menu_bevande(self):
        """
        Genera una rappresentazione testuale del menu delle bevande
        
        Returns:
            Stringa contenente il menu delle bevande
        """
        menu_text = "🥤 MENU BEVANDE 🥤\n"
        
        # Categorie di bevande da cercare nel menu
        categorie_bevande = ["Bevande", "Bibite"]
        
        for section_title, items in self.menu_index.menu_data.items():
            if any(categoria in section_title for categoria in categorie_bevande):
                menu_text += f"\n{section_title}:\n"
                for item_name, details in items.items():
                    menu_text += f"- {item_name}: €{details['price']:.2f}\n"
        
        return menu_text
    
    def _calcola_totale_ordine(self, ordine):
        """
        Calcola il prezzo totale dell'ordine
        
        Args:
            ordine: Dizionario dell'ordine
            
        Returns:
            Prezzo totale dell'ordine
        """
        totale = 0.0
        
        # Calcola prezzo per le pizze
        for pizza in ordine["pizze"]:
            nome_pizza = pizza["nome"]
            # Cerca il prezzo della pizza nel menu
            for section, items in self.menu_index.menu_data.items():
                if nome_pizza in items:
                    totale += items[nome_pizza]["price"]
                    break
        
        # Calcola prezzo per i fritti
        for fritto in ordine["fritti"]:
            nome_fritto = fritto["nome"]
            # Cerca il prezzo del fritto nel menu
            for section, items in self.menu_index.menu_data.items():
                if nome_fritto in items:
                    totale += items[nome_fritto]["price"]
                    break
        
        # Calcola prezzo per le bevande
        for bevanda in ordine["bevande"]:
            nome_bevanda = bevanda["nome"]
            # Cerca il prezzo della bevanda nel menu
            for section, items in self.menu_index.menu_data.items():
                if nome_bevanda in items:
                    totale += items[nome_bevanda]["price"]
                    break
        
        return totale
    
    def _aggiungi_prezzi_prodotti(self, ordine):
        """
        Aggiunge i prezzi ai singoli prodotti nell'ordine
        
        Args:
            ordine: Dizionario dell'ordine
        """
        # Aggiungi prezzi alle pizze
        for pizza in ordine["pizze"]:
            nome_pizza = pizza["nome"]
            # Cerca il prezzo della pizza nel menu
            for section, items in self.menu_index.menu_data.items():
                if nome_pizza in items:
                    pizza["prezzo"] = items[nome_pizza]["price"]
                    break
        
        # Aggiungi prezzi ai fritti
        for fritto in ordine["fritti"]:
            nome_fritto = fritto["nome"]
            # Cerca il prezzo del fritto nel menu
            for section, items in self.menu_index.menu_data.items():
                if nome_fritto in items:
                    fritto["prezzo"] = items[nome_fritto]["price"]
                    break
        
        # Aggiungi prezzi alle bevande
        for bevanda in ordine["bevande"]:
            nome_bevanda = bevanda["nome"]
            # Cerca il prezzo della bevanda nel menu
            for section, items in self.menu_index.menu_data.items():
                if nome_bevanda in items:
                    bevanda["prezzo"] = items[nome_bevanda]["price"]
                    break
    
    def _aggiorna_stato_ordine(self, user_id: str) -> None:
        """
        Funzione stub per mantenere traccia delle modifiche all'ordine.
        Non salva fisicamente nulla, solo per log e debug.
        
        Args:
            user_id: ID utente
        """
        # Genera un ID per la comanda se non ne ha già uno
        ordine = self.ordini_attivi[user_id]
        if not ordine["comanda_id"]:
            ordine["comanda_id"] = self._genera_id_comanda()
            
        # Solo per debug
        print(f"Ordine {ordine['comanda_id']} aggiornato - Stato: {ordine['stato']}")
    
    def inizia_nuovo_ordine(self, user_id: str) -> str:
        """
        Inizializza un nuovo ordine per un utente
        
        Args:
            user_id: ID utente
            
        Returns:
            Messaggio di benvenuto per l'ordine con il menu delle pizze
        """
        self.ordini_attivi[user_id] = {
            "pizze": [],
            "fritti": [],
            "bevande": [],
            "cliente": {
                "nome": None,
                "indirizzo": None,
                "telefono": None
            },
            "pagamento": None,
            "orario_consegna": None,  # Nuovo campo per l'orario di consegna
            "risposte_cliente": [],
            "stato": "raccolta_pizze",  # Stato iniziale: raccolta delle pizze
            "comanda_id": None  # ID numerico progressivo della comanda
        }
        
        # Genera il menu delle pizze
        menu_pizze = self._genera_menu_pizze()
        
        # Salva la risposta del cliente (vuota per iniziare)
        self.ordini_attivi[user_id]["risposte_cliente"].append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "messaggio": "INIZIO ORDINE"
        })
        
        # Messaggio di benvenuto con menu
        return f"Buonasera, pizzeria da Mario! Che pizza desidera ordinare?\n\n{menu_pizze}"
    
    def _estrai_pizze(self, messaggio):
        """
        Estrae le pizze menzionate nel messaggio del cliente
        
        Args:
            messaggio: Testo del messaggio utente
            
        Returns:
            Lista di tuple (nome_pizza, quantità)
        """
        # Questa è una versione semplificata per l'estrazione delle pizze
        
        pizze_comuni = {
            "margherit": "Margherita",
            "diavol": "Diavola",
            "4 stagioni": "Quattro Stagioni",
            "quattro stagioni": "Quattro Stagioni",
            "marinara": "Marinara",
            "napoli": "Napoletana",
            "capricciosa": "Capricciosa"
        }
        
        pizze_trovate = []
        messaggio_lower = messaggio.lower()
        
        # Cerca le pizze nel messaggio
        for keyword, nome_pizza in pizze_comuni.items():
            if keyword in messaggio_lower:
                # Cerca quantità (es. "2 margherite")
                match = re.search(r'(\d+)\s+\w*' + re.escape(keyword), messaggio_lower)
                quantita = int(match.group(1)) if match else 1
                
                pizze_trovate.append((nome_pizza, quantita))
        
        return pizze_trovate
    
    def _estrai_fritti(self, messaggio):
        """
        Estrae i fritti menzionati nel messaggio del cliente
        
        Args:
            messaggio: Testo del messaggio utente
            
        Returns:
            Lista di tuple (nome_fritto, quantità)
        """
        # Versione semplificata per l'estrazione dei fritti
        
        fritti_comuni = {
            "patatine": "Patatine",
            "crocchette": "Crocchette",
            "suppl": "Supplì",
            "arancin": "Arancini"
        }
        
        fritti_trovati = []
        messaggio_lower = messaggio.lower()
        
        # Cerca i fritti nel messaggio
        for keyword, nome_fritto in fritti_comuni.items():
            if keyword in messaggio_lower:
                # Cerca quantità (es. "2 porzioni di patatine")
                match = re.search(r'(\d+)\s+\w*' + re.escape(keyword), messaggio_lower)
                quantita = int(match.group(1)) if match else 1
                
                fritti_trovati.append((nome_fritto, quantita))
        
        return fritti_trovati
    
    def _estrai_bevande(self, messaggio):
        """
        Estrae le bevande menzionate nel messaggio del cliente
        
        Args:
            messaggio: Testo del messaggio utente
            
        Returns:
            Lista di tuple (nome_bevanda, quantità)
        """
        # Versione semplificata per l'estrazione delle bevande
        
        bevande_comuni = {
            "acqua": "Acqua",
            "coca cola": "Coca Cola",
            "coca-cola": "Coca Cola", 
            "coca": "Coca Cola",
            "pepsi": "Pepsi",
            "fanta": "Fanta",
            "sprite": "Sprite",
            "birra": "Birra",
            "vino": "Vino"
        }
        
        bevande_trovate = []
        messaggio_lower = messaggio.lower()
        
        # Cerca prima le combinazioni di parole come "coca cola"
        for keyword in ["coca cola", "coca-cola"]:
            if keyword in messaggio_lower:
                match = re.search(r'(\d+)\s+\w*' + re.escape(keyword), messaggio_lower)
                quantita = int(match.group(1)) if match else 1
                bevande_trovate.append((bevande_comuni[keyword], quantita))
                # Rimuovi la keyword dal messaggio per evitare duplicati
                messaggio_lower = messaggio_lower.replace(keyword, "")
        
        # Cerca le bevande singole nel messaggio
        for keyword, nome_bevanda in bevande_comuni.items():
            # Salta le combinazioni già controllate
            if keyword in ["coca cola", "coca-cola"]:
                continue
                
            if keyword in messaggio_lower:
                # Cerca quantità (es. "2 birre")
                match = re.search(r'(\d+)\s+\w*' + re.escape(keyword), messaggio_lower)
                quantita = int(match.group(1)) if match else 1
                
                # Evita duplicati (es. se abbiamo già trovato "coca cola", non aggiungere "coca")
                if not any(nome_bevanda == bevanda[0] for bevanda in bevande_trovate):
                    bevande_trovate.append((nome_bevanda, quantita))
        
        return bevande_trovate
    
    def _estrai_orario(self, messaggio):
        """
        Estrae l'orario di consegna dal messaggio del cliente
        
        Args:
            messaggio: Testo del messaggio utente
            
        Returns:
            Orario nel formato "HH:MM" o None se non trovato
        """
        # Cerca un orario nel formato "19:15" o "19.15" o "19 e 15"
        match = re.search(r'(\d{1,2})[:\s\.e]*(\d{2})', messaggio)
        
        if match:
            ore = int(match.group(1))
            minuti = int(match.group(2))
            
            # Validazione base
            if 0 <= ore <= 23 and 0 <= minuti <= 59:
                # Arrotonda ai 15 minuti più vicini
                minuti_arrotondati = (minuti // 15) * 15
                return f"{ore:02d}:{minuti_arrotondati:02d}"
        
        return None
    
    def gestisci_messaggio(self, user_id: str, messaggio: str) -> str:
        """
        Gestisce un messaggio dell'utente nel contesto dell'ordine
        
        Args:
            user_id: ID utente
            messaggio: Testo del messaggio utente
            
        Returns:
            Risposta al messaggio dell'utente
        """
        # Debug
        print(f"Messaggio ricevuto: '{messaggio}'")
        
        # Se non c'è un ordine attivo, iniziane uno nuovo
        if user_id not in self.ordini_attivi:
            return self.inizia_nuovo_ordine(user_id)
        
        # Salva la risposta del cliente
        self.ordini_attivi[user_id]["risposte_cliente"].append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "messaggio": messaggio
        })
        
        ordine = self.ordini_attivi[user_id]
        
        # Gestione in base allo stato dell'ordine
        if ordine["stato"] == "raccolta_pizze":
            # Cerca pizze nel messaggio
            pizze = self._estrai_pizze(messaggio)
            if pizze:
                # Aggiungi le pizze all'ordine
                for nome_pizza, quantita in pizze:
                    for _ in range(quantita):
                        ordine["pizze"].append({
                            "nome": nome_pizza,
                            "quantita": 1  # Ogni voce rappresenta una pizza
                        })
                
                # Passa allo stato successivo
                ordine["stato"] = "raccolta_fritti"
                
                # Genera il menu dei fritti
                menu_fritti = self._genera_menu_fritti()
                
                # Aggiorna stato ordine
                self._aggiorna_stato_ordine(user_id)
                
                # Chiedi dei fritti
                return f"Perfetto! Ho registrato: {', '.join([f'{q} {p}' for p, q in pizze])}. Vuole anche dei fritti?\n\n{menu_fritti}"
            else:
                # Se non abbiamo riconosciuto le pizze, chiedi di nuovo
                return "Mi scusi, non ho capito quali pizze desidera. Può ripetere per favore?"
                
        elif ordine["stato"] == "raccolta_fritti":
            # Verifica se il cliente vuole fritti
            messaggio_lower = messaggio.lower()
            
            # Se il cliente rifiuta esplicitamente i fritti
            if any(keyword in messaggio_lower for keyword in ["no", "niente", "non voglio", "basta così"]):
                # Passa allo stato successivo senza aggiungere fritti
                ordine["stato"] = "raccolta_bevande"
                
                # Genera il menu delle bevande
                menu_bevande = self._genera_menu_bevande()
                
                # Aggiorna stato ordine
                self._aggiorna_stato_ordine(user_id)
                
                # Chiedi delle bevande
                return f"Vuole anche delle bibite?\n\n{menu_bevande}"
            
            # Cerca fritti nel messaggio
            fritti = self._estrai_fritti(messaggio)
            if fritti:
                # Aggiungi i fritti all'ordine
                for nome_fritto, quantita in fritti:
                    for _ in range(quantita):
                        ordine["fritti"].append({
                            "nome": nome_fritto,
                            "quantita": 1  # Ogni voce rappresenta una porzione
                        })
                
                # Passa allo stato successivo
                ordine["stato"] = "raccolta_bevande"
                
                # Genera il menu delle bevande
                menu_bevande = self._genera_menu_bevande()
                
                # Aggiorna stato ordine
                self._aggiorna_stato_ordine(user_id)
                
                # Chiedi delle bevande
                fritti_str = ", ".join([f"{q} {f}" for f, q in fritti])
                return f"Ottimo! Ho aggiunto {fritti_str}. Vuole anche delle bibite?\n\n{menu_bevande}"
            else:
                # Se non abbiamo riconosciuto i fritti, chiedi di nuovo
                return "Mi scusi, non ho capito quali fritti desidera. Può ripetere per favore? Se non desidera fritti, può dirmi 'no grazie'."
                
        elif ordine["stato"] == "raccolta_bevande":
            # Verifica se il cliente vuole bevande
            messaggio_lower = messaggio.lower()
            
            # Se il cliente rifiuta esplicitamente le bevande
            if any(keyword in messaggio_lower for keyword in ["no", "niente", "non voglio", "basta così"]):
                # Passa alla conferma dell'ordine
                ordine["stato"] = "conferma_ordine"
                
                # Aggiorna stato ordine
                self._aggiorna_stato_ordine(user_id)
                
                # Prepara il riepilogo dell'ordine
                riepilogo = self._genera_riepilogo_ordine(ordine)
                
                # Chiedi conferma
                return f"L'ordine è: {riepilogo} È corretto?"
            
            # Cerca bevande nel messaggio
            bevande = self._estrai_bevande(messaggio)
            if bevande:
                # Aggiungi le bevande all'ordine
                for nome_bevanda, quantita in bevande:
                    for _ in range(quantita):
                        ordine["bevande"].append({
                            "nome": nome_bevanda,
                            "quantita": 1  # Ogni voce rappresenta una bevanda
                        })
                
                # Passa alla conferma dell'ordine
                ordine["stato"] = "conferma_ordine"
                
                # Aggiorna stato ordine
                self._aggiorna_stato_ordine(user_id)
                
                # Prepara il riepilogo dell'ordine
                riepilogo = self._genera_riepilogo_ordine(ordine)
                
                # Chiedi conferma
                bevande_str = ", ".join([f"{q} {b}" for b, q in bevande])
                return f"Ottimo! Ho aggiunto {bevande_str}. L'ordine è: {riepilogo} È corretto?"
            else:
                # Se non abbiamo riconosciuto le bevande, chiedi di nuovo
                return "Mi scusi, non ho capito quali bibite desidera. Può ripetere per favore? Se non desidera bibite, può dirmi 'no grazie'."
                
        elif ordine["stato"] == "conferma_ordine":
            # Controlla se l'utente conferma l'ordine
            messaggio_lower = messaggio.lower()
            
            # Se l'utente conferma
            if any(keyword in messaggio_lower for keyword in ["sì", "si", "yes", "ok", "giusto", "corretto", "esatto", "confermo"]):
                # Passa alla raccolta delle informazioni del cliente
                ordine["stato"] = "raccolta_nome"
                
                # Aggiorna stato ordine
                self._aggiorna_stato_ordine(user_id)
                
                # Chiedi nome, indirizzo, telefono e metodo di pagamento
                return "Per gestire l'ordine correttamente ho bisogno di: nome, indirizzo di consegna, numero di telefono, metodo di pagamento. Iniziamo con il nome, come si chiama?"
                
            # Se l'utente non conferma
            elif any(keyword in messaggio_lower for keyword in ["no", "sbagliato", "non va bene", "cambia", "modifica"]):
                # Torna alla raccolta delle pizze
                ordine["stato"] = "raccolta_pizze"
                
                # Reset dell'ordine
                ordine["pizze"] = []
                ordine["fritti"] = []
                ordine["bevande"] = []
                
                # Genera il menu delle pizze
                menu_pizze = self._genera_menu_pizze()
                
                # Aggiorna stato ordine
                self._aggiorna_stato_ordine(user_id)
                
                # Richiedi nuovamente l'ordine
                return f"Mi scusi per l'errore. Ricominciamo. Che pizza desidera ordinare?\n\n{menu_pizze}"
                
            else:
                # Se non abbiamo capito la risposta, chiedi di nuovo
                return "Mi scusi, non ho capito se l'ordine è corretto. Può rispondere con 'sì' o 'no'?"
                
        elif ordine["stato"] == "raccolta_nome":
            # Salva il nome del cliente
            ordine["cliente"]["nome"] = messaggio
            
            # Passa alla raccolta dell'indirizzo
            ordine["stato"] = "raccolta_indirizzo"
            
            # Aggiorna stato ordine
            self._aggiorna_stato_ordine(user_id)
            
            # Chiedi l'indirizzo
            return "Grazie. Qual è l'indirizzo di consegna?"
            
        elif ordine["stato"] == "raccolta_indirizzo":
            # Salva l'indirizzo del cliente
            ordine["cliente"]["indirizzo"] = messaggio
            
            # Passa alla raccolta del telefono
            ordine["stato"] = "raccolta_telefono"
            
            # Aggiorna stato ordine
            self._aggiorna_stato_ordine(user_id)
            
            # Chiedi il telefono
            return "Mi può lasciare un numero di telefono per eventuali comunicazioni sulla consegna?"
            
        elif ordine["stato"] == "raccolta_telefono":
            # Verifica che sia un possibile numero di telefono
            if re.match(r'\+?\d[\d\s-]{7,}', messaggio):
                # Salva il telefono del cliente
                ordine["cliente"]["telefono"] = messaggio
                
                # Passa alla raccolta del metodo di pagamento
                ordine["stato"] = "raccolta_pagamento"
                
                # Aggiorna stato ordine
                self._aggiorna_stato_ordine(user_id)
                
                # Chiedi il metodo di pagamento
                return "Come preferisce pagare? Accettiamo contanti e carta alla consegna."
            else:
                # Se il formato del telefono non è valido
                return "Mi scusi, non sembra un numero di telefono valido. Può inserire un numero di telefono corretto?"
                
        elif ordine["stato"] == "raccolta_pagamento":
            messaggio_lower = messaggio.lower()
            
            # Determina il metodo di pagamento
            if "contanti" in messaggio_lower or "cash" in messaggio_lower:
                ordine["pagamento"] = "Contanti alla consegna"
            elif any(keyword in messaggio_lower for keyword in ["carta", "bancomat", "credit", "credito", "debito", "pos"]):
                ordine["pagamento"] = "Carta alla consegna"
            else:
                # Se non abbiamo capito il metodo di pagamento
                return "Mi scusi, non ho capito il metodo di pagamento. Può scegliere tra contanti o carta alla consegna?"
            
            # Passa alla raccolta dell'orario di consegna
            ordine["stato"] = "raccolta_orario"
            
            # Aggiorna stato ordine
            self._aggiorna_stato_ordine(user_id)
            
            # Genera la lista degli orari disponibili
            orari_disponibili = self._genera_orari_disponibili()
            
            # Formatta gli orari disponibili in blocchi per maggiore leggibilità
            orari_formattati = []
            for i, orario in enumerate(orari_disponibili):
                orari_formattati.append(orario)
                # Aggiungi una nuova riga ogni 5 orari
                if (i + 1) % 5 == 0 and i < len(orari_disponibili) - 1:
                    orari_formattati.append("\n")
            
            orari_str = ", ".join(orari_formattati)
            
            # Chiedi l'orario di consegna
            return f"Quale orario preferisce per la consegna? Ecco gli orari disponibili:\n{orari_str}"
            
        elif ordine["stato"] == "raccolta_orario":
            # Estrai l'orario dal messaggio
            orario = self._estrai_orario(messaggio)
            
            if orario:
                # Verifica se l'orario è tra quelli disponibili
                orari_disponibili = self._genera_orari_disponibili()
                
                if orario in orari_disponibili:
                    # Salva l'orario di consegna
                    ordine["orario_consegna"] = orario
                    
                    # Aggiorna il contatore degli orari prenotati
                    if orario in self.orari_prenotati:
                        self.orari_prenotati[orario] += 1
                    else:
                        self.orari_prenotati[orario] = 1
                    
                    # Passa alla conferma finale
                    ordine["stato"] = "conferma_finale"
                    
                    # Genera un ID univoco per la comanda se non ne ha già uno
                    if not ordine["comanda_id"]:
                        ordine["comanda_id"] = self._genera_id_comanda()
                    
                    # Aggiorna stato ordine
                    self._aggiorna_stato_ordine(user_id)
                    
                    # Prepara il riepilogo completo
                    riepilogo = self._genera_riepilogo_completo(ordine)
                    
                    # Chiedi conferma finale
                    return f"{riepilogo}\n\nÈ tutto corretto? Conferma l'ordine?"
                else:
                    # Se l'orario non è disponibile
                    return f"Mi dispiace, l'orario {orario} non è disponibile. Scelga uno tra questi orari: {', '.join(orari_disponibili[:5])}..."
            else:
                # Se non abbiamo riconosciuto l'orario
                orari_disponibili = self._genera_orari_disponibili()
                return f"Mi scusi, non ho capito l'orario. Può scegliere uno tra questi orari: {', '.join(orari_disponibili[:5])}..."
            
        elif ordine["stato"] == "conferma_finale":
            # Controlla se l'utente conferma tutto
            messaggio_lower = messaggio.lower()
            
            # Se l'utente conferma
            if any(keyword in messaggio_lower for keyword in ["sì", "si", "yes", "ok", "giusto", "corretto", "esatto", "confermo"]):
                # Calcola il totale dell'ordine
                ordine_completato = self.ordini_attivi[user_id]
                ordine_completato["totale"] = self._calcola_totale_ordine(ordine_completato)
                
                # Aggiungi prezzi ai singoli prodotti per la generazione della comanda
                self._aggiungi_prezzi_prodotti(ordine_completato)
                
                # Ora i dati saranno salvati su Supabase tramite le funzioni di profilo.py
                # Nessun salvataggio locale qui
                crea_comanda_txt(user_id, ordine_completato)
                aggiorna_profilo_cliente(user_id, ordine_completato["cliente"])
                aggiorna_file_clienti(ordine_completato["cliente"])
                
                # Ottieni l'ID della comanda per mostrarlo all'utente
                comanda_id = ordine_completato["comanda_id"]
                
                # Resetta l'ordine (elimina dalla memoria)
                del self.ordini_attivi[user_id]
                
                # Messaggio di conferma finale
                return f"Grazie {ordine_completato['cliente']['nome']}! Il suo ordine #{comanda_id} è stato confermato. Consegneremo a {ordine_completato['cliente']['indirizzo']} alle {ordine_completato['orario_consegna']}. In caso di problemi, la contatteremo al numero {ordine_completato['cliente']['telefono']}. Grazie per aver scelto la pizzeria da Mario! In caso di problemi o modifiche all'ordine la preghiamo di contattare direttamente il numero della pizzeria, a presto!"
                
            # Se l'utente non conferma
            elif any(keyword in messaggio_lower for keyword in ["no", "sbagliato", "non va bene", "cambia", "modifica"]):
                # Torna alla raccolta delle pizze
                ordine["stato"] = "raccolta_pizze"
                
                # Reset dell'ordine
                ordine["pizze"] = []
                ordine["fritti"] = []
                ordine["bevande"] = []
                ordine["cliente"]["nome"] = None
                ordine["cliente"]["indirizzo"] = None
                ordine["cliente"]["telefono"] = None
                ordine["pagamento"] = None
                ordine["orario_consegna"] = None
                
                # Genera il menu delle pizze
                menu_pizze = self._genera_menu_pizze()
                
                # Aggiorna stato ordine
                self._aggiorna_stato_ordine(user_id)
                
                # Richiedi nuovamente l'ordine
                return f"Mi scusi per l'errore. Ricominciamo da capo. Che pizza desidera ordinare?\n\n{menu_pizze}"
                
            else:
                # Se non abbiamo capito la risposta, chiedi di nuovo
                return "Mi scusi, non ho capito se vuole confermare l'ordine. Può rispondere con 'sì' o 'no'?"
        
        # Fallback in caso di stato non riconosciuto
        return "Mi scusi, c'è stato un errore. Può ricominciare l'ordine?"
    
    def _genera_riepilogo_ordine(self, ordine):
        """
        Genera un riepilogo dell'ordine completo
        
        Args:
            ordine: Dizionario dell'ordine
            
        Returns:
            Stringa con il riepilogo dell'ordine
        """
        parti_riepilogo = []
        
        # Aggiungi le pizze al riepilogo
        if ordine["pizze"]:
            nomi_pizze = [p["nome"] for p in ordine["pizze"]]
            # Conta le occorrenze di ciascuna pizza
            conteggio_pizze = Counter(nomi_pizze)
            pizze_str = ", ".join([f"{conteggio} {pizza}" for pizza, conteggio in conteggio_pizze.items()])
            parti_riepilogo.append(pizze_str)
        
        # Aggiungi i fritti al riepilogo
        if ordine["fritti"]:
            nomi_fritti = [f["nome"] for f in ordine["fritti"]]
            # Conta le occorrenze di ciascun fritto
            conteggio_fritti = Counter(nomi_fritti)
            fritti_str = ", ".join([f"{conteggio} {fritto}" for fritto, conteggio in conteggio_fritti.items()])
            parti_riepilogo.append(fritti_str)
        
        # Aggiungi le bevande al riepilogo
        if ordine["bevande"]:
            nomi_bevande = [b["nome"] for b in ordine["bevande"]]
            # Conta le occorrenze di ciascuna bevanda
            conteggio_bevande = Counter(nomi_bevande)
            bevande_str = ", ".join([f"{conteggio} {bevanda}" for bevanda, conteggio in conteggio_bevande.items()])
            parti_riepilogo.append(bevande_str)
        
        # Costruisci il riepilogo finale
        if parti_riepilogo:
            return f"{' e '.join(parti_riepilogo)}"
        else:
            return "non ci sono prodotti nel suo ordine"
    
    def _genera_riepilogo_completo(self, ordine):
        """
        Genera un riepilogo completo dell'ordine con i dati del cliente
        
        Args:
            ordine: Dizionario dell'ordine
            
        Returns:
            Stringa con il riepilogo completo
        """
        # Riepilogo dell'ordine (prodotti)
        riepilogo_prodotti = self._genera_riepilogo_ordine(ordine)
        
        # Riepilogo delle informazioni del cliente
        nome = ordine["cliente"]["nome"]
        indirizzo = ordine["cliente"]["indirizzo"]
        telefono = ordine["cliente"]["telefono"]
        pagamento = ordine["pagamento"]
        orario_consegna = ordine["orario_consegna"]
        comanda_id = ordine["comanda_id"]
        
        # Costruisci il riepilogo completo
        riepilogo = f"Riepilogo del suo ordine #{comanda_id}:\n"
        riepilogo += f"Prodotti: {riepilogo_prodotti}\n"
        riepilogo += f"Nome: {nome}\n"
        riepilogo += f"Indirizzo di consegna: {indirizzo}\n"
        riepilogo += f"Telefono: {telefono}\n"
        riepilogo += f"Orario di consegna: {orario_consegna}\n"
        riepilogo += f"Metodo di pagamento: {pagamento}"
        
        return riepilogo


def e_intento_ordine(messaggio: str) -> bool:
    """
    Determina se il messaggio dell'utente indica l'intento di effettuare un ordine
    
    Args:
        messaggio: Testo del messaggio utente
        
    Returns:
        True se l'utente intende effettuare un ordine, False altrimenti
    """
    messaggio_lower = messaggio.lower()
    
    # Parole chiave che indicano l'intento di ordinare
    keywords_ordine = [
        "ordina", "ordinare", "vorrei ordinare", "voglio ordinare", 
        "fare un ordine", "ordine", "prendere", "vorrei prendere",
        "voglio prendere", "vorrei una pizza", "vorrei un fritto",
        "vorrei da bere", "portami", "consegnami", "voglio una pizza",
        "prenoto", "prenotare", "prenotazione"
    ]
    
    # Controlla se una delle parole chiave è presente nel messaggio
    return any(keyword in messaggio_lower for keyword in keywords_ordine)