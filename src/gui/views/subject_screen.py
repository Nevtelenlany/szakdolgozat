from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QStackedWidget
from PyQt6.QtCore import pyqtSignal
from views.pdf_view import pdf_view
from views.chatbot_view import chatbot_view
from views.quiz_generator_view import quiz_generator_view

class Subject_screen(QWidget):

    vissza_fomenube = pyqtSignal()

    def __init__(self, temakor_neve):
        super().__init__()
        
        fo_layout = QHBoxLayout()
        bal_menu = QVBoxLayout()
        cimke = QLabel(temakor_neve)

        self.kviz_gomb = QPushButton("Kvíz generálás")
        self.chat_gomb = QPushButton("Beszélgetés")
        self.pdf_gomb = QPushButton("PDF feltöltése")
        self.fomenu_gomb = QPushButton("Vissza a főmenübe")
        
        udvozlo_szoveg = QLabel("Válassz a bal oldali menüből!")

        bal_menu.addWidget(cimke)
        bal_menu.addWidget(self.pdf_gomb)
        bal_menu.addWidget(self.chat_gomb)
        bal_menu.addWidget(self.kviz_gomb)
        bal_menu.addWidget(self.fomenu_gomb)
        bal_menu.addStretch()

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
        self.fomenu_gomb.clicked.connect(self.vissza_fomenube.emit)

        fo_layout.addLayout(bal_menu)
        fo_layout.addWidget(self.tartalom_pakli)
        self.setLayout(fo_layout)
        