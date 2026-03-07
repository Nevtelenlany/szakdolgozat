import os
from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget, QLabel, QInputDialog, QApplication, QGridLayout, QHBoxLayout, QSizePolicy, QScrollArea
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QIcon
from backend.temakoroklistaja import Temakorlista

class HomeScreen(QWidget):
    valasztott_temakor = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.backend = Temakorlista()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        jelenlegi_mappa = os.path.dirname(os.path.abspath(__file__)) #ennek a file-nak a helye
        stilus_utvonal = os.path.join(jelenlegi_mappa, "..", "..", "..", "assets", "style.qss")
        stilus_utvonal = os.path.normpath(stilus_utvonal) #rendet tesz a perjelek között

        if os.path.exists(stilus_utvonal):
            with open(stilus_utvonal, "r", encoding="utf-8") as style_file:
                self.setStyleSheet(style_file.read())

        self.frissit_kepernyot()

    def button_push(self):  #Temakor nevenek a megadasa
        while True:
            text, ok = QInputDialog().getText(self, "Új témakör","Mi legyen az új témakör neve?")
            if not ok:
                    return
            tiszta_szoveg = text.strip()
            
            if tiszta_szoveg == "": continue
            if ok: 
                 self.backend.create_subject(tiszta_szoveg)
                 break
        self.frissit_kepernyot()
            

    def frissit_kepernyot(self):
        #Vegigmegy a layout elemein es letorol mindent
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater() # letorli a memoriabol es a kepernyorol
            elif item.layout() is not None:
                self.torol_layout(item.layout())

        cim_szoveg = QLabel("Témakörök listája")
        cim_szoveg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cim_szoveg.setObjectName("MainTitle")

        self.layout.addWidget(cim_szoveg)

        lista = self.backend.get_subjects()

        if len(lista) == 0:  #Nincs tantargy -> gomb rajzolasa
            szoveg = QLabel("Hmm még nincs létrehozva témakör. Esetleg hozz létre újat! ")
            szoveg.setObjectName("EmptyText")

            szoveg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            szoveg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.layout.addWidget(szoveg)
            self.layout.addWidget(szoveg)
             
        else:
            #Rács létrehozasa 
            grid_layout = QGridLayout()
            oszlopok_szama = 4

            for index, mappa_nev in enumerate(lista):
                 pozicio = index
                 sor = pozicio // oszlopok_szama
                 oszlop = pozicio % oszlopok_szama
            
                 tantargy_gomb = QPushButton(mappa_nev)
                 tantargy_gomb.setMinimumSize(140, 140)
                 tantargy_gomb.setObjectName("SubjectButton")
                 tantargy_gomb.setMaximumSize(300, 300)
                 tantargy_gomb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                 tantargy_gomb.setCheckable(True)
                 tantargy_gomb.clicked.connect(lambda ellenorzes=False, nev=mappa_nev: self.tantargy_megnyitasa(nev))
                 grid_layout.addWidget(tantargy_gomb, sor, oszlop)

            grid_doboz = QWidget()
            grid_doboz.setLayout(grid_layout)
            
            #létrehozzuk a görgetősávot
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(grid_doboz)
            self.layout.addWidget(scroll_area)
        
        also_gombok_layout = QHBoxLayout()

        self.uj_gomb = QPushButton("Új témakör létrehozása")
        self.uj_gomb.setIcon(QIcon("assets/icons/hozzadas_gomb.png"))
        self.uj_gomb.setIconSize(QSize(24, 24)) #ikon merete
        self.uj_gomb.setObjectName("ActionButton")
        
        self.uj_gomb.clicked.connect(self.button_push)
        also_gombok_layout.addWidget(self.uj_gomb)
        
        self.kilepes_gomb = QPushButton("Kilépés")
        self.kilepes_gomb.setObjectName("ActionButton2")
        self.kilepes_gomb.clicked.connect(QApplication.instance().quit)
        also_gombok_layout.addWidget(self.kilepes_gomb)

        self.layout.addLayout(also_gombok_layout)

    def tantargy_megnyitasa(self, kivalasztott_temakor):
        self.valasztott_temakor.emit(kivalasztott_temakor)

    def torol_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self.torol_layout(item.layout())
        layout.deleteLater()