from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, 
                             QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QAbstractItemView, QMessageBox)
from PyQt6.QtCore import Qt
from functools import partial

from backend.temakor_kezelo import TemakorKezelo

class PdfNezet(QWidget):
    # inicializálja az osztályt
    def __init__(self, temakor_neve: str) -> None:
        # super().__init__() meghívja a szülőosztály (QWidget) inicializáló metódusát
        super().__init__()
        
        self.temakor_neve = temakor_neve

        # példányosítja a háttérlogikát a megadott témakörhöz
        self.backend = TemakorKezelo(temakor_neve)

        # UI (felhasználói felület) elemeinek inicializálása
        self._elrendezes_beallitasa()
        self._ures_allapot_beallitasa()
        self._tablazat_beallitasa()
        self._gombok_beallitasa()
        
        # miután minden felületi elem felépült, frissíti a képernyőt a mappában meglévő fájlokkal
        self.kepernyo_frissitese()

    def _elrendezes_beallitasa(self) -> None:
        # QVBoxLayout: függőlegesen egymás alá rendezi a benne elhelyezett elemeket (widgeteket)
        self.fobb_elrendezes = QVBoxLayout()
        # setLayout: beállítja a fenti függőleges elrendezést az ablak fő elrendezéseként
        self.setLayout(self.fobb_elrendezes)
        
    def _ures_allapot_beallitasa(self) -> None:
        # QLabel: megjeleníti ezt a figyelmeztető szöveget, ha még nincs PDF feltöltve
        self.ures_szoveg = QLabel("Hmm, még nincs PDF feltöltve. Esetleg tölts fel egyet!")
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.ures_szoveg.setObjectName("EmptyText2")
        
        # setSizePolicy: beállítja, hogyan reagáljon az elem az ablak átméretezésére
        # a QSizePolicy.Policy.Expanding paraméterekkel dinamikusan kitölti a rendelkezésre álló üres helyet vízszintesen és függőlegesen is
        # ez garantálja, hogy a címke (láthatatlan doboza) felvegye a teljes rendelkezésre álló képernyőméretet
        self.ures_szoveg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # setAlignment: beállítja a szöveg igazítását
        # az AlignmentFlag.AlignCenter a korábban kinyújtott dobozon belül vízszintesen és függőlegesen is pontosan középre zárja a szöveget
        self.ures_szoveg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # hozzáadja az üres állapot szövegét a fő elrendezéshez
        self.fobb_elrendezes.addWidget(self.ures_szoveg)
        
    def _tablazat_beallitasa(self) -> None:
        # QTableWidget: egy táblázatot hoz létre az adatok (fájlok) megjelenítésére
        self.tablazat = QTableWidget()
        # setColumnCount: beállítja az oszlopok számát 2-re (1. oszlop: név, 2. oszlop: művelet)
        self.tablazat.setColumnCount(2)
        
        # setSizePolicy: beállítja, hogyan reagáljon a táblázat az ablak átméretezésére
        # a QSizePolicy.Policy.Expanding paraméterekkel dinamikusan kitölti a rendelkezésre álló üres helyet vízszintesen és függőlegesen is
        # ez garantálja, hogy a táblázat felvegye a képernyőn elérhető teljes méretet
        self.tablazat.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # setHorizontalHeaderLabels: beállítja a vízszintes fejléc (az oszlopok) feliratait
        self.tablazat.setHorizontalHeaderLabels(["A fájl neve", "Művelet"])
        
        # horizontalHeader(): lekéri a táblázat felső (vízszintes) fejlécét, hogy módosítani lehessen a beállításait
        # | (VAGY) operátor bit-szinten "összeadja" a két kapcsolót, így mindkettő érvényesül (az ÉS operátor itt mindent kinullázna)
        # setDefaultAlignment: a fejléc összes feliratát balra (AlignLeft) és függőlegesen középre (AlignVCenter) igazítja.
        self.tablazat.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # horizontalHeader(): lekéri a táblázat vízszintes fejlécét
        # ResizeMode.Stretch: a megadott oszlopot úgy nyújtja meg, hogy kitöltse a táblázatban maradt összes üres helyet
        # setSectionResizeMode: a 0. indexű (első, "A fájl neve") oszlopot rugalmasra állítja, hogy felvegye a szabad helyet
        self.tablazat.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        # horizontalHeader(): lekéri a táblázat vízszintes fejlécét
        # ResizeMode.ResizeToContents: az oszlop szélességét pontosan akkorára állítja be, amekkora a benne lévő legszélesebb tartalom
        # setSectionResizeMode: az 1. indexű (második, "Művelet") oszlopot csak akkorára nyitja, hogy a "Törlés" gombok pont elférjenek benne
        self.tablazat.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        # verticalHeader().setVisible(False): elrejti a sorok automatikus számozását jelző függőleges fejlécet a bal oldalon
        self.tablazat.verticalHeader().setVisible(False)
        # setEditTriggers: letiltja a cellák szerkesztését (NoEditTriggers), így pl. dupla kattintással nem lehet átírni a fájl nevét a felületen
        self.tablazat.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # setSelectionMode: letiltja a cellák kék színű kijelölését kattintáskor (NoSelection), hogy letisztultabb maradjon a táblázat
        self.tablazat.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        
        # hozzáadja a felépített táblázatot a fő elrendezéshez
        self.fobb_elrendezes.addWidget(self.tablazat)

    def _gombok_beallitasa(self) -> None:
        # QPushButton: kattintható gomb a fájl feltöltéséhez
        self.hozzadas_gomb = QPushButton("Új PDF hozzáadása")
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.hozzadas_gomb.setObjectName("ActionButton")
        # clicked.connect: ha rákattintanak a gombra, lefuttatja a PDF hozzáadását végző metódust
        self.hozzadas_gomb.clicked.connect(self._pdf_hozzadasa)
        
        # hozzáadja a gombot a fő elrendezéshez
        self.fobb_elrendezes.addWidget(self.hozzadas_gomb)
        
        
    def kepernyo_frissitese(self) -> None:
        # lekéri a témakörhöz tartozó PDF fájlok listáját a háttérlogikából
        lista = self.backend.fajlok_lekerese()
        
        # ha a lista üres (nincs még egyetlen PDF sem feltöltve)
        if not lista:
            # hide(): elrejti a táblázatot
            self.tablazat.hide()
            # show(): megjeleníti az üres állapotot jelző szöveget
            self.ures_szoveg.show()
        else:
            # ha van legalább egy fájl a listában
            # hide(): elrejti a figyelmeztető szöveget
            self.ures_szoveg.hide()
            # show(): megjeleníti a táblázatot
            self.tablazat.show()
            # setRowCount: beállítja a táblázat sorainak számát pontosan a lista hosszára
            self.tablazat.setRowCount(len(lista))
            
            # enumerate: végigmegy a listán, és minden lépésben egyszerre adja vissza a sor indexét és magát a fájl nevét
            for sor_index, fajl_nev in enumerate(lista):
                # QTableWidgetItem: létrehoz egy egyszerű táblázatcellát a fájl nevével
                elem = QTableWidgetItem(fajl_nev)
                # setItem: beteszi a létrehozott cellát az aktuális sorba, az 1. oszlopba (0-s index)
                self.tablazat.setItem(sor_index, 0, elem)
                # létrehoz egy egyedi "Törlés" gombot az adott sorhoz
                torles_gomb = QPushButton("Törlés")
                
                # clicked.connect: összeköti a gombkattintás eseményét a fájltörlő metódussal
                # partial: paraméterként "belefagyasztja" a fájl nevét ebbe a kattintás eseménybe
                # erre azért van szükség, hogy a függvény meghívásakor a gomb tudja, pontosan melyik sor fájlját kell törölnie
                torles_gomb.clicked.connect(partial(self._pdf_torlese, fajl_nev))
                
                # setCellWidget: a törlés gombot (widgetet) beleteszi a táblázat aktuális sorának 2. oszlopába (1-es index)
                self.tablazat.setCellWidget(sor_index, 1, torles_gomb)
                
    def _pdf_hozzadasa(self) -> None:
        # QFileDialog.getOpenFileName: megnyit egy beépített, operációs rendszer szintű fájlválasztó ablakot
        # paraméterek: szülő widget (self), ablak címe, kezdő mappa (üres = alapértelmezett), választható fájltípusok (csak .pdf)
        # függvény két értéket ad vissza: a fájl teljes elérési útját, használt fájltípus-szűrő nevét
        # az _ (alsóvonal) jelzi a Pythonnak, hogy a második visszatérési értéket (a szűrő nevét) eldobjuk, mert nincs rá szükségünk
        utvonal, _ = QFileDialog.getOpenFileName(self, "PDF kiválasztása", "", "PDF fájlok (*.pdf)")
        
        # := (walrus operátor) értékadás és vizsgálat egyben
        # strip() eltávolítja a felesleges szóközöket az útvonal széléről
        # ellenőrzi, hogy a felhasználó tényleg választott-e fájlt, és nem zárta-e be véletlenül az ablakot (vagyis nem üres-e az útvonal)
        if utvonal and (tiszta_utvonal := utvonal.strip()):
            # meghívja a háttérlogikát, ami átmásolja, darabolja, vektorizálja és elmenti a PDF-et a ChromaDB-be
            self.backend.pdf_hozzadasa(tiszta_utvonal)
            # frissíti a táblázatot, hogy az új fájl azonnal megjelenjen a felületen
            self.kepernyo_frissitese()
            
    def _pdf_torlese(self, fajl_nev: str) -> None:
        # QMessageBox.question: megjelenít egy beépített felugró ablakot a törlés megerősítéséhez
        # paraméterek: szülő widget (self), ablak címe, a kérdés szövege, a megjelenő gombok, az alapértelmezett gomb
        valasz = QMessageBox.question(self, 'Törlés megerősítése', f'Biztosan törölni szeretnéd a(z) "{fajl_nev}" fájlt és a hozzá tartozó adatbázis adatokat?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, # | (VAGY) operátorral mindkét gombot hozzáadja az ablakhoz
            QMessageBox.StandardButton.No # az alapértelmezett (kijelölt) gomb a "Nem" (No) lesz, a véletlen törlés elkerülése miatt
        )
        # ellenőrzi, hogy a felhasználó az "Igen" (Yes) gombra kattintott-e
        if valasz == QMessageBox.StandardButton.Yes:
            # meghívja a háttérlogikát, ami törli a fizikai fájlt, a ChromaDB vektorokat és a tanulási haladást is
            self.backend.pdf_torlese(fajl_nev)
            # frissíti a táblázatot, amiből így azonnal eltűnik a törölt fájl sora
            self.kepernyo_frissitese()