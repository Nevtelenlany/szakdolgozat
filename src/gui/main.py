import sys
from pathlib import Path

# __file__: az aktuális fájl (main.py) elérési útja
# resolve(): feloldja a relatív hivatkozásokat, és a teljes, abszolút útvonalat adja meg
# parent.parent: visszalép két mappaszintet (a projekt gyökérkönyvtárába), hogy a program "lássa" a többi mappát
szulo_mappa = Path(__file__).resolve().parent.parent
# sys.path.append: hozzáadja ezt a könyvtárat a Python keresési útvonalaihoz, 
# így hiba nélkül be tudja importálni a 'backend' és 'gui' mappákban lévő saját modulokat
sys.path.append(str(szulo_mappa))

# ez biztosítja, hogy a kód csak akkor fusson le, ha ezt a fájlt közvetlenül indítják el
#  megakadályozza, hogy véletlenül elinduljon a program, ha ezt a fájlt egy másik modulba importálják
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
    
    from gui.views.fomenu_nezet import FomenuNezet
    from gui.views.temakor_nezet import TemakorNezet
    
    class FoAblak(QMainWindow):
        # inicializálás
        def __init__(self) -> None:
            # super().__init__() meghívja a szülőosztály (QMainWindow) inicializáló metódusát
            super().__init__()
            
            # UI (felhasználói felület) elemeinek és az ablak tulajdonságainak inicializálása
            self._ablak_tulajdonsagok_beallitasa()
            self._navigacio_beallitasa()

        def _ablak_tulajdonsagok_beallitasa(self) -> None:
            # setWindowTitle: beállítja az ablak címsorában megjelenő szöveget
            self.setWindowTitle("Tanulást támogató chatbot")
            # setMinimumSize: megakadályozza, hogy a felhasználó ennél (700x600 pixel) kisebbre méretezze át az ablakot
            self.setMinimumSize(700, 600)
            # showMaximized: az alkalmazás indításkor automatikusan kitölti a teljes képernyőt
            self.showMaximized()

        def _navigacio_beallitasa(self) -> None:
            # QStackedWidget: egy olyan tároló, amibe több nézetet is be lehet tenni, de egyszerre mindig csak egyet mutat
            # ez fog felelni a főmenü és a témakör nézetek közötti lapozásért
            self.oldalak = QStackedWidget()
            # setCentralWidget: a QMainWindow középső, fő tartalmának beállítja ezt a lapozható tárolót
            self.setCentralWidget(self.oldalak)

            # példányosítja a főmenüt (a kezdőképernyőt)
            self.kezdo_kepernyo = FomenuNezet()
            # .connect(): összeköti a főmenü által küldött jelet (amikor a felhasználó rákattint egy témakörre) a nézetváltó metódussal
            self.kezdo_kepernyo.valasztott_temakor.connect(self.valtas_tantargy_nezetre)
            
            # addWidget: beteszi a kezdőképernyőt a QStackedWidget legelső helyére (ez fog megjelenni indításkor)
            self.oldalak.addWidget(self.kezdo_kepernyo)
            # kezdetben nincs kiválasztott tantárgy, ezért a változót None-ra állítjuk
            self.aktualis_tantargy_nezet = None

        def valtas_tantargy_nezetre(self, kivalasztott_temakor: str) -> None:
            # mielőtt betölti az újat, biztonságosan letörli a régit a memóriából
            self._tisztit_korabbi_nezetet()
            # példányosítja a témakör részletes nézetét a megkapott tantárgynév alapján
            self.aktualis_tantargy_nezet = TemakorNezet(kivalasztott_temakor)
            # .connect(): összeköti az új nézet visszalépés gombja által küldött jelet (pyqtSignal) a főmenübe visszatérő metódussal
            self.aktualis_tantargy_nezet.vissza_fomenube.connect(self.vissza_a_kezdo_kepernyore)
            # addWidget: beteszi az imént létrehozott új tantárgy nézetet a QStackedWidget "paklijába"
            self.oldalak.addWidget(self.aktualis_tantargy_nezet)
            # setCurrentWidget: utasítja a tárolót, hogy lapozzon oda, és ezt az új nézetet mutassa a képernyőn
            self.oldalak.setCurrentWidget(self.aktualis_tantargy_nezet)
            
        def vissza_a_kezdo_kepernyore(self) -> None:
            # setCurrentWidget: visszavált a lapozható tároló legelső oldalára (a főmenüre)
            self.oldalak.setCurrentWidget(self.kezdo_kepernyo)
            # meghívja a kezdőképernyő frissítő metódusát, hogy a meglévő témakörök/mappák listája naprakész legyen
            self.kezdo_kepernyo.kepernyo_frissitese()
            # miután sikeresen visszaléptünk, törli a korábbi tantárgy nézetet a memóriából az erőforrások felszabadítása érdekében
            self._tisztit_korabbi_nezetet()
            
        def _tisztit_korabbi_nezetet(self) -> None:
            # ellenőrzi, hogy van-e éppen aktív tantárgy nézet betöltve
            if self.aktualis_tantargy_nezet:
                # removeWidget: kiveszi a widgetet a QStackedWidget "kártyapaklijából"
                self.oldalak.removeWidget(self.aktualis_tantargy_nezet)
                # deleteLater: jelzi a Qt motornak, hogy amint tudja, biztonságosan törölje a widgetet és szabadítsa fel a hozzá tartozó memóriát
                self.aktualis_tantargy_nezet.deleteLater()
                # a referenciát visszaállítja None-ra, hogy a következő ellenőrzésnél már ne lássa aktívnak
                self.aktualis_tantargy_nezet = None

    # QApplication: a PyQt6 alkalmazás alapja, ez kezeli a grafikus felületet és a rendszereseményeket (kattintások, ablakméretezés)
    # sys.argv átadja a parancssori argumentumokat (ha a terminálból indítanák paraméterekkel)
    app = QApplication(sys.argv)
    # példányosítja a főablakot
    ablak = FoAblak()
    # show(): megjeleníti az ablakot a képernyőn
    ablak.show()
    # app.exec(): elindítja az alkalmazás végtelenített fő eseményhurkát (event loop), ami folyamatosan fut és várja a felhasználói interakciókat
    # sys.exit(): biztosítja, hogy amikor a felhasználó bezárja az ablakot, a Python folyamat is tisztán, memóriaszivárgás és hibakód nélkül álljon le
    sys.exit(app.exec())