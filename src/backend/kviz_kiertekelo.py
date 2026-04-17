from pathlib import Path
import json
from abc import ABC, abstractmethod

ALAP_UTVONAL = Path("./data/subjects")

class KerdesKiertekelo(ABC):
    # absztrakt alaposztály
    @abstractmethod
    def kiertekel(self, kerdes_adat: dict, valasz: any) -> tuple[bool, dict]:
        pass

class EgyvalaszosKiertekelo(KerdesKiertekelo):
    def kiertekel(self, kerdes_adat: dict, valasz: any) -> tuple[bool, dict]:
        # kinyeri a JSON-ből a konkrét helyes választ
        helyes_valasz = kerdes_adat.get("helyes_valasz") 
        # ellenőrzi, hogy a felhasználó válasza megegyezik-e a helyes válasszal
        helyes_e = (valasz == helyes_valasz) 
        # lekéri a magyarázatot, de beállít egy alapértelmezett szöveget, ha az hiányozna
        magyarazat = kerdes_adat.get("magyarazat", "Nincs elérhető magyarázat.") 
        return helyes_e, {"magyarazat": magyarazat, "helyes_valasz": helyes_valasz}

class TobbvalaszosKiertekelo(KerdesKiertekelo):
    def kiertekel(self, kerdes_adat: dict, valasz: any) -> tuple[bool, dict]:
        # kinyeri a JSON-ből a konkrét helyes válaszokat halmazként
        helyes_valaszok = set(kerdes_adat.get("helyes_valaszok", []))
        # a felhasználó válaszait halmazzá alakítja
        # ha nincs válasz akkor [] vagyis egy üres listát ad
        felhasznalo_valaszai = set(valasz or []) 
        # ellenőrzi, hogy a felhasználó válasza megegyezik-e a helyes válasszal
        helyes_e = (felhasznalo_valaszai == helyes_valaszok)
        # lekéri a magyarázatot, de beállít egy alapértelmezett szöveget, ha az hiányozna
        magyarazat = kerdes_adat.get("magyarazat", "Nincs elérhető magyarázat.")
        return helyes_e, {"magyarazat": magyarazat, "helyes_valaszok": list(helyes_valaszok)}
    
class ParositosKiertekelo(KerdesKiertekelo):
    def kiertekel(self, kerdes_adat: dict, valasz: any) -> tuple[bool, dict]:
        # helyes párokat lekéri a JSON-ből, vagy ha valamiért hiányzik, egy üres {} szótárat ad vissza
        eredeti_parok = kerdes_adat.get("parok", {})
        # felhasználó válasza. Ha üresen hagyta, akkor egy üres {} szótárat ad vissza
        valasz_szotar = valasz or {}
        # ellenőrzi, hogy a felhasználó válasza pontosan megegyezik-e a helyes válasszal
        helyes_e = (valasz_szotar == eredeti_parok)
        # lekéri a magyarázatot, de beállít egy alapértelmezett szöveget, ha az hiányozna
        magyarazat = kerdes_adat.get("magyarazat", "Nincs elérhető magyarázat.")
        return helyes_e, {"magyarazat": magyarazat, "parok": eredeti_parok}

class SorbarendezosKiertekelo(KerdesKiertekelo):
    def kiertekel(self, kerdes_adat: dict, valasz: any) -> tuple[bool, dict]:
        # helyes sorrendet lekéri a JSON-ből, vagy ha valamiért hiányzik, egy üres listát ad vissza
        eredeti_sorrend = kerdes_adat.get("sorbarendezett_elemek", [])
        # felhasználó válasza. Ha üresen hagyta, akkor egy üres [] listát ad vissza
        valasz_lista = valasz or []
        # ellenőrzi, hogy a felhasználó válasza pontosan megegyezik-e a helyes válasszal
        helyes_e = (valasz_lista == eredeti_sorrend)
        # lekéri a magyarázatot, de beállít egy alapértelmezett szöveget, ha az hiányozna
        magyarazat = kerdes_adat.get("magyarazat", "Nincs elérhető magyarázat.")
        return helyes_e, {"magyarazat": magyarazat, "sorbarendezett_elemek": eredeti_sorrend}
    
