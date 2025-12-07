# database_clausole.py

TITOLI_FASCE = {
    "PROFESSIONALE": {
        1: "STANDARD DI EFFICIENZA OPERATIVA",
        2: "PROTOCOLLO DI DISTANZIAMENTO FORMALE",
        3: "REGIME DI MEDIAZIONE OBBLIGATORIA",
        4: "STATO DI SEGREGAZIONE FUNZIONALE"
    },
    "CONVIVENZA": {
        1: "CAPITOLATO DI GESTIONE ORDINARIA",
        2: "PROTOCOLLO DI TUTELA DELLE RISORSE",
        3: "REGIME DI SEPARAZIONE DOMESTICA",
        4: "STATO DI DISSOCIAZIONE ABITATIVA"
    },
    "CONOSCENZA": {
        1: "PROTOCOLLO DI CORTESIA CIVILE",
        2: "LIVELLO DI INTERAZIONE SUPERFICIALE",
        3: "REGIME DI DISTACCO PREVENTIVO",
        4: "STATO DI IRRILEVANZA RECIPROCA"
    },
    "AMICIZIA": {
        1: "PATTO DI LEALTÀ BASE",
        2: "PROTOCOLLO DI MANUTENZIONE PREVENTIVA",
        3: "REGIME DI FREQUENTAZIONE REGOLAMENTATA",
        4: "STATO DI SOSPENSIONE AFFETTIVA"
    }
}

