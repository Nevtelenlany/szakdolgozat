import os
import shutil

from backend.pdf_loader import PDFProcessor

class Temakorlista:
    def __init__(self, temakor_neve=None, base_path="./data/subjects/"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)
        
        self.temakor_neve = temakor_neve
        if self.temakor_neve:
            self.mappa_utvonal = os.path.join(self.base_path, self.temakor_neve, "raw")
            os.makedirs(self.mappa_utvonal, exist_ok=True)
            self.pdf_processor = PDFProcessor()

    def get_subjects(self):
        return os.listdir(self.base_path)

    def create_subject(self, name):
        path = os.path.join(self.base_path, name)
        os.makedirs(path, exist_ok=True)

    def rename_subject(self, old_name, new_name):
            old_path = os.path.join(self.base_path, old_name)
            new_path = os.path.join(self.base_path, new_name)

            if os.path.exists(new_path):
                return False, "Ilyen nevű témakör már létezik!"
            try:
                os.rename(old_path, new_path)
                return True, "Sikeres átnevezés."
            except Exception as e:
                return False, f"Hiba történt az átnevezés során: {str(e)}"

    def delete_subject(self, name):
        path = os.path.join(self.base_path, name)
        
        if not os.path.exists(path):
            return False, "A témakör nem található."
        try:
            # shutil.rmtree törli a mappát és a tartalmát
            shutil.rmtree(path)
            return True, "Sikeres törlés."
        except Exception as e:
            return False, f"Hiba történt a törlés során: {str(e)}"
        

    def get_files(self):
        if not self.temakor_neve: return []
        return os.listdir(self.mappa_utvonal)

    def add_pdf(self, forras_utvonal):
        if not self.temakor_neve: return
        fajl_neve = os.path.basename(forras_utvonal)
        cel_utvonal = os.path.join(self.mappa_utvonal, fajl_neve)
        shutil.copy(forras_utvonal, cel_utvonal)
        self.pdf_processor.process_and_store(forras_utvonal, self.temakor_neve, fajl_neve)

    def delete_pdf(self, fajl_nev):
        if not self.temakor_neve: return
        fajl_utvonal = os.path.join(self.mappa_utvonal, fajl_nev)
        if os.path.exists(fajl_utvonal):
            os.remove(fajl_utvonal)
        self.pdf_processor.delete_pdf_data(self.temakor_neve, fajl_nev)

    def get_chroma_db_path(self):
        """Visszaadja a ChromaDB elérési útját az aktuális témakörhöz."""
        if not self.temakor_neve:
            return None
        return os.path.join(self.base_path, self.temakor_neve, "chroma_db")

    def has_active_db(self):
        """Ellenőrzi, hogy létezik-e az adatbázis a témakörhöz."""
        db_path = self.get_chroma_db_path()
        if not db_path:
            return False
        
        db_file = os.path.join(db_path, "chroma.sqlite3")
        return os.path.exists(db_file)