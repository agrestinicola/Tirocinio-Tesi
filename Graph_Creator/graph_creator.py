import matplotlib.pyplot as plt # per creare l'immagine del grafo
import networkx as nx # per creare il grafo 
import psycopg2 # per connettermi al database
import os # per pulire la console tramite il menù
import datetime # per gestire i timestamp del database e calcolare gli intervalli di tempo
import math # per gestire il valore infinito
import filecmp # per confrontare i file.edgelist che si creano tramite il path-consistency
import copy # per eseguire la deepcopy del grafo e dei dizionari delle etichette
from datetime import datetime
from collections import OrderedDict # per creare un dizionario ordinato dei retweet
from collections import defaultdict # per creare un dizionario con delle liste come valori
from ordered_set import OrderedSet # per mantenere l'ordine di una lista
from myAppConfig import myHost, myUser, myPsw, myDatabase # file che contiene le mie credenziali per la connessione

edge_colors = [] # lista dove assegno un colore per ogni edge in base alle caratteristiche
node_colors = [] # lista dove assegno un colore per ogni nodo in base alle caratteristiche
retweet_id = [] # lista dove salverò l' id di ogni retweet in modo da poter colorare l'arco di verde
attr_dict_qualitativo = {"Start" : 0, "End": math.inf} # dizionario per assegnare dei valori qualitativi
tuplaQualitativa = (0, math.inf) # tupla per gli archi qualitativi

# creo la connessione con le credenziali del database postgresql
connessione = psycopg2.connect(host = myHost, database = myDatabase, user = myUser, password = myPsw)

######################### FUNZIONI PER APPLICARE ALGORITMO PATH CONSISTENCY##################################
def path_consistency(G):
    changed = True
    count = 0 # contatore per il numero di esecuzioni dell'algoritmo
    while(changed == True): # esegue l'algoritmo finchè apporta delle modifiche al grafo
        count = count + 1
        # Salvo il grafo iniziale
        G_edgelist = open('G_file.txt', 'wb')
        nx.write_edgelist(G, G_edgelist)
        G_edgelist.close()

        # Genero il nuovo grafo con l'algoritmo applicato
        G_new = copy.deepcopy(path_consistency_step(G))
        
        # Salvo il nuovo grafo
        G_new_edgelist = open('G_new_file.txt', 'wb')
        nx.write_edgelist(G_new, G_new_edgelist)
        G_new_edgelist.close()

        G_edgelist = open('G_file.txt')
        G_new_edgelist = open('G_new_file.txt')

        # Controllo se i due grafi sono uguali facendo il confronto dei loro file con lista di archi+etichette
        if filecmp.cmp('G_file.txt', 'G_new_file.txt', shallow=False) == True:
            G_edgelist.close()
            G_new_edgelist.close()
            print("La "+str(count)+"° esecuzione non ha apportato modifiche.")
            changed = False # se sono uguali chiudo il ciclo while in quanto non ha apportato nessuna modifica
        else: # se il grafo dopo l'algoritmo è diverso da quello originale
            G_edgelist.close()
            G_new_edgelist.close()
            G = copy.deepcopy(G_new) # aggiorno l'originale con il grafo nuovo e rieseguo l'algoritmo
            print(str(count) + "° esecuzione dell'algoritmo.")

    return G_new

