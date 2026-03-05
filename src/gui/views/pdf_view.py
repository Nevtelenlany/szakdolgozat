from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
from backend.pdf_loader import PDFProcessor
import shutil
import os

class pdf_view(QWidget):
    def __init__(self, temakor_neve):
        super().__init__()

        self.temakor_neve = temakor_neve

        self.mappa_utvonal = f"./data/subjects/{temakor_neve}/raw/"
        os.makedirs(self.mappa_utvonal, exist_ok=True)

        #peldanyositas
        self.pdf_processor = PDFProcessor()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.frissit_kepernyot()
    
    def frissit_kepernyot(self):
        #Vegigmegy a layout elemein es letorol mindent
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater() # letorli a memoriabol es a kepernyorol
        
        lista = os.listdir(self.mappa_utvonal)

        if len(lista) == 0:  #Nincs tantargy -> gomb rajzolasa
            szoveg = QLabel("Hmm még nincs pdf feltöltve. Esetleg tölts fel egyet! ")
            gomb = QPushButton("Új pdf hozzá adása")
            gomb.setCheckable(True)
            gomb.clicked.connect(self.button_push)
            self.layout.addWidget(szoveg)
            self.layout.addWidget(gomb)
             
        else:
            gomb = QPushButton("Új pdf hozzá adása")
            gomb.setCheckable(True)
            gomb.clicked.connect(self.button_push)
            self.layout.addWidget(gomb)
            for fajl_nev in lista:
                pdf_cimke = QLabel(fajl_nev)
                self.layout.addWidget(pdf_cimke)
        self.layout.addStretch()

    def button_push(self):
        #fajl utvonala
        utvonal, _ = QFileDialog.getOpenFileName(self,"PDF kiválasztása", "","PDF fájlok (*.pdf)")
        if utvonal:
            tiszta_utvonal = utvonal.strip()
            #fajl nev elmentese
            fajl_neve = os.path.basename(tiszta_utvonal)
            cel_utvonal = os.path.join(self.mappa_utvonal, fajl_neve)

            #fajl masolasa
            shutil.copy(tiszta_utvonal, cel_utvonal)

            # pdf_loader.py meghívása
            self.pdf_processor.process_and_store(tiszta_utvonal, self.temakor_neve, fajl_neve)
            
            # Képernyő frissítése
            self.frissit_kepernyot()