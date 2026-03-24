import os
import textwrap
from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.db_worker import hatter_kereses

class ChatBot:
    
    # inicializálás
    def __init__(self, adatbazis_utvonal: str) -> None:
        load_dotenv()  # .env fájl megkereséséhez és betöltéséhez 
        api_kulcs = os.getenv('GOOGLE_API_KEY')  # megkeresi a GOOGLE_API_KEY-t   
        self.kliens = genai.Client(api_key=api_kulcs)  # átadja az API kulcsot a kliensnek    
        
        self.adatbazis_utvonal = adatbazis_utvonal  # példányváltozó        

    def kerdes_feltevese(self, kerdes: str) -> str:
        # feldolgozza a kérdést és visszaadja a választ
        vektor = self._vektorizalas(kerdes)
        kontextus = self._kontextus_lekeres(vektor)
        utasitas = self._utasitas_osszeallitasa(kerdes, kontextus)
        return self._valasz_generalasa(utasitas)

    def _vektorizalas(self, kerdes: str) -> list[list[float]]:
        # kérdést vektorrá alakítja
        eredmeny = self.kliens.models.embed_content( # genai kliens használata
            model="gemini-embedding-001", # vektorizáló modell
            contents=kerdes,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY", # dokumentumokban való kereséshez
                output_dimensionality=768 # 768 darab számból áll a vektor
                )
            )
        # embeddings-ből kinyeri a values-t, amiben a vektor van
        return [beagyazas.values for beagyazas in eredmeny.embeddings]
    
    def _kontextus_lekeres(self, vektor: list[list[float]]) -> str:
        # kérdéshez kapcsolódó releváns részek megkeresése
        return hatter_kereses(self.adatbazis_utvonal, vektor)

    def _utasitas_osszeallitasa(self, kerdes: str, kontextus: str) -> str:
        # textwrap.dedent levágja a felesleges behúzásokat a sorok elejéről
        return textwrap.dedent(f"""
            A kérdés, amire válaszolnod kell: {kerdes}
            Itt van a tananyag releváns része, ami alapján válaszolnod kell. Mindegyik részlet felett ott van a [Forrás: fájlnév.pdf] megjelölés:
            {kontextus}
            SZABÁLYOK:
            1. A válaszod megfogalmazásakor KÖTELEZŐ hivatkoznod a forrás(ok)ra!
            2. A mondatok vagy a válaszod végén zárójelben tüntesd fel a forrásfájl nevét.
            3. Ha a fenti kontextus üres, vagy nem tartalmazza a választ a kérdésre, akkor írd le, hogy a feltöltött tananyagban nem találtál erre releváns részt (ne találj ki információkat a kontextuson kívülről).
        """).strip() # eltávolítja az üres sorokat és szóközöket a szöveg legelejéről és legvégéről

    def _valasz_generalasa(self, utasitas: str) -> str:
        eredmeny = self.kliens.models.generate_content(
            model="gemini-2.5-flash",
            contents=[utasitas],
            config=types.GenerateContentConfig(temperature=0.1) # modell kreativitása
        )
        return eredmeny.text