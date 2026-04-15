import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google.genai import types
from dotenv import load_dotenv
from google import genai
import os
import multiprocessing
from pathlib import Path
import time

from backend.adatbazis_kezelo import hatter_mentes, hatter_torles

ALAP_UTVONAL = Path("./data/subjects")

class PdfFeldolgozo:

    # inicializálás
    def __init__(self) -> None:
        load_dotenv()  # .env fájl megkereséséhez és betöltéséhez 
        api_kulcs = os.getenv('GOOGLE_API_KEY')  # megkeresi a GOOGLE_API_KEY-t   
        # átadja az API kulcsot a kliensnek   
        # csak akkor hozza létre, ha van kulcs
        self.kliens = genai.Client(api_key=api_kulcs) if api_kulcs else None
    
    def feldolgozas_es_mentes(self, pdf_utvonal: str, temakor_neve: str, fajl_neve: str, kerdes_callback=None, allapot_callback=None) -> None:
        # ellenőrzi, hogy van-e kliens (API kulcs)
        if not self.kliens:
            raise ValueError("Nincs API kulcs megadva! Kérlek, pótold a .env fájlban.")
        
        # PDF feldolgozása
        szoveg = self._pdf_szoveg_kinyerese(pdf_utvonal)
        # ha a szöveg teljesen üres
        if not szoveg.strip():
            raise ValueError("A PDF fájl üres, vagy csak képeket tartalmaz, amiből nem lehet szöveget kinyerni.")
        
        darabok = self._szoveg_darabolasa(szoveg)
        vektorok = self._vektorok_generalasa(darabok, kerdes_callback, allapot_callback)
        self._adatbazisba_mentes(temakor_neve, fajl_neve, darabok, vektorok)

    def _pdf_szoveg_kinyerese(self, pdf_utvonal: str) -> str:
        # 'with' automatikusan és biztonságosan lezárja a PDF fájlt a művelet végén
        # 'as' pedig 'dokumentum' néven hivatkozik a megnyitott fájlra
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
    
    def _vektorok_generalasa(self, darabok: list[str], kerdes_callback=None, allapot_callback=None) -> list[list[float]]:
        vektorok = []
        # alapértelmezetten 100-as kötegekben küldi az adatokat, hogy minimalizálja a hálózati kérések számát
        koteg_meret = 100 
        # jelzi, hogy a program jelenleg a normál (gyors), vagy a hálózati korlátok miatti lassított módban fut-e
        lassu_mod = False

        i = 0
        # eltárolja a szövegdarabok teljes számát a felületen lévő százalékos haladás kiszámításához
        osszes_darab = len(darabok) 
        
        # for ciklus helyett while ciklust használ, hogy hálózati hiba esetén újra tudja próbálni
        while i < osszes_darab: 
            aktualis_koteg = darabok[i:i + koteg_meret]

            try:
                # ha a program korábban beleütközött az API percenkénti korlátjába, aktiválódik a lassú mód
                if lassu_mod:
                    szazalek = int((i / osszes_darab) * 100)
                    
                    # ha a grafikus felület átadott egy állapotfrissítő csatornát, felküldi neki a jelenlegi százalékot
                    if allapot_callback:
                        allapot_callback(f"Lassított feldolgozás: {szazalek}%...")
                    
                    # 15 másodpercre szünetelteti a szálat, mielőtt elküldené a kérést
                    # ezzel garantálja a percenkénti max 4 kérést, ami biztonságosan a limit alatt marad
                    time.sleep(15) 

                eredmeny = self.kliens.models.embed_content(
                    model="gemini-embedding-001", 
                    contents=aktualis_koteg, # átadja a chunkokat
                    config=types.EmbedContentConfig(output_dimensionality=768)  # 768 darab lebegőpontos számból álló vektort kér vissza
                )
                
                # kinyeri a válaszból a vektorokat, és a listához fűzi őket
                vektorok.extend([beagyazas.values for beagyazas in eredmeny.embeddings])
                
                # ha a kérés sikeres volt (nem dobott hibát a szerver), továbblép a következő kötegre
                i += koteg_meret

            except Exception as e:
                # csupa kisbetűssé alakítja a hibaüzenetet a könnyebb és biztonságosabb kulcsszó-keresés érdekében
                hiba_szoveg = str(e).lower()
                
                # ellenőrzi, hogy a Google szervere a túl sok kérés miatt dobott-e hibát
                if "429" in hiba_szoveg or "quota" in hiba_szoveg:
                    
                    if lassu_mod:
                        # ha a program a drasztikus lassítás ellenére is elutasítást kap, az azt jelenti, 
                        # hogy a percenkénti (RPM) limit helyett a napi (Daily) limit fogyott el, így a folyamat nem folytatható
                        raise RuntimeError("A szerver ismét elutasította a kérést. Valószínűleg elérted az ingyenes API kulcs napi limitjét! Kérlek, próbáld újra holnap, vagy használj másik kulcsot.")

                    # ha ez az első alkalom, hogy elérte a percenkénti korlátot, rákérdez a felhasználónál a lassított folytatásra
                    if kerdes_callback:
                        # megállítja a háttérszálat, és a grafikus felületen felugró ablakban várja a felhasználó döntését
                        folytassa = kerdes_callback() 
                        
                        if folytassa:
                            # átváltja a rendszert lassított üzemmódba
                            lassu_mod = True
                            # lecsökkenti a kötegméretet, hogy ne lépje túl a TPM (Token Per Minute) korlátot sem
                            koteg_meret = 25 
                            
                            if allapot_callback:
                                allapot_callback("Elérted az API korlátait! Várj 60 másodpercet a nullázódásig...")
                                
                            # 60 másodperces várakozással megvárja, amíg a Google szervere lenullázza az 1 perces büntetőszámlálót
                            time.sleep(60) 
                            
                            # visszaugrik a while ciklus elejére anélkül, hogy növelné az 'i' értékét, 
                            # így adatvesztés nélkül újrapróbálja elküldeni
                            continue 
                        else:
                            # ha a felhasználó a megszakítás mellett döntött
                            raise RuntimeError("A feltöltés megszakítva a korlátozások elérése miatt.")
                    else:
                        raise e
                else:
                    # ha a hiba nem a kvótával kapcsolatos (pl. megszakadt az internet), azonnal továbbdobja a hibát a felület felé
                    raise e 

        return vektorok

    def _adatbazisba_mentes(self, temakor_neve: str, fajl_neve: str, darabok: list[str], vektorok: list[list[float]]) -> None:
        # egyedi azonosítók generálása minden egyes szövegdarabhoz
        darab_azonositok = [f"{fajl_neve}_chunk_{x}" for x in range(len(darabok))]
        # metaadatok előkészítése a darabokhoz
        # az _ jelzi, hogy a ciklusváltozó értéke nem lesz felhasználva
        # létrehozunk egy listát, amiben a {"forras": fajl_neve} szótár annyiszor szerepel, ahány darab chunk van
        metaadatok = [{"forras": fajl_neve} for _ in range(len(darabok))]
        
        adatbazis_utvonal = ALAP_UTVONAL / temakor_neve / "chroma_db"
        # parents=True: ha az útvonalban szereplő mappák még nem léteznek, akkor automatikusan létrehozza azokat
        # exist_ok=True: ha a mappák már léteznek, akkor nem történik semmi (nem dob hibát)
        adatbazis_utvonal.mkdir(parents=True, exist_ok=True)

        # egy különálló háttérfolyamat (process) létrehozása a mentéshez.
        # erre azért van szükség, mert a ChromaDB és a PyQt6 szálkezelési ütközései miatt a főszálon történő futtatás azonnali, hibaüzenet nélküli programleállást okoz
        mentesi_folyamat = multiprocessing.Process(
            target=hatter_mentes, # a hatter_mentes függvényt kell végrehajtania
            args=(str(adatbazis_utvonal), darab_azonositok, vektorok, darabok, metaadatok) # paraméterek, amikre szüksége van a függvénynek
        )
        mentesi_folyamat.start() # elindítja a háttérfolyamatot
        mentesi_folyamat.join() # a főszál itt megáll, és megvárja, amíg a mentési folyamat teljesen befejeződik, mielőtt továbblépne

    def pdf_adatok_torlese(self, temakor_neve: str, fajl_neve: str) -> None:
        adatbazis_utvonal = ALAP_UTVONAL / temakor_neve / "chroma_db"

        # exists() egy Igaz (True) vagy Hamis (False) értékkel tér vissza
        # megnézi, hogy a megadott útvonalon valóban létezik-e az az adott mappa vagy fájl
        if adatbazis_utvonal.exists():
            torlesi_folyamat = multiprocessing.Process(
                target=hatter_torles, # a hatter_torles függvényt kell végrehajtania
                args=(str(adatbazis_utvonal), fajl_neve) # paraméterek, amikre szüksége van a függvénynek
            )
            torlesi_folyamat.start() # elindítja a háttérfolyamatot
            torlesi_folyamat.join() # a főszál itt megáll, és megvárja, amíg a törlési folyamat teljesen befejeződik, mielőtt továbblépne