def path_consistency_step(G):
    G_new = nx.DiGraph() # genero un nuovo grafo vuoto
    G_new.add_nodes_from(copy.deepcopy(G.nodes(data = False))) # copio all'intero solamente i nodi del grafo G, senza archi ed etichette
    
    for edge in G.edges(): # per ogni arco del grafo
        triangles = []
        triangles = get_triangles(G, edge[0], edge[1]) # trovo tutte le combinazioni tra nodi (i,j,k) che formano un triangolo
        for t in triangles: # per ogni triangolo
            if (G.has_edge(t[0], t[1]) and G.has_edge(t[1], t[2])): # nel caso il triangolo sia del tipo i->k, k->j

                if G_new.has_edge(t[0], t[2]) == True: # se il nuovo arco ha l'arco i->j prendo la sua etichetta
                    Rij_label = {}
                    Rij_label =  copy.deepcopy(G_new.get_edge_data(t[0], t[2])) # salvo una copia dell'etichetta dell'arco i->j
                    Rij = (Rij_label['attr_dict']['Start'], Rij_label['attr_dict']['End']) # creo una tupla con i valori (Start, End)
                else: # altrimenti prendo quella dell'arco precedente
                    Rij_label = {}
                    Rij_label =  copy.deepcopy(G.get_edge_data(t[0], t[2])) # salvo una copia dell'etichetta dell'arco i->j
                    Rij = (Rij_label['attr_dict']['Start'], Rij_label['attr_dict']['End']) # creo una tupla con i valori (Start, End)

                Rik_label = {}
                Rik_label =  copy.deepcopy(G.get_edge_data(t[0], t[1])) # salvo una copia dell'etichetta dell'arco i->k
                Rik = (Rik_label['attr_dict']['Start'], Rik_label['attr_dict']['End'])
                
                Rkj_label = {}
                Rkj_label = copy.deepcopy(G.get_edge_data(t[1], t[2])) # salvo una copia dell'etichetta dell'arco k->j
                Rkj = (Rkj_label['attr_dict']['Start'], Rkj_label['attr_dict']['End'])
                
                autori = []
                for autore1 in Rik_label['attr_dict']['Authors']:
                    for autore2 in Rkj_label['attr_dict']['Authors']:
                        if autore1[0] == autore2[0]:
                            autori.append((autore1[0], max(autore1[1], autore2[1])))
                        else:
                            autori.append(autore1)
                            autori.append(autore2)

                Rikj = (Rik[0]+Rkj[0], Rik[1]+Rkj[1]) # eseguo la composizione dei valori delle tuple (i,k) (k,j)

                # eseguo la congiunzione della tupla (i,j) con il risultato della combinazione precedente
                if Rij[0] >= Rikj[0]:
                    if Rij[1] >= Rikj[1]:
                        Rij_new = [Rij[0], Rikj[1], Rij_label['attr_dict']['Authors']]
                    else:
                        Rij_new = [Rij[0], Rij[1], Rij_label['attr_dict']['Authors']]
                elif Rij[0] < Rikj[0]:
                    if Rij[1] >= Rikj[1]:
                        Rij_new = [Rikj[0], Rikj[1], Rij_label['attr_dict']['Authors']]
                    else:
                        Rij_new = [Rikj[0], Rij[1], Rij_label['attr_dict']['Authors']]
                
                for index, autore in enumerate(autori):
                    y = list(autore)
                    y[1] = similarity(Rikj[0], Rikj[1], Rij_new[0], Rij_new[1])
                    autori[index] = y

                for index, autore in enumerate(Rij_new[2]):
                    y = list(autore)
                    y[1] = similarity(Rij_label['attr_dict']['Start'], Rij_label['attr_dict']['End'], Rij_new[0], Rij_new[1])
                    Rij_new[2][index] = y

                Rij_new[2] = Rij_new[2]+autori

                for index1, autore1 in enumerate(Rij_new[2]):
                    for index2, autore2 in enumerate(Rij_new[2]):
                        if autore1 == autore2:
                            continue
                        elif autore1[0] == autore2[0]:
                            Rij_new[2][index1] = [autore1[0], max(autore1[1], autore2[1])]
                            Rij_new[2][index2] = [autore2[0], max(autore1[1], autore2[1])]


                Rij_new[2] = [t for t in (set(tuple(i) for i in Rij_new[2]))]

                # aggiorno i valori dell'etichetta
                Rij_label['attr_dict']['Start'] = Rij_new[0]
                Rij_label['attr_dict']['End'] = Rij_new[1]
                Rij_label['attr_dict']['Authors'] = Rij_new[2]

                # genero la nuova etichetta per il grafo in modo leggibile, uso una tupla per contenere i valori
                new_time = tuple(x for x in Rij_label['attr_dict'].values())
                
                # se la nuova etichetta calcolata non è nella lista di etichette dell'arco la aggiungo
                # if new_time not in Rij_label['time_list']:
                #     Rij_label['time_list'].append(new_time)

                # aggiungo l'arco al nuovo grafo nel caso non sia presente, altrimenti aggiorna solamente le etichette con i nuovi valori
                G_new.add_edge(t[0], t[2], attr_dict = Rij_label['attr_dict'], time = new_time)

            elif (G.has_edge(t[0], t[1]) and G.has_edge(t[2], t[1])): # nel caso il triangolo sia del tipo i->k, j->k

                if G_new.has_edge(t[0], t[2]) == True:
                    Rij_label = {}
                    Rij_label =  copy.deepcopy(G_new.get_edge_data(t[0], t[2])) # salvo una copia dell'etichetta dell'arco i->j
                    Rij = (Rij_label['attr_dict']['Start'], Rij_label['attr_dict']['End']) # creo una tupla con i valori (Start, End)
                else:
                    Rij_label = {}
                    Rij_label =  copy.deepcopy(G.get_edge_data(t[0], t[2])) # salvo una copia dell'etichetta dell'arco i->j
                    Rij = (Rij_label['attr_dict']['Start'], Rij_label['attr_dict']['End']) # creo una tupla con i valori (Start, End)
                
                Rik_label = {}
                Rik_label =  copy.deepcopy(G.get_edge_data(t[0], t[1]))
                Rik = (Rik_label['attr_dict']['Start'], Rik_label['attr_dict']['End'])
                
                Rjk_label = {}
                Rjk_label =  copy.deepcopy(G.get_edge_data(t[2], t[1]))
                Rjk = (-Rjk_label['attr_dict']['End'], -Rjk_label['attr_dict']['Start'])
                
                autori = []
                for autore1 in Rik_label['attr_dict']['Authors']:
                    for autore2 in Rjk_label['attr_dict']['Authors']:
                        if autore1[0] == autore2[0]:
                            autori.append((autore1[0], max(autore1[1], autore2[1])))
                        else:
                            autori.append(autore1)
                            autori.append(autore2)

                Rijk = (Rik[0]+Rjk[0], Rik[1]+Rjk[1])
                
                if Rij[0] >= Rijk[0]:
                    if Rij[1] >= Rijk[1]:
                        Rij_new = [Rij[0], Rijk[1], Rij_label['attr_dict']['Authors']]
                    else:
                        Rij_new = [Rij[0], Rij[1], Rij_label['attr_dict']['Authors']]
                elif Rij[0] < Rijk[0]:
                    if Rij[1] >= Rijk[1]:
                        Rij_new = [Rijk[0], Rijk[1], Rij_label['attr_dict']['Authors']]
                    else:
                        Rij_new = [Rijk[0], Rij[1], Rij_label['attr_dict']['Authors']]

                for index, autore in enumerate(autori):
                    y = list(autore)
                    y[1] = similarity(Rijk[0], Rijk[1], Rij_new[0], Rij_new[1])
                    autori[index] = y

                for index, autore in enumerate(Rij_new[2]):
                    y = list(autore)
                    y[1] = similarity(Rij_label['attr_dict']['Start'], Rij_label['attr_dict']['End'], Rij_new[0], Rij_new[1])
                    Rij_new[2][index] = y

                Rij_new[2] = Rij_new[2]+autori

                for index1, autore1 in enumerate(Rij_new[2]):
                    for index2, autore2 in enumerate(Rij_new[2]):
                        if autore1 == autore2:
                            continue
                        elif autore1[0] == autore2[0]:
                            Rij_new[2][index1] = [autore1[0], max(autore1[1], autore2[1])]
                            Rij_new[2][index2] = [autore2[0], max(autore1[1], autore2[1])]

                Rij_new[2] = [t for t in (OrderedSet(tuple(i) for i in Rij_new[2]))]

                # aggiorno i valori dell'etichetta
                Rij_label['attr_dict']['Start'] = Rij_new[0]
                Rij_label['attr_dict']['End'] = Rij_new[1]
                Rij_label['attr_dict']['Authors'] = Rij_new[2]

                # genero la nuova etichetta per il grafo in modo leggibile
                new_time = tuple(x for x in Rij_label['attr_dict'].values())
                
                # if new_time not in Rij_label['time_list']:
                #     Rij_label['time_list'].append(new_time)

                G_new.add_edge(t[0], t[2], attr_dict = Rij_label['attr_dict'], time = new_time)

            elif (G.has_edge(t[1], t[0]) and G.has_edge(t[1], t[2])): # nel caso il triangolo sia del tipo k->i, k->j

                if G_new.has_edge(t[0], t[2]) == True:
                    Rij_label = {}
                    Rij_label =  copy.deepcopy(G_new.get_edge_data(t[0], t[2])) # salvo una copia dell'etichetta dell'arco i->j
                    Rij = (Rij_label['attr_dict']['Start'], Rij_label['attr_dict']['End']) # creo una tupla con i valori (Start, End)
                else:
                    Rij_label = {}
                    Rij_label =  copy.deepcopy(G.get_edge_data(t[0], t[2])) # salvo una copia dell'etichetta dell'arco i->j
                    Rij = (Rij_label['attr_dict']['Start'], Rij_label['attr_dict']['End']) # creo una tupla con i valori (Start, End)
                
                Rki_label = {}
                Rki_label =  copy.deepcopy(G.get_edge_data(t[1], t[0]))
                Rki = (-Rki_label['attr_dict']['End'], -Rki_label['attr_dict']['Start'])
                
                Rkj_label = {}
                Rkj_label =  copy.deepcopy(G.get_edge_data(t[1], t[2]))
                Rkj = (Rkj_label['attr_dict']['Start'], Rkj_label['attr_dict']['End'])
                
                Rkij = (Rki[0]+Rkj[0], Rki[1]+Rkj[1])
                
                if Rij[0] >= Rkij[0]:
                    if Rij[1] >= Rkij[1]:
                        Rij_new = [Rij[0], Rkij[1], Rij_label['attr_dict']['Authors']]
                    else:
                        Rij_new = [Rij[0], Rij[1], Rij_label['attr_dict']['Authors']]
                elif Rij[0] < Rkij[0]:
                    if Rij[1] >= Rkij[1]:
                        Rij_new = [Rkij[0], Rkij[1], Rij_label['attr_dict']['Authors']]
                    else:
                        Rij_new = [Rkij[0], Rij[1], Rij_label['attr_dict']['Authors']]

                for index, autore in enumerate(autori):
                    y = list(autore)
                    y[1] = similarity(Rkij[0], Rkij[1], Rij_new[0], Rij_new[1])
                    autori[index] = y

                for index, autore in enumerate(Rij_new[2]):
                    y = list(autore)
                    y[1] = similarity(Rij_label['attr_dict']['Start'], Rij_label['attr_dict']['End'], Rij_new[0], Rij_new[1])
                    Rij_new[2][index] = y

                Rij_new[2] = Rij_new[2]+autori

                for index1, autore1 in enumerate(Rij_new[2]):
                    for index2, autore2 in enumerate(Rij_new[2]):
                        if autore1 == autore2:
                            continue
                        elif autore1[0] == autore2[0]:
                            Rij_new[2][index1] = [autore1[0], max(autore1[1], autore2[1])]
                            Rij_new[2][index2] = [autore2[0], max(autore1[1], autore2[1])]

                Rij_new[2] = [t for t in (set(tuple(i) for i in Rij_new[2]))]

                # aggiorno i valori dell'etichetta
                Rij_label['attr_dict']['Start'] = Rij_new[0]
                Rij_label['attr_dict']['End'] = Rij_new[1]
                Rij_label['attr_dict']['Authors'] = Rij_new[2]

                # genero la nuova etichetta per il grafo in modo leggibile
                new_time = tuple(x for x in Rij_label['attr_dict'].values())
                
                # if new_time not in Rij_label['time_list']:
                #     Rij_label['time_list'].append(new_time)

                G_new.add_edge(t[0], t[2], attr_dict = Rij_label['attr_dict'], time = new_time)

            elif (G.has_edge(t[1], t[0]) and G.has_edge(t[2], t[1])): # nel caso il triangolo sia del tipo k->i, j->k

                if G_new.has_edge(t[0], t[2]) == True:
                    Rij_label = {}
                    Rij_label =  copy.deepcopy(G_new.get_edge_data(t[0], t[2])) # salvo una copia dell'etichetta dell'arco i->j
                    Rij = (Rij_label['attr_dict']['Start'], Rij_label['attr_dict']['End']) # creo una tupla con i valori (Start, End)
                else:
                    Rij_label = {}
                    Rij_label =  copy.deepcopy(G.get_edge_data(t[0], t[2])) # salvo una copia dell'etichetta dell'arco i->j
                    Rij = (Rij_label['attr_dict']['Start'], Rij_label['attr_dict']['End']) # creo una tupla con i valori (Start, End)
                
                Rki_label = {}
                Rki_label =  copy.deepcopy(G.get_edge_data(t[1], t[0]))  
                Rki = (-Rki_label['attr_dict']['End'], -Rki_label['attr_dict']['Start'])
                
                Rjk_label = {}
                Rjk_label =  copy.deepcopy(G.get_edge_data(t[2], t[1]))
                Rjk = (Rjk_label['attr_dict']['Start'], Rjk_label['attr_dict']['End'])
                
                autori = []
                for autore1 in Rki_label['attr_dict']['Authors']:
                    for autore2 in Rjk_label['attr_dict']['Authors']:
                        if autore1[0] == autore2[0]:
                            autori.append((autore1[0], max(autore1[1], autore2[1])))
                        else:
                            autori.append(autore1)
                            autori.append(autore2)

                Rijk = (Rki[0]+Rjk[0], Rki[1]+Rjk[1])
                
                if Rij[0] >= Rijk[0]:
                    if Rij[1] >= Rijk[1]:
                        Rij_new = [Rij[0], Rijk[1], Rij_label['attr_dict']['Authors']]
                    else:
                        Rij_new = [Rij[0], Rij[1], Rij_label['attr_dict']['Authors']]
                elif Rij[0] < Rijk[0]:
                    if Rij[1] >= Rijk[1]:
                        Rij_new = [Rijk[0], Rijk[1], Rij_label['attr_dict']['Authors']]
                    else:
                        Rij_new = [Rijk[0], Rij[1], Rij_label['attr_dict']['Authors']]
            
                for index, autore in enumerate(autori):
                    y = list(autore)
                    y[1] = similarity(Rijk[0], Rijk[1], Rij_new[0], Rij_new[1])
                    autori[index] = y

                for index, autore in enumerate(Rij_new[2]):
                    y = list(autore)
                    y[1] = similarity(Rij_label['attr_dict']['Start'], Rij_label['attr_dict']['End'], Rij_new[0], Rij_new[1])
                    Rij_new[2][index] = y

                Rij_new[2] = Rij_new[2]+autori

                for index1, autore1 in enumerate(Rij_new[2]):
                    for index2, autore2 in enumerate(Rij_new[2]):
                        if autore1 == autore2:
                            continue
                        elif autore1[0] == autore2[0]:
                            Rij_new[2][index1] = [autore1[0], max(autore1[1], autore2[1])]
                            Rij_new[2][index2] = [autore2[0], max(autore1[1], autore2[1])]

                Rij_new[2] = [t for t in (set(tuple(i) for i in Rij_new[2]))]

                # aggiorno i valori dell'etichetta
                Rij_label['attr_dict']['Start'] = Rij_new[0]
                Rij_label['attr_dict']['End'] = Rij_new[1]
                Rij_label['attr_dict']['Authors'] = Rij_new[2]

                # genero la nuova etichetta per il grafo in modo leggibile
                new_time = tuple(x for x in Rij_label['attr_dict'].values())

                # if new_time not in Rij_label['time_list']:
                #     Rij_label['time_list'].append(new_time)

                G_new.add_edge(t[0], t[2], attr_dict = Rij_label['attr_dict'], time = new_time)
    
    return G_new 

