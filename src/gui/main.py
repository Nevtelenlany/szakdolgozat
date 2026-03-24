import sys
import chromadb
import os
from pathlib import Path

szulo_mappa = Path(__file__).resolve().parent.parent
sys.path.append(str(szulo_mappa))

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
    from views.home_screen import HomeScreen
    from views.subject_screen import SubjectScreen 

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            
            self._setup_window_properties()
            self._setup_navigation()

        def _setup_window_properties(self) -> None:
            self.setWindowTitle("Szakdolgozat")
            self.setMinimumSize(700, 600)
            self.showMaximized()

        def _setup_navigation(self) -> None:
            self.oldalak = QStackedWidget()
            self.setCentralWidget(self.oldalak)
            self.kezdo_kepernyo = HomeScreen()
            self.kezdo_kepernyo.valasztott_temakor.connect(self.valtas_tantargy_nezetre)
            self.oldalak.addWidget(self.kezdo_kepernyo)
            self.aktualis_tantargy_nezet = None

        def valtas_tantargy_nezetre(self, kivalasztott_temakor: str) -> None:
            self._tisztit_korabbi_nezetet()

            self.aktualis_tantargy_nezet = SubjectScreen(kivalasztott_temakor)
            self.aktualis_tantargy_nezet.vissza_fomenube.connect(self.vissza_a_kezdo_kepernyore)
            
            self.oldalak.addWidget(self.aktualis_tantargy_nezet)
            self.oldalak.setCurrentWidget(self.aktualis_tantargy_nezet)

        def vissza_a_kezdo_kepernyore(self) -> None:
            self.oldalak.setCurrentWidget(self.kezdo_kepernyo)
            self.kezdo_kepernyo.frissit_kepernyot()
            
            self._tisztit_korabbi_nezetet()

        def _tisztit_korabbi_nezetet(self) -> None:
            if self.aktualis_tantargy_nezet:
                self.oldalak.removeWidget(self.aktualis_tantargy_nezet)
                self.aktualis_tantargy_nezet.deleteLater()
                self.aktualis_tantargy_nezet = None

    # Program indítása
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())