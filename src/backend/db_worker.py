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
    

def hatter_teljes_szoveg_lekeres(db_path, pdf_neve, queue):
    """Lekéri az összes chunkot egy adott PDF-hez a ChromaDB-ből."""
    klien = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
    kollekcio = klien.get_or_create_collection(name="my-collection")
    
    minden_adat = kollekcio.get(where={"forras": pdf_neve})
    
    if not minden_adat or not minden_adat.get("documents"):
        queue.put({"status": "hiba", "uzenet": f"Nincs adat az adatbázisban a(z) {pdf_neve} fájlhoz!"})
        return
        
    teljes_szoveg = "\n".join(minden_adat["documents"])
    queue.put({"status": "ok", "szoveg": teljes_szoveg})

def hatter_kviz_kereses(db_path, vektorok, pdf_neve, queue):
    """Vektoros RAG keresést végez a kvíz generálásához."""
    klien = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
    kollekcio = klien.get_or_create_collection(name="my-collection")
    
    eredmeny = kollekcio.query(
        query_embeddings=vektorok,
        n_results=3,
        where={"forras": pdf_neve}
    )
    
    kontextus_halmaz = set()
    for docs in eredmeny['documents']:
        for doc in docs:
            kontextus_halmaz.add(doc)
            
    kontextus_szoveg = "\n\n---\n\n".join(kontextus_halmaz)
    queue.put({"status": "ok", "kontextus": kontextus_szoveg})