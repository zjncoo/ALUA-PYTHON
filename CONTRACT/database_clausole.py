"""
DATABASE CLAUSOLE ALUA
Struttura: 6 Categorie -> 4 Fasce di Rischio -> 5 Clausole per fascia.
Logica cumulativa: La Fascia 4 include automaticamente le clausole di Fascia 1, 2 e 3.
"""

# Definizioni delle Fasce di Rischio (Titoli che appaiono nel PDF)
TITOLI_FASCE = {
    "AMICIZIA": {
        1: "CONOSCENZA SUPERFICIALE (Livello 1)",
        2: "AMICIZIA STABILE (Livello 2)",
        3: "FRATELLANZA ELETIVA (Livello 3)",
        4: "SIMBIOSI AMICALE (Rischio Critico)"
    },
    "COPPIA": {
        1: "FREQUENTAZIONE (Livello 1)",
        2: "RELAZIONE ESCLUSIVA (Livello 2)",
        3: "PROGETTUALITA' CONDIVISA (Livello 3)",
        4: "FUSIONE ROMANTICA (Rischio Critico)"
    },
    "FAMIGLIA": {
        1: "LEGAME BIOLOGICO BASE (Livello 1)",
        2: "SUPPORTO FAMILIARE (Livello 2)",
        3: "DIPENDENZA AFFETTIVA (Livello 3)",
        4: "NUCLEO INDISSOLUBILE (Rischio Critico)"
    },
    "LAVORO": {
        1: "COLLABORAZIONE OCCASIONALE (Livello 1)",
        2: "TEAM WORKING (Livello 2)",
        3: "PARTNERSHIP STRATEGICA (Livello 3)",
        4: "DIPENDENZA GERARCHICA (Rischio Critico)"
    },
    "CONVIVENZA": {
        1: "COABITAZIONE TECNICA (Livello 1)",
        2: "CONDIVISIONE SPAZI (Livello 2)",
        3: "ECOSISTEMA DOMESTICO (Livello 3)",
        4: "COMPENETRAZIONE ABITATIVA (Rischio Critico)"
    },
    "CONOSCENZA": {
        1: "INTERAZIONE CASUALE (Livello 1)",
        2: "CONTATTO RIPETUTO (Livello 2)",
        3: "SCAMBIO SIGNIFICATIVO (Livello 3)",
        4: "VINCOLO NON CLASSIFICATO (Rischio Critico)"
    }
}

# DATABASE DELLE CLAUSOLE
# Ogni lista contiene 5 clausole specifiche per quella fascia.
# Il generatore sommerà le liste (es. Fascia 2 = Lista 1 + Lista 2).

