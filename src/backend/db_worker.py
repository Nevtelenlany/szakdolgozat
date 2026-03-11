import chromadb
from chromadb.config import Settings

#yQt6 vagy GUI import mentes övezet

def hatter_mentes(db_path, chunk_ids, vektorok, chunks, metaadatok):
    #ChromaDB inicializalasa
    klien = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
    
    #lekeres vagy letrehozas
    kollekcio = klien.get_or_create_collection(name="my-collection")
    
    #vektorok mentese
    kollekcio.add(
        ids=chunk_ids, #stringet var
        embeddings=vektorok,
        documents=chunks,
        metadatas=metaadatok
    )

def hatter_kereses(db_path, vektorok, queue):
    klien = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
    kollekcio = klien.get_or_create_collection(name="my-collection")
    
    eredmeny = kollekcio.query(
        query_embeddings=vektorok,
        n_results=3)
    
    kontextus_lista = []
    
    for doc, meta in zip(eredmeny['documents'][0], eredmeny['metadatas'][0]):
        forras_nev = meta.get("forras", "Ismeretlen forrás")
        kontextus_lista.append(f"[Forrás: {forras_nev}]\n{doc}")
        
    kontextus = "\n\n---\n\n".join(kontextus_lista)
    
    #eredmény vissza kuldese
    queue.put({"status": "ok", "kontextus": kontextus})

def hatter_torles(db_path, fajl_neve):
    #ChromaDB inicializálása
    klien = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
    
    try:
        #lekerjuk a kollekciot 
        kollekcio = klien.get_collection(name="my-collection")
        #lkerjuk az adatbazisban levo osszes adat azonositojat
        minden_adat = kollekcio.get()
        torlendo_id_k = [uid for uid in minden_adat['ids'] if uid.startswith(f"{fajl_neve}_chunk_")]
        if torlendo_id_k:
            kollekcio.delete(ids=torlendo_id_k)

    except ValueError:
        pass