CLAUSOLE_DB = {
    "PROFESSIONALE": {
        1: "01. Protocollo di Denominazione Asettica: Vietati soprannomi e confidenza.",
        2: "02. Sterilizzazione Tematica: Vietato small talk e argomenti privati.",
        3: "03. Distanziamento Prossemico: Mantenere 120cm di distanza.",
        4: "04. Divieto Simultaneità: Pause scaglionate obbligatorie.",
        5: "05. Divieto Espressività: Niente emoji o toni emotivi nelle email.",
        6: "06. Policy Anti-Dono: Vietato scambiarsi favori o cibo.",
        7: "07. Disposizione Non Adiacente: Postazioni orientate per evitare sguardi.",
        8: "08. Supporto Vicario: Aiuto reciproco solo tramite ticket formale.",
        9: "09. Zero-Touch Policy: Abolita la stretta di mano e contatto fisico.",
        10: "10. Segregazione Extra-Lavorativa: Vietato frequentare stessi locali.",
        11: "11. Tracciabilità Forense: Ogni parola detta va verbalizzata.",
        12: "12. Feedback Depersonalizzato: Valutazioni solo anonime via sistema.",
        13: "13. Divieto Accordi Autonomi: Nulle le decisioni a quattr'occhi.",
        14: "14. Soglia Gottman: Contatto visivo max 15 secondi.",
        15: "15. Inalienabilità Risorse: Vietato toccare la cancelleria altrui.",
        16: "16. Script Approvati: Parlare solo usando frasi pre-fatte.",
        17: "17. Congelamento Competitivo: Se uno viene promosso, l'altro no.",
        18: "18. Divieto Peer-to-Peer: Vietato scambio diretto di documenti.",
        19: "19. Isolamento Coatto: Trasferimento di sede per uno dei due.",
        20: "20. Risoluzione Preventiva: Licenziamento per incompatibilità."
    },
    "CONVIVENZA": {
        1: "01. Etichettatura Alimentare: Ogni cibo deve avere le iniziali.",
        2: "02. Decadenza Organico: Piatti sporchi nel lavello max 30 min.",
        3: "03. Divieto Colonizzazione: Rimuovere oggetti personali dalle aree comuni.",
        4: "04. Soglie Decibel: Silenzio assoluto (40db) dalle 23 alle 07.",
        5: "05. Turnazione Bagno: Max 15 minuti a testa la mattina.",
        6: "06. Visti Ingresso: Ospiti ammessi solo con preavviso 24h.",
        7: "07. Divieto Appropriazione: Vietato usare olio/sapone altrui.",
        8: "08. Invarianza Termica: Vietato toccare il termostato.",
        9: "09. Neutralità Olfattiva: Vietati incensi, fritti o profumi forti.",
        10: "10. Divieto Post-It: Comunicazioni solo via chat tracciabile.",
        11: "11. Flussi Finanziari: Pagamenti solo via bonifico automatico.",
        12: "12. Zone Rosse: Vietato entrare nella camera dell'altro.",
        13: "13. Razionamento Idrico: Doccia a tempo limitato.",
        14: "14. Organismi Non Contrattualizzati: Vietati animali o piante.",
        15: "15. Stasi Arredo: Vietato spostare mobili comuni.",
        16: "16. Segregazione Pasti: Mangiare in orari diversi.",
        17: "17. Isolamento Acustico: Obbligo di cuffie nelle aree comuni.",
        18: "18. Prenotazione Salotto: Uso divano solo su appuntamento.",
        19: "19. Intermediazione Digitale: Scriversi anche se si è nella stessa stanza.",
        20: "20. Dissoluzione Abitativa: Sfratto selettivo deciso da ALUA."
    },
    "CONOSCENZA": {
        1: "01. Identificazione Nominale: Obbligo di ricordare il nome.",
        2: "02. Perimetro Neutro: Parlare solo di meteo e traffico.",
        3: "03. Saluto Standard: Solo cenno del capo, niente baci.",
        4: "04. Diritto Recesso: Possibilità di chiudere la chat in ogni momento.",
        5: "05. Moratoria Digital: Niente social prima di 48 ore.",
        6: "06. Distanza Sociale: Stare ad almeno 1 metro.",
        7: "07. Divieto Divulgazione: Non raccontare i propri traumi.",
        8: "08. Intento Esplicito: Chiarire subito se è lavoro o flirt.",
        9: "09. Divieto Procrastinazione: Vietato dire 'ci vediamo' se è falso.",
        10: "10. Invisibilità Digital: Vietato fare foto o storie insieme.",
        11: "11. Conti Separati: Ognuno paga il suo, niente giri offerti.",
        12: "12. Informativa Terzi: Avvisare prima di presentare altri amici.",
        13: "13. Divieto Deep Liking: Non mettere like a foto vecchie.",
        14: "14. Letteralità Rifiuto: Se dice no, significa no.",
        15: "15. Proibizione Omaggi: Vietato fare regali.",
        16: "16. Inibizione Approccio: Se ci si incrocia, ignorarsi.",
        17: "17. Segregazione Privacy: Nascondere le storie 'Amici Stretti'.",
        18: "18. Turnazione Spazi: Andare in palestra a orari diversi.",
        19: "19. Divieto Gossip: Vietato parlare dell'altro con terzi.",
        20: "20. Patto Indifferenza: Tornare a essere perfetti estranei."
    },
    "AMICIZIA": {
        1: "01. Tolleranza Cronometrica: Ritardo massimo 15 minuti.",
        2: "02. Solvibilità Immediata: Restituire i soldi entro 24h.",
        3: "03. Tracciabilità Comodato: Restituire libri/vestiti entro 30gg.",
        4: "04. Penale Cancellazione: Avvisare 12h prima se si dà buca.",
        5: "05. Stop Vocali: Vietati audio sopra i 60 secondi.",
        6: "06. Regolamentazione Sfoghi: Chiedere permesso prima di lamentarsi.",
        7: "07. Divieto +1: Non portare fidanzati se non concordato.",
        8: "08. Divieto Giudizio: Non criticare le scelte passate.",
        9: "09. Segretezza NDA: I segreti restano segreti.",
        10: "10. Pluralità: Accettare che l'altro abbia altri amici.",
        11: "11. Divieto Ibridazione: Non mischiare gruppi diversi a caso.",
        12: "12. Prestiti Scritti: Niente soldi sulla fiducia.",
        13: "13. No Competizione: Non vantarsi dei successi per sminuire.",
        14: "14. Obbligo Riscontro: Rispondere ai messaggi entro 48h.",
        15: "15. No Strumentalizzazione: Non chiedere sconti professionali.",
        16: "16. Calendarizzazione: Vedersi solo su appuntamento.",
        17: "17. Sterilizzazione Temi: Vietato parlare di politica/ex.",
        18: "18. Razionamento Contatto: Max 1 chiamata a settimana.",
        19: "19. Neutralità: Non schierarsi nelle liti altrui.",
        20: "20. Dissoluzione Formale: Chiudere l'amicizia ufficialmente."
    }
}