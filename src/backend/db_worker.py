import chromadb
from chromadb.config import Settings
import multiprocessing


def _get_kollekcio(db_path: str):
    klien = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
    return klien.get_or_create_collection(name="my-collection")

def hatter_mentes(db_path: str, chunk_ids: list[str], vektorok: list[list[float]], chunks: list[str], metaadatok: list[dict]) -> None:
    kollekcio = _get_kollekcio(db_path)
    kollekcio.add(
        ids=chunk_ids,
        embeddings=vektorok,
        documents=chunks,
        metadatas=metaadatok
    )

def hatter_torles(db_path: str, fajl_neve: str) -> None:
    kollekcio = _get_kollekcio(db_path)
    try:
        minden_adat = kollekcio.get()
        torlendo_id_k = [uid for uid in minden_adat['ids'] if uid.startswith(f"{fajl_neve}_chunk_")]
        if torlendo_id_k:
            kollekcio.delete(ids=torlendo_id_k)
    except ValueError:
        pass

def _elszigetelt_kereses(db_path: str, vektorok: list[list[float]], queue: multiprocessing.Queue):
    try:
        klien = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
        kollekcio = klien.get_or_create_collection(name="my-collection")
        
        eredmeny = kollekcio.query(query_embeddings=vektorok, n_results=3)
        
        if not eredmeny.get('documents') or not eredmeny['documents'][0]:
            queue.put({"status": "ok", "kontextus": ""})
            return
            
        kontextus_lista = [
            f"[Forrás: {meta.get('forras', 'Ismeretlen forrás')}]\n{doc}"
            for doc, meta in zip(eredmeny['documents'][0], eredmeny['metadatas'][0])
        ]
        
        queue.put({"status": "ok", "kontextus": "\n\n---\n\n".join(kontextus_lista)})
    except Exception as e:
        queue.put({"status": "hiba", "kontextus": str(e)})

def hatter_kereses(db_path: str, vektorok: list[list[float]]) -> str:
    q = multiprocessing.Queue()
    process = multiprocessing.Process(target=_elszigetelt_kereses, args=(db_path, vektorok, q))
    process.start()
    
    valasz = q.get()
    process.join()
    
    if valasz["status"] == "hiba":
        raise RuntimeError(f"ChromaDB hiba a keresésnél: {valasz['kontextus']}")
        
    return valasz["kontextus"]


def _elszigetelt_kviz_kereses(db_path: str, vektorok: list[list[float]], pdf_neve: str, queue: multiprocessing.Queue):
    try:
        klien = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
        kollekcio = klien.get_or_create_collection(name="my-collection")
        eredmeny = kollekcio.query(
            query_embeddings=vektorok,
            n_results=3,
            where={"forras": pdf_neve}
        )
        kontextus_halmaz = {doc for docs in eredmeny.get('documents', []) for doc in docs}
        queue.put({"status": "ok", "kontextus": "\n\n---\n\n".join(kontextus_halmaz)})
    except Exception as e:
        queue.put({"status": "hiba", "kontextus": str(e)})

def hatter_kviz_kereses(db_path: str, vektorok: list[list[float]], pdf_neve: str) -> str:
    q = multiprocessing.Queue()
    process = multiprocessing.Process(target=_elszigetelt_kviz_kereses, args=(db_path, vektorok, pdf_neve, q))
    process.start()
    
    valasz = q.get()
    process.join()
    
    if valasz["status"] == "hiba":
        raise RuntimeError(f"ChromaDB hiba a kvíznél: {valasz['kontextus']}")
        
    return valasz["kontextus"]


def _elszigetelt_teljes_szoveg(db_path: str, pdf_neve: str, queue: multiprocessing.Queue):
    try:
        klien = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
        kollekcio = klien.get_or_create_collection(name="my-collection")
        minden_adat = kollekcio.get(where={"forras": pdf_neve})
        
        if not (minden_adat and minden_adat.get("documents")):
            queue.put({"status": "hiba", "uzenet": f"Nincs adat az adatbázisban a(z) {pdf_neve} fájlhoz!"})
            return
            
        teljes_szoveg = "\n".join(minden_adat["documents"])
        queue.put({"status": "ok", "szoveg": teljes_szoveg})
    except Exception as e:
        queue.put({"status": "hiba", "uzenet": str(e)})

def hatter_teljes_szoveg_lekeres(db_path: str, pdf_neve: str) -> dict:
    q_szoveg = multiprocessing.Queue()
    process = multiprocessing.Process(target=_elszigetelt_teljes_szoveg, args=(db_path, pdf_neve, q_szoveg))
    process.start()
    
    valasz = q_szoveg.get()
    process.join()
    
    return valasz