# Ritorna una lista di tuple (i,k,j) formate da nodi collegati con le seguenti combinazioni:
# (i,j) (i,k) (k,j) or
# (i,j) (i,k) (j,k) or
# (i,j) (k,i) (k,j) or
# (i,j) (k,i) (j,k)
def get_triangles(G, i, j):
    result = []
    for nodo in G.nodes():
        if (G.has_edge(i, nodo) and G.has_edge(nodo, j)) or \
           (G.has_edge(i, nodo) and G.has_edge(j, nodo)) or \
           (G.has_edge(nodo, i) and G.has_edge(nodo, j)) or \
           (G.has_edge(nodo, i) and G.has_edge(j, nodo)):
            
            triangle = (i, nodo, j)
            result.append(triangle)

    return result

#############################################################################################################

################################## FUNZIONI PER CALCOLARE LA SIMILARITA' ####################################
def intersection (start1, end1, start2, end2): # [start1, end1] è il primo intervallo e [start2, end2] è il secondo
    start = max(start1, start2)
    end = min(end1, end2)
    if end >= start:
        return end - start
    else:
        return 0

def union (start1, end1, start2, end2): # [start1, end1] è il primo intervallo e [start2, end2] è il secondo
    start = min(start1, start2)
    end = max(end1, end2)
    if end >= start:
        return end - start
    else:
        return 0

