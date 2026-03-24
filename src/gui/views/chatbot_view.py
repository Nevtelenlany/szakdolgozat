from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

from backend.chatbot import ChatBot
from backend.temakoroklistaja import Temakorlista

import traceback


class ChatbotView(QWidget):
    def __init__(self, temakor_neve: str) -> None:
        super().__init__()
        self.temakor_neve = temakor_neve
        self.backend = Temakorlista(temakor_neve=self.temakor_neve)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)

        self._setup_chat_area()
        self._setup_input_area()
        
        self.main_layout.addWidget(self.chat_container)

    def _setup_chat_area(self) -> None:
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.messages_widget = QWidget()
        self.messages_widget.setObjectName("MessagesWidget")
        
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop) 
        self.messages_layout.setSpacing(15) 
        self.messages_layout.setContentsMargins(10, 10, 10, 10)

        self.scroll_area.setWidget(self.messages_widget)        
        self.chat_layout.addWidget(self.scroll_area)

    def _setup_input_area(self) -> None:
        self.input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setObjectName("MessageInput")
        self.message_input.setPlaceholderText("Írd ide a kérdésed...")
        self.message_input.returnPressed.connect(self.send_message)
        
        self.send_btn = QPushButton("Küldés")
        self.send_btn.setObjectName("SendButton")
        self.send_btn.clicked.connect(self.send_message)

        self.input_layout.addWidget(self.message_input)
        self.input_layout.addWidget(self.send_btn)
        
        self.chat_layout.addLayout(self.input_layout)

    def showEvent(self, event) -> None:
        self.chat_container.show()
        if not self.messages_layout.count():
            self.add_message("Szia! Miben segíthetek?", is_user=False)

    def _set_ui_ready(self, is_ready: bool) -> None:
        self.send_btn.setEnabled(is_ready)
        self.message_input.setEnabled(is_ready)
        if is_ready:
            self.message_input.setFocus()

    def send_message(self) -> None:
        if not (szoveg := self.message_input.text().strip()):
            return

        self.add_message(szoveg, is_user=True)
        self.message_input.clear()
        
        self._set_ui_ready(is_ready=False)
        
        self.gondolkodik_szoveg = QLabel("A Gemini keresi a választ a PDF-ben...")
        self.gondolkodik_szoveg.setObjectName("ThinkingLabel")
        self.messages_layout.addWidget(self.gondolkodik_szoveg)
        QTimer.singleShot(10, self.scroll_to_bottom)

        db_utvonal = self.backend.get_chroma_db_path()

        self.futar = FutarSzal(kerdes=szoveg, adatbazis_utvonal=db_utvonal)
        self.futar.valasz_megerkezett.connect(self.valasz_megjelenitese)
        self.futar.hiba_torent.connect(self.hiba_megjelenitese)
        self.futar.start()

    def valasz_megjelenitese(self, valasz_szoveg: str) -> None:
        self.gondolkodik_szoveg.deleteLater()
        self.add_message(valasz_szoveg, is_user=False)
        self._set_ui_ready(is_ready=True)

    def hiba_megjelenitese(self, hiba_szoveg: str) -> None:
        self.gondolkodik_szoveg.deleteLater()
        self.add_message(f"Hiba a válaszadásnál:\n{hiba_szoveg}", is_user=False)
        self._set_ui_ready(is_ready=True)

    def add_message(self, text: str, is_user: bool) -> None:
        sor_widget = self._create_bubble_widget(text, is_user)
        self.messages_layout.addWidget(sor_widget)
        
        QTimer.singleShot(50, self.scroll_to_bottom)

    def _create_bubble_widget(self, text: str, is_user: bool) -> QWidget:
        sor_widget = QWidget()
        sor_layout = QHBoxLayout(sor_widget)
        sor_layout.setContentsMargins(0, 0, 0, 0) 
        
        szoveg_doboz = self._create_bubble_label(text, is_user)
        
        if is_user:
            sor_layout.addStretch()
            sor_layout.addWidget(szoveg_doboz)
        else:
            sor_layout.addWidget(szoveg_doboz)
            sor_layout.addStretch()
            
        return sor_widget

    def _create_bubble_label(self, text: str, is_user: bool) -> QLabel:
        szoveg_doboz = QLabel(text)
        szoveg_doboz.setWordWrap(True) 
        szoveg_doboz.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        szoveg_doboz.setObjectName("UserBubble" if is_user else "BotBubble")
        szorzo = 0.75 if is_user else 0.90
        
        max_szelesseg = int(self.scroll_area.width() * szorzo)
        if max_szelesseg > 0:
            szoveg_doboz.setMaximumWidth(max_szelesseg)
            
        szoveg_doboz.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        return szoveg_doboz

    def scroll_to_bottom(self) -> None:
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

class FutarSzal(QThread):
    valasz_megerkezett = pyqtSignal(str)
    hiba_torent = pyqtSignal(str)

    def __init__(self, kerdes: str, adatbazis_utvonal: str) -> None:
        super().__init__()
        self.kerdes = kerdes
        self.adatbazis_utvonal = adatbazis_utvonal

    def run(self) -> None:
        try:
            bot = ChatBot(adatbazis_utvonal=self.adatbazis_utvonal)
            valasz = bot.kerdes_feltevese(self.kerdes)
            self.valasz_megerkezett.emit(valasz)
            
        except ValueError as ve:
            self.hiba_torent.emit(f"Konfigurációs vagy adathiba: {ve}")
        except ConnectionError:
            self.hiba_torent.emit("Hálózati hiba: Nem sikerült kapcsolódni a Google Gemini szervereihez.")
        except Exception as e:
            self.hiba_torent.emit(f"Futási hiba történt a háttérfolyamatban: {e}")