import fitz
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import json

class quiz_generator:
    def __init__(self, raw_folder_path):
       
       #api key
       load_dotenv()
       self.api_key = os.getenv('GOOGLE_API_KEY')
       self.client = genai.Client(api_key=self.api_key)       
       self.raw_folder_path = raw_folder_path 

    def _get_pdf_content(self, pdf_neve):
      pdf_path = os.path.join(self.raw_folder_path, pdf_neve)
        
      #pdf megnyitasa
      with fitz.open(pdf_path) as doc:  #documentum megnyitasa
        szoveg = chr(12).join([page.get_text() for page in doc])
        
      return szoveg
    
    def generalj_kvizt(self, pdf_neve, maximumkerdes ):
        szoveg = self._get_pdf_content(pdf_neve)

        #pdf temakorokre valo bontasa
        temakor_prompt = f"""
        Elemezd a lenti megadott tananyagot, és oszd fel logikai témakörökre.

        SZABÁLYOK:
        1. Bontsd fel a szöveget maximum {maximumkerdes} darab témakörre (nem baj, ha kevesebb témát találsz).
        2. KIZÁRÓLAG olyan témaköröket sorolj fel, amelyek ténylegesen szerepelnek a lenti tananyagban. Ne találj ki újakat!
        3. A válaszod KIZÁRÓLAG egy érvényes JSON formátum legyen, pontosan a következő minta alapján:

        JSON MINTA:
        {{
          "temakorok_szama": 3,
          "temakorok_listaja": [
            "Az ókori Róma történelme",
            "A római társadalom felépítése",
            "A hadsereg szerepe"
          ]
        }}

        TANANYAG:
        {szoveg}
        """

        temakorok = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=temakor_prompt,
            config={"response_mime_type": "application/json"}
        )

        #json adatok kinyerese
        temakor_adatok = json.loads(temakorok.text)
        temakorok_szama = temakor_adatok["temakorok_szama"]
        temakorok_lista = temakor_adatok["temakorok_listaja"] 

        #kvizek generalasa
        kvizek_prompt = f"""
        Készíts egy változatos kvíz-feladatsort az alábbi tananyagból.

        SZABÁLYOK:
        1. A kérdések száma összesen: {temakorok_szama} db legyen.
        2. Minden témakörből 1 kérdést tegyél fel. A témakörök: {temakorok_lista}.
        3. A válaszod KIZÁRÓLAG egy érvényes JSON lista legyen, annyi elemmel, ahány kérdést kértem.
        4. Olyan feladattípust válassz a témakörökhöz, amivel azt a legjobban számon lehet kérni.
        5. Tartsd szem előtt, hogy KIZÁRÓLAG a lenti tananyag tartalmát kell számon kérned.
        6. Használd vegyesen a következő típusokat a JSON séma alapján:

        JSON SÉMA (Ezt kövesd pontosan a struktúra kialakításakor!):
        [
          {{
            "id": 1,
            "type": "single_choice",
            "question": "Kérdés szövege...",
            "options": ["Rossz 1", "Helyes", "Rossz 2", "Rossz 3"],
            "correct_answer": "Helyes"
          }},
          {{
            "id": 2,
            "type": "multiple_choice",
            "question": "Melyek igazak?",
            "options": ["A", "B", "C", "D"],
            "correct_answers": ["A", "C"]
          }},
          {{
            "id": 3,
            "type": "matching",
            "instruction": "Párosítsd össze!",
            "pairs": {{
              "Bal 1": "Jobb 1",
              "Bal 2": "Jobb 2"
            }}
          }},
          {{
            "id": 4,
            "type": "ordering",
            "instruction": "Tedd sorrendbe!",
            "ordered_items": ["Első", "Második", "Harmadik"]
          }},
          {{
            "id": 5,
            "type": "short_answer",
            "question": "Mi a neve...?",
            "accepted_keywords": ["kulcsszó1", "kulcsszó2"]
          }}
        ]

        TANANYAG:
        {szoveg}
        """

        kvizek = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=kvizek_prompt,
            config={"response_mime_type": "application/json"}
        )

        #json adatok kinyerese
        return json.loads(kvizek.text)