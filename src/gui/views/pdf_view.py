from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, 
                             QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QAbstractItemView, QMessageBox)
from PyQt6.QtCore import Qt
from functools import partial
import os

from backend.temakoroklistaja import Temakorlista

class PdfView(QWidget):
    def __init__(self, temakor_neve: str) -> None:
        super().__init__()
        
        self.temakor_neve = temakor_neve
        self.backend = Temakorlista(temakor_neve)

        self._setup_layout()
        self._setup_empty_state()
        self._setup_table()
        self._setup_buttons()
        
        self.frissit_kepernyot()

    def _setup_layout(self) -> None:
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
    def _setup_empty_state(self) -> None:
        self.ures_szoveg = QLabel("Hmm még nincs pdf feltöltve. Esetleg tölts fel egyet! ")
        self.ures_szoveg.setObjectName("EmptyText2")
        self.ures_szoveg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.ures_szoveg)

    def _setup_table(self) -> None:
        self.tablazat = QTableWidget()
        self.tablazat.setColumnCount(2)
        self.tablazat.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.tablazat.setHorizontalHeaderLabels(["A fájl neve", ""])
        self.tablazat.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.tablazat.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tablazat.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        self.tablazat.verticalHeader().setVisible(False)
        self.tablazat.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tablazat.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        
        self.layout.addWidget(self.tablazat)

    def _setup_buttons(self) -> None:
        self.hozzaad_gomb = QPushButton("Új pdf hozzá adása")
        self.hozzaad_gomb.setObjectName("ActionButton")
        self.hozzaad_gomb.clicked.connect(self._hozzaad_pdf_kattintas)
        self.layout.addWidget(self.hozzaad_gomb)

    def frissit_kepernyot(self) -> None:
        lista = self.backend.get_files()
        
        if len(lista) == 0:
            self.tablazat.hide()
            self.ures_szoveg.show()
        else:
            self.ures_szoveg.hide()
            self.tablazat.show()
            
            self.tablazat.setRowCount(len(lista))
            
            for sor_index, fajl_nev in enumerate(lista):
                item = QTableWidgetItem(fajl_nev)
                self.tablazat.setItem(sor_index, 0, item)
                
                torles_gomb = QPushButton("Törlés")
                torles_gomb.clicked.connect(partial(self._torol_pdf_kattintas, fajl_nev))
                self.tablazat.setCellWidget(sor_index, 1, torles_gomb)

    def _hozzaad_pdf_kattintas(self) -> None:
        utvonal, _ = QFileDialog.getOpenFileName(self, "PDF kiválasztása", "", "PDF fájlok (*.pdf)")
        
        if utvonal and (tiszta_utvonal := utvonal.strip()):
            self.backend.add_pdf(tiszta_utvonal)
            self.frissit_kepernyot()

    def _torol_pdf_kattintas(self, fajl_nev: str) -> None:
        valasz = QMessageBox.question(
            self, 
            'Törlés megerősítése', 
            f'Biztosan törölni szeretnéd a(z) "{fajl_nev}" fájlt és az adatait?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No 
        )
        
        if valasz == QMessageBox.StandardButton.Yes:
            self.backend.delete_pdf(fajl_nev)
            self.frissit_kepernyot()