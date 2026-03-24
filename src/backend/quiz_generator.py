import os
import json
import random
import textwrap
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.db_worker import hatter_teljes_szoveg_lekeres, hatter_kviz_kereses

class QuizGenerator:
    def __init__(self, raw_folder_path: str) -> None:
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))        
        self.raw_folder_path = Path(raw_folder_path)

    def generalj_kvizt(self, pdf_neve: str, maximumkerdes: int) -> list[dict]:
        db_path, json_path = self._utvonalak_lekerese(pdf_neve)
        temak = self._temakorok_betoltese(pdf_neve, db_path, json_path)
        kivalasztott_temak = self._temak_kivalasztasa(temak, maximumkerdes)
        kontextus_szoveg = self._kontextus_lekerese(kivalasztott_temak, str(db_path), pdf_neve)
        return self._kviz_generalasa_api_val(kivalasztott_temak, kontextus_szoveg)

    def _utvonalak_lekerese(self, pdf_neve: str) -> tuple[Path, Path]:
        subject_folder = self.raw_folder_path.resolve().parent 
        db_path = subject_folder / "chroma_db"
        progress_folder = subject_folder / "progress"
        progress_folder.mkdir(parents=True, exist_ok=True)
        json_path = progress_folder / f"{pdf_neve}_progress.json"
        return db_path, json_path

    def _temakorok_betoltese(self, pdf_neve: str, db_path: Path, json_path: Path) -> dict:
        if not json_path.exists():
            self._temakorok_letrehozasa(pdf_neve, db_path, json_path)
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _temakorok_letrehozasa(self, pdf_neve: str, db_path: Path, json_path: Path) -> None:

        eredmeny_szoveg = hatter_teljes_szoveg_lekeres(str(db_path), pdf_neve)

        if eredmeny_szoveg["status"] == "hiba":
            raise ValueError(eredmeny_szoveg["uzenet"])
        
        prompt = self._temakor_prompt_keszites(eredmeny_szoveg["szoveg"])
        temakorok = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        temakor_adatok = json.loads(temakorok.text)
        temakorok_lista = temakor_adatok.get("mikrotemak_listaja", []) 
        temak = {tema: {"valaszok": 5, "elsajatitva": False} for tema in temakorok_lista}
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(temak, f, ensure_ascii=False, indent=4)

    def _temak_kivalasztasa(self, temak: dict, maximumkerdes: int) -> list[str]:
        meg_tanulando = [tema for tema, adatok in temak.items() if not adatok.get("elsajatitva", False)]
        meg_tanulando = meg_tanulando or list(temak.keys())
        temakorok_szama = min(len(meg_tanulando), maximumkerdes) 
        return random.sample(meg_tanulando, temakorok_szama)

    def _kontextus_lekerese(self, temak: list[str], db_path: str, pdf_neve: str) -> str:
        result = self.client.models.embed_content(
            model="gemini-embedding-001",
            contents=temak,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=768)
        )
        vektorok = [emb.values for emb in result.embeddings]
        try:
            kontextus = hatter_kviz_kereses(db_path, vektorok, pdf_neve)
            return kontextus
        except RuntimeError as e:
            raise ValueError(f"Hiba a RAG keresés során: {e}")

    def _kviz_generalasa_api_val(self, kivalasztott_temak: list[str], kontextus_szoveg: str) -> list[dict]:
        prompt = self._kviz_prompt_keszites(kivalasztott_temak, kontextus_szoveg)
        kvizek = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return json.loads(kvizek.text)

    def _temakor_prompt_keszites(self, teljes_szoveg: str) -> str:
        return textwrap.dedent(f"""
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
                              """)

    def _kviz_prompt_keszites(self, kivalasztott_temak: list[str], kontextus_szoveg: str) -> str:
        temakorok_szama = len(kivalasztott_temak)
        return textwrap.dedent(f"""
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
                                """)