from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QSizePolicy, QTableWidget, QHeaderView, QAbstractItemView, QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
import os
from functools import partial

from backend.temakoroklistaja import Temakorlista

class pdf_view(QWidget):
    def __init__(self, temakor_neve):
        super().__init__()
        
        self.temakor_neve = temakor_neve

        #peldanyositas
        self.backend = Temakorlista(temakor_neve)

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
        
        lista = self.backend.get_files()

        if len(lista) == 0:  #Nincs tantargy -> gomb rajzolasa
            szoveg = QLabel("Hmm még nincs pdf feltöltve. Esetleg tölts fel egyet! ")
            szoveg.setObjectName("EmptyText2")
            szoveg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            self.layout.addWidget(szoveg)
             
        else:
            # tablazat letrehozasa
            tablazat = QTableWidget()
            tablazat.setColumnCount(2) # oszlopok szama
            tablazat.setRowCount(len(lista)) # sorok szama
            tablazat.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            # fejlec
            tablazat.setHorizontalHeaderLabels(["A fájl neve", ""])
            tablazat.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            tablazat.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            tablazat.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

            # alapméretezetten sorszámozott eltüntetése
            tablazat.verticalHeader().setVisible(False)
            # csak olvashato
            tablazat.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            
            for sor_index, fajl_nev in enumerate(lista):
                #fajl neve cim
                item = QTableWidgetItem(fajl_nev)
                tablazat.setItem(sor_index, 0, item)
                
                #torles gomb
                torles_gomb = QPushButton("Törlés")
                torles_gomb.clicked.connect(partial(self.torol_pdf, fajl_nev))
                tablazat.setCellWidget(sor_index, 1, torles_gomb)
                
            self.layout.addWidget(tablazat)

        #self.layout.addStretch()
        gomb = QPushButton("Új pdf hozzá adása")
        gomb.setObjectName("ActionButton")
        gomb.clicked.connect(self.button_push)
        
        self.layout.addWidget(gomb)

    def button_push(self):
        #fajl utvonala
        utvonal, _ = QFileDialog.getOpenFileName(self,"PDF kiválasztása", "","PDF fájlok (*.pdf)")
        if utvonal:
            tiszta_utvonal = utvonal.strip()
            self.backend.add_pdf(tiszta_utvonal)
            self.frissit_kepernyot()

    def torol_pdf(self, fajl_nev):
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