def similarity (start1, end1, start2, end2): # start1,end1 Rij vecchio, start2,end2 Rij_new
    i = intersection (start1, end1, start2, end2)
    u = union (start1, end1, start2, end2)
    if u == math.inf:
        return 0.1
    elif u != 0:
        return i / u    
    else:
        return 0
#############################################################################################################

################### FUNZIONE PER MAPPARE I COLORI DEL SOTTO-GRAFO ###########################################
def mapping_colors_nodes_edges(G):
    edge_colors.clear()
    node_colors.clear()
    for node in G: # per ogni nodo del sotto-grafo
            if node in check_tweetTW: # se il nodo è un tweet originale
                node_colors.append('#269AED') # il nodo lo metto azzurro
            elif node in check_tweetQT: # se il nodo è un quotes
                node_colors.append('#EB8D00') # il nodo lo metto arancione
            elif node in check_tweetRE: # se il nodo è un reply
                node_colors.append('#FFE100') # il nodo lo metto giallo
            elif node in check_tweetREQT: # se il nodo è un reply con quotes
                node_colors.append('#AA00FF') # il nodo lo metto viola
            elif node == 'DB': # se è il nodo radice
                node_colors.append('red') # il nodo lo coloro di rosso
            else: # se il nodo è un retweet
                node_colors.append('#0DA342') # il nodo lo metto verde                
                
    for edge in G.edges: # per ogni arco del grafo
        if any(ele in edge for ele in retweet_id) == True: # se è un retweet
            edge_colors.append('#0DA342') # coloro l'arco di verde
        elif any(ele in edge for ele in check_tweetQT) == True: # se è un quotes
            edge_colors.append('#EB8D00') # coloro l'arco di arancione
        elif any(ele in edge for ele in check_tweetRE) == True: # se è un reply
            edge_colors.append('#FFE100') # coloro l'arco di giallo
        elif any(ele in edge for ele in check_tweetREQT) == True: # se è un reply con quotes
            edge_colors.append('#AA00FF') # coloro l'arco di viola
        elif any(ele in edge for ele in check_tweetTW) == True: # se è un tweet originale
            edge_colors.append('#269AED') # coloro l'arco di azzurro
