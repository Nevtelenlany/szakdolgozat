import os
from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget, QLabel, QInputDialog, QApplication
from PyQt6.QtCore import pyqtSignal

class HomeScreen(QWidget):
    valasztott_temakor = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.path_ = "./data/subjects/"
        os.makedirs(self.path_, exist_ok=True)
        lista = os.listdir(self.path_)
        self.layout = QVBoxLayout()

        self.setLayout(self.layout)
        self.frissit_kepernyot()

    def button_push(self):  #Temakor nevenek a megadasa
        while True:
            text, ok = QInputDialog().getText(self, "Új témakör","Mi legyen az új témakör neve?")
            if not ok:
                    return
            tiszta_szoveg = text.strip()
            
            if tiszta_szoveg == "": continue
            if ok: 
                 uj_mappa_utvonal = os.path.join(self.path_, tiszta_szoveg) 
                 os.makedirs(uj_mappa_utvonal, exist_ok=True) 
                 break
        self.frissit_kepernyot()
            

    def frissit_kepernyot(self):
        #Vegigmegy a layout elemein es letorol mindent
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater() # letorli a memoriabol es a kepernyorol

        lista = os.listdir(self.path_)

        if len(lista) == 0:  #Nincs tantargy -> gomb rajzolasa
            szoveg = QLabel("Hmm még nincs létrehozva témakör. Esetleg hozz létre újat! ")
            gomb = QPushButton("Új témakör létrehozása")
            gomb.setCheckable(True)
            gomb.clicked.connect(self.button_push)
            self.layout.addWidget(szoveg)
            self.layout.addWidget(gomb)
             
        else:
            gomb = QPushButton("Új témakör létrehozása")
            gomb.setCheckable(True)
            gomb.clicked.connect(self.button_push)
            self.layout.addWidget(gomb)
            for mappa_nev in lista:
                 tantargy_gomb = QPushButton(mappa_nev)
                 tantargy_gomb.setCheckable(True)
                 tantargy_gomb.clicked.connect(lambda ellenorzes=False, nev=mappa_nev: self.tantargy_megnyitasa(nev))
                 self.layout.addWidget(tantargy_gomb)
        
        self.layout.addStretch() 
        
        self.kilepes_gomb = QPushButton("Kilépés")
        self.kilepes_gomb.clicked.connect(QApplication.instance().quit)
        self.layout.addWidget(self.kilepes_gomb)

    def tantargy_megnyitasa(self, kivalasztott_temakor):
        self.valasztott_temakor.emit(kivalasztott_temakor)