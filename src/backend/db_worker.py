import chromadb
from chromadb.config import Settings

#yQt6 vagy GUI import mentes övezet

def hatter_mentes(db_path, chunk_ids, vektorok, chunks):
    #ChromaDB inicializalasa
    klien = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
    
    #lekeres vagy letrehozas
    kollekcio = klien.get_or_create_collection(name="my-collection")
    
    #vektorok mentese
    kollekcio.add(
        ids=chunk_ids, #stringet var
        embeddings=vektorok,
        documents=chunks
    )

def hatter_kereses(db_path, vektorok, queue):
    klien = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
    kollekcio = klien.get_or_create_collection(name="my-collection")
    
    eredmeny = kollekcio.query(
        query_embeddings=vektorok,
        n_results=3)
    
    kontextus = "\n\n".join(eredmeny['documents'][0])
    
    #eredmény vissza kuldese
    queue.put({"status": "ok", "kontextus": kontextus})