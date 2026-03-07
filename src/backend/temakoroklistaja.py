import os
import shutil

class Temakorlista:
    def __init__(self, base_path="./data/subjects/"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

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