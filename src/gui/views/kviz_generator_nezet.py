from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, 
                             QSlider, QScrollArea, QSpinBox, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QStringListModel
import json
from pathlib import Path

from backend.kviz_generator import KvizGenerator
from backend.kviz_kiertekelo import KvizKiertekelo, KvizFajlKezelo
from gui.views.kviz_widget import WIDGET_REGISZTER
from gui.views.hatterszal import KvizHatterszal

ALAP_UTVONAL = Path("./data/subjects")

class KvizGeneratorNezet(QWidget):
    def __init__(self, temakor_neve: str) -> None:
        # super().__init__() meghívja a szülőosztály (QWidget) inicializáló metódusát
        super().__init__()
        self.temakor_neve = temakor_neve
        self.mappa_utvonal = ALAP_UTVONAL / temakor_neve / "raw"

        # QVBoxLayout: függőlegesen egymás alá rendezi a benne elhelyezett elemeket (widgeteket)
        self.fobb_elrendezes = QVBoxLayout()
        # setLayout: beállítja a fenti függőleges elrendezést az ablak fő elrendezéseként
        self.setLayout(self.fobb_elrendezes)

        # UI (felhasználói felület) elemeinek inicializálása
        self._hiba_felulet_beallitasa()
        self._vezerlo_felulet_beallitasa()
        self._kviz_terulet_beallitasa()
        self._kiertekelo_felulet_beallitasa()
        
    def _hiba_felulet_beallitasa(self) -> None:
        # létrehoz egy üres widgetet, ami a hibaüzenetet fogja tartalmazni
        self.hiba_widget = QWidget()
        # QVBoxLayout: függőlegesen egymás alá rendezi a benne elhelyezett elemeket (widgeteket) és hozzárendeli a self.hiba_widget-et
        hiba_elrendezes = QVBoxLayout(self.hiba_widget)
        
        # addStretch(): egy rugalmas, üres teret ad az elrendezéshez
        # ha felülés alul is van egy, az pontosan középre tolja a köztük lévő tartalmat
        hiba_elrendezes.addStretch()
        
        self.hiba_cimke = QLabel("Nincs PDF feltöltve. Tölts fel egyet, mielőtt kvízt kérnél!")
        # setObjectName: ez alapján tud hivatkozni rá a stíluslapokban (qss)
        self.hiba_cimke.setObjectName("EmptyText2")
        # setAlignment: beállítja a szöveg igazítását, a Qt.AlignmentFlag.AlignCenter pedig pontosan középre zárja a számot a dobozon belül
        self.hiba_cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # hozzáadja a címkét az elrendezéshez
        hiba_elrendezes.addWidget(self.hiba_cimke)
        # addStretch(): egy rugalmas, üres teret ad az elrendezéshez
        # ha felülés alul is van egy, az pontosan középre tolja a köztük lévő tartalmat
        hiba_elrendezes.addStretch()

        # hozzáadja a kész hiba-tárolót a fő elrendezésünkhöz
        self.fobb_elrendezes.addWidget(self.hiba_widget)
        # .hide(): alapértelmezetten elrejti ezt a felületet
        self.hiba_widget.hide()

    def _vezerlo_felulet_beallitasa(self) -> None:
        # létrehoz egy üres widgetet, ami a hibaüzenetet fogja tartalmazni
        self.vezerlo_widget = QWidget()
        # QVBoxLayout: függőlegesen egymás alá rendezi a benne elhelyezett elemeket (widgeteket) és hozzárendeli a self.vezerlo_widget-et
        self.vezerlo_elrendezes = QVBoxLayout(self.vezerlo_widget)

        # QHBoxLayout: vízszintesen (egymás mellé) rendezi a benne lévő elemeket
        pdf_sor = QHBoxLayout()
        pdf_cimke = QLabel("Válaszd ki a tananyagot (PDF):")
        # setObjectName: ez alapján tud hivatkozni rá a stíluslapokban (qss)
        pdf_cimke.setObjectName("EmptyText2")

        # QComboBox: legördülő menüt hoz létre
        self.pdf_valaszto = QComboBox()
        # setObjectName: ez alapján tud hivatkozni rá a stíluslapokban (qss)
        self.pdf_valaszto.setObjectName("PdfSelector")
        
        # QStringListModel: ez a modell tárolja a legördülő menü választható szöveges elemeit
        self.pdf_modell = QStringListModel()
        # setModel összekapcsolja a vizuális menüt (self.pdf_valaszto) az adatmodellel (self.pdf_modell)
        # legördülő menü automatikusan frissül
        self.pdf_valaszto.setModel(self.pdf_modell)
        
        # hozzáadjuk a címkét és a legördülő menüt a vízszintes sorhoz
        pdf_sor.addWidget(pdf_cimke)
        pdf_sor.addWidget(self.pdf_valaszto)
        
        # addStretch(): egy rugalmas, üres teret ad az elrendezéshez
        # kitölti az üres helyet a sor végén, így a bal oldalra igazítja a felületelemeket
        pdf_sor.addStretch()
        
        # a kész vízszintes sort betesszük a függőleges vezérlő elrendezésbe
        self.vezerlo_elrendezes.addLayout(pdf_sor)

        # QHBoxLayout: vízszintesen (egymás mellé) rendezi a benne lévő elemeket
        csuszka_sor = QHBoxLayout()
        csuszka_cimke = QLabel("Kérdések maximális száma:")
        # setObjectName: ez alapján tud hivatkozni rá a stíluslapokban (qss)
        csuszka_cimke.setObjectName("EmptyText2")
        
        # QSlider: létrehoz egy csúszkát, a Qt.Orientation.Horizontal paraméter megadja, hogy az vízszintes tájolású legyen
        self.csuszka = QSlider(Qt.Orientation.Horizontal)
        # setObjectName: ez alapján tud hivatkozni rá a stíluslapokban (qss)
        self.csuszka.setObjectName("QuizSlider")
        self.csuszka.setRange(1, 50) # beállítja a minimum és maximum értéket
        self.csuszka.setValue(10) # beállítja az alapértelmezett kezdőértéket
        # setTickPosition: megjeleníti a beosztásokat a vízszintes csúszka sávja alatt
        #TicksBelow mondja meg, hogy a beosztások a csúszka vonala alá kerüljenek
        self.csuszka.setTickPosition(QSlider.TickPosition.TicksBelow)
        
        # QSpinBox: egy számbeviteli mező (amiben alapesetben nyíilal is lehet állítani az értéket)
        self.csuszka_ertek_cimke = QSpinBox()
        # setObjectName: ez alapján tud hivatkozni rá a stíluslapokban (qss)
        self.csuszka_ertek_cimke.setObjectName("SliderValueBadge")
        self.csuszka_ertek_cimke.setRange(1, 50) # beállítja a minimum és maximum értéket
        self.csuszka_ertek_cimke.setValue(10) # beállítja az alapértelmezett kezdőértéket
        # setAlignment: beállítja a szöveg igazítását, a Qt.AlignmentFlag.AlignCenter pedig pontosan középre zárja a számot a dobozon belül
        self.csuszka_ertek_cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # setButtonSymbols: szabályozza a léptető nyilak megjelenését
        # QSpinBox.ButtonSymbols.NoButtons paraméter teljesen elrejti azokat, így a doboz egy letisztult címkének tűnik
        self.csuszka_ertek_cimke.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)

        # .connect(): összeköti a csúszkát és a beviteli mezőt, hogy szinkronban legyenek
        # valueChanged: jelzi, ha megváltozott a csúszka értéke, a setValue pedig megváltoztatja azt a dobozban
        self.csuszka.valueChanged.connect(self.csuszka_ertek_cimke.setValue)
        
        # .connect(): összeköti a csúszkát és a beviteli mezőt, hogy szinkronban legyenek
        # textChanged: jelzi, ha megváltozott a beviteli mező szövege
        self.csuszka_ertek_cimke.textChanged.connect(
            # lambda függvény: egy egysoros, névtelen függvény
            # isdigit: ha a dobozba beírnak egy szöveget, megvizsgálja, hogy szám-e
            # ha igen, a setValue beállítja a csúszkát erre az értékre
            lambda szoveg: self.csuszka.setValue(int(szoveg)) if szoveg.isdigit() else None
        )
        
        # hozzáadjuk az elemeket a csúszka vízszintes sorához
        csuszka_sor.addWidget(csuszka_cimke)
        csuszka_sor.addWidget(self.csuszka)
        csuszka_sor.addWidget(self.csuszka_ertek_cimke)
        
        # addLayout: a korábban összeállított vízszintes sort (csoportot) beágyazza a függőleges elrendezésbe
        self.vezerlo_elrendezes.addLayout(csuszka_sor)

        # generáló gomb létrehozása
        self.generalas_gomb = QPushButton("Kvíz generálása")
        # setObjectName: ez alapján tud hivatkozni rá a stíluslapokban (qss)
        self.generalas_gomb.setObjectName("GenerateButton")
        # clicked.connect: ha rákattintanak a gombra, le futatja a self.kviz_inditasa metódust
        self.generalas_gomb.clicked.connect(self.kviz_inditasa)
        # hozzáadja a gombot a függőleges elrendezéshez
        self.vezerlo_elrendezes.addWidget(self.generalas_gomb)
        
        # teljes vezérlő widgetet hozzáadja a főablak elrendezéséhez
        self.fobb_elrendezes.addWidget(self.vezerlo_widget)
        
    def _kviz_terulet_beallitasa(self) -> None:
        self.info_cimke = QLabel()
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.info_cimke.setObjectName("InfoLabel")
        # setAlignment: beállítja a szöveg igazítását, a Qt.AlignmentFlag.AlignCenter pedig pontosan középre zárja a szöveget a címkén belül
        self.info_cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # hozzáadja az info_cimkét a fő elrendezéshez
        self.fobb_elrendezes.addWidget(self.info_cimke)
        # .hide(): alapértelmezetten elrejti ezt a felületet
        self.info_cimke.hide()

        # QScrollArea: figyeli a benne lévő tartalmat, és csak akkor jeleníti meg az oldalán a gördítősávot, ha a kérdések már nem férnek ki a képernyőre
        self.gorgetheto_terulet = QScrollArea()
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.gorgetheto_terulet.setObjectName("QuizScrollArea")
        # setWidgetResizable: engedélyezi, hogy a bekerülő tartalom (a kérdések widgetjei) dinamikusan alkalmazkodjanak a külső ablak méretéhez
        self.gorgetheto_terulet.setWidgetResizable(True)
        
        # hozzáadja a görgethető területet a fő elrendezéshez
        self.fobb_elrendezes.addWidget(self.gorgetheto_terulet)
        # .hide(): alapértelmezetten elrejti ezt a felületet
        self.gorgetheto_terulet.hide()
        
    def _kiertekelo_felulet_beallitasa(self) -> None:
        # létrehoz egy gombot a kvíz beküldéséhez és kiértékeléséhez
        self.kiertekel_gomb = QPushButton("Kvíz beküldése és értékelése")
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.kiertekel_gomb.setObjectName("GenerateButton")
        # clicked.connect: ha rákattintanak a gombra, lefuttatja a self.kviz_kiertekelese metódust
        self.kiertekel_gomb.clicked.connect(self.kviz_kiertekelese)
        
        # hozzáadja a gombot a fő elrendezéshez
        self.fobb_elrendezes.addWidget(self.kiertekel_gomb)
        # .hide(): alapértelmezetten elrejti ezt a gombot
        self.kiertekel_gomb.hide()
        
        # eredménycímke létrehozása a pontszám megjelenítésére
        self.eredmeny_cimke = QLabel()
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.eredmeny_cimke.setObjectName("EredmenyCimke")
        # setAlignment: beállítja a szöveg igazítását, a Qt.AlignmentFlag.AlignCenter pedig pontosan középre zárja a szöveget a címkén belül
        self.eredmeny_cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # hozzáadja az eredménycímkét a fő elrendezéshez
        self.fobb_elrendezes.addWidget(self.eredmeny_cimke)
        # .hide(): alapértelmezetten elrejti ezt a címkét
        self.eredmeny_cimke.hide()

        # létrehoz egy üres widgetet, ami térkitöltőként fog funkcionálni
        self.ures_ter = QWidget()

        # setSizePolicy: beállítja, hogyan reagáljon a widget az ablak átméretezésére
        # a QSizePolicy.Policy.Expanding biztosítja, hogy az elem dinamikusan kitöltse a rendelkezésre álló üres helyet
        # az első paraméter a vízszintes (oldalirányú), a második a függőleges (fel-le irányú) méretváltozását engedélyezi
        self.ures_ter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # hozzáadja a térkitöltőt a fő elrendezéshez, ami így feltolja a többi (látható) elemet az ablak tetejére
        self.fobb_elrendezes.addWidget(self.ures_ter)

