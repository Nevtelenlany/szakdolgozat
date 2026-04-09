from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

from backend.temakor_kezelo import TemakorKezelo
from gui.views.hatterszal import ChatbotHatterszal

class ChatbotNezet(QWidget):
    # inicializálja az osztályt
    def __init__(self, temakor_neve: str) -> None:
        # super().__init__() meghívja a szülőosztály (QWidget) inicializáló metódusát
        super().__init__()
        self.temakor_neve = temakor_neve
        # példányosítja a háttérlogikát a megadott témakörhöz
        self.backend = TemakorKezelo(temakor_neve=self.temakor_neve)
        # inicializálja a felhasználói felület (UI) elemeit
        self._felulet_beallitasa()
        
    def _felulet_beallitasa(self) -> None:
        # QVBoxLayout: függőlegesen egymás alá rendezi a benne elhelyezett elemeket (widgeteket)
        self.fobb_elrendezes = QVBoxLayout(self)
        # létrehoz egy üres widgetet, ami a teljes chat felületet magába foglalja (tárolja)
        self.chat_tarolo = QWidget()
        # létrehoz egy függőleges elrendezést a chat tárolón belül
        self.chat_elrendezes = QVBoxLayout(self.chat_tarolo)
        # setContentsMargins: eltávolítja a belső margókat (bal, felső, jobb, alsó) a pontos illeszkedésért
        self.chat_elrendezes.setContentsMargins(0, 0, 0, 0)
        # a felület két fő részének összeállítása
        self._chat_terulet_beallitasa()
        self._beviteli_terulet_beallitasa()
        # hozzáadja a az ablak fő elrendezéséhez
        self.fobb_elrendezes.addWidget(self.chat_tarolo)

    def _chat_terulet_beallitasa(self) -> None:
        # QScrollArea: létrehoz egy görgethető területet az üzenetek számára
        self.gorgetheto_terulet = QScrollArea()
        # setWidgetResizable: engedélyezi, hogy a belső tartalom dinamikusan alkalmazkodjon a külső ablak méretéhez
        self.gorgetheto_terulet.setWidgetResizable(True)

        # létrehoz egy üres widgetet, ezen fognak egymás alá kerülni a szövegbuborékok
        self.uzenetek_widget = QWidget()
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.uzenetek_widget.setObjectName("MessagesWidget")
        # QVBoxLayout: létrehoz egy függőleges elrendezést az üzenetek tárolójának
        self.uzenetek_elrendezes = QVBoxLayout(self.uzenetek_widget)
        # setAlignment: az üzeneteket fentről lefelé rendezi, az ablak tetejéhez igazítva
        self.uzenetek_elrendezes.setAlignment(Qt.AlignmentFlag.AlignTop) 
        # setSpacing: 15 pixel távolságot hagy az egyes üzenetbuborékok között
        self.uzenetek_elrendezes.setSpacing(15) 
        # setContentsMargins: 10 pixeles belső margót állít be minden oldalon (bal, felső, jobb, alsó)
        self.uzenetek_elrendezes.setContentsMargins(10, 10, 10, 10)

        # setWidget: a görgethető területbe beleteszi a most összeállított üzenet-tárolót
        self.gorgetheto_terulet.setWidget(self.uzenetek_widget)        
        # addWidget: hozzáadja a görgethető területet a fő chat elrendezéshez
        self.chat_elrendezes.addWidget(self.gorgetheto_terulet)
        
    def _beviteli_terulet_beallitasa(self) -> None:
        # QHBoxLayout: létrehoz egy vízszintes elrendezést a beviteli mezőnek és a küldés gombnak
        self.bevitel_elrendezes = QHBoxLayout()
        
        # QLineEdit: létrehoz egy egysoros szövegbeviteli mezőt
        self.uzenet_beviteli_mezo = QLineEdit()
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.uzenet_beviteli_mezo.setObjectName("MessageInput")
        # setPlaceholderText: halványszürke szöveget jelenít meg, ami eltűnik, amint a felhasználó gépelni kezd
        self.uzenet_beviteli_mezo.setPlaceholderText("Írd ide a kérdésed...")
        # returnPressed.connect: összeköti az Enter billentyű lenyomását a self.uzenet_kuldese metódussal
        self.uzenet_beviteli_mezo.returnPressed.connect(self.uzenet_kuldese)
        
        # QPushButton: létrehoz egy kattintható gombot a küldéshez
        self.kuldes_gomb = QPushButton("Küldés")
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.kuldes_gomb.setObjectName("SendButton")
        # clicked.connect: összeköti a gombkattintást a self.uzenet_kuldese metódussal
        self.kuldes_gomb.clicked.connect(self.uzenet_kuldese)

        # addWidget: hozzáadja a beviteli mezőt és a gombot a vízszintes elrendezéshez
        self.bevitel_elrendezes.addWidget(self.uzenet_beviteli_mezo)
        self.bevitel_elrendezes.addWidget(self.kuldes_gomb)
        
        # addLayout: a vízszintes beviteli sort hozzáadja a fő chat elrendezéshez
        self.chat_elrendezes.addLayout(self.bevitel_elrendezes)
        
    # a showEvent a PyQt6 beépített metódusa, automatikusan lefut, amikor a widget megjelenik a képernyőn
    def showEvent(self, event) -> None:
        # super(): meghívja a szülőosztály (QWidget) eredeti showEvent metódusát a biztonságos kirajzolásért
        super().showEvent(event)
        # megjeleníti a teljes chat tárolót
        self.chat_tarolo.show()
        
        # count(): megnézi, hány elem (üzenetbuborék) van jelenleg az elrendezésben
        # ha a szám 0 (azaz nincs még egyetlen üzenet sem), egy automatikus üzenet fogadja a felhasználót
        if not self.uzenetek_elrendezes.count():
            self.uzenet_hozzadasa("Szia! Miben segíthetek?", felhasznalo_e=False)
            
    # segédmetódus
    def _ui_visszakapcsolasa(self, engedelyezve: bool) -> None:
        # beállítja, hogy a gomb és a beviteli mező kattintható-e a kapott logikai érték alapján
        self.kuldes_gomb.setEnabled(engedelyezve)
        self.uzenet_beviteli_mezo.setEnabled(engedelyezve)

        # ha újra engedélyezve van a felület, a kurzor automatikusan visszaugrik a beviteli mezőbe
        if engedelyezve:
            self.uzenet_beviteli_mezo.setFocus()
            
    def uzenet_kuldese(self) -> None:
        # := (walrus operátor) lekéri a szöveget, eltávolítja a felesleges szóközöket a szélekről (strip)
        # ha a szöveg teljesen üres (pl. csak szóközöket küldtek), azonnal kilép a függvényből (return)
        if not (szoveg := self.uzenet_beviteli_mezo.text().strip()):
            return

        # megjeleníti a felhasználó kérdését a felületen a megfelelő (jobb) oldalon
        self.uzenet_hozzadasa(szoveg, felhasznalo_e=True)
        # kiüríti a beviteli mezőt a következő kérdésnek
        self.uzenet_beviteli_mezo.clear()
        # letiltja a szövegbevitelt, amíg nem érkezik meg a válasz
        self._ui_visszakapcsolasa(engedelyezve=False)
        
        # létrehoz egy ideiglenes címkét, ami jelzi a felhasználónak, hogy a bot dolgozik a háttérben
        self.gondolkodik_szoveg = QLabel("A Gemini keresi a választ a PDF-ben...")
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.gondolkodik_szoveg.setObjectName("ThinkingLabel")
        # beteszi az ideiglenes üzenetet az üzenetek függőleges elrendezésébe
        self.uzenetek_elrendezes.addWidget(self.gondolkodik_szoveg)
        
        # QTimer: 10 milliszekundum késleltetéssel legörget az ablak aljára, hogy biztosan látszódjon a "gondolkodik" szöveg
        QTimer.singleShot(10, self.gorgetes_legalulra)

        # adatbázis útvonal lekérése a háttérlogikától a megadott témakörhöz
        db_utvonal = self.backend.adatbazis_utvonal_lekerese()

        # QThread: elindítja a keresést és a generálást egy külön háttérszálon
        # ezzel biztosítja, hogy a grafikus felület (GUI) ne fagyjon le a hálózati kommunikáció alatt
        self.futar = ChatbotHatterszal(kerdes=szoveg, adatbazis_utvonal=db_utvonal)  
        # összeköti a háttérszál jeleit (signals) a megfelelő UI-frissítő metódusokkal
        self.futar.valasz_megerkezett.connect(self.valasz_megjelenitese)
        self.futar.hiba_tortent.connect(self.hiba_megjelenitese)
        # elindítja a háttérszál futását
        self.futar.start()
        
    def valasz_megjelenitese(self, valasz_szoveg: str) -> None:
        # deleteLater: törli a "gondolkodik..." feliratot a felületről és felszabadítja a memóriát
        self.gondolkodik_szoveg.deleteLater()
        # megjeleníti a bot által generált választ a chat felületen
        self.uzenet_hozzadasa(valasz_szoveg, felhasznalo_e=False)
        # újra engedélyezi a szövegbevitelt és a küldés gombot a felhasználónak
        self._ui_visszakapcsolasa(engedelyezve=True)
        
    def hiba_megjelenitese(self, hiba_szoveg: str) -> None:
        # deleteLater: törli a "gondolkodik..." feliratot a felületről és felszabadítja a memóriát
        self.gondolkodik_szoveg.deleteLater()
        # hiba esetén egy bot üzenet formájában írja ki a problémát a chat felületen (bal oldalon)
        self.uzenet_hozzadasa(f"Hiba a válaszadásnál:\n{hiba_szoveg}", felhasznalo_e=False)
        # újra engedélyezi a szövegbevitelt és a küldés gombot a felhasználónak
        self._ui_visszakapcsolasa(engedelyezve=True)
        
    def uzenet_hozzadasa(self, szoveg: str, felhasznalo_e: bool) -> None:
        # létrehozza a buborékot tartalmazó widgetet a kapott szöveg alapján
        sor_widget = self._szovegbuborek_letrehozasa(szoveg, felhasznalo_e)
        # beteszi a widgetet az üzenetek függőleges elrendezésébe
        self.uzenetek_elrendezes.addWidget(sor_widget)
        # QTimer: 50 milliszekundum késleltetéssel legörget az ablak aljára
        # a késleltetésre azért van szükség, mert a grafikus motornak (GUI) idő kell, amíg kiszámolja az új elem magasságát a görgetés előtt
        QTimer.singleShot(50, self.gorgetes_legalulra)
        
    def _szovegbuborek_letrehozasa(self, szoveg: str, felhasznalo_e: bool) -> QWidget:
        # létrehoz egy üres widgetet
        sor_widget = QWidget()
        # QHBoxLayout: vízszintesen rendezi el a sornak a tartalmát
        sor_elrendezes = QHBoxLayout(sor_widget)
        # setContentsMargins: eltávolítja a belső margókat a pontos illeszkedésért
        sor_elrendezes.setContentsMargins(0, 0, 0, 0) 
        # meghívja a segédmetódust, ami legenerálja magát a formázott szöveges címkét (a tényleges buborékot)
        szoveg_doboz = self._buborek_cimke_letrehozasa(szoveg, felhasznalo_e)
        
        if felhasznalo_e:
            # ha a felhasználó írta, először egy rugalmas üres teret (Stretch) tesz be a bal oldalra
            sor_elrendezes.addStretch()
            # majd utána adja hozzá a buborékot, így az teljesen a jobb oldalra tolódik
            sor_elrendezes.addWidget(szoveg_doboz)
        else:
            # ha a bot írta, először a buborékot teszi be a bal oldalra
            sor_elrendezes.addWidget(szoveg_doboz)
            # majd utána az üres teret, ami kitölti a maradék helyet jobbra
            sor_elrendezes.addStretch()
            
        # visszaadja a kész sort a buborékkal és a megfelelő (jobbos vagy balos) igazítással
        return sor_widget
    
    def _buborek_cimke_letrehozasa(self, szoveg: str, felhasznalo_e: bool) -> QLabel:
        # QLabel: létrehozza a szöveges címkét a kapott tartalommal
        szoveg_doboz = QLabel(szoveg)
        
        # setWordWrap(True): engedélyezi a sortörést a hosszú szövegeknél, hogy ne lógjanak ki az ablakból
        szoveg_doboz.setWordWrap(True) 
        
        # setTextInteractionFlags: felülírja az alapértelmezett, statikus címke-viselkedést
        # a TextSelectableByMouse paraméter engedélyezi, hogy a felhasználó az egerével kijelölhesse és kimásolhassa a szöveget
        szoveg_doboz.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # setObjectName: stíluslap (QSS) hivatkozás beállítása (más háttere/színe lesz a felhasználó és a bot buborékjának)
        szoveg_doboz.setObjectName("UserBubble" if felhasznalo_e else "BotBubble")
        
        # a felhasználó üzenete picit keskenyebb lehet (a képernyő 75%-a), a boté szélesebb (90%)
        szorzo = 0.75 if felhasznalo_e else 0.90
        
        # kiszámolja a görgethető terület aktuális szélességét a fenti szorzó alapján
        max_szelesseg = int(self.gorgetheto_terulet.width() * szorzo)
        
        # ha sikeresen kiszámolta a szélességet (nagyobb, mint 0)
        if max_szelesseg > 0:
            # setMaximumWidth: beállít egy abszolút felső korlátot a buborék szélességének (pixelekben)
            # ez kényszeríti a hosszú szövegeket arra, hogy a képernyő szélének elérésekor új sorba törjenek
            szoveg_doboz.setMaximumWidth(max_szelesseg)
            
        # setSizePolicy: meghatározza a widget átméretezési viselkedését vízszintesen és függőlegesen
        # a MinimumExpanding biztosítja, hogy a doboz legalább akkora legyen, mint a benne lévő szöveg, de 
        # ha kell, rugalmasan kitöltse a rendelkezésre álló helyet (a beállított maximumig)
        szoveg_doboz.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        
        return szoveg_doboz

    def gorgetes_legalulra(self) -> None:
        # verticalScrollBar: lekéri a görgethető terület függőleges görgetősávját
        gorgetosav = self.gorgetheto_terulet.verticalScrollBar()
        
        # setValue: beállítja a csúszkát a lehetséges maximális értékre, 
        # így a nézet automatikusan a legutolsó üzenethez (az ablak aljára) ugrik
        gorgetosav.setValue(gorgetosav.maximum())