class RovidValaszKiertekelo(KerdesKiertekelo):
    def kiertekel(self, kerdes_adat: dict, valasz: any) -> tuple[bool, dict]:
        # elfogadott kulcsszavakat lekéri a JSON-ből, és minden szót kisbetűssé alakít a lower() segítségével
        elfogadott = [k.lower() for k in kerdes_adat.get("elfogadott_kulcsszavak", [])]
        # felhasználó által beírt választ szöveggé alakítja (ha nem írt be semmit, akkor üres szöveget használ)
        # strip() eltávolítja a felesleges szóközöket a szélekről, a lower() pedig kisbetűssé teszi
        beirt = str(valasz or "").strip().lower()
        # megnézi, hogy a beírt szöveg tartalmaz-e legalább egyet az elfogadott kulcsszavak közül. Ha igen, True értéket ad vissza
        helyes_e = any(k in beirt for k in elfogadott)
        # lekéri a magyarázatot, de beállít egy alapértelmezett szöveget, ha az hiányozna
        magyarazat = kerdes_adat.get("magyarazat", "Nincs elérhető magyarázat.")
        return helyes_e, {"magyarazat": magyarazat, "elfogadott_kulcsszavak": elfogadott}
    
# szótár (térkép), ami összeköti a JSON-ből kapott kérdéstípusokat a megfelelő kiértékelő osztályokkal
KIERTEKELOK = {
    "egyvalaszos": EgyvalaszosKiertekelo(),
    "tobbvalaszos": TobbvalaszosKiertekelo(),
    "rovid_valasz": RovidValaszKiertekelo(),
    "parositos": ParositosKiertekelo(),
    "sorbarendezos": SorbarendezosKiertekelo()
}

class KvizFajlKezelo:
    @staticmethod
    def elerheto_pdf_ek_lekerese(alap_utvonal: str | Path) -> list[str]:
        mappa = Path(alap_utvonal)
        
        # mappa.is_dir() ellenőrzi, hogy a megadott útvonalon tényleg egy mappa található-e
        if not mappa.is_dir():
            return []
        
        # f.name levágja az útvonalat de megtartja a fájl nevét
        # mappa.glob("*.pdf") a mappában megkeres minden fájlt
        # f.is_file() ellenőrzi hogy tényleg fájl-e
        return [f.name for f in mappa.glob("*.pdf") if f.is_file()]

