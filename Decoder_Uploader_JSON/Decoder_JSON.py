# PROGRAMMA PER FORMATTARE CORRETTAMENTE IL DATASET IN MODO DA POTERLO USARE CORRETTAMENTE E CARICARE SUL DATABASE POSTGRESQL
# HO PRESO SPUNTO DA: https://stackoverflow.com/questions/55555095/how-to-add-commas-in-between-json-objects-present-in-a-txt-file-and-then-conver
#                     https://www.geeksforgeeks.org/reading-and-writing-json-to-a-file-in-python/

import json

parser = json.JSONDecoder() # creo un oggetto di tipo JSONDecoder per correggere il dataset
parsed = [] # lista vuota che conterrà il dataset identato correttamente
with open("tweet.json", encoding='utf8') as f: # specifico la codifica perché ci sono delle emoji in tweet.text
    data = f.read() # assegno a data il dataset come fosse una stringa
    data = data.replace("'", "'"+"'") # sostituisco ogni apice con un doppio apice per renderlo compatibile con SQL

head = 0
for row in data: # scorro tutti il dataset
    head = (data.find('{', head) + 1 or data.find('[', head) + 1) - 1 # prendo l'inizio di ogni "oggetto" del dataset
    try:
        struct, head = parser.raw_decode(data, head) # attraverso l'uso del decodificatore correggo ogni oggetto del dataset
        parsed.append(struct)   # mette la stringa "decodificata" in fondo alla lista
    except (ValueError, json.JSONDecodeError):
        break

with open("tweet2.json", "w") as outfile: 
    json.dump(parsed, outfile, separators = (',', ': '), indent = 1) # creo un file con una formattazione leggibile

print("\nFile JSON formattato correttamente!")
