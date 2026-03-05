import os

class Temakorlista:
    def __init__(self, base_path="./data/subjects/"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def get_subjects(self):
        return os.listdir(self.base_path)

    def create_subject(self, name):
        path = os.path.join(self.base_path, name)
        os.makedirs(path, exist_ok=True)