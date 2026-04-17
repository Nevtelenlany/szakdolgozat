from pathlib import Path
from PyQt6.QtWidgets import (QPushButton, QVBoxLayout, QWidget, QLabel, QInputDialog, QApplication, QHBoxLayout, QSizePolicy, QScrollArea, QGridLayout, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt, QSize


from backend.temakor_kezelo import TemakorKezelo

class FomenuNezet(QWidget):
    # pyqtSignal: kommunikációs csatorna (jel), amelyen keresztül ez a nézet üzenni tud a főablaknak,
    # átadva a kiválasztott témakör nevét (szövegként), hogy az betöltse a hozzá tartozó felületet
    valasztott_temakor = pyqtSignal(str)
    
    def __init__(self) -> None:
        # super().__init__() meghívja a szülőosztály (QWidget) inicializáló metódusát
        super().__init__()
        # példányosítja a háttérlogikát a témakörök kezeléséhez
        self.backend = TemakorKezelo()
        
        # UI (felhasználói felület) elemeinek inicializálása
        self._elrendezes_beallitasa()
        self._stiluslap_betoltese()
        self._fejlec_es_ures_allapot_beallitasa()
        self._racsos_nezet_beallitasa()
        self._also_gombok_beallitasa()
        
        # miután minden felületi elem felépült, betölti és megjeleníti a már meglévő témaköröket
        self.kepernyo_frissitese()

    def _elrendezes_beallitasa(self) -> None:
        # QVBoxLayout: függőlegesen egymás alá rendezi a benne elhelyezett elemeket
        self.fobb_elrendezes = QVBoxLayout()
        # setLayout: beállítja ezt a függőleges elrendezést az ablak fő elrendezéseként
        self.setLayout(self.fobb_elrendezes)

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
            print(f"Hiba (FomenuNezet): Nem találom a stíluslapot itt: {stilus_utvonal}")
            
    def _fejlec_es_ures_allapot_beallitasa(self) -> None:
        # QLabel: megjeleníti a főcímet legfelül
        self.cim_szoveg = QLabel("Témakörök listája")
        # setAlignment: pontosan középre zárja a szöveget a dobozán belül
        self.cim_szoveg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.cim_szoveg.setObjectName("FoCimsor")
        # hozzáadja a címet a fő elrendezéshez
        self.fobb_elrendezes.addWidget(self.cim_szoveg)

        # QLabel: megjeleníti ezt a figyelmeztető szöveget, ha még nincsenek létrehozva témakörök
        self.ures_szoveg = QLabel("Hmm, még nincs létrehozva témakör. Esetleg hozz létre egy újat!")
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.ures_szoveg.setObjectName("UresAllapotSzoveg")
        # setSizePolicy: dinamikusan kitölti a rendelkezésre álló üres helyet vízszintesen és függőlegesen is, hogy a szöveg középre kerüljön
        self.ures_szoveg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # setAlignment: pontosan középre zárja a szöveget a dobozán belül
        self.ures_szoveg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # hozzáadja az üres állapot szövegét a fő elrendezéshez
        self.fobb_elrendezes.addWidget(self.ures_szoveg)
        # hide(): alapértelmezetten elrejti ezt a felületet
        self.ures_szoveg.hide()

    def _racsos_nezet_beallitasa(self) -> None:
        # QScrollArea: létrehoz egy görgethető területet a témakörök gombjainak
        self.gorgetheto_terulet = QScrollArea()
        # setWidgetResizable: engedélyezi, hogy a belső tartalom dinamikusan alkalmazkodjon a külső ablak méretéhez
        self.gorgetheto_terulet.setWidgetResizable(True)

        # létrehoz egy üres tárolót (widgetet), ami magát a rácsot fogja tartalmazni
        self.racs_tarolo = QWidget()
        # QGridLayout: rácsos (sorok és oszlopok) elrendezést hoz létre a tárolóban
        self.racs_elrendezes = QGridLayout(self.racs_tarolo)
        
        # setWidget: a görgethető területbe beleteszi az imént létrehozott rácsos tárolót
        self.gorgetheto_terulet.setWidget(self.racs_tarolo)
        # hozzáadja a görgethető területet a fő elrendezéshez
        self.fobb_elrendezes.addWidget(self.gorgetheto_terulet)

    def _also_gombok_beallitasa(self) -> None:
        # QHBoxLayout: vízszintesen (egymás mellé) rendezi az alsó gombokat
        also_gombok_elrendezes = QHBoxLayout()

        # QPushButton: kattintható gomb az új témakör létrehozásához
        self.uj_gomb = QPushButton("Új témakör létrehozása")
        self.uj_gomb.setIconSize(QSize(24, 24))
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.uj_gomb.setObjectName("HozzadasGomb")
        # clicked.connect: ha rákattintanak, lefuttatja az uj_temakor_hozzadasa metódust
        self.uj_gomb.clicked.connect(self.uj_temakor_hozzadasa)
        
        # hozzáadja a gombot a vízszintes elrendezéshez
        also_gombok_elrendezes.addWidget(self.uj_gomb)
        
        # QPushButton: gomb az alkalmazásból való kilépéshez
        self.kilepes_gomb = QPushButton("Kilépés")
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.kilepes_gomb.setObjectName("MuveletiGomb")
        # clicked.connect: közvetlenül összeköti a gombot a teljes PyQt6 alkalmazás bezárásával
        self.kilepes_gomb.clicked.connect(QApplication.instance().quit)
        
        # hozzáadja a gombot a vízszintes elrendezéshez
        also_gombok_elrendezes.addWidget(self.kilepes_gomb)
        # addLayout: a kész vízszintes gombsort hozzáadja az ablak fő, függőleges elrendezéséhez alulra
        self.fobb_elrendezes.addLayout(also_gombok_elrendezes)

    def uj_temakor_hozzadasa(self) -> None:  
        # QInputDialog.getText: egy beépített felugró ablak, amiben a felhasználó szöveget tud beírni
        # visszaadja a beírt szöveget (szoveg) és egy logikai értéket (ok), ami True, ha az OK gombra kattintott a felhasználó
        szoveg, ok = QInputDialog.getText(self, "Új témakör", "Mi legyen az új témakör neve?")
        
        # := (walrus operátor) értékadás és vizsgálat egyben
        # strip() eltávolítja a felesleges szóközöket a beírt szöveg széleiről, eltárolja a tiszta_szoveg változóban
        # és egyből ellenőrzi, hogy a felhasználó rányomott-e az OK-ra és nem hagyta-e teljesen üresen a mezőt
        if ok and (tiszta_szoveg := szoveg.strip()):
            # meghívja a háttérlogikát, ami létrehozza a mappát az új témakörnek
            siker, uzenet =self.backend.temakor_letrehozasa(tiszta_szoveg)

            if siker:
                # frissíti a képernyőt, hogy az új gomb azonnal megjelenjen (a rács újraépítésével)
                self.kepernyo_frissitese()
            else:
                # ha hiba volt egy ablakban kiírja a backendtől kapott hibaüzenetet
                QMessageBox.warning(self, "Hiba a létrehozás során", uzenet)
            
    def kepernyo_frissitese(self) -> None:
        # lekéri a létező témakörök (mappák) nevét egy listában a háttérlogikából
        lista = self.backend.temakorok_lekerese()

        # ha a lista üres (nincs még témakör)
        if not lista:
            self.gorgetheto_terulet.hide()
            self.ures_szoveg.show()
        else:
            # ha van legalább egy témakör
            self.ures_szoveg.hide()
            self.gorgetheto_terulet.show()
            
            # törli az összes eddigi gombot a rácsból, hogy ne duplikálódjanak a frissítésnél
            # count() megadja a rácsban lévő elemek számát, amíg ez nem nulla (vagyis van még benne elem), fut a ciklus
            while self.racs_elrendezes.count():
                # takeAt(0): kiveszi a legelső (0. indexű) elemet az elrendezésből
                elem = self.racs_elrendezes.takeAt(0)
                # := (walrus operátor) lekéri a widgetet az elemből. Ha sikeres, törli a memóriából (deleteLater)
                if widget := elem.widget():
                    widget.deleteLater()

            # újraépíti a rácsot a friss lista alapján
            oszlopok_szama = 4
            # enumerate: egyszerre adja vissza az indexet (0, 1, 2...) és a mappa nevét (témakör nevét)
            for index, mappa_nev in enumerate(lista):
                # kiszámolja, hogy az adott indexű gomb melyik sorba és oszlopba kerüljön a rácsban
                # // (egész osztás): megadja a sort (pl. 5 // 4 = 1. sor)
                sor = index // oszlopok_szama
                # % (maradékos osztás): megadja az oszlopot (pl. 5 % 4 = 1. oszlop)
                oszlop = index % oszlopok_szama
                
                # létrehoz egy nagy, négyzet alakú gombot a témakör nevével
                temakor_gomb = QPushButton(mappa_nev)
                # setMinimumSize/setMaximumSize: beállítja a gomb méretkorlátait, hogy szép négyzet maradjon
                temakor_gomb.setMinimumSize(140, 140)
                temakor_gomb.setMaximumSize(300, 300)
                # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
                temakor_gomb.setObjectName("TemakorGomb")
                # setSizePolicy: engedi, hogy a gomb rugalmasan kitöltse a rácsban lévő celláját
                temakor_gomb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                
                # clicked.connect: ha a gombra kattintanak, meghívja a temakor_megnyitasa metódust a mappa nevével
                # lambda: névtelen függvény, ami becsomagolja a paraméterátadást 
                # checked=False a kattintás alapértelmezett állapota miatt kell
                temakor_gomb.clicked.connect(lambda checked=False, nev=mappa_nev: self.temakor_megnyitasa(nev))
                
                # addWidget: elhelyezi a gombot a rács kiszámolt sorába és oszlopába
                self.racs_elrendezes.addWidget(temakor_gomb, sor, oszlop)

    def temakor_megnyitasa(self, kivalasztott_temakor: str) -> None:
        # .emit(): jelet küld a 'valasztott_temakor' nevű pyqtSignal-nak
        # és átadja a gombnyomáskor kapott témakör nevét
        # ezt a jelet a program főablaka (main) figyeli, és ez alapján fogja tudni, hogy melyik témakör részletes nézetét kell megnyitnia
        self.valasztott_temakor.emit(kivalasztott_temakor)