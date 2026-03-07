from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QStackedWidget, QSizePolicy, QMessageBox, QInputDialog
from PyQt6.QtCore import pyqtSignal, Qt

import os

from views.pdf_view import pdf_view
from views.chatbot_view import chatbot_view
from views.quiz_generator_view import quiz_generator_view
from backend.temakoroklistaja import Temakorlista

class Subject_screen(QWidget):

    vissza_fomenube = pyqtSignal()

    def __init__(self, temakor_neve):
        super().__init__()

        fo_layout = QHBoxLayout()
        bal_menu = QVBoxLayout()

        jelenlegi_mappa = os.path.dirname(os.path.abspath(__file__)) #ennek a file-nak a helye
        stilus_utvonal = os.path.join(jelenlegi_mappa, "..", "..", "..", "assets", "style.qss")
        stilus_utvonal = os.path.normpath(stilus_utvonal) #rendet tesz a perjelek között

        if os.path.exists(stilus_utvonal):
            with open(stilus_utvonal, "r", encoding="utf-8") as style_file:
                self.setStyleSheet(style_file.read())

        self.temakor_neve = temakor_neve
        self.backend = Temakorlista()

        self.kviz_gomb = QPushButton("Kvíz generálás")
        self.chat_gomb = QPushButton("Beszélgetés")
        self.pdf_gomb = QPushButton("PDF feltöltése")
        self.atnevezes_gomb = QPushButton("Témakör átnevezése")
        self.torles_gomb = QPushButton("Témakör törlése")
        self.fomenu_gomb = QPushButton("Vissza a főmenübe")

        bal_menu.addWidget(self.pdf_gomb)
        bal_menu.addWidget(self.chat_gomb)
        bal_menu.addWidget(self.kviz_gomb)
        bal_menu.addWidget(self.atnevezes_gomb)
        bal_menu.addWidget(self.torles_gomb)
        bal_menu.addWidget(self.fomenu_gomb)
        bal_menu.addStretch()

        self.kviz_gomb.setObjectName("MenuButton")
        self.chat_gomb.setObjectName("MenuButton")
        self.pdf_gomb.setObjectName("MenuButton")
        self.atnevezes_gomb.setObjectName("MenuButton")
        self.torles_gomb.setObjectName("MenuButton")
        self.fomenu_gomb.setObjectName("MenuButton") 

        bal_menu_doboz = QWidget()
        bal_menu_doboz.setObjectName("LeftMenuWidget")
        bal_menu_doboz.setLayout(bal_menu)

        jobb_oldal_layout = QVBoxLayout()
        self.cimke = QLabel(temakor_neve)
        self.cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cimke.setObjectName("MainTitle")
        jobb_oldal_layout.addWidget(self.cimke)

        udvozlo_szoveg = QLabel("Válassz a bal oldali menüből!")
        udvozlo_szoveg.setObjectName("EmptyText2")
        udvozlo_szoveg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        udvozlo_szoveg.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tartalom_pakli = QStackedWidget()
        self.tartalom_pakli.addWidget(udvozlo_szoveg)

        #pdf
        self.pdf_oldal = pdf_view(temakor_neve)
        self.tartalom_pakli.addWidget(self.pdf_oldal)

        #chat
        self.chat_oldal = chatbot_view(temakor_neve)
        self.tartalom_pakli.addWidget(self.chat_oldal)

        #quiz
        self.quiz_oldal = quiz_generator_view(temakor_neve)
        self.tartalom_pakli.addWidget(self.quiz_oldal)

        self.pdf_gomb.clicked.connect(lambda: self.tartalom_pakli.setCurrentWidget(self.pdf_oldal))
        self.chat_gomb.clicked.connect(lambda: self.tartalom_pakli.setCurrentWidget(self.chat_oldal))
        self.kviz_gomb.clicked.connect(lambda: self.tartalom_pakli.setCurrentWidget(self.quiz_oldal))
        self.atnevezes_gomb.clicked.connect(self.temakor_atnevezese)
        self.torles_gomb.clicked.connect(self.temakor_torlese)
        self.fomenu_gomb.clicked.connect(self.vissza_fomenube.emit)

        jobb_oldal_layout.addWidget(self.tartalom_pakli)
        fo_layout.addWidget(bal_menu_doboz)
        fo_layout.addLayout(jobb_oldal_layout)

        fo_layout.setStretch(0, 1) 
        fo_layout.setStretch(1, 4)

        fo_layout.setContentsMargins(0, 0, 0, 0)
        jobb_oldal_layout.setContentsMargins(20, 20, 20, 20)

        self.setLayout(fo_layout)

    def temakor_atnevezese(self):
        uj_nev, ok = QInputDialog.getText(self, "Témakör átnevezése", "Add meg a témakör új nevét:", text=self.temakor_neve)
        
        if ok and uj_nev.strip():
            tiszta_nev = uj_nev.strip()
            if tiszta_nev != self.temakor_neve:
                siker, uzenet = self.backend.rename_subject(self.temakor_neve, tiszta_nev)
                if siker:
                    self.temakor_neve = tiszta_nev
                    self.cimke.setText(self.temakor_neve)
                    QMessageBox.information(self, "Siker", "A témakör sikeresen átnevezve!")
                else:
                    QMessageBox.warning(self, "Hiba", uzenet)

    def temakor_torlese(self):
        valasz = QMessageBox.question(self, "Törlés megerősítése", 
                                      f"Biztosan törölni szeretnéd a(z) '{self.temakor_neve}' témakört és minden tartalmát?\nEz a folyamat nem vonható vissza!", 
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if valasz == QMessageBox.StandardButton.Yes:
            siker, uzenet = self.backend.delete_subject(self.temakor_neve)
            if siker:
                self.vissza_fomenube.emit()
            else:
                QMessageBox.warning(self, "Hiba", uzenet)