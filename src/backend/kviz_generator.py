import os
import json
import random
import textwrap
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.adatbazis_kezelo import hatter_teljes_szoveg_lekeres, hatter_kviz_kereses

ALAP_UTVONAL = Path("./data/subjects")

class KvizGenerator:

    # inicializálás
    def __init__(self) -> None:
        load_dotenv()  # .env fájl megkereséséhez és betöltéséhez 
        api_kulcs = os.getenv('GOOGLE_API_KEY')  # megkeresi a GOOGLE_API_KEY-t   
        # átadja az API kulcsot a kliensnek   
        # csak akkor hozza létre, ha van kulcs
        self.kliens = genai.Client(api_key=api_kulcs) if api_kulcs else None 

    def generalj_kvizt(self, temakor_neve: str, fajl_neve: str, maximum_kerdes: int) -> list[dict]:
        # ellenőrzi, hogy van-e kliens (API kulcs)
        if not self.kliens:
            raise ValueError("Nincs API kulcs megadva! Kérlek, pótold a .env fájlban.")
        
        # lekéri a szükséges fájlok elérési útját a témakör és a fájlnév alapján
        adatbazis_utvonal, json_utvonal = self._utvonalak_lekerese(temakor_neve, fajl_neve)
        # betölti a tanulási folyamatot (json), vagy létrehozza, ha még nincs
        temak = self._temakorok_betoltese(fajl_neve, adatbazis_utvonal, json_utvonal)
        # kiválasztja azokat a témákat, amikből a kvízt generál
        kivalasztott_temak = self._temak_kivalasztasa(temak, maximum_kerdes)
        # (RAG) kinyerjük a témákhoz tartozó konkrét tananyagot
        kontextus_szoveg = self._kontextus_lekerese(kivalasztott_temak, str(adatbazis_utvonal), fajl_neve)
        # elküldi a promptot a Gemini API-nak és visszaadja a kész kvízt
        return self._kviz_generalasa_api_val(kivalasztott_temak, kontextus_szoveg)

    def _utvonalak_lekerese(self, temakor_neve: str, fajl_neve: str) -> tuple[Path, Path]:
        temakor_mappa = ALAP_UTVONAL / temakor_neve
        adatbazis_utvonal = temakor_mappa / "chroma_db"
        haladas_mappa = temakor_mappa / "progress"

        # parents=True: ha az útvonalban szereplő mappák még nem léteznek, akkor automatikusan létrehozza azokat
        # exist_ok=True: ha a mappák már léteznek, akkor nem történik semmi (nem dob hibát)
        haladas_mappa.mkdir(parents=True, exist_ok=True)

        json_utvonal = haladas_mappa / f"{fajl_neve}_progress.json"
        return adatbazis_utvonal, json_utvonal

    def _temakorok_betoltese(self, fajl_neve: str, adatbazis_utvonal: Path, json_utvonal: Path) -> dict:
        # exists() egy Igaz (True) vagy Hamis (False) értékkel tér vissza
        # megnézi, hogy a megadott útvonalon valóban létezik-e az az adott mappa vagy fájl
        if not json_utvonal.exists():
            self._temakorok_letrehozasa(fajl_neve, adatbazis_utvonal, json_utvonal)
        
        # 'with' automatikusan és biztonságosan lezárja a json fájlt a művelet végén
        # 'as' pedig 'fajl' néven hivatkozik a megnyitott fájlra.
        with open(json_utvonal, 'r', encoding='utf-8') as fajl: 
            # a json.load() beolvassa a fájl tartalmát, és átalakítja szótárrá
            return json.load(fajl)
        
    def _temakorok_letrehozasa(self, fajl_neve: str, adatbazis_utvonal: Path, json_utvonal: Path) -> None:
        eredmeny_szoveg = hatter_teljes_szoveg_lekeres(str(adatbazis_utvonal), fajl_neve)

        # ha a háttérfolyamat hibát jelez, a program dob egy kivételt
        if eredmeny_szoveg["status"] == "hiba":
            raise ValueError(eredmeny_szoveg["uzenet"])
        
        prompt = self._temakor_prompt_keszites(eredmeny_szoveg["szoveg"])
        
        modellek = ["gemini-3.1-flash-lite-preview", "gemini-3-flash-preview", "gemini-2.5-flash", "gemini-3.1-pro-preview", "gemini-2.5-pro"]
        api_valasz = None
        utolso_hiba = None

        for modell in modellek:
            try:
                print(f"[Kvíz Témakör] Próbálkozás a következő modellel: {modell}...")
                api_valasz = self.kliens.models.generate_content(
                    model=modell,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json") # arra kényszeríti a modellt, hogy csak JSON formátumot adjon vissza
                )
                break # ha sikeres volt a generálás, azonnal kilép a for ciklusból
                
            except Exception as e:
                # csupa kisbetűssé alakítja a hibaüzenetet a könnyebb kulcsszó-keresés érdekében
                hiba_szoveg = str(e).lower()
                
                # ellenőrzi, hogy a hiba a napi API kvóta kimerülése miatt történt-e
                if "429" in hiba_szoveg or "quota" in hiba_szoveg:
                    # ha igen, azonnal megszakítja a folyamatot, mert felesleges a többi modellt is végigpróbálni ugyanazzal a kulccsal
                    raise RuntimeError("A szerver elutasította a kérést. Valószínűleg elérted az ingyenes API kulcs napi (Daily) limitjét! Kérlek, próbáld újra holnap, vagy használj másik kulcsot.")
                utolso_hiba = e
        
        if not api_valasz:
            raise RuntimeError(f"Nem sikerült kapcsolódni egyik modellhez sem a témaköröknél. Hiba: {utolso_hiba}")

        # a json.loads() beolvassa az api_valasz szöveges tartalmát, és átalakítja szótárrá
        temakor_adatok = json.loads(api_valasz.text)

        # ".get()" biztonságosan kinyeri a témák listáját a szótárból
        # ha valami hiba történne, vagy nem talál kinyerhető témát, [] üres listát ad vissza
        temakorok_lista = temakor_adatok.get("mikrotemak_listaja", []) 

        if not temakorok_lista:
            raise ValueError("A feltöltött fájl nem tartalmaz olyan tanulható, vizsgáztatható anyagot, amiből kvízt lehetne generálni (pl. csak egy tájékoztató).")

        # végigmegy a temakorok_lista témáin, és mindegyikhez szótárként hozzárendeli ezt: {"valaszok": 5, "elsajatitva": False}
        temak = {tema: {"valaszok": 5, "elsajatitva": False} for tema in temakorok_lista}

        # 'with' automatikusan és biztonságosan lezárja a json fájlt a művelet végén
        # 'as' pedig 'fajl' néven hivatkozik a megnyitott fájlra.
        with open(json_utvonal, 'w', encoding='utf-8') as fajl:
            # json.dump a szótárat json fájllá alakítja
            # az ensure_ascii=False megtartja az ékezeteket, ami a magyar nyelv miatt szükséges
            # indent=4 a json fájlban a szinteket 4 szóközzel választja el a szebb megjelenésért
            json.dump(temak, fajl, ensure_ascii=False, indent=4)

    def _temak_kivalasztasa(self, temak: dict, maximum_kerdes: int) -> list[str]:
        # szögletes zárójel [] létrehoz egy új listát, amibe a 'tema' (kulcs) kerül
        # "for tema, adatok in temak.items()" párosával végigmegy a szótár elemein
        # "if not adatok.get(...)" kiszűri azokat, amiknél az 'elsajatitva' érték False
        meg_tanulando = [tema for tema, adatok in temak.items() if not adatok.get("elsajatitva", False)]

        # ha a meg_tanulando lista üres, akkor a teljes listát kapja meg (az összes témát)
        # ha a meg_tanulando nem üres, akkor csak azt (a szűrt listát) adja vissza
        meg_tanulando = meg_tanulando or list(temak.keys())

        temakorok_szama = min(len(meg_tanulando), maximum_kerdes) 
        # visszatevés nélkül visszaad 'temakorok_szama' darab véletlenszerű témát a listából
        return random.sample(meg_tanulando, temakorok_szama)
    
    def _kontextus_lekerese(self, temak: list[str], adatbazis_utvonal: str, fajl_neve: str) -> str:    
        try:
            # témákat vektorrá alakítja
            eredmeny = self.kliens.models.embed_content(
                model="gemini-embedding-001",
                contents=temak,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY", # dokumentumokban való kereséshez
                    output_dimensionality=768 # 768 darab számból áll a vektor
                )
            )
            # embeddings-ből kinyeri a values-t, amiben a vektor van
            vektorok = [beagyazas.values for beagyazas in eredmeny.embeddings]
            
        except Exception as e:
            # csupa kisbetűssé alakítja a hibaüzenetet a könnyebb kulcsszó-keresés érdekében
            hiba_szoveg = str(e).lower()
            
            # ellenőrzi, hogy a Google szervere a túl sok kérés (napi limit) miatt dobott-e hibát
            if "429" in hiba_szoveg or "quota" in hiba_szoveg or "resource_exhausted" in hiba_szoveg:
                # ha elfogyott a keret, megszakítja a folyamatot egy beszédes hibaüzenettel a felület felé
                raise RuntimeError("A szerver elutasította a keresési kérést. Valószínűleg elérted az ingyenes API kulcs napi (Daily) limitjét! Kérlek, próbáld újra holnap, vagy használj másik kulcsot.")
            else:
                # minden egyéb hiba esetén továbbdobja az eredeti problémát
                raise RuntimeError(f"Hiba a témák vektorizálásakor: {e}")
        
        try:
            # témakörökhöz kapcsolódó releváns részek megkeresése
            kontextus = hatter_kviz_kereses(adatbazis_utvonal, vektorok, fajl_neve)
            return kontextus
        except RuntimeError as e:
            raise ValueError(f"Hiba a tananyag keresése során: {e}")

    def _kviz_generalasa_api_val(self, kivalasztott_temak: list[str], kontextus_szoveg: str) -> list[dict]:

        prompt = self._kviz_prompt_keszites(kivalasztott_temak, kontextus_szoveg)

        modellek = ["gemini-3.1-flash-lite-preview", "gemini-3-flash-preview", "gemini-2.5-flash", "gemini-3.1-pro-preview", "gemini-2.5-pro"]
        api_valasz = None
        utolso_hiba = None

        for modell in modellek:
            try:
                print(f"[Kvízkérdések] Próbálkozás a következő modellel: {modell}...")
                api_valasz = self.kliens.models.generate_content(
                    model=modell,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json") # arra kényszeríti a modellt, hogy csak JSON formátumot adjon vissza
                )
                break
            except Exception as e:
                hiba_szoveg = str(e).lower()
                
                # ha a napi limit kimerült, megszakítja a folyamatot
                if "429" in hiba_szoveg or "quota" in hiba_szoveg:
                    raise RuntimeError("A szerver elutasította a kérést. Valószínűleg elérted az ingyenes API kulcs napi (Daily) limitjét! Kérlek, próbáld újra holnap, vagy használj másik kulcsot.")
                
                print(f"[Kvízkérdések] Hiba a {modell} modellnél: {e}")
                utolso_hiba = e

        if not api_valasz:
            # ha a ciklus lefutott, és mindegyik modell hibát dobott
            raise RuntimeError(f"Kvíz generálása sikertelen, az összes modell elérhetetlen. Hiba: {utolso_hiba}")

        # a json.loads() beolvassa az api_valasz szöveges tartalmát, és átalakítja egy Python listává (ami a kvízkérdéseket tartalmazza)
        return json.loads(api_valasz.text)

    def _temakor_prompt_keszites(self, teljes_szoveg: str) -> str:
        # textwrap.dedent levágja a felesleges behúzásokat a sorok elejéről
        return textwrap.dedent(f"""
                                Elemezd a lenti megadott tananyagot, és oszd fel jól körülhatárolható, vizsgáztatható mikrotémákra (kulcsfogalmakra, összefüggésekre, tényekre).
                                SZABÁLYOK:
                                1. Szűrd ki a bevezető, leíró "rizsát"! Csak olyan specifikus témákat emelj ki, amikből konkrét, egyértelmű kvízkérdéseket lehet írni.
                                2. Ne nagy, átfogó kategóriákat írj (pl. "Biológia alapjai"), hanem konkrétumokat (pl. "A mitokondrium szerepe a sejtlégzésben").
                                3. Szerepeltesd a listában a tananyag összes releváns, vizsgáztatható mikrotémáját.
                                4. KIZÁRÓLAG olyan témákat sorolj fel, amelyek ténylegesen szerepelnek a lenti tananyagban. Ne találj ki újakat!
                                5. HA A SZÖVEG NEM TARTALMAZ vizsgáztatható tananyagot (pl. csak egy tartalomjegyzék, tematika vagy tájékoztató), akkor a "mikrotemak_listaja" kötelezően legyen egy ÜRES LISTA: []
                                6. A válaszod KIZÁRÓLAG egy érvényes JSON formátum legyen, pontosan a következő minta alapján:

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
        # textwrap.dedent levágja a felesleges behúzásokat a sorok elejéről
        return textwrap.dedent(f"""
                                Készíts egy változatos kvíz-feladatsort az alábbi tananyagrészletekből.
                                
                                SZABÁLYOK:
                                1. A kérdések száma összesen: {temakorok_szama} db legyen.
                                2. Minden alábbi témakörből pontosan 1 kérdést tegyél fel. A témakörök: {kivalasztott_temak}.
                                3. A válaszod KIZÁRÓLAG egy érvényes JSON lista legyen, annyi elemmel, ahány kérdést kértem.
                                4. Olyan feladattípust válassz az adott témakörhöz, amivel azt a leglogikusabban számon lehet kérni.
                                5. 'parositos' (párosítás) típus esetén: SOHA ne vágj ketté egy összefüggő mondatot! Csak akkor használd ezt a típust, ha egyértelmű párokat találsz a szövegben (pl. fogalom és a hozzá tartozó definíció, évszám és esemény).
                                6. 'sorbarendezos' (sorbarendezés) típus esetén: KIZÁRÓLAG akkor használd, ha a tananyagban egyértelmű időrendiség, logikai sorrend vagy egy folyamat lépései szerepelnek. Ne rendeztesd sorba a szöveg egymás után következő, de független bekezdéseit!
                                7. 'rovid_valasz' (rövid válasz) típus esetén: A kérdés csak olyan egyértelmű fogalomra vagy tényre vonatkozhat, amire 1-2 szavas, egzakt válasz adható. Ne tegyél fel olyan kérdést, amit többféleképpen is meg lehet fogalmazni!
                                8. Tartsd szem előtt, hogy KIZÁRÓLAG a lenti tananyag tartalmát kell számon kérned, ne használj külső tudást!
                                9. Használd vegyesen a következő típusokat a JSON séma alapján:

                                JSON SÉMA (Ezt kövesd pontosan a struktúra kialakításakor!):
                                [
                                  {{
                                    "id": 1,
                                    "tipus": "egyvalaszos",
                                    "kerdes": "Kérdés szövege...",
                                    "opciok": ["Rossz 1", "Helyes", "Rossz 2", "Rossz 3"],
                                    "helyes_valasz": "Helyes",
                                    "magyarazat": "Itt írd le röviden 1-2 mondatban, hogy miért ez a helyes válasz a tananyag alapján.",
                                    "tema": "Ide írd be, hogy melyik témakörhöz tartozik ez a kérdés a listából"
                                  }},
                                  {{
                                    "id": 2,
                                    "tipus": "tobbvalaszos",
                                    "kerdes": "Melyek igazak?",
                                    "opciok": ["A", "B", "C", "D"],
                                    "helyes_valaszok": ["A", "C"],
                                    "magyarazat": "Itt írd le röviden 1-2 mondatban, hogy miért ez a helyes válasz a tananyag alapján.",
                                    "tema": "Ide írd be, hogy melyik témakörhöz tartozik ez a kérdés a listából"
                                  }},
                                  {{
                                    "id": 3,
                                    "tipus": "parositos",
                                    "utasitas": "Párosítsd össze a fogalmakat a leírásukkal!",
                                    "parok": {{
                                      "Fogalom 1": "Definíció 1",
                                      "Fogalom 2": "Definíció 2"
                                    }},
                                    "magyarazat": "Itt írd le röviden 1-2 mondatban, hogy miért ez a helyes válasz a tananyag alapján.",
                                    "tema": "Ide írd be, hogy melyik témakörhöz tartozik ez a kérdés a listából"
                                  }},
                                  {{
                                    "id": 4,
                                    "tipus": "sorbarendezos",
                                    "utasitas": "Tedd helyes logikai/időrendi sorrendbe!",
                                    "sorbarendezett_elemek": ["Első lépés", "Második lépés", "Harmadik lépés"],
                                    "magyarazat": "Itt írd le röviden 1-2 mondatban, hogy miért ez a helyes válasz a tananyag alapján.",
                                    "tema": "Ide írd be, hogy melyik témakörhöz tartozik ez a kérdés a listából"
                                  }},
                                  {{
                                    "id": 5,
                                    "tipus": "rovid_valasz",
                                    "kerdes": "Mi a pontos neve a...?",
                                    "elfogadott_kulcsszavak": ["kulcsszó1", "kulcsszó2"],
                                    "magyarazat": "Itt írd le röviden 1-2 mondatban, hogy miért ez a helyes válasz a tananyag alapján.",
                                    "tema": "Ide írd be, hogy melyik témakörhöz tartozik ez a kérdés a listából"
                                  }}
                                ]

                                TANANYAG (Csak ebből dolgozz!):
                                {kontextus_szoveg}
                                """)