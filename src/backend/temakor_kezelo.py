from pathlib import Path
import shutil
import re

from backend.pdf_feldolgozo import PdfFeldolgozo

ALAP_UTVONAL = Path("./data/subjects")

class TemakorKezelo:
    
    # inicializálás
    def __init__(self, temakor_neve: str | None = None) -> None:
        self.alap_utvonal = ALAP_UTVONAL
        
        # parents=True: ha az útvonalban szereplő mappák még nem léteznek, akkor automatikusan létrehozza azokat
        # exist_ok=True: ha a mappák már léteznek, akkor nem történik semmi (nem dob hibát)
        self.alap_utvonal.mkdir(parents=True, exist_ok=True)
        self.temakor_neve = temakor_neve
        
        if self.temakor_neve:
            self.mappa_utvonal = self.alap_utvonal / self.temakor_neve / "raw"
            self.mappa_utvonal.mkdir(parents=True, exist_ok=True)
            self.pdf_feldolgozo = PdfFeldolgozo()

    def temakorok_lekerese(self) -> list[str]:
        # iterdir() végigmegy az alap_utvonalon található összes elemen
        # is_dir() kiszűri, hogy csak a mappákat (a témakörök neveit) kapjuk meg, fájlokat ne
        return [mappa.name for mappa in self.alap_utvonal.iterdir() if mappa.is_dir()]
    
    def _nev_validalasa(self, nev: str) -> tuple[bool, str]:
        # ellenőrzi a hosszúságát
        if len(nev) > 200:
            return False, "A név túl hosszú (maximum 200 karakter lehet)."

        # fájlrendszer által tiltott karakterek szűrése regex segítségével
        tiltott_karakterek = r'[<>:"/\\|?*]'
        if re.search(tiltott_karakterek, nev):
            return False, 'A név nem tartalmazhatja a következő karaktereket:\n< > : " / \\ | ? *'
     
        # windows által fenntartott nevek szűrése
        fenntartott_nevek = {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}
        if nev.upper() in fenntartott_nevek:
            return False, "Ez a név az operációs rendszer által fenntartott. Kérlek, válassz másikat!"
        return True, ""
    
    def temakor_letrehozasa(self, temakor_neve: str) -> tuple[bool, str]:

        siker, uzenet = self._nev_validalasa(temakor_neve)
        if not siker:
            return False, uzenet

        utvonal = self.alap_utvonal / temakor_neve
        
        try:
            # ténylegesen létrehozzuk a mappát a fájlrendszerben
            utvonal.mkdir(parents=True, exist_ok=False)
            return True, "Témakör sikeresen létrehozva."
        except OSError as e:
            return False, f"Fájlrendszeri hiba a létrehozás során: {e}"

    def temakor_atnevezese(self, regi_temakor_neve: str, uj_temakor_neve: str) -> tuple[bool, str]:

        siker, uzenet = self._nev_validalasa(uj_temakor_neve)
        if not siker:
            return False, uzenet
            
        regi_utvonal = self.alap_utvonal / regi_temakor_neve
        uj_utvonal = self.alap_utvonal / uj_temakor_neve

        # ellenőrizzük, hogy az új néven létezik-e már mappa
        if uj_utvonal.exists():
            return False, "Ilyen nevű témakör már létezik!"
            
        try:
            # a rename() átnevezi a mappát a fájlrendszerben
            regi_utvonal.rename(uj_utvonal)
            
            # frissítjük a belső változókat az új névre
            if self.temakor_neve == regi_temakor_neve:
                self.temakor_neve = uj_temakor_neve
                self.mappa_utvonal = self.alap_utvonal / self.temakor_neve / "raw"
                
            return True, "Sikeres átnevezés."
        except FileNotFoundError:
            return False, "Hiba: Az átnevezni kívánt témakör nem található."
        except PermissionError:
            return False, "Hiba: Nincs jogosultság a mappa átnevezéséhez."
        except OSError as e:
            return False, f"Fájlrendszeri hiba történt az átnevezés során: {e}"

    def temakor_torlese(self, temakor_neve: str) -> tuple[bool, str]:
        utvonal = self.alap_utvonal / temakor_neve

        try:
            # shutil.rmtree() rekurzívan törli a mappát és annak minden tartalmát (fájlokat, almappákat)
            # ez azért kell, mert sima mappa-törlő paranccsal csak üres mappákat lehetne törölni
            shutil.rmtree(utvonal)
            return True, "Sikeres törlés."
        except FileNotFoundError:
            return False, "Hiba: A témakör nem található."
        except PermissionError:
            return False, "Hiba: Nincs jogosultság a mappa törléséhez."
        except OSError as e:
            return False, f"Fájlrendszeri hiba történt a törlés során: {e}"
        
    def fajlok_lekerese(self) -> list[str]:
        # ha nincs kiválasztott témakör, egy üres listát adunk vissza
        if not self.temakor_neve: 
            return []
            
        # f.name levágja az útvonalat de megtartja a fájl nevét
        # self.mappa_utvonal.glob("*.pdf") a mappában megkeres minden fájlt
        # f.is_file() ellenőrzi hogy tényleg fájl-e
        return [f.name for f in self.mappa_utvonal.glob("*.pdf") if f.is_file()]

    def pdf_hozzadasa(self, forras_utvonal: str | Path) -> None:
        # ha nincs kiválasztott témakör, kilépünk a folyamatból
        if not self.temakor_neve: 
            return
            
        forras_utvonal = Path(forras_utvonal)
        # name levágja az útvonalat de megtartja a fájl nevét
        fajl_neve = forras_utvonal.name
        self._masol_fizikai_fajlt(forras_utvonal, fajl_neve)
        self._vektorizalas_es_mentes(forras_utvonal, fajl_neve)

    def _masol_fizikai_fajlt(self, forras_utvonal: Path, fajl_neve: str) -> None:
        # parents=True: ha az útvonalban szereplő mappák még nem léteznek, akkor automatikusan létrehozza azokat
        # exist_ok=True: ha a mappák már léteznek, akkor nem történik semmi (nem dob hibát)
        self.mappa_utvonal.mkdir(parents=True, exist_ok=True)

        cel_utvonal = self.mappa_utvonal / fajl_neve
        
        # shutil.copy átmásolja a fájlt a forrásból a program célmappájába
        shutil.copy(forras_utvonal, cel_utvonal)

    def _vektorizalas_es_mentes(self, forras_utvonal: Path, fajl_neve: str) -> None:
        self.pdf_feldolgozo.feldolgozas_es_mentes(str(forras_utvonal), self.temakor_neve, fajl_neve)

    def pdf_torlese(self, fajl_neve: str) -> None:
        # ha nincs kiválasztott témakör, kilépünk a folyamatból
        if not self.temakor_neve: 
            return
        
        self._torol_fizikai_fajlt(fajl_neve)
        self._torol_adatbazis_adatokat(fajl_neve)
        self._torol_haladas_adatokat(fajl_neve)

    def _torol_fizikai_fajlt(self, fajl_neve: str) -> None:
        fajl_utvonal = self.mappa_utvonal / fajl_neve
        # az unlink() parancs letörli a konkrét fájlt
        # missing_ok=True: ha a fájl valamiért már nincs ott, nem dob hibát, csak továbbmegy
        fajl_utvonal.unlink(missing_ok=True)
        
    def _torol_adatbazis_adatokat(self, fajl_neve: str) -> None:
        self.pdf_feldolgozo.pdf_adatok_torlese(self.temakor_neve, fajl_neve)

    def _torol_haladas_adatokat(self, fajl_neve: str) -> None:
        haladas_json_utvonal = self.alap_utvonal / self.temakor_neve / "progress" / f"{fajl_neve}_progress.json"
        # az unlink() parancs letörli a konkrét fájlt
        # missing_ok=True: ha a fájl valamiért már nincs ott, nem dob hibát, csak továbbmegy
        haladas_json_utvonal.unlink(missing_ok=True)
        
    def adatbazis_utvonal_lekerese(self) -> str | None:
        # ha nincs kiválasztott témakör, kilépünk a folyamatból
        if not self.temakor_neve:
            return None
            
        return str(self.alap_utvonal / self.temakor_neve / "chroma_db")

    def van_aktiv_adatbazis(self) -> bool:
        # := (walrus operátor) értékadás és vizsgálat egyben.
        # lekéri az adatbázis útvonalát, eltárolja a db_utvonal változóban, és ha az nem None, rögtön belép az if-be.
        if db_utvonal := self.adatbazis_utvonal_lekerese():
             # megnézi, hogy a megadott útvonalon valóban létezik-e az az adott mappa vagy fájl
            return (Path(db_utvonal) / "chroma.sqlite3").exists()
        return False