#############################################################################################################

############################ FUNZIONE CHE SALVA UN GRAFO SOTTO FORMA DI EDGE LIST ###########################
def save_file_edgelist(G):
    if not nx.is_empty(G):
        nome = input("Inserire un nome per il salvataggio del grafo: ")
        nome = ''+nome+'.txt'
        f = open(nome, 'wb')
        nx.write_edgelist(G, f)
        print("Sotto-grafo salvato correttamente.")
        f.close()
    else:
        print("Non c'è nessun sotto-grafo da salvare.")
#############################################################################################################

############################ FUNZIONE CHE LEGGE UN GRAFO SOTTO FORMA DI EDGE LIST ###########################
def read_file_edgelist():
    nome = input("Inserire il nome del grafo da caricare: ")
    nome = ''+nome+'.txt'
    try:
        f = open(nome, 'rb')
        G = nx.read_edgelist(f, create_using = nx.DiGraph())
        f.close()
        print("Sotto-grafo letto correttamente.")
        return G
    except:
        print("Il nome inserito non esiste!")
#############################################################################################################

############################### FUNZIONE PER DISEGNARE IL SOTTO-GRAFO #######################################
def print_graph (sub_G):
    posSub_G = nx.shell_layout(sub_G) # mappo la posizione dei nodi del sotto-grafo in cerchi concentrici
    mapping_colors_nodes_edges(sub_G) # coloro i nodi e archi del sotto-grafo
    nx.draw_networkx(sub_G, pos = posSub_G, with_labels = True, node_color = node_colors, edge_color = edge_colors, font_size = 9) # disegno il sotto-grafo con le mappature adeguate in precedenza
    nx.draw_networkx_edge_labels(sub_G, pos = posSub_G, edge_labels = nx.get_edge_attributes(sub_G, 'time'), font_color = 'red', font_size = 7)
    plt.plot(1)
    plt.show(block = False)
