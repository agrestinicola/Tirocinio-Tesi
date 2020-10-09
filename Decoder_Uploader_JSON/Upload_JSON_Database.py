# PROGRAMMA PER CREARE LE TABELLE SU UN DATABASE POSGRESQL E POPOLARLE CON UN DATASET.JSON
# HO PRESO SPUNTO DA: https://stackoverflow.com/questions/48604563/creating-a-data-structure-from-json-using-python

import json
import psycopg2
from myAppConfig import myHost, myDatabase, myUser, myPsw # file dove ho le credenziali per connettermi con il database

connessione = psycopg2.connect (host = myHost, database = myDatabase, user = myUser, password = myPsw) # creo la connessione

with connessione:
    with connessione.cursor() as cursore:
        # apro il dataset Json
        with open("createsRT.json", encoding='utf8') as f:
            data = json.load(f)

        keys = []
        for row in data: # scorro ogni oggetto nel dataset
            for key in row.keys(): # per ogni chiave trovata tramite il metodo keys()
                if key not in keys: # se non è già presente nella lista
                    keys.append(key) # la inserisco nella lista

        for row in data:
            # per ogni oggetto del dataset creo la stringa query per inserirlo nel database e la eseguo
            query = "INSERT INTO creates (user_id, status_id, type, reply_to_status_id, reply_to_user_id) VALUES({0});".format(",".join(map(lambda key: "'{0}'".format(row[key]) if key in row else "NULL", keys)))
            cursore.execute(query)

        print("Caricamento completato, tuple inserite!")

connessione.close()
print("Connessione chiusa con successo!")