class KvizKiertekelo:
    @staticmethod
    def kviz_kiertekelese(kviz_adatok: list[dict], felhasznalo_valaszai: dict, temakor_neve: str | None = None, fajl_neve: str | None = None) -> tuple[int, int, dict]:
        ossz_pont, elert_pont, eredmenyek = KvizKiertekelo._kiertekel_valaszokat(kviz_adatok, felhasznalo_valaszai)
        if temakor_neve and fajl_neve:
            KvizKiertekelo._haladas_frissitese(temakor_neve, fajl_neve, eredmenyek)
        return elert_pont, ossz_pont, eredmenyek
    
    @staticmethod
    def _kiertekel_valaszokat(kviz_adatok: list[dict], felhasznalo_valaszai: dict) -> tuple[int, int, dict]:
        ossz_pont = len(kviz_adatok)
        elert_pont = 0
        eredmenyek = {}

        for kerdes_adat in kviz_adatok:
            k_id = kerdes_adat.get("id")
            tipus = kerdes_adat.get("tipus")
            tema = kerdes_adat.get("tema")
            valasz = felhasznalo_valaszai.get(k_id) 
            kiertekelo = KIERTEKELOK.get(tipus)
            if kiertekelo:
                helyes_e, visszajelzes = kiertekelo.kiertekel(kerdes_adat, valasz)
                if helyes_e:
                    elert_pont += 1
            else:
                helyes_e = False
                visszajelzes = {"magyarazat": f"Ismeretlen kérdéstípus: {tipus}"}
                
            eredmenyek[k_id] = {"helyes": helyes_e, "visszajelzes": visszajelzes, "tema": tema}

        return ossz_pont, elert_pont, eredmenyek
    
    @staticmethod
    def _haladas_frissitese(temakor_neve: str, fajl_neve: str, eredmenyek: dict) -> None:
        json_utvonal = KvizKiertekelo._haladas_fajl_utvonal_lekerese(temakor_neve, fajl_neve)

        # exists() egy Igaz (True) vagy Hamis (False) értékkel tér vissza
        # megnézi, hogy a megadott útvonalon valóban létezik-e az az adott mappa vagy fájl
        if not json_utvonal.exists(): 
            return
        
        try:
            # 'with' automatikusan és biztonságosan lezárja a JSON-fájlt a művelet végén
            # 'as' pedig 'f' néven hivatkozik a megnyitott fájlra.
            with open(json_utvonal, 'r', encoding='utf-8') as f:
                # a json.load() beolvassa a megnyitott fájlt, és a benne lévő JSON adatokat Python szótárrá alakítja
                temak = json.load(f)               
            frissitett_temak = KvizKiertekelo._haladas_logika_alkalmazasa(temak, eredmenyek)
            
            # json.dump a szótárat JSON-fájllá alakítja
            # az ensure_ascii=False megtartja az ékezeteket, ami a magyar nyelv miatt szükséges
            # indent=4 a JSON-fájlban a szinteket 4 szóközzel választja el a szebb megjelenésért
            with open(json_utvonal, 'w', encoding='utf-8') as f:
                json.dump(frissitett_temak, f, ensure_ascii=False, indent=4)

        except (FileNotFoundError, PermissionError, json.JSONDecodeError, OSError) as hiba:
            # type(hiba) visszaadja a hiba típusát
            # __name__ letisztítja a kimenetet (csak a hiba nevét adja vissza)
            # {hiba} kiírja a pontos hibaüzenetet
            print(f"Hiba történt a haladás mentésekor ({type(hiba).__name__}): {hiba}")

    @staticmethod
    def _haladas_fajl_utvonal_lekerese(temakor_neve: str, fajl_neve: str) -> Path:
        temakor_mappa = ALAP_UTVONAL / temakor_neve
        haladas_mappa = temakor_mappa / "progress"
        return haladas_mappa / f"{fajl_neve}_progress.json"

    @staticmethod
    def _haladas_logika_alkalmazasa(temak: dict, eredmenyek: dict) -> dict:
        # az _ jelzi, hogy a ciklusváltozó értéke nem lesz felhasználva
        for _, adat in eredmenyek.items():
            tema_neve = adat.get("tema")
            helyes_e = adat.get("helyes")

            # ha a kérdéshez nem tartozik téma, vagy ismeretlen a téma, átugorjuk
            if not tema_neve or tema_neve not in temak:
                continue   
            tema_adat = temak[tema_neve]
            if helyes_e:
                # helyes válasz esetén: közeledik a célhoz (0-ig). Ha elérte, elsajátítottnak számít a témakör
                tema_adat["valaszok"] = max(0, tema_adat["valaszok"] - 1)
                if tema_adat["valaszok"] == 0:
                    tema_adat["elsajatitva"] = True
            else:
                # hibás válasz esetén: visszalépés a tanulásban (max 5-ig), és elveszti az elsajátított státuszt
                tema_adat["valaszok"] = min(5, tema_adat["valaszok"] + 1)
                tema_adat["elsajatitva"] = False
        return temak

    @staticmethod
    def kiertekeles_osszegzese(elert_pont: int, ossz_pont: int) -> tuple[str, str, float]:
        szazalek = (elert_pont / ossz_pont) * 100 if ossz_pont > 0 else 0

        if szazalek == 100:
            return "tokeletes", "Hibátlan munka!", szazalek
        elif szazalek >= 60:
            return "kozepes", "Szép eredmény, de van még mit tanulni!", szazalek
        else:
            return "rossz", "Ezt még át kell ismételned!", szazalek
        
    @staticmethod
    def haladas_szazalek_lekerese(temakor_neve: str, fajl_neve: str) -> str:
        json_utvonal = KvizKiertekelo._haladas_fajl_utvonal_lekerese(temakor_neve, fajl_neve)

        # exists() egy Igaz (True) vagy Hamis (False) értékkel tér vissza
        # megnézi, hogy a megadott útvonalon valóban létezik-e az az adott mappa vagy fájl
        if not json_utvonal.exists(): 
            return "0%"
        
        try:
            # 'with' automatikusan és biztonságosan lezárja a JSON-fájlt a művelet végén
            # 'as' pedig 'f' néven hivatkozik a megnyitott fájlra.
            with open(json_utvonal, 'r', encoding='utf-8') as f:
                # a json.load() beolvassa a megnyitott fájlt, és a benne lévő JSON adatokat Python szótárrá alakítja
                temak = json.load(f)

            # Ha nincs benne téma akkor jelezzűk hogy nincs mit értékelni
            if not temak:
                return "Nincs értékelhető tartalom"
                
            osszes_tema = len(temak)*5

            # végigmegy az összes témán
            # 5-öt ad hozzá, ha az "elsajatitva": True
            # különben megnézi, milyen szám van a "valaszok" értéknél, azt kivonja 5-ből, és az eredményt adja hozzá
            elsajatitott = sum(5 if adat.get("elsajatitva", False) else (5 - adat.get("valaszok", 0)) for adat in temak.values())
            
            szazalek = int((elsajatitott / osszes_tema) * 100)
            return f"{szazalek}%"
            
        except (FileNotFoundError, PermissionError, json.JSONDecodeError, OSError) as hiba:
            # type(hiba) visszaadja a hiba típusát
            # __name__ letisztítja a kimenetet (csak a hiba nevét adja vissza)
            # {hiba} kiírja a pontos hibaüzenetet a konzolra (fejlesztői segítség)
            print(f"Hiba történt a haladás beolvasásakor ({type(hiba).__name__}): {hiba}")
            return "Hiba"