#############################################################################################################

##################################### FUNZIONI GESTIONE MENU ################################################
def menu(): # menù di scelte per scegliere cosa fare
    print('*' * 55)
    comando = input("Scegliere uno dei seguenti comandi:\n"\
                    "1) Applica l'algoritmo Path Consistency al grafo.\n"\
                    "2) Salvare il grafo creato in un file.\n"\
                    "3) Caricare un grafo da un file.\n"\
                    "4) Visualizzare il grafo creato/modificato o caricato dal file.\n"\
                    "0) Pulire la console.\n"\
                    "q) exit()\n\n")

    if comando == 'q':
        print('*' * 55)
        return comando
    else:
        print('*' * 55)
        return int(comando)

def loop(G): # continuo a chiedere di inserire un valore fino a quando non viene inserita la 'q'
    try:
        # sub_G = nx.DiGraph(name = "Sotto-grafo del Database") # inizializzo un sotto-grafo
        x = menu()
        while x in {0, 1, 2, 3, 4, 'q'}:
            if x == 'q':
                print("Sto chiudendo il programma...")
                break
            if x == 0:
                os.system("cls")
                x = menu()
            if x == 1:
                G = path_consistency(G)
                print("Algoritmo applicato.") 
                x = menu()
            if x == 2:
                save_file_edgelist(G)
                x = menu()
            if x == 3:
                G = read_file_edgelist()
                x = menu()
            if x == 4:
                print_graph(G)
                x = menu()
        if x not in {0, 1, 2, 3, 4, 'q'}:
            raise ValueError
    except ValueError:
        print("Hai inserito una scelta del menù non valida, ritenta!\n")
        loop(G)
#############################################################################################################

