import sys
import chromadb
import os

jelenlegi_mappa = os.path.dirname(os.path.abspath(__file__))
szulo_mappa = os.path.dirname(jelenlegi_mappa)
sys.path.append(szulo_mappa)

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
    from views.home_screen import HomeScreen
    from views.subject_screen import Subject_screen

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()

            self.setWindowTitle("Szakdolgozat")
            self.setMinimumSize(700,600)
            self.showMaximized()

            self.kezdo_kepernyo = HomeScreen()
            self.kezdo_kepernyo.valasztott_temakor.connect(self.valtas_tantargy_nezetre)

            # oldalak
            self.oldalak = QStackedWidget()  
            #kezdokepernyo
            self.oldalak.addWidget(self.kezdo_kepernyo)
            #kozepre teszuk
            self.setCentralWidget(self.oldalak)
            
        def valtas_tantargy_nezetre(self, kivalasztott_temakor):
            # peldanyositas
            uj_ablak = Subject_screen(kivalasztott_temakor)
            
            uj_ablak.vissza_fomenube.connect(self.vissza_a_kezdo_kepernyore)
            #uj ablak hozza dadasa
            self.oldalak.addWidget(uj_ablak)
            # oldalvaltas
            self.oldalak.setCurrentWidget(uj_ablak)

        def vissza_a_kezdo_kepernyore(self):
            # Visszaváltjuk a paklit az 1. oldalra (ami a HomeScreen)
            self.oldalak.setCurrentWidget(self.kezdo_kepernyo)
            
            # Opcionális, de nagyon hasznos: frissítjük a főképernyőt, hátha 
            # valami változott (pl. lettek új mappák) amíg a másik nézetben voltunk
            self.kezdo_kepernyo.frissit_kepernyot()

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()