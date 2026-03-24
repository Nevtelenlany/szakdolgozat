from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QStackedWidget, QSizePolicy, QMessageBox, QInputDialog
from PyQt6.QtCore import pyqtSignal, Qt
from pathlib import Path

from views.pdf_view import PdfView
from views.chatbot_view import ChatbotView
from views.quiz_generator_view import QuizGeneratorView
from backend.temakoroklistaja import Temakorlista

class SubjectScreen(QWidget):
    vissza_fomenube = pyqtSignal()

    def __init__(self, temakor_neve: str) -> None:
        super().__init__()
        self.temakor_neve = temakor_neve
        self.backend = Temakorlista()

        self.fo_layout = QHBoxLayout()
        self.setLayout(self.fo_layout)

        self._load_stylesheet()
        self._setup_left_menu()
        self._setup_right_content()
        self._connect_signals()

        self.fo_layout.setStretch(0, 1) 
        self.fo_layout.setStretch(1, 4)
        self.fo_layout.setContentsMargins(0, 0, 0, 0)

    def _load_stylesheet(self) -> None:
        stilus_utvonal = Path(__file__).resolve().parents[3] / "assets" / "style.qss"
        if stilus_utvonal.exists():
            self.setStyleSheet(stilus_utvonal.read_text(encoding="utf-8"))
        else:
            print(f"Hiba (SubjectScreen): Nem találom a stíluslapot itt: {stilus_utvonal}")

    def _setup_left_menu(self) -> None:
        bal_menu = QVBoxLayout()

        self.pdf_gomb = QPushButton("PDF feltöltése")
        self.chat_gomb = QPushButton("Beszélgetés")
        self.kviz_gomb = QPushButton("Kvíz generálás")
        self.atnevezes_gomb = QPushButton("Témakör átnevezése")
        self.torles_gomb = QPushButton("Témakör törlése")
        self.fomenu_gomb = QPushButton("Vissza a főmenübe")

        gombok = [self.pdf_gomb, self.chat_gomb, self.kviz_gomb, 
                  self.atnevezes_gomb, self.torles_gomb, self.fomenu_gomb]
        
        for gomb in gombok:
            bal_menu.addWidget(gomb)
            gomb.setObjectName("MenuButton")

        bal_menu.addStretch()

        self.bal_menu_doboz = QWidget()
        self.bal_menu_doboz.setObjectName("LeftMenuWidget")
        self.bal_menu_doboz.setLayout(bal_menu)
        
        self.fo_layout.addWidget(self.bal_menu_doboz)

    def _setup_right_content(self) -> None:
        jobb_oldal_layout = QVBoxLayout()
        jobb_oldal_layout.setContentsMargins(20, 20, 20, 20)

        self.cimke = QLabel(self.temakor_neve)
        self.cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cimke.setObjectName("MainTitle")
        jobb_oldal_layout.addWidget(self.cimke)

        udvozlo_szoveg = QLabel("Válassz a bal oldali menüből!")
        udvozlo_szoveg.setObjectName("EmptyText2")
        udvozlo_szoveg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        udvozlo_szoveg.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tartalom_pakli = QStackedWidget()
        self.tartalom_pakli.addWidget(udvozlo_szoveg)

        self.pdf_oldal = PdfView(self.temakor_neve)
        self.chat_oldal = ChatbotView(self.temakor_neve)
        self.quiz_oldal = QuizGeneratorView(self.temakor_neve)

        self.tartalom_pakli.addWidget(self.pdf_oldal)
        self.tartalom_pakli.addWidget(self.chat_oldal)
        self.tartalom_pakli.addWidget(self.quiz_oldal)

        jobb_oldal_layout.addWidget(self.tartalom_pakli)
        self.fo_layout.addLayout(jobb_oldal_layout)

    def _connect_signals(self) -> None:
        self.pdf_gomb.clicked.connect(lambda: self.tartalom_pakli.setCurrentWidget(self.pdf_oldal))
        self.chat_gomb.clicked.connect(lambda: self.tartalom_pakli.setCurrentWidget(self.chat_oldal))
        self.kviz_gomb.clicked.connect(lambda: self.tartalom_pakli.setCurrentWidget(self.quiz_oldal))
        
        self.atnevezes_gomb.clicked.connect(self.temakor_atnevezese)
        self.torles_gomb.clicked.connect(self.temakor_torlese)
        self.fomenu_gomb.clicked.connect(self.vissza_fomenube.emit)

    def temakor_atnevezese(self) -> None:
        uj_nev, ok = QInputDialog.getText(self, "Témakör átnevezése", "Add meg a témakör új nevét:", text=self.temakor_neve)
        if ok and (tiszta_nev := uj_nev.strip()):
            if tiszta_nev != self.temakor_neve:
                siker, uzenet = self.backend.rename_subject(self.temakor_neve, tiszta_nev)
                if siker:
                    self.temakor_neve = tiszta_nev
                    self.cimke.setText(self.temakor_neve)
                    QMessageBox.information(self, "Siker", "A témakör sikeresen átnevezve!")
                else:
                    QMessageBox.warning(self, "Hiba", uzenet)

    def temakor_torlese(self) -> None:
        valasz = QMessageBox.question(self, "Törlés megerősítése", 
                                      f"Biztosan törölni szeretnéd a(z) '{self.temakor_neve}' témakört és minden tartalmát?\nEz a folyamat nem vonható vissza!", 
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if valasz == QMessageBox.StandardButton.Yes:
            siker, uzenet = self.backend.delete_subject(self.temakor_neve)
            if siker:
                self.vissza_fomenube.emit()
            else:
                QMessageBox.warning(self, "Hiba", uzenet)