######################################## CREAZIONE DELLA CONNESSIONE AL DATABASE, QUERY E CREAZIONE DEL GRAFO #################################################
with connessione:
    with connessione.cursor() as cursore:
        graph = nx.DiGraph(name = 'Database') # inizializzo il grafO
        ############################################ CREO UN ARCO COLLEGATO AL NODO RADICE PER OGNI TWEET ORIGINALE ###########################################
        # QUERY dove prendo tutti gli status_id univoci dalla tabella tweet e se presente aggiungo 
        cursore.execute(''' 
                            DROP VIEW IF EXISTS user_id_quotes;
                            CREATE VIEW user_id_quotes AS (
                                SELECT U.screen_name, U.user_id, T.status_id
                                FROM utente U
                                    JOIN creates C ON U.user_id = C.user_id
                                    JOIN tweet T ON C.status_id = T.status_id
                                WHERE C.type = 'TW' AND 
                                    T.status_id IN (SELECT Ci.quotes_to_status_id
                                                    FROM creates Ci
                                                    WHERE Ci.quotes_to_status_id IS NOT NULL)
                            );
                            SELECT T.status_id, T.created_at, U.screen_name, U.user_id, C.type, C.quotes_to_status_id, V.screen_name AS authorTW
                            FROM tweet T
                                 JOIN creates C ON T.status_id = C.status_id
                                 JOIN utente U ON C.user_id = U.user_id
                                 LEFT JOIN user_id_quotes V ON C.quotes_to_status_id = V.status_id
                            WHERE C.type <> 'RT' AND
                                  T.status_id IN ('1255930357691453442',
                                                  '1255711619436273665')
                            ORDER BY U.user_id, T.created_at;
                        ''')
        tweetIdOriginale = cursore.fetchall()
        status_id_tweet = [tupla[0] for tupla in tweetIdOriginale]
        created_at_tweet = [tupla[1] for tupla in tweetIdOriginale]
        screen_name_tweet = [tupla[2] for tupla in tweetIdOriginale]
        user_id_tweet = [tupla[3] for tupla in tweetIdOriginale]
        type_tweet = [tupla[4] for tupla in tweetIdOriginale]
        original_tw_quoted = [tupla[5] for tupla in tweetIdOriginale]
        author_tw_quoted = [tupla[6] for tupla in tweetIdOriginale]

        startDB = datetime.strptime('2020-04-30 00:00:00', '%Y-%m-%d %H:%M:%S') # timestamp iniziale del database
        

        for x in range(len(tweetIdOriginale)): # per ogni tweet della tabella tweet
            node_created_at = datetime.strptime(str(created_at_tweet[x]), '%Y-%m-%d %H:%M:%S') # converto il timestamp in datetime
            interval = node_created_at - startDB # calcolo il tempo trascorso dalla creazione del tweet rispetto al nodo radice
            minuteInterval = int(interval.total_seconds()/60) # calcolo l'intervallo in minuti
            attr_dict = {}
            time_list = []
            if type_tweet[x] != 'QT':
                attr_dict["Start"] = minuteInterval
                attr_dict["End"] = minuteInterval
                attr_dict["Authors"] = [(screen_name_tweet[x], 1)]
                stringa = tuple(x for x in attr_dict.values()) # unisco in una tupla leggibile i valori dell'etichetta
                time_list.append(stringa)
                graph.add_edge('DB', status_id_tweet[x], attr_dict = attr_dict, time = stringa, time_list = time_list) # collego il tweet alla radice
            elif type_tweet[x] == 'QT': # se il tweet è un QT
                attr_dict["Start"] = minuteInterval
                attr_dict["End"] = minuteInterval
                attr_dict["Authors"] = [(screen_name_tweet[x], 0.5)]
                stringa = tuple(x for x in attr_dict.values()) # unisco in una tupla leggibile i valori dell'etichetta
                time_list.append(stringa)
                graph.add_edge('DB', status_id_tweet[x],  attr_dict = attr_dict, time = stringa, time_list = time_list) # collego il QT al suo tweet originale
                attr_dict["Start"] = 0
                attr_dict["End"] = math.inf
                attr_dict["Authors"] = [(screen_name_tweet[x], 0.5)]
                stringa = tuple(x for x in attr_dict.values()) # unisco in una tupla leggibile i valori dell'etichetta
                time_list = []
                time_list.append(stringa)
                graph.add_edge(original_tw_quoted[x], status_id_tweet[x], attr_dict = attr_dict, time = stringa, time_list = time_list)
            if x < len(tweetIdOriginale) - 1: # se non sono all'ultimo tweet
                if user_id_tweet[x] == user_id_tweet[x+1]: # se l'utente del tweet è uguale all'utente del tweet successivo
                    attr_dict = {}
                    attr_dict["Start"] = 0
                    attr_dict["End"] = math.inf
                    attr_dict["Authors"] = [(screen_name_tweet[x], 1)]
                    stringa = tuple(x for x in attr_dict.values()) # unisco in una tupla leggibile i valori dell'etichetta
                    time_list = []
                    time_list.append(stringa)
                    graph.add_edge(status_id_tweet[x], status_id_tweet[x+1], attr_dict = attr_dict, time = stringa, time_list = time_list) # collego il tweet successivo a quello precedente
        ######################################################################################################################################################

        ########################### CREO GLI ARCHI TRA UN UTENTE CHE HA FATTO ALMENO UN RT E IL TWEET ORIGINALE CORRISPONDENTE ###############################
        ########################### SE UN UTENTE HA ALMENO 2 TWEET COLLEGO IL TWEET PRECEDENTE/SUCCESSIVO AL RETWEET #########################################
        cursore.execute(''' 
                            DROP VIEW IF EXISTS User_Id_Originale;
                            CREATE VIEW User_Id_Originale AS (
                                SELECT U.user_id, T.status_id, U.screen_name
                                FROM tweet T
                                    JOIN creates C ON T.status_id = C.status_id
                                    JOIN utente U ON C.user_id = U.user_id
                                WHERE C.type <> 'RT' AND
                                    T.status_id IN ('1255930357691453442',
                                                    '1255711619436273665')
                                ORDER BY U.user_id 
                            );

                            SELECT U.user_id, T.status_id, T.created_at, U.screen_name, V.user_id, V.screen_name
                            FROM utente U
                                 JOIN creates C ON U.user_id = C.user_id
                                 JOIN tweet T ON C.status_id = T.status_id
                                 JOIN User_Id_Originale V ON T.status_id = V.status_id
                            WHERE C.type = 'RT' AND
                                  T.status_id IN ('1255930357691453442',
                                                  '1255711619436273665')
                            ORDER BY V.user_id, T.created_at;
                        ''')
        utenti_tweet_RT = cursore.fetchall()
        user_id = [tupla[0] for tupla in utenti_tweet_RT]
        status_id = [tupla[1] for tupla in utenti_tweet_RT]
        status_id_no_duplicates = list(OrderedDict.fromkeys(status_id)) # salvo in una lista gli status_id univoci dei RT, praticamente la lista dei tweet originali
        created_at = [tupla[2] for tupla in utenti_tweet_RT]
        screen_name = [tupla[3] for tupla in utenti_tweet_RT]
        creator_user_id = [tupla[4] for tupla in utenti_tweet_RT]
        creator_screen_name = [tupla[5] for tupla in utenti_tweet_RT]

        # creo un dizionario dove ad ogni utente creatore del TW originale assegno la lista dei suoi tweet
        user_tweet_duplicates = defaultdict(list)
        for i, j in zip(creator_screen_name, status_id):
            user_tweet_duplicates[i].append(j)
        user_tweet = {a:list(OrderedSet(b)) for a, b in user_tweet_duplicates.items()}
        
        for i in range(len(utenti_tweet_RT)): # per ogni tupla che è un RT
            rt_id = status_id[i]+'-'+str(i) # creo un nome per il nodo
            retweet_id.append(rt_id) # lo aggiungo alla lista che mi servirà per colorare il nodo e l'arco dei RT
            attr_dict = {}
            attr_dict["Start"] = 0
            attr_dict["End"] = math.inf
            attr_dict["Authors"] = [(screen_name[i], 0.1)]
            stringa = tuple(x for x in attr_dict.values()) # unisco in una tupla leggibile i valori dell'etichetta
            time_list = []
            time_list.append(stringa)
            graph.add_edge(status_id[i], retweet_id[i], attr_dict = attr_dict, time = stringa, time_list = time_list) # collego il nodo TW originale al suo RT
            graph.add_edge('DB', retweet_id[i], attr_dict = attr_dict, time = stringa, time_list = time_list) # collego il nodo RT al nodo radice DB

        posRT = 0 # variabile per scorrere tutti i retweet_id
        rt_id_precedenti = [] # lista dove salverò i retweet collegati
        for user, tweet in user_tweet.items(): # per ogni utente e i suoi tweet con almeno un retweet
            posTW = 0 # azzero per ritornare alla prima posizione in quanto è un nuovo utente
            for tw in tweet: # per ogni tweet dell'utente
                nodes = []
                nodes = nx.dfs_preorder_nodes(graph, tw, depth_limit = 1) # salvo i nodi con immediatamente successivi al tweet
                for n in nodes:
                    if n == 'DB': # se il nodo è DB lo salto
                        continue
                    elif n in status_id_no_duplicates: # se il nodo è un altro tweet dell'utente lo salto
                        continue
                    elif n in rt_id_precedenti: # se il nodo è un retweet a cui ho già creato un arco lo salto
                        continue
                    else: # altrimenti se il nodo è un retweet ancora da connettere
                        for x in range(0, posRT): # scorro i retweet fino all'immediato precedente di quello che sto collegando
                            if retweet_id[x] not in rt_id_precedenti: # se il nodo del retweet non è già dentro alla lista    
                                rt_id_precedenti.append(retweet_id[x]) # lo aggiungo
                        posRT = posRT + 1 # incremento la posizione del retweet_id a cui sono arrivato
                        if len(tweet) > 1 and posTW < len(tweet) - 1: # se ho almeno 2 retweet e non sono arrivato all'ultimo
                            attr_dict = {}
                            attr_dict["Start"] = 0
                            attr_dict["End"] = math.inf
                            attr_dict["Authors"] = [(creator_screen_name[posTW+1], 1)]
                            stringa = tuple(x for x in attr_dict.values()) # unisco in una tupla leggibile i valori dell'etichetta
                            time_list = []
                            time_list.append(stringa)
                            graph.add_edge(n, tweet[posTW+1],  attr_dict = attr_dict, time = stringa, time_list = time_list) # collego il tweet successivo al retweet
                        if len(tweet) > 1 and posTW > 0: # se ho almeno due retweet e sono almeno al secondo tweet dell'utente
                            attr_dict = {}
                            attr_dict["Start"] = 0
                            attr_dict["End"] = math.inf
                            attr_dict["Authors"] = [(screen_name[posTW], 0.1)]
                            stringa = tuple(x for x in attr_dict.values()) # unisco in una tupla leggibile i valori dell'etichetta
                            time_list = []
                            time_list.append(stringa)
                            graph.add_edge(tweet[posTW-1], n, attr_dict = attr_dict, time = stringa, time_list = time_list) # collego il nodo del retweet al tweet precedente
                posTW = posTW + 1 # incremento la posizione del tweet a cui sono arrivato
        
        ########################################################################################################################################################

        ######################################## CREO LE LISTE CHE MI SERVIRANNO PER COLORARE NODI ED ARCHI DEL GRAFO ##########################################
        # QUERY che mi serve per creare una lista di tutti gli user_id che hanno fatto almeno un RT
        cursore.execute(''' 
                            SELECT DISTINCT C.user_id
                            FROM creates C
                            WHERE C.type = 'RT';
                        ''')
        check_userRT = {user_id for (user_id,) in cursore.fetchall()}

        # QUERY che mi serve per creare una lista di tutti gli status_id di tipo TW
        cursore.execute(''' 
                            SELECT C.status_id
                            FROM creates C
                            WHERE C.type = 'TW';
                        ''')
        check_tweetTW = {status_id for (status_id,) in cursore.fetchall()}
        
        # QUERY che mi serve per creare una lista di tutti gli status_id di tipo QT
        cursore.execute(''' 
                            SELECT C.status_id
                            FROM creates C
                            WHERE C.type = 'QT';
                        ''')
        check_tweetQT = {status_id for (status_id,) in cursore.fetchall()}

        # QUERY che mi serve per creare una lista di tutti gli status_id di tipo RE
        cursore.execute(''' 
                            SELECT C.status_id
                            FROM creates C
                            WHERE C.type = 'RE';
                        ''')
        check_tweetRE = {status_id for (status_id,) in cursore.fetchall()}

        # QUERY che mi serve per creare una lista di tutti gli status_id di tipo REQT
        cursore.execute(''' 
                            SELECT C.status_id
                            FROM creates C
                            WHERE C.type = 'REQT';
                        ''')
        check_tweetREQT = {status_id for (status_id,) in cursore.fetchall()}
        ############################################################################################################################################################

        print("Ho caricato correttamente il grafo! Ecco le sue info:")
        print(nx.info(graph))
        
        loop(graph)

connessione.close()
print("Connessione al database chiusa.")
####################################################################################################################################################################