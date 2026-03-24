import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google.genai import types
from dotenv import load_dotenv
from google import genai
import os
import multiprocessing
from pathlib import Path

from backend.db_worker import hatter_mentes, hatter_torles

ALAP_UTVONAL = Path("./data/subjects")

class PdfFeldolgozo:

    # inicializálás
    def __init__(self) -> None:
        load_dotenv()  # .env fájl megkereséséhez és betöltéséhez 
        api_kulcs = os.getenv('GOOGLE_API_KEY')  # megkeresi a GOOGLE_API_KEY-t   
        self.kliens = genai.Client(api_key=api_kulcs)  # átadja az API kulcsot a kliensnek   
    
    def feldolgozas_es_mentes(self, pdf_utvonal: str, temakor_neve: str, fajl_neve: str) -> None:
        # PDF feldolgozása
        szoveg = self._pdf_szoveg_kinyerese(pdf_utvonal)
        darabok = self._szoveg_darabolasa(szoveg)
        vektorok = self._vektorok_generalasa(darabok)
        self._adatbazisba_mentes(temakor_neve, fajl_neve, darabok, vektorok)

    def _pdf_szoveg_kinyerese(self, pdf_utvonal: str) -> str:
        # 'with' automatikusan és biztonságosan lezárja a PDF fájlt a művelet végén
        # 'as' pedig 'dokumentum' néven hivatkozik a megnyitott fájlra.
        with fitz.open(pdf_utvonal) as dokumentum: 
            # for oldal in dokumentum: végigmegy a dokumentum összes oldalán
            # oldal.get_text(): beolvassa az aktuális oldal szövegét (stringként)
            # "\f".join(...): az oldalakat egyetlen szöveggé fűzi össze, oldaltöréssel (\f) elválasztva
            return "\f".join(oldal.get_text() for oldal in dokumentum)

    def _szoveg_darabolasa(self, szoveg: str) -> list[str]:
        # chunk_size: szövegdarab maximálisan 500 karakter hosszú lehet
        # chunk_overlap: egymást követő darabok között 50 karakteres ismétlődés van
        darabolo = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50) 
        return darabolo.split_text(szoveg) # split_text: elvégzi a darabolást, és visszaad egy listát a szövegdarabokkal

    def _vektorok_generalasa(self, darabok: list[str]) -> list[list[float]]:
        vektorok = []
        koteg_meret = 100 # egyszerre 100 darab chunkot küld, hogy ne terhelje túl a hálózatot
    
        for i in range(0, len(darabok), koteg_meret): # 0-tól chunkok számáig megy 100-as lépésközzel
            aktualis_koteg = darabok[i:i + koteg_meret] # kivágja a listából i-től az utána lévő 100 darabot
            eredmeny = self.kliens.models.embed_content(
                model="gemini-embedding-001", 
                contents=aktualis_koteg, # átadja a chunkokat
                config=types.EmbedContentConfig(output_dimensionality=768) # 768 darab számból áll a vektor
            )
            # embeddings-ből kinyeri a values-t, amiben a vektor van
            # .extend külön teszi bele a lista elemeit és nem egy 100 elemű listaként
            vektorok.extend([beagyazas.values for beagyazas in eredmeny.embeddings])
        return vektorok

    def _adatbazisba_mentes(self, temakor_neve: str, fajl_neve: str, darabok: list[str], vektorok: list[list[float]]) -> None:
        chunk_ids = [f"{fajl_neve}_chunk_{x}" for x in range(len(darabok))]
        metaadatok = [{"forras": fajl_neve} for _ in range(len(darabok))]
        
        db_path = ALAP_UTVONAL / temakor_neve / "chroma_db"
        db_path.mkdir(parents=True, exist_ok=True)

        mentes_process = multiprocessing.Process(
            target=hatter_mentes,
            args=(str(db_path), chunk_ids, vektorok, darabok, metaadatok)
        )
        mentes_process.start()
        mentes_process.join()

    def delete_pdf_data(self, temakor_neve: str, fajl_neve: str) -> None:
        db_path = ALAP_UTVONAL / temakor_neve / "chroma_db"
        if db_path.exists():
            torles_process = multiprocessing.Process(
                target=hatter_torles,
                args=(str(db_path), fajl_neve)
            )
            torles_process.start()
            torles_process.join()