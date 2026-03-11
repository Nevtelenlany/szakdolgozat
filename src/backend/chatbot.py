from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
import chromadb
from chromadb.config import Settings
import multiprocessing

from backend.db_worker import hatter_kereses

class Chatbot:
    def __init__(self, db_path):

        #api key
        load_dotenv()
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.client = genai.Client(api_key=self.api_key)
        self.db_path = db_path

    def kerdes_feltevese(self, kerdes):
        #vektorizalas (Embedding)
        result = self.client.models.embed_content(
            model="gemini-embedding-001",
            contents= kerdes,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=768)
            )
        vektorok = [emb.values for emb in result.embeddings]

        #multiprocessing
        #egy független folyamat aminek elkülönített memóriája van ezért a chromadb és a pyqt6 egymástól függetlenül tud müködni
        q = multiprocessing.Queue()
        
        #független folyamat elinditasa
        process = multiprocessing.Process(#folyamat deffinialasa
            target=hatter_kereses,#ezt a függvényt kell lefuttatnia a független folyamatban
            args=(self.db_path, vektorok, q)#ezeket az argumentumokat varja a függvény
        )
        process.start()
        
        #eredmeny megvarasa
        eredmeny_dict = q.get()#a fő program nem fut amíg a háttérfolyamat nem végzett
        process.join() #folyamat lezarasa
            
        kotnextus_lista = eredmeny_dict["kontextus"]
        
        #valasz generalasa
        response = self.client.models.generate_content(
            model="gemini-2.5-flash", #gemini-3-flash-preview
            contents=[f"""
                        A kérdés, amire válaszolnod kell: {kerdes}

                        Itt van a tananyag releváns része, ami alapján válaszolnod kell. Mindegyik részlet felett ott van a [Forrás: fájlnév.pdf] megjelölés:
                        {kotnextus_lista}

                        SZABÁLYOK:
                        1. A válaszod megfogalmazásakor KÖTELEZŐ hivatkoznod a forrás(ok)ra!
                        2. A mondatok vagy a válaszod végén zárójelben tüntesd fel a forrásfájl nevét.
                        3. Ha a fenti kontextus üres, vagy nem tartalmazza a választ a kérdésre, akkor írd le, hogy a feltöltött tananyagban nem találtál erre releváns részt (ne találj ki információkat a kontextuson kívülről).
                        """],
            config=types.GenerateContentConfig(temperature=0.1))
        return response.text