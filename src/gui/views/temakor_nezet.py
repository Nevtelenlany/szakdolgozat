from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QStackedWidget, QSizePolicy, QMessageBox, QInputDialog
from PyQt6.QtCore import pyqtSignal, Qt
from pathlib import Path

from gui.views.pdf_nezet import PdfNezet
from gui.views.chatbot_nezet import ChatbotNezet
from gui.views.kviz_generator_nezet import KvizGeneratorNezet
from backend.temakor_kezelo import TemakorKezelo

class TemakorNezet(QWidget):
    # pyqtSignal: kommunikációs csatorna (jel), amelyen keresztül ez a nézet üzenni tud a főablaknak
    # hogy ha felhasználó szeretne visszalépni a főmenübe
    vissza_fomenube = pyqtSignal()
    
    # inicializálja az osztályt
    def __init__(self, temakor_neve: str) -> None:
        # super().__init__() meghívja a szülőosztály (QThread) inicializáló metódusát
        super().__init__()
        self.temakor_neve = temakor_neve
        # példányosítja a háttérlogikát a témakörök fájlszintű kezeléséhez
        self.backend = TemakorKezelo()
        # QHBoxLayout: vízszintesen egymás mellé rendezi a bal menüt és a jobb oldali tartalmat
        self.fobb_elrendezes = QHBoxLayout()
        # setLayout: beállítja ezt a vízszintes elrendezést az ablak fő elrendezéseként
        self.setLayout(self.fobb_elrendezes)

        # UI (felhasználói felület) elemeinek inicializálása
        self._stiluslap_betoltese()
        self._bal_menu_beallitasa()
        self._jobb_oldali_tartalom_beallitasa()
        self._jelek_osszekapcsolasa()

        # setStretch: beállítja a vízszintes elrendezés elemeinek méretarányát
        # 0. index (bal menü) 1 egységnyi relatív szélességet kap
        self.fobb_elrendezes.setStretch(0, 1) 
        # 1. index (jobb oldali tartalom) 4 egységnyi relatív szélességet kap (tehát 4x szélesebb lesz, mint a menü)
        self.fobb_elrendezes.setStretch(1, 4)
        # setContentsMargins: eltávolítja a külső margókat a pontos illeszkedésért
        self.fobb_elrendezes.setContentsMargins(0, 0, 0, 0)

    def _stiluslap_betoltese(self) -> None:
        stilus_utvonal = Path("./assets/style.qss")
        
        # exists(): egy Igaz (True) vagy Hamis (False) értékkel tér vissza
        # ellenőrzi, hogy a megadott qss fájl tényleg létezik-e az útvonalon
        if stilus_utvonal.exists():
            # read_text(encoding="utf-8"): beolvassa a qss fájl tartalmát
            # utf-8 kódolás a magyar karakterek miatt fontos
            # setStyleSheet: ráhúzza a beolvasott vizuális stílust a teljes ablakra és annak minden elemére
            self.setStyleSheet(stilus_utvonal.read_text(encoding="utf-8"))
        else:
            print(f"Hiba (TemakorNezet): Nem találom a stíluslapot itt: {stilus_utvonal}")

    def _bal_menu_beallitasa(self) -> None:
        # QVBoxLayout: függőlegesen egymás alá rendezi a gombokat a bal oldali menüben
        bal_menu_elrendezes = QVBoxLayout()

        # QPushButton: kattintható gombok létrehozása a különböző funkciókhoz
        self.pdf_gomb = QPushButton("PDF feltöltése")
        self.chat_gomb = QPushButton("Beszélgetés")
        self.kviz_gomb = QPushButton("Kvíz generálás")
        self.atnevezes_gomb = QPushButton("Témakör átnevezése")
        self.torles_gomb = QPushButton("Témakör törlése")
        self.torles_gomb.setToolTip("Ez a művelet véglegesen törli a témakört, az összes feltöltött PDF-et és az adatbázist!")
        self.fomenu_gomb = QPushButton("Vissza a főmenübe")

        # gombok listába rendezése, hogy egyetlen ciklussal könnyebb legyen iterálni rajtuk
        gombok = [self.pdf_gomb, self.chat_gomb, self.kviz_gomb, 
                  self.atnevezes_gomb, self.torles_gomb, self.fomenu_gomb]
        
        # végigmegyünk a listán, és minden gombot hozzáadunk a menühöz
        for gomb in gombok:
            # addWidget: hozzáadja az aktuális gombot a függőleges elrendezéshez
            bal_menu_elrendezes.addWidget(gomb)
            # setObjectName: ez alapján lehet hivatkozni a gombokra a stíluslapokban (QSS)
            gomb.setObjectName("MenuGomb")

        # addStretch(): egy rugalmas, üres teret ad az elrendezés aljához
        # ez kitölti a maradék üres helyet lefelé, így feltolja a gombokat szorosan a képernyő tetejére
        bal_menu_elrendezes.addStretch()

        # létrehoz egy üres widgetet (tárolót), ami a teljes bal menüt magába foglalja
        self.bal_menu_doboz = QWidget()
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.bal_menu_doboz.setObjectName("BalOldaliMenuPanel")
        # setLayout: beállítja a gombokat tartalmazó függőleges elrendezést a tárolóba
        self.bal_menu_doboz.setLayout(bal_menu_elrendezes)
        
        # hozzáadja a bal menü tárolót a főablak vízszintes elrendezéséhez
        self.fobb_elrendezes.addWidget(self.bal_menu_doboz)
        
    def _jobb_oldali_tartalom_beallitasa(self) -> None:
        # QVBoxLayout: függőlegesen egymás alá rendezi a jobb oldali elemeket
        jobb_oldal_elrendezes = QVBoxLayout()
        # setContentsMargins: 20 pixeles belső margót hagy a széleken (bal, felső, jobb, alsó)
        jobb_oldal_elrendezes.setContentsMargins(20, 20, 20, 20)

        # QLabel: megjeleníti a kiválasztott témakör nevét legfelül címként
        self.cimke = QLabel(self.temakor_neve)
        # setAlignment: pontosan középre zárja a szöveget a dobozán belül
        self.cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.cimke.setObjectName("FoCimsor")
        # hozzáadja a címet a jobb oldali elrendezéshez
        jobb_oldal_elrendezes.addWidget(self.cimke)

        udvozlo_szoveg = QLabel("Válassz a bal oldali menüből!")
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        udvozlo_szoveg.setObjectName("UresAllapotSzoveg")
        # setSizePolicy: dinamikusan kitölti a rendelkezésre álló üres helyet vízszintesen és függőlegesen is, hogy a szöveg középre kerüljön
        udvozlo_szoveg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # setAlignment: pontosan középre zárja a szöveget a dobozán belül
        udvozlo_szoveg.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # QStackedWidget: egy olyan tároló, amibe több widgetet (alkalmazás részt) is be lehet tenni,
        # de egyszerre mindig csak egyet mutat
        self.tartalom_pakli = QStackedWidget()
        # elsőként az üdvözlő szöveget adjuk hozzá, így ez fog alapértelmezetten megjelenni
        self.tartalom_pakli.addWidget(udvozlo_szoveg)

        # példányosíás
        self.pdf_oldal = PdfNezet(self.temakor_neve)
        self.chat_oldal = ChatbotNezet(self.temakor_neve)
        self.kviz_oldal = KvizGeneratorNezet(self.temakor_neve)

        # betesszük a felépített oldalakat a "pakliba"
        self.tartalom_pakli.addWidget(self.pdf_oldal)
        self.tartalom_pakli.addWidget(self.chat_oldal)
        self.tartalom_pakli.addWidget(self.kviz_oldal)

        # a paklit hozzáadjuk a jobb oldali elrendezéshez
        jobb_oldal_elrendezes.addWidget(self.tartalom_pakli)
        
        # addLayout: a kész jobb oldalt hozzáadjuk a főablak vízszintes elrendezéséhez
        self.fobb_elrendezes.addLayout(jobb_oldal_elrendezes)
        
    def _jelek_osszekapcsolasa(self) -> None:
        # lambda: egysoros, névtelen függvény. Itt azért van rá szükség, hogy a setCurrentWidget csak a kattintáskor fusson le, ne pedig azonnal az összekötéskor
        # setCurrentWidget: megmondja a kártyapaklinak (QStackedWidget), hogy az adott gomb megnyomására melyik oldalt hozza legfelülre
        self.pdf_gomb.clicked.connect(lambda: self.tartalom_pakli.setCurrentWidget(self.pdf_oldal))
        self.chat_gomb.clicked.connect(lambda: self.tartalom_pakli.setCurrentWidget(self.chat_oldal))
        self.kviz_gomb.clicked.connect(lambda: self.tartalom_pakli.setCurrentWidget(self.kviz_oldal))
        
        # clicked.connect: összeköti a gombkattintást a megfelelő osztályszintű metódussal
        self.atnevezes_gomb.clicked.connect(self.temakor_atnevezese)
        self.torles_gomb.clicked.connect(self.temakor_torlese)
        
        # .emit: jelet küld (pyqtSignal), amit a program főablaka figyel, innen tudja, hogy vissza kell váltania a főmenüre
        self.fomenu_gomb.clicked.connect(self.vissza_fomenube.emit)
        
    def temakor_atnevezese(self) -> None:
        # QInputDialog.getText: egy beépített felugró ablak, amiben a felhasználó szöveget tud beírni
        # visszaadja a beírt szöveget (uj_nev) és egy logikai értéket (ok), ami True, ha az OK gombra kattintott
        uj_nev, ok = QInputDialog.getText(self, "Témakör átnevezése", "Add meg a témakör új nevét:", text=self.temakor_neve)
        
        # := (walrus operátor) értékadás és vizsgálat egyben
        # strip() eltávolítja a felesleges szóközöket a beírt szöveg széleiről, eltárolja a tiszta_nev változóban
        # és egyből ellenőrzi, hogy a felhasználó rányomott-e az OK-ra ÉS nem hagyta-e teljesen üresen a mezőt
        if ok and (tiszta_nev := uj_nev.strip()):
            # ellenőrzi, hogy a beírt név ténylegesen különbözik-e a jelenlegitől (nincs értelme átnevezni önmagára)
            if tiszta_nev != self.temakor_neve:
                # meghívja a háttérlogikát, ami átnevezi a mappát, és visszaad egy sikert jelző logikai értéket, illetve egy üzenetet
                siker, uzenet = self.backend.temakor_atnevezese(self.temakor_neve, tiszta_nev)
                
                if siker:
                    # ha a backend sikeresen átnevezte, frissíti a memóriában lévő nevet és a felületen megjelenő címet is
                    self.temakor_neve = tiszta_nev
                    self.cimke.setText(self.temakor_neve)
                    # QMessageBox.information: beépített, sikeres tájékoztató felugró ablak
                    QMessageBox.information(self, "Siker", "A témakör sikeresen átnevezve!")
                else:
                    # QMessageBox.warning: beépített, figyelmeztető felugró ablak a háttérből kapott hibaüzenettel
                    QMessageBox.warning(self, "Hiba", uzenet)
                    
    def temakor_torlese(self) -> None:
        # QMessageBox.question: egy beépített felugró ablak, amely egy eldöntendő kérdést tesz fel a felhasználónak
        # QMessageBox.StandardButton paraméterekkel megadja, hogy egy "Igen" (Yes) és egy "Nem" (No) gomb jelenjen meg
        valasz = QMessageBox.question(self, "Törlés megerősítése", f"Biztosan törölni szeretnéd a(z) '{self.temakor_neve}' témakört és minden tartalmát?\nEz a folyamat nem vonható vissza!", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        # ellenőrzi, hogy a felhasználó az "Igen" gombra kattintott-e
        if valasz == QMessageBox.StandardButton.Yes:
            # meghívja a háttérlogikát, ami fizikailag törli a mappát és annak minden tartalmát
            # visszaad egy sikert jelző logikai értéket, illetve egy üzenetet
            siker, uzenet = self.backend.temakor_torlese(self.temakor_neve)
            
            if siker:
                # ha a törlés sikeres volt, küld egy jelet (emit), amit a főablak figyel
                # így a program automatikusan visszaugrik a főmenübe, hiszen a jelenlegi nézet témaköre már nem létezik
                self.vissza_fomenube.emit()
            else:
                # QMessageBox.warning: beépített, figyelmeztető felugró ablak a háttérből kapott hibaüzenettel
                QMessageBox.warning(self, "Hiba", uzenet)