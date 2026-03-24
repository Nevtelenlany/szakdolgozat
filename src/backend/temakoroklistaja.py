from pathlib import Path
import shutil

from backend.pdf_feldolgozo import PdfFeldolgozo

class Temakorlista:
    def __init__(self, temakor_neve: str | None = None, base_path: str | Path = "./data/subjects/") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.temakor_neve = temakor_neve
        if self.temakor_neve:
            self.mappa_utvonal = self.base_path / self.temakor_neve / "raw"
            self.mappa_utvonal.mkdir(parents=True, exist_ok=True)
            self.pdf_processor = PdfFeldolgozo()

    def get_subjects(self) -> list[str]:
        return [mappa.name for mappa in self.base_path.iterdir() if mappa.is_dir()]

    def create_subject(self, name: str) -> None:
        path = self.base_path / name
        path.mkdir(parents=True, exist_ok=True)

    def rename_subject(self, old_name: str, new_name: str) -> tuple[bool, str]:
        old_path = self.base_path / old_name
        new_path = self.base_path / new_name

        if new_path.exists():
            return False, "Ilyen nevű témakör már létezik!"
            
        try:
            old_path.rename(new_path)
            return True, "Sikeres átnevezés."
        except FileNotFoundError:
            return False, "Hiba: Az átnevezni kívánt témakör nem található."
        except PermissionError:
            return False, "Hiba: Nincs jogosultság a mappa átnevezéséhez."
        except OSError as e:
            return False, f"Fájlrendszeri hiba történt az átnevezés során: {e}"

    def delete_subject(self, name: str) -> tuple[bool, str]:
        path = self.base_path / name

        try:
            shutil.rmtree(path)
            return True, "Sikeres törlés."
        except FileNotFoundError:
            return False, "Hiba: A témakör nem található."
        except PermissionError:
            return False, "Hiba: Nincs jogosultság a mappa törléséhez."
        except OSError as e:
            return False, f"Fájlrendszeri hiba történt a törlés során: {e}"

    def get_files(self) -> list[str]:
        if not self.temakor_neve: 
            return []
            
        return [f.name for f in self.mappa_utvonal.iterdir() if f.is_file() and f.name.lower().endswith('.pdf')]
    
    def add_pdf(self, forras_utvonal: str | Path) -> None:
        if not self.temakor_neve: 
            return
            
        forras_path = Path(forras_utvonal)
        fajl_neve = forras_path.name
        self._masol_fizikai_fajlt(forras_path, fajl_neve)
        self._vektorizalas_es_mentes(forras_path, fajl_neve)

    def _masol_fizikai_fajlt(self, forras_path: Path, fajl_neve: str) -> None:
        cel_utvonal = self.mappa_utvonal / fajl_neve
        shutil.copy(forras_path, cel_utvonal)

    def _vektorizalas_es_mentes(self, forras_path: Path, fajl_neve: str) -> None:
        self.pdf_processor.feldolgozas_es_mentes(str(forras_path), self.temakor_neve, fajl_neve)

    def delete_pdf(self, fajl_nev: str) -> None:
        if not self.temakor_neve: 
            return
        
        self._torol_fizikai_fajlt(fajl_nev)
        self._torol_adatbazis_adatokat(fajl_nev)
        self._torol_haladas_adatokat(fajl_nev)

    def _torol_fizikai_fajlt(self, fajl_nev: str) -> None:
        fajl_utvonal = self.mappa_utvonal / fajl_nev
        fajl_utvonal.unlink(missing_ok=True)
            
    def _torol_adatbazis_adatokat(self, fajl_nev: str) -> None:
        self.pdf_processor.delete_pdf_data(self.temakor_neve, fajl_nev)

    def _torol_haladas_adatokat(self, fajl_nev: str) -> None:
        progress_json_utvonal = self.base_path / self.temakor_neve / "progress" / f"{fajl_nev}_progress.json"
        progress_json_utvonal.unlink(missing_ok=True)

    def get_chroma_db_path(self) -> str | None:
        if not self.temakor_neve:
            return None
        return str(self.base_path / self.temakor_neve / "chroma_db")

    def has_active_db(self) -> bool:
        if db_path := self.get_chroma_db_path():
            return (Path(db_path) / "chroma.sqlite3").exists()
        return False