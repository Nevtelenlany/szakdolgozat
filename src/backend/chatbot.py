import os
import textwrap
from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.adatbazis_kezelo import hatter_kereses

class ChatBot:
    
    # inicializálás
    def __init__(self, adatbazis_utvonal: str) -> None:
        load_dotenv()  # .env fájl megkereséséhez és betöltéséhez 
        api_kulcs = os.getenv('GOOGLE_API_KEY')  # megkeresi a GOOGLE_API_KEY-t   
        # átadja az API kulcsot a kliensnek   
        # csak akkor hozza létre, ha van kulcs
        self.kliens = genai.Client(api_key=api_kulcs) if api_kulcs else None 
        self.adatbazis_utvonal = adatbazis_utvonal  # példányváltozó        

    def kerdes_feltevese(self, kerdes: str) -> str:
        # ellenőrzi, hogy van-e kliens (API kulcs)
        if not self.kliens:
            raise ValueError("Nincs API kulcs megadva! Kérlek, pótold a .env fájlban.")
        
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
            4. Ha a felhasználó kérdése értelmetlen karaktersorozat, vagy nyilvánvalóan nem egy értelmes kérdés, kérd meg udvariasan, hogy fogalmazza meg pontosabban.
        """).strip() # eltávolítja az üres sorokat és szóközöket a szöveg legelejéről és legvégéről

    def _valasz_generalasa(self, utasitas: str) -> str:
        modellek = ["gemini-3.1-flash-lite-preview", "gemini-3-flash-preview", "gemini-2.5-flash", "gemini-3.1-pro-preview", "gemini-2.5-pro"]
        utolso_hiba = None

        for modell in modellek:
            try:
                print(f"[Chatbot] Próbálkozás a következő modellel: {modell}...")
                eredmeny = self.kliens.models.generate_content(
                    model=modell,
                    contents=[utasitas],
                    config=types.GenerateContentConfig(temperature=1.0) # modell kreativitása
                )
                print(f"[Chatbot] Sikeres válasz a {modell} modelltől!")
                return eredmeny.text
            
            except Exception as e:
                print(f"[Chatbot] Hiba a {modell} modellnél: {e}")
                utolso_hiba = e

        # ha a ciklus lefutott, és mindegyik modell hibát dobott
        raise RuntimeError(f"Az összes AI modell túlterhelt vagy elérhetetlen. Utolsó hiba: {utolso_hiba}")