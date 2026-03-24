from pathlib import Path
from PyQt6.QtWidgets import (QPushButton, QVBoxLayout, QWidget, QLabel, 
                             QInputDialog, QApplication, QHBoxLayout, 
                             QSizePolicy, QScrollArea, QGridLayout)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QIcon

from backend.temakoroklistaja import Temakorlista

class HomeScreen(QWidget):
    valasztott_temakor = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.backend = Temakorlista()
        
        self._setup_layout()
        self._load_stylesheet()
        self._setup_header_and_empty_state()
        self._setup_grid_view()
        self._setup_bottom_buttons()
        
        self.frissit_kepernyot()

    def _setup_layout(self) -> None:
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def _load_stylesheet(self) -> None:
        stilus_utvonal = Path(__file__).resolve().parents[3] / "assets" / "style.qss"
        if stilus_utvonal.exists():
            self.setStyleSheet(stilus_utvonal.read_text(encoding="utf-8"))
        else:
            print(f"Hiba (HomeScreen): Nem találom a stíluslapot itt: {stilus_utvonal}")

    def _setup_header_and_empty_state(self) -> None:
        self.cim_szoveg = QLabel("Témakörök listája")
        self.cim_szoveg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cim_szoveg.setObjectName("MainTitle")
        self.layout.addWidget(self.cim_szoveg)

        self.ures_szoveg = QLabel("Hmm még nincs létrehozva témakör. Esetleg hozz létre újat!")
        self.ures_szoveg.setObjectName("EmptyText")
        self.ures_szoveg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.ures_szoveg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.ures_szoveg)
        self.ures_szoveg.hide()

    def _setup_grid_view(self) -> None:
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("SubjectScrollArea")

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        
        self.scroll_area.setWidget(self.grid_container)
        self.layout.addWidget(self.scroll_area)

    def _setup_bottom_buttons(self) -> None:
        also_gombok_layout = QHBoxLayout()

        self.uj_gomb = QPushButton("Új témakör létrehozása")
        self.uj_gomb.setIcon(QIcon("assets/icons/hozzadas_gomb.png"))
        self.uj_gomb.setIconSize(QSize(24, 24))
        self.uj_gomb.setObjectName("ActionButton")
        self.uj_gomb.clicked.connect(self.button_push)
        also_gombok_layout.addWidget(self.uj_gomb)
        
        self.kilepes_gomb = QPushButton("Kilépés")
        self.kilepes_gomb.setObjectName("ActionButton2")
        self.kilepes_gomb.clicked.connect(QApplication.instance().quit)
        also_gombok_layout.addWidget(self.kilepes_gomb)

        self.layout.addLayout(also_gombok_layout)

    def button_push(self) -> None:  
        text, ok = QInputDialog().getText(self, "Új témakör", "Mi legyen az új témakör neve?")
        
        if ok and (tiszta_szoveg := text.strip()):
            self.backend.create_subject(tiszta_szoveg)
            self.frissit_kepernyot()

    def frissit_kepernyot(self) -> None:
        lista = self.backend.get_subjects()

        if not lista:
            self.scroll_area.hide()
            self.ures_szoveg.show()
        else:
            self.ures_szoveg.hide()
            self.scroll_area.show()
            
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                if widget := item.widget():
                    widget.deleteLater()

            oszlopok_szama = 4
            for index, mappa_nev in enumerate(lista):
                sor = index // oszlopok_szama
                oszlop = index % oszlopok_szama
                
                tantargy_gomb = QPushButton(mappa_nev)
                tantargy_gomb.setMinimumSize(140, 140)
                tantargy_gomb.setMaximumSize(300, 300)
                tantargy_gomb.setObjectName("SubjectButton")
                tantargy_gomb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                tantargy_gomb.clicked.connect(lambda checked=False, nev=mappa_nev: self.tantargy_megnyitasa(nev))
                
                self.grid_layout.addWidget(tantargy_gomb, sor, oszlop)

    def tantargy_megnyitasa(self, kivalasztott_temakor: str) -> None:
        self.valasztott_temakor.emit(kivalasztott_temakor)