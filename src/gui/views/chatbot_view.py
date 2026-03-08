from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

from backend.chatbot import Chatbot
from backend.temakoroklistaja import Temakorlista

class chatbot_view(QWidget):
    def __init__(self, temakor_neve):
        super().__init__()
        self.temakor_neve = temakor_neve

        #peldanyositas
        self.backend = Temakorlista(temakor_neve=self.temakor_neve)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.hiba_cimke = QLabel("Nincs PDF feltöltve. Tölts fel egyet, mielőtt beszélgetést indítanál!")
        self.hiba_cimke.setObjectName("EmptyText2")
        self.hiba_cimke.hide()
        self.main_layout.addWidget(self.hiba_cimke)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)

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
        self.main_layout.addWidget(self.chat_container)

    def showEvent(self, event):
        #Amikor átkattintunk erre a fülre, ellenőrzi, hogy van-e már adatbázis
        super().showEvent(event)
        
        if not self.backend.has_active_db():

            self.hiba_cimke.show()
            self.chat_container.hide()
        else:

            self.hiba_cimke.hide()
            self.chat_container.show()
            
            if self.messages_layout.count() == 0:
                self.add_message(f"Szia! Miben segíthetek?", is_user=False)

    def send_message(self):
        """Az input mezőből kiolvassa a szöveget, és elindítja a futárt."""
        szoveg = self.message_input.text().strip()
        if not szoveg:
            return

        self.add_message(szoveg, is_user=True)
        self.message_input.clear()
        
        self.send_btn.setEnabled(False)
        self.message_input.setEnabled(False)
        
        self.gondolkodik_szoveg = QLabel("A Gemini keresi a választ a PDF-ben...")
        self.gondolkodik_szoveg.setObjectName("ThinkingLabel")
        self.messages_layout.addWidget(self.gondolkodik_szoveg)
        QTimer.singleShot(10, self.scroll_to_bottom)

        self.futar = FutarSzal(kerdes=szoveg, backend=self.backend)
        self.futar.valasz_megerkezett.connect(self.valasz_megjelenitese)
        self.futar.hiba_torent.connect(self.hiba_megjelenitese)
        self.futar.start()

    def valasz_megjelenitese(self, valasz_szoveg):
        """Ezt a függvényt hívja meg a futár, ha végzett."""
        self.gondolkodik_szoveg.deleteLater()
        self.add_message(valasz_szoveg, is_user=False)
        self.gomb_visszakapcsolas()

    def hiba_megjelenitese(self, hiba_szoveg):
        """Ezt a függvényt hívja meg a futár, ha baj volt a backendben."""
        self.gondolkodik_szoveg.deleteLater()
        self.add_message(f"Hiba a válaszadásnál:\n{hiba_szoveg}", is_user=False)
        self.gomb_visszakapcsolas()

    def gomb_visszakapcsolas(self):
        """Újra lehet írni az input mezőbe."""
        self.send_btn.setEnabled(True)
        self.message_input.setEnabled(True)
        self.message_input.setFocus()

    def add_message(self, text, is_user):
        """Létrehoz egy chat buborékot, és beleteszi a görgethető listába."""
        
        sor_widget = QWidget()
        sor_layout = QHBoxLayout(sor_widget)
        sor_layout.setContentsMargins(0, 0, 0, 0) 
        
        szoveg_doboz = QLabel(text)
        szoveg_doboz.setWordWrap(True) 
        szoveg_doboz.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        if is_user:
            szoveg_doboz.setObjectName("UserBubble") 
            sor_layout.addStretch()
            sor_layout.addWidget(szoveg_doboz)
            max_szelesseg = int(self.scroll_area.width() * 0.75)
            
        else:
            szoveg_doboz.setObjectName("BotBubble")
            sor_layout.addWidget(szoveg_doboz)
            sor_layout.addStretch()
            max_szelesseg = int(self.scroll_area.width() * 0.90)

        if max_szelesseg > 0:
            szoveg_doboz.setMaximumWidth(max_szelesseg)
            
        szoveg_doboz.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.messages_layout.addWidget(sor_widget)
        
        QTimer.singleShot(50, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

class FutarSzal(QThread):
    valasz_megerkezett = pyqtSignal(str)
    hiba_torent = pyqtSignal(str)

    def __init__(self, kerdes, backend):
        super().__init__()
        self.kerdes = kerdes
        self.backend = backend

    def run(self):
        try:
            db_path = self.backend.get_chroma_db_path()
            bot = Chatbot(db_path=db_path)
            valasz = bot.kerdes_feltevese(self.kerdes)
            self.valasz_megerkezett.emit(valasz)
        except Exception as e:
            self.hiba_torent.emit(str(e))