# a showEvent a PyQt6 beépített metódusa, automatikusan lefut, amikor a widget megjelenik a képernyőn
    def showEvent(self, event) -> None:
        # super(): meghívja a szülőosztály (QWidget) eredeti showEvent metódusát
        # ez garantálja, hogy a grafikus motor elvégezze a felület alapvető kirajzolását, mielőtt lefutna a hozzáadott logika
        super().showEvent(event)
        
        pdf_lista = KvizFajlKezelo.elerheto_pdf_ek_lekerese(self.mappa_utvonal)
        
        if not pdf_lista:
            # ha nincs PDF, megjeleníti a hibaüzenetet, és elrejti a kvíz vezérlőit, valamint a térkitöltőt
            self.hiba_widget.show()
            self.vezerlo_widget.hide()
            self.ures_ter.hide()
        else:
            # ha van PDF, a setStringList parancs betölti a fájlneveket a legördülő menü modelljébe, így az automatikusan frissül
            self.pdf_modell.setStringList(pdf_lista)
            # elrejti a hibaüzenetet, és láthatóvá teszi a vezérlőfelületet a térkitöltővel együtt
            self.hiba_widget.hide()
            self.vezerlo_widget.show()
            self.ures_ter.show()

    def kviz_inditasa(self) -> None:
        # currentText: lekéri a legördülő menüben (QComboBox) aktuálisan kiválasztott PDF fájl nevét
        kivalasztott_pdf = self.pdf_valaszto.currentText()
        if not kivalasztott_pdf: return
            
        # value: lekéri a csúszkán (QSlider) beállított maximális kérdésszámot
        max_k = self.csuszka.value()
        
        # letiltja a vezérlőelemeket (gombok, menük), hogy a generálás alatt a felhasználó ne kattinthasson rájuk újra
        self.ui_visszakapcsolasa(False)
        
        # setText: beállítja a címkén megjelenő szöveget, tájékoztatva a felhasználót a háttérben zajló elemzésről
        self.info_cimke.setText(f"A(z) {kivalasztott_pdf} elemzése folyamatban... Ez eltarthat egy darabig.")
        
        # setProperty: beállítja a címke egyedi "feedback" (visszajelzés) tulajdonságát a QSS-ben
        # üres string "" megadása törli a korábbi hiba- vagy sikerállapotot
        self.info_cimke.setProperty("feedback", "")
        # unpolish: eltávolítja a widgetről a jelenleg érvényes stíluslap (QSS) beállításait
        self.info_cimke.style().unpolish(self.info_cimke)
        # polish: újraalkalmazza a stíluslapot
        # beolvassa az új "feedback" értéket, és frissíti a színeket a képernyőn
        self.info_cimke.style().polish(self.info_cimke)
        self.info_cimke.show()
        
        # elrejti a korábbi kvíz kérdéseit (ha voltak), és megjeleníti a térkitöltőt a betöltőképernyőhöz
        self.gorgetheto_terulet.hide()
        self.ures_ter.show()
        
        # QThread: elindítja a kvíz generálását egy külön háttérszálon
        self.futar = KvizHatterszal(self.temakor_neve, kivalasztott_pdf, max_k)
        # összeköti a háttérszál jelzéseit (sikeres generálás vagy hiba) a megfelelő kezelő metódusokkal
        self.futar.kviz_kesz.connect(self.kviz_megerkezett)
        self.futar.hiba_tortent.connect(self.kviz_hiba)
        # elindítja a háttérszál futását
        self.futar.start()

    def kviz_hiba(self, hiba_uzenet: str) -> None:
        # újra engedélyezi a vezérlőelemeket (gombok, csúszka), hogy a felhasználó rájuk kattinthasson
        self.ui_visszakapcsolasa(True)
        
        # setText: beállítja a címkén megjelenő szöveget, tájékoztatva a felhasználót a hibáról
        self.info_cimke.setText(f"Hiba történt a generálás során:\n{hiba_uzenet}")
        
        # setProperty: beállítja a címke egyedi "feedback" (visszajelzés) tulajdonságát a QSS-ben
        # üres string "" megadása törli a korábbi hiba- vagy sikerállapotot
        self.info_cimke.setProperty("feedback", "")
        # unpolish: eltávolítja a widgetről a jelenleg érvényes stíluslap (QSS) beállításait
        self.info_cimke.style().unpolish(self.info_cimke)
        # polish: újraalkalmazza a stíluslapot
        # beolvassa az új "feedback" értéket, és frissíti a színeket a képernyőn
        self.info_cimke.style().polish(self.info_cimke)
        
        self.ures_ter.show()

    def kviz_megerkezett(self, kviz_json: list[dict]) -> None:
        # újra engedélyezi a vezérlőelemeket, miután a háttérszál végzett a generálással
        self.ui_visszakapcsolasa(True)
        self.info_cimke.hide()
        self.ures_ter.hide()
        self.gorgetheto_terulet.show()
        self.kviz_kirajzolasa(kviz_json)

    # segédmetódus, amely a kapott logikai érték alapján letiltja vagy engedélyezi a vezérlőelemeket
    # megakadályozva ezzel, hogy a felhasználó a betöltés alatt újra rákattintson a gombokra
    def ui_visszakapcsolasa(self, engedelyezve: bool) -> None:
        # setEnabled: az elemek kattinthatóságát a kapott logikai érték (True vagy False) alapján állítja be
        self.generalas_gomb.setEnabled(engedelyezve)
        self.pdf_valaszto.setEnabled(engedelyezve)
        self.csuszka.setEnabled(engedelyezve)
        self.csuszka_ertek_cimke.setEnabled(engedelyezve)

    def kviz_kirajzolasa(self, kviz_lista: list[dict]) -> None:
        # eltárolja a memóriában a megkapott kvíz adatait
        self.jelenlegi_kviz_adatok = kviz_lista 
        self.valasz_vezerlok = {}

        # létrehoz egy üres widgetet, ami az összes kérdést magába foglalja majd
        uj_tartalom_widget = QWidget()
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        uj_tartalom_widget.setObjectName("QuizContentWidget")
        
        # QVBoxLayout: függőlegesen egymás alá rendezi a benne elhelyezett elemeket (widgeteket) és hozzárendeli az uj_tartalom_widgethez
        uj_tartalom_elrendezes = QVBoxLayout(uj_tartalom_widget)
        # setAlignment: az AlignTop beállítás fentről lefelé rendezi az elemeket, az ablak tetejéhez húzva őket, felesleges űr nélkül
        uj_tartalom_elrendezes.setAlignment(Qt.AlignmentFlag.AlignTop)

        # enumerate: egyszerre adja vissza a sorszámot (kerdes_szamlalo) és az aktuális elemet (kerdes_adat)
        # start=1: a sorszámozás 1-től induljon, ne 0-tól
        for kerdes_szamlalo, kerdes_adat in enumerate(kviz_lista, start=1):
            tipus = kerdes_adat.get("type")
            kerdes_id = kerdes_adat.get("id", kerdes_szamlalo)

            # := (walrus operátor) értékadás és vizsgálat egyben
            # lekéri a registry-ből az adott típushoz (pl. "single_choice") tartozó widget osztályt
            # ha létezik ilyen osztály, elmenti a WidgetOsztaly változóba, és azonnal belép az if blokkba
            if WidgetOsztaly := WIDGET_REGISZTER.get(tipus):
                # létrehoz egy konkrét példányt a kérdés felületéből
                widget_peldany = WidgetOsztaly(kerdes_adat, kerdes_szamlalo)
                # eltárolja a szótárba, hogy később le lehessen kérni belőle a felhasználó válaszát
                self.valasz_vezerlok[kerdes_id] = widget_peldany
                # hozzáadja a megjelenítendő elemek listájához
                uj_tartalom_elrendezes.addWidget(widget_peldany)
            else:
                # ha véletlenül olyan típust ad vissza az AI, amire nincs felkészítve a program
                uj_tartalom_elrendezes.addWidget(QLabel(f"<i>(Ismeretlen feladattípus: '{tipus}')</i>"))

        # addStretch(): egy rugalmas, üres teret ad az elrendezéshez
        # kitölti az üres helyet alul, így feltolja a kérdéseket, hogy ne nyúljanak meg indokolatlanul
        uj_tartalom_elrendezes.addStretch()

        # setWidget: a görgethető területbe beleteszi a most összeállított kvízkérdéseket tartalmazó dobozt
        self.gorgetheto_terulet.setWidget(uj_tartalom_widget)
        
        # setEnabled: az elemek kattinthatóságát a kapott logikai érték (True vagy False) alapján állítja be
        self.kiertekel_gomb.setEnabled(True)
        self.kiertekel_gomb.show()
        self.eredmeny_cimke.hide()
    
    def kviz_kiertekelese(self) -> None:
        # setEnabled: az elemek kattinthatóságát a kapott logikai érték (True vagy False) alapján állítja be
        self.kiertekel_gomb.setEnabled(False)
        # végigmegy az összes kérdésen, és kinyeri a felhasználó által adott válaszokat
        felhasznalo_valaszai = self._felhasznalo_valaszainak_begyujtese()
        # lekéri a lenyíló listából, hogy melyik PDF-hez lett generálva a kvíz
        kivalasztott_pdf = self.pdf_valaszto.currentText()
        # meghívja a backend statikus metódusát a válaszok ellenőrzéséhez és a tanulási haladás frissítéséhez
        # a függvény három értékkel tér vissza: elért pontszám, maximális pontszám, és a kérdésenkénti részletes eredmények szótára
        elert_pont, ossz_pont, eredmenyek = KvizKiertekelo.kviz_kiertekelese(self.jelenlegi_kviz_adatok, felhasznalo_valaszai, temakor_neve=self.temakor_neve, fajl_neve=kivalasztott_pdf)
        # átadja a részletes eredményeket a felületnek, hogy a kérdések alatt megjelenjen a zöld/piros jelzés és a magyarázat
        self._visszajelzesek_alkalmazasa(eredmenyek)
        # kiírja az összegzést (százalék és szöveges értékelés) az ablak aljára
        self.eredmeny_megjelenitese(elert_pont, ossz_pont)

    def _felhasznalo_valaszainak_begyujtese(self) -> dict:
        # {} létrehoz egy szótárt
        # végigmegy a self.valasz_vezerlok szótár összes elemén (.items()), ahol a k_id a kérdés azonosítója, a widget pedig maga a felületi elem
        # meghívja minden widget saját get_user_answer() metódusát, és az eredményt a k_id kulcshoz rendeli az új szótárban.
        return {k_id: widget.felhasznalo_valaszanak_lekerese() for k_id, widget in self.valasz_vezerlok.items()}
    
    def _visszajelzesek_alkalmazasa(self, eredmenyek: dict) -> None:
        # végigmegy a kiértékelő által visszaadott eredmények szótárán
        # k_id a kérdés azonosítója, az eredmeny pedig a hozzá tartozó értékelés (helyes-e, magyarázat stb.)
        for k_id, eredmeny in eredmenyek.items():
            # := (walrus operátor) értékadás és vizsgálat egyben
            # lekéri a szótárból az adott azonosítójú widgetet (felületi elemet)
            # ha létezik, elmenti a widget változóba, és belép az if blokkba
            if widget := self.valasz_vezerlok.get(k_id):
                # meghívja az adott kérdés-widget saját metódusát
                # ami a kapott eredmény alapján frissíti a felületet
                widget.visszajelzes_alkalmazasa(eredmeny)
                
    def eredmeny_megjelenitese(self, elert_pont: int, ossz_pont: int) -> None:
        kategoria, szoveg, szazalek = KvizKiertekelo.kiertekeles_osszegzese(elert_pont, ossz_pont)
        # setProperty: beállítja a címke egyedi "kategoria" tulajdonságát
        # ez alapján fogja a QSS a megfelelő színeket (állapotot) alkalmazni
        self.eredmeny_cimke.setProperty("kategoria", kategoria)
        
        # unpolish: eltávolítja a widgetről a jelenleg érvényes stíluslap (QSS) beállításait
        self.eredmeny_cimke.style().unpolish(self.eredmeny_cimke)
        # polish: újraalkalmazza a stíluslapot
        # beolvassa az új "kategoria" értéket, és frissíti a widget megjelenését
        self.eredmeny_cimke.style().polish(self.eredmeny_cimke) 
        
        # setText: formázott szövegként (f-string) beállítja a megjelenő szöveget
        # a .0f formázó biztosítja, hogy a százalék kerekítve, tizedesjegyek nélkül jelenjen meg
        self.eredmeny_cimke.setText(f"Eredményed: {elert_pont} / {ossz_pont} ({szazalek:.0f}%)\n{szoveg}")
        self.eredmeny_cimke.show()
        
        # verticalScrollBar().maximum(): lekéri a görgethető terület függőleges görgetősávjának maximális értékét
        # setValue() pedig beállítja a csúszkát erre a maximális értékre
        # így a nézet automatikusan az ablak legaljára ugrik
        self.gorgetheto_terulet.verticalScrollBar().setValue(self.gorgetheto_terulet.verticalScrollBar().maximum())