# PROGRAMMA PER CREARE UNA TUPLA UNIVOCA CHE RAPPRESENTA UN RETWEET E LA SUA CREAZIONE DA PARTE DI UN UTENTE

import json
import random

retweet = [] # lista che contiene le tuple generate dei creates per il type RT
user = [] # lista che contiene tutti gli user_id del dataset
tweetRT = [] # lista che contiene le tuple generate in base ai creates
posUtente = 1 # posizione nella lista degli user_id
count = 0

with open ("creates_rtcount.json", encoding='utf8') as file1: # apro il file che contiene il numero dei retweet
                                                                                                                                                              # il testo, la data di creazione e l'id
    reader = json.load(file1)

    with open ("utente.json") as file2: # apro il file con gli user_id

        utenti = json.load(file2)

        # salvo tutti gli user_id nella lista
        for utente in utenti:
            u = utente['user_id']
            user.append(u)

    for row in reader: # per ogni tupla nel file creates.json
        if row['retweet_count'] > 0: # controllo se ha più di 0 retweet
            for tupla in range(row['retweet_count']): # se sì genero N tuple tante quante il numeri dei retweet
                stringa = {"user_id": user[posUtente], # creo una nuova tupla con un user_id preso dalla lista e la scorro in ordine crescente
                           "status_id": row['status_id'], # lo status_id del tweet originale
                           "type": "RT", # assegno il tipo RT
                           "reply_to_status_id": None, # valori null in quanto non è una risposta 'RE'
                           "reply_to_user_id": None}
                retweet.append(stringa)
                if posUtente != len(user) - 1: # se non sono alla fine della lista degli user_id
                    posUtente = posUtente + 1 # incremento il contatore per scorrerla
                else:
                    posUtente = 0 # altrimenti ritorno all'inizio
        count = count + 1
        print("{}{}".format("Riga del file creates.csv numero: ", count))

    # creo i file in output
    with open("createsRT.json", "w") as outfile: 
        json.dump(retweet, outfile, indent = 1)    
    print("File creato!")