CLAUSOLE_DB = {
    # --------------------------------------------------------
    # CATEGORIA 1: AMICIZIA
    # --------------------------------------------------------
    "AMICIZIA": {
        1: [ # Fascia 1
            "1. Divieto di condivisione password o account streaming.",
            "2. Obbligo di preavviso di 24h per chiamate superiori ai 10 minuti.",
            "3. Limitazione dei temi di conversazione a hobby e meteo.",
            "4. Divieto di prestito di somme di denaro superiori a 5€.",
            "5. Esclusione di responsabilità per mancata risposta ai messaggi."
        ],
        2: [ # Fascia 2 (Si somma alla 1)
            "6. Autorizzazione allo scambio di confidenze di livello medio.",
            "7. Accesso limitato alla sfera emotiva del Contraente.",
            "8. Obbligo di partecipazione a n.1 evento sociale mensile.",
            "9. Regolamentazione della suddivisione conti (metodo alla romana).",
            "10. Diritto di veto su nuovi partner introdotti nel gruppo."
        ],
        3: [ # Fascia 3 (Si somma a 1+2)
            "11. Condivisione della geolocalizzazione in tempo reale.",
            "12. Obbligo di supporto emotivo H24 in caso di rottura sentimentale.",
            "13. Accesso alle chiavi di casa per emergenze (e.g. annaffiare piante).",
            "14. Patto di non aggressione con ex-partner dell'altro Contraente.",
            "15. Pianificazione ferie congiunte con preavviso di 6 mesi."
        ],
        4: [ # Fascia 4 (Si somma a 1+2+3)
            "16. Fusione dei patrimoni esperienziali.",
            "17. Diritto di prelazione sul tempo libero festivo.",
            "18. Obbligo di testamento biologico reciproco.",
            "19. Divieto assoluto di segreti, pena la decadenza del rapporto.",
            "20. Clausola di fedeltà amicale esclusiva."
        ]
    },

    # --------------------------------------------------------
    # CATEGORIA 2: COPPIA (ROMANTICA)
    # --------------------------------------------------------
    "COPPIA": {
        1: [
            "1. Definizione chiara dello status 'Non Esclusivo'.",
            "2. Divieto di pubblicazione foto di coppia sui social media.",
            "3. Separazione netta dei beni e delle spese.",
            "4. Coprifuoco digitale: nessun messaggio dopo le 23:00.",
            "5. Protocollo di igiene pre-incontro obbligatorio."
        ],
        2: [
            "6. Attivazione dell'Esclusività Sessuale e Sentimentale.",
            "7. Obbligo di 'Like' tattico ai post del partner entro 1 ora.",
            "8. Condivisione password piattaforme streaming (esclusi profili privati).",
            "9. Diritto di conoscere la password di sblocco telefono (solo emergenze).",
            "10. Calendarizzazione obbligatoria degli incontri con i suoceri."
        ],
        3: [
            "11. Monitoraggio biometrico dello stress durante le discussioni.",
            "12. Obbligo di rendicontazione spese superiori a 100€.",
            "13. Accesso illimitato alla cronologia posizioni.",
            "14. Clausola 'Nessun Segreto': accesso ai messaggi archiviati.",
            "15. Pianificazione riproduttiva vincolante quinquennale."
        ],
        4: [
            "16. Fusione legale e finanziaria delle identità (Matrimonio/Unione).",
            "17. Clausola di Dissoluzione Abitativa Immediata in caso di crisi.",
            "18. Penalità economica per calo del desiderio non giustificato.",
            "19. Obbligo di terapia di coppia preventiva mensile.",
            "20. Diritto di vita e di morte digitale sull'altro in caso di tradimento."
        ]
    },

    # --------------------------------------------------------
    # CATEGORIA 3: FAMIGLIA
    # --------------------------------------------------------
    "FAMIGLIA": {
        1: [
            "1. Partecipazione obbligatoria solo a Natale e Pasqua.",
            "2. Divieto di domande intrusive su lavoro e vita sentimentale.",
            "3. Limite massimo di 1 chiamata a settimana.",
            "4. Regalo di compleanno monetario o generico.",
            "5. Diritto al silenzio durante i pranzi domenicali."
        ],
        2: [
            "6. Supporto logistico per traslochi o commissioni.",
            "7. Obbligo di risposta ai messaggi nel gruppo famiglia.",
            "8. Tolleranza di consigli non richiesti (max 3 per incontro).",
            "9. Accesso al frigorifero senza richiesta preventiva.",
            "10. Partecipazione a matrimoni di cugini di secondo grado."
        ],
        3: [
            "11. Gestione congiunta di proprietà e eredità.",
            "12. Obbligo di assistenza domiciliare in caso di malattia.",
            "13. Diritto di veto sulle scelte di carriera dei figli.",
            "14. Condivisione account bancari di emergenza.",
            "15. Presenza obbligatoria a tutte le recite scolastiche."
        ],
        4: [
            "16. Sacrificio delle ambizioni personali per il bene del clan.",
            "17. Obbligo di residenza entro 10km dal nucleo matriarcale.",
            "18. Fusione totale delle finanze.",
            "19. Divieto di emancipazione prima dei 40 anni.",
            "20. Clausola 'Sangue del mio Sangue': lealtà assoluta."
        ]
    },

    # --------------------------------------------------------
    # CATEGORIA 4: LAVORO
    # --------------------------------------------------------
    "LAVORO": {
        1: [
            "1. Comunicazione limitata esclusivamente all'orario d'ufficio e per fini professionali.",
            "2. Divieto di aggiunta sui social media personali o scambio di contatti privati.",
            "3. Pausa pranzo separata e indipendente, senza obbligo di interazione.",
            "4. Utilizzo esclusivo della mail aziendale per comunicazioni interne ed esterne.",
            "5. Divieto di contatto fisico non strettamente necessario (es. strette di mano formali)."
        ],
        2: [
            "6. Partecipazione a eventi aziendali (cene, meeting) con frequenza massima di 2 all'anno.",
            "7. Tolleranza di conversazioni informali alla macchinetta del caffè o in aree comuni.",
            "8. Scambio di numeri di cellulare per sole emergenze lavorative, con consenso esplicito.",
            "9. Copertura reciproca su piccoli ritardi o assenze giustificate (max 15 min/giorno).",
            "10. Condivisione di pareri su colleghi terzi, purché costruttivi e non lesivi della reputazione."
        ],
        3: [
            "11. Reperibilità estesa (serale/weekend).",
            "12. Patto di non concorrenza e fedeltà aziendale.",
            "13. Obbligo di mentorship verso i junior.",
            "14. Condivisione obiettivi di carriera a lungo termine.",
            "15. Partecipazione emotiva ai successi del team."
        ],
        4: [
            "16. Identificazione totale con il Brand Aziendale.",
            "17. Rinuncia alle ferie in periodi di crunch.",
            "18. Reperibilità H24.",
            "19. Clausola di riservatezza assoluta (NDA esteso).",
            "20. Il lavoro ha priorità sulle relazioni familiari."
        ]
    },

    # --------------------------------------------------------
    # CATEGORIA 5: CONVIVENZA (New!)
    # --------------------------------------------------------
    "CONVIVENZA": {
        1: [
            "1. Separazione netta degli scaffali in frigo e dispensa.",
            "2. Etichettatura obbligatoria dei beni alimentari personali.",
            "3. Divieto di accesso alla camera altrui senza invito.",
            "4. Orari di silenzio rigidi (23:00 - 07:00).",
            "5. Turni di pulizia bagno settimanali non negoziabili."
        ],
        2: [
            "6. Acquisto condiviso di beni essenziali (sale, olio, carta igienica).",
            "7. Autorizzazione a ospitare terzi con preavviso di 24h.",
            "8. Uso condiviso degli elettrodomestici in aree comuni.",
            "9. Tolleranza rumore moderata fino alle 24:00.",
            "10. Creazione cassa comune per bollette e utenze."
        ],
        3: [
            "11. Condivisione dei pasti serali (Cena sociale).",
            "12. Libero accesso agli spazi comuni senza prenotazione.",
            "13. Gestione congiunta delle manutenzioni domestiche.",
            "14. Supporto reciproco in caso di malattia lieve.",
            "15. Diritto di ospitare partner per la notte (max 3 notti/settimana)."
        ],
        4: [ # Queste sono quelle del tuo DOC
            "16. Separazione Spaziale Pasti: Divieto di consumare pasti insieme.",
            "17. Isolamento Acustico Obbligatorio (cuffie ANC in spazi comuni).",
            "18. Accesso alle Aree Comuni su Prenotazione oraria.",
            "19. Intermediazione Digitale: Solo messaggi, niente voce in casa.",
            "20. Clausola di Dissoluzione Abitativa Immediata (Sfratto Selettivo)."
        ]
    },

    # --------------------------------------------------------
    # CATEGORIA 6: ALTRO / SCONOSCIUTI
    # --------------------------------------------------------
    "ALTRO": {
        1: [
            "1. Mantenimento della distanza di sicurezza di 1 metro.",
            "2. Divieto di contatto visivo prolungato (> 3 secondi).",
            "3. Nessun obbligo di saluto o riconoscimento.",
            "4. Rispetto della privacy e dell'anonimato.",
            "5. Divieto di rivolgere la parola se non per emergenze."
        ],
        2: [
            "6. Scambio di cenni di cortesia in ambienti condivisi (ascensore).",
            "7. Tolleranza della presenza fisica nello stesso ambiente.",
            "8. Possibilità di scambio informazioni meteorologiche.",
            "9. Assistenza minima in caso di pericolo immediato.",
            "10. Rispetto della fila e delle precedenze sociali."
        ],
        3: [
            "11. Scambio di contatti social (LinkedIn/Instagram).",
            "12. Partecipazione a conversazioni di gruppo occasionali.",
            "13. Condivisione di opinioni su temi generici.",
            "14. Possibilità di evoluzione in categoria 'Amicizia'.",
            "15. Diritto all'oblio: possibilità di cancellare il contatto."
        ],
        4: [
            "16. Monitoraggio a distanza delle attività online.",
            "17. Creazione di un dossier informativo sul soggetto.",
            "18. Ingaggio di investigatori privati per verifica background.",
            "19. Blocco preventivo su tutti i canali di comunicazione.",
            "20. Ordine restrittivo cautelare preventivo."
        ]
    }
}