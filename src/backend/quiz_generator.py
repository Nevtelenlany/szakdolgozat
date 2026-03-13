import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import json
import random
import multiprocessing
from backend.db_worker import hatter_teljes_szoveg_lekeres, hatter_kviz_kereses

class quiz_generator:
    def __init__(self, raw_folder_path):
       
       #api key
       load_dotenv()
       self.api_key = os.getenv('GOOGLE_API_KEY')
       self.client = genai.Client(api_key=self.api_key)       
       self.raw_folder_path = raw_folder_path 

    def generalj_kvizt(self, pdf_neve, maximumkerdes):
        tiszta_raw_utvonal = os.path.normpath(self.raw_folder_path)
        subject_folder = os.path.dirname(tiszta_raw_utvonal) 
        db_path = os.path.join(subject_folder, "chroma_db")

        progress_folder = os.path.join(subject_folder, "progress")
        os.makedirs(progress_folder, exist_ok=True)
        json_path = os.path.join(progress_folder, f"{pdf_neve}_progress.json")

        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                temak = json.load(f)
            temakorok_lista = list(temak.keys()) 
        else:
            q_szoveg = multiprocessing.Queue()
            process_szoveg = multiprocessing.Process(
                target=hatter_teljes_szoveg_lekeres,
                args=(db_path, pdf_neve, q_szoveg)
            )
            process_szoveg.start()
            eredmeny_szoveg = q_szoveg.get()
            process_szoveg.join()

            if eredmeny_szoveg["status"] == "hiba":
                raise ValueError(eredmeny_szoveg["uzenet"])
            
            teljes_szoveg = eredmeny_szoveg["szoveg"]
            
            temakor_prompt = f"""
            Elemezd a lenti megadott tananyagot, és oszd fel jól körülhatárolható, vizsgáztatható mikrotémákra (kulcsfogalmakra, összefüggésekre, tényekre).

            SZABÁLYOK:
            1. Szűrd ki a bevezető, leíró "rizsát"! Csak olyan specifikus témákat emelj ki, amikből konkrét, egyértelmű kvízkérdéseket lehet írni.
            2. Ne nagy, átfogó kategóriákat írj (pl. "Biológia alapjai"), hanem konkrétumokat (pl. "A mitokondrium szerepe a sejtlégzésben", "Az enzimek kulcs-zár modellje").
            3. Szerepeltesd a listában a tananyag összes releváns, vizsgáztatható mikrotémáját (mennyiségi korlát nincs, de csak a lényeget emeld ki).
            4. KIZÁRÓLAG olyan témákat sorolj fel, amelyek ténylegesen szerepelnek a lenti tananyagban. Ne találj ki újakat!
            5. A válaszod KIZÁRÓLAG egy érvényes JSON formátum legyen, pontosan a következő minta alapján:

            JSON MINTA:
            {{
              "mikrotemak_szama": 3,
              "mikrotemak_listaja": [
                "A sejtmembrán felépítése (folyékony mozaik modell)",
                "A fotoszintézis fényszakaszának lépései",
                "A DNS kettős hélix szerkezete és bázispárjai"
              ]
            }}

            TANANYAG:
            {teljes_szoveg}
            """

            temakorok = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=temakor_prompt,
                config={"response_mime_type": "application/json"}
            )

            #json adatok kinyerese
            temakor_adatok = json.loads(temakorok.text)
            temakorok_szama = temakor_adatok["mikrotemak_szama"]
            temakorok_lista = temakor_adatok["mikrotemak_listaja"] 

            temak = {}
            for tema in temakor_adatok["mikrotemak_listaja"]:
                temak[tema] = {
                    "valaszok": 5,
                    "elsajatitva": False
                }
            
            #Lementjük a JSON fájlba
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(temak, f, ensure_ascii=False, indent=4)

        meg_tanulando = [tema for tema, adatok in temak.items() if not adatok["elsajatitva"]]

        if not meg_tanulando:
            meg_tanulando = temakorok_lista
            
        temakorok_szama = min(len(meg_tanulando), maximumkerdes)
        kivalasztott_temak = random.sample(meg_tanulando, temakorok_szama)

        result = self.client.models.embed_content(
            model="gemini-embedding-001",
            contents=kivalasztott_temak,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=768)
        )
        vektorok = [emb.values for emb in result.embeddings]

        # 2. BIZTONSÁGOS LEKÉRDEZÉS (RAG kontextus) MULTIPROCESSINGGEL
        q_kontextus = multiprocessing.Queue()
        process_kontextus = multiprocessing.Process(
            target=hatter_kviz_kereses,
            args=(db_path, vektorok, pdf_neve, q_kontextus)
        )
        process_kontextus.start()
        eredmeny_kontextus = q_kontextus.get()
        process_kontextus.join()

        if eredmeny_kontextus["status"] == "hiba":
            raise ValueError(eredmeny_kontextus.get("uzenet", "Hiba a RAG keresés során."))
            
        kontextus_szoveg = eredmeny_kontextus["kontextus"]

        kvizek_prompt = f"""
        Készíts egy változatos kvíz-feladatsort az alábbi tananyagrészletekből.

        SZABÁLYOK:
        1. A kérdések száma összesen: {temakorok_szama} db legyen.
        2. Minden alábbi témakörből 1 kérdést tegyél fel. A témakörök: {kivalasztott_temak}.
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
            "correct_answer": "Helyes",
            "explanation": "Itt írd le röviden 1-2 mondatban, hogy miért ez a helyes válasz a tananyag alapján.",
            "tema": "Ide írd be, hogy melyik témakörhöz tartozik ez a kérdés a listából"
          }},
          {{
            "id": 2,
            "type": "multiple_choice",
            "question": "Melyek igazak?",
            "options": ["A", "B", "C", "D"],
            "correct_answers": ["A", "C"],
            "explanation": "Itt írd le röviden 1-2 mondatban, hogy miért ez a helyes válasz a tananyag alapján.",
            "tema": "Ide írd be, hogy melyik témakörhöz tartozik ez a kérdés a listából"
          }},
          {{
            "id": 3,
            "type": "matching",
            "instruction": "Párosítsd össze!",
            "pairs": {{
              "Bal 1": "Jobb 1",
              "Bal 2": "Jobb 2"
            }},
            "explanation": "Itt írd le röviden 1-2 mondatban, hogy miért ez a helyes válasz a tananyag alapján.",
            "tema": "Ide írd be, hogy melyik témakörhöz tartozik ez a kérdés a listából"
          }},
          {{
            "id": 4,
            "type": "ordering",
            "instruction": "Tedd sorrendbe!",
            "ordered_items": ["Első", "Második", "Harmadik"],
            "explanation": "Itt írd le röviden 1-2 mondatban, hogy miért ez a helyes válasz a tananyag alapján.",
            "tema": "Ide írd be, hogy melyik témakörhöz tartozik ez a kérdés a listából"
          }},
          {{
            "id": 5,
            "type": "short_answer",
            "question": "Mi a neve...?",
            "accepted_keywords": ["kulcsszó1", "kulcsszó2"],
            "explanation": "Itt írd le röviden 1-2 mondatban, hogy miért ez a helyes válasz a tananyag alapján.",
            "tema": "Ide írd be, hogy melyik témakörhöz tartozik ez a kérdés a listából"
          }}
        ]

        TANANYAG (Csak ebből dolgozz!):
        {kontextus_szoveg}
        """

        kvizek = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=kvizek_prompt,
            config={"response_mime_type": "application/json"}
        )

        return json.loads(kvizek.text)