from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, 
                             QSlider, QScrollArea, QSpinBox, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QStringListModel
import json
from pathlib import Path

from backend.quiz_generator import QuizGenerator
from backend.quiz_logic import QuizEvaluator, QuizFileManager
from views.quiz_widgets import WIDGET_REGISTRY

class QuizGeneratorView(QWidget):
    def __init__(self, temakor_neve: str) -> None:
        super().__init__()
        self.temakor_neve = temakor_neve
        self.mappa_utvonal = str(Path("./data/subjects") / temakor_neve / "raw")

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self._setup_error_ui()
        self._setup_control_ui()
        self._setup_quiz_area_ui()
        self._setup_evaluation_ui()

    def _setup_error_ui(self) -> None:
        self.hiba_widget = QWidget()
        hiba_layout = QVBoxLayout(self.hiba_widget)
        hiba_layout.addStretch()
        
        self.hiba_cimke = QLabel("Nincs PDF feltöltve. Tölts fel egyet, mielőtt kvízt kérnél!")
        self.hiba_cimke.setObjectName("EmptyText2")
        self.hiba_cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        hiba_layout.addWidget(self.hiba_cimke)
        hiba_layout.addStretch()

        self.main_layout.addWidget(self.hiba_widget)
        self.hiba_widget.hide()

    def _setup_control_ui(self) -> None:
        self.vezerlo_widget = QWidget()
        self.vezerlo_layout = QVBoxLayout(self.vezerlo_widget)

        pdf_sor = QHBoxLayout()

        pdf_cimke = QLabel("Válaszd ki a tananyagot (PDF):")
        pdf_cimke.setObjectName("EmptyText2")

        self.pdf_valaszto = QComboBox()
        self.pdf_valaszto.setObjectName("PdfSelector")
        self.pdf_modell = QStringListModel()
        self.pdf_valaszto.setModel(self.pdf_modell)
        pdf_sor.addWidget(pdf_cimke)
        pdf_sor.addWidget(self.pdf_valaszto)
        pdf_sor.addStretch()
        self.vezerlo_layout.addLayout(pdf_sor)

        csuszka_sor = QHBoxLayout()
        csuszka_cimke = QLabel("Kérdések maximális száma:")
        csuszka_cimke.setObjectName("EmptyText2")
        
        self.csuszka = QSlider(Qt.Orientation.Horizontal)
        self.csuszka.setObjectName("QuizSlider")
        self.csuszka.setRange(1, 50)
        self.csuszka.setValue(10)
        self.csuszka.setTickPosition(QSlider.TickPosition.TicksBelow)
        
        self.csuszka_ertek_cimke = QSpinBox()
        self.csuszka_ertek_cimke.setObjectName("SliderValueBadge")
        self.csuszka_ertek_cimke.setRange(1, 50)
        self.csuszka_ertek_cimke.setValue(10)
        self.csuszka_ertek_cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.csuszka_ertek_cimke.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)

        self.csuszka.valueChanged.connect(self.csuszka_ertek_cimke.setValue)
        self.csuszka_ertek_cimke.textChanged.connect(
            lambda text: self.csuszka.setValue(int(text)) if text.isdigit() else None
        )
        
        csuszka_sor.addWidget(csuszka_cimke)
        csuszka_sor.addWidget(self.csuszka)
        csuszka_sor.addWidget(self.csuszka_ertek_cimke)
        self.vezerlo_layout.addLayout(csuszka_sor)

        self.generalas_gomb = QPushButton("Kvíz generálása")
        self.generalas_gomb.setObjectName("GenerateButton")
        self.generalas_gomb.clicked.connect(self.kviz_inditasa)
        self.vezerlo_layout.addWidget(self.generalas_gomb)
        
        self.main_layout.addWidget(self.vezerlo_widget)

    def _setup_quiz_area_ui(self) -> None:
        self.info_cimke = QLabel()
        self.info_cimke.setObjectName("InfoLabel")
        self.info_cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.info_cimke)
        self.info_cimke.hide()

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("QuizScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)
        self.scroll_area.hide()

    def _setup_evaluation_ui(self) -> None:
        self.kiertekel_gomb = QPushButton("Kvíz beküldése és értékelése")
        self.kiertekel_gomb.setObjectName("GenerateButton")
        self.kiertekel_gomb.clicked.connect(self.kviz_kiertekelese)
        self.main_layout.addWidget(self.kiertekel_gomb)
        self.kiertekel_gomb.hide()
        
        self.eredmeny_cimke = QLabel()
        self.eredmeny_cimke.setObjectName("EredmenyCimke")
        self.eredmeny_cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.eredmeny_cimke)
        self.eredmeny_cimke.hide()

        self.ures_ter = QWidget()
        self.ures_ter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.main_layout.addWidget(self.ures_ter)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        pdf_lista = QuizFileManager.get_available_pdfs(self.mappa_utvonal)
        
        if not pdf_lista:
            self.hiba_widget.show()
            self.vezerlo_widget.hide()
            self.ures_ter.hide()
        else:
            self.pdf_modell.setStringList(pdf_lista)
            self.hiba_widget.hide()
            self.vezerlo_widget.show()
            self.ures_ter.show()

    def kviz_inditasa(self) -> None:
        kivalasztott_pdf = self.pdf_valaszto.currentText()
        if not kivalasztott_pdf: return
            
        max_k = self.csuszka.value()
        self.ui_visszakapcsolasa(False)
        
        self.info_cimke.setText(f"A(z) {kivalasztott_pdf} elemzése folyamatban... Ez eltarthat egy darabig.")
        self.info_cimke.setProperty("feedback", "")
        self.info_cimke.style().unpolish(self.info_cimke)
        self.info_cimke.style().polish(self.info_cimke)
        self.info_cimke.show()
        
        self.scroll_area.hide()
        self.ures_ter.show()
        
        self.futar = KvizFutarSzal(self.mappa_utvonal, kivalasztott_pdf, max_k)
        self.futar.kviz_kesz.connect(self.kviz_megerkezett)
        self.futar.hiba_torent.connect(self.kviz_hiba)
        self.futar.start()

    def kviz_hiba(self, hiba_uzenet: str) -> None:
        self.ui_visszakapcsolasa(True)
        self.info_cimke.setText(f"Hiba történt a generálás során:\n{hiba_uzenet}")
        self.info_cimke.setProperty("feedback", "wrong")
        self.info_cimke.style().unpolish(self.info_cimke)
        self.info_cimke.style().polish(self.info_cimke)
        self.ures_ter.show()

    def kviz_megerkezett(self, kviz_json: list[dict]) -> None:
        self.ui_visszakapcsolasa(True)
        self.info_cimke.hide()
        self.ures_ter.hide()
        self.scroll_area.show()
        self.kviz_kirajzolasa(kviz_json)

    def ui_visszakapcsolasa(self, is_enabled: bool) -> None:
        self.generalas_gomb.setEnabled(is_enabled)
        self.pdf_valaszto.setEnabled(is_enabled)
        self.csuszka.setEnabled(is_enabled)
        self.csuszka_ertek_cimke.setEnabled(is_enabled)

    def kviz_kirajzolasa(self, kviz_lista: list[dict]) -> None:
        self.jelenlegi_kviz_adatok = kviz_lista 
        self.valasz_vezerlok = {}

        uj_tartalom_widget = QWidget()
        uj_tartalom_widget.setObjectName("QuizContentWidget")
        uj_tartalom_layout = QVBoxLayout(uj_tartalom_widget)
        uj_tartalom_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        for kerdes_szamlalo, kerdes_adat in enumerate(kviz_lista, start=1):
            tipus = kerdes_adat.get("type")
            kerdes_id = kerdes_adat.get("id", kerdes_szamlalo)

            if WidgetOsztaly := WIDGET_REGISTRY.get(tipus):
                widget_peldany = WidgetOsztaly(kerdes_adat, kerdes_szamlalo)
                self.valasz_vezerlok[kerdes_id] = widget_peldany
                uj_tartalom_layout.addWidget(widget_peldany)
            else:
                uj_tartalom_layout.addWidget(QLabel(f"<i>(Ismeretlen feladattípus: '{tipus}')</i>"))

        uj_tartalom_layout.addStretch()

        self.scroll_area.setWidget(uj_tartalom_widget)
        self.kiertekel_gomb.setEnabled(True)
        self.kiertekel_gomb.show()
        self.eredmeny_cimke.hide()
    
    def kviz_kiertekelese(self) -> None:
        self.kiertekel_gomb.setEnabled(False)
        user_answers = self._collect_user_answers()

        kivalasztott_pdf = self.pdf_valaszto.currentText()
        elert_pont, ossz_pont, eredmenyek = QuizEvaluator.evaluate_quiz(
            self.jelenlegi_kviz_adatok, 
            user_answers,
            raw_folder_path=self.mappa_utvonal, 
            pdf_neve=kivalasztott_pdf
        )
        
        self._apply_feedback_to_widgets(eredmenyek)
        self.eredmeny_megjelenitese(elert_pont, ossz_pont)

    def _collect_user_answers(self) -> dict:
        return {k_id: widget.get_user_answer() for k_id, widget in self.valasz_vezerlok.items()}

    def _apply_feedback_to_widgets(self, eredmenyek: dict) -> None:
        for k_id, eredmeny in eredmenyek.items():
            if widget := self.valasz_vezerlok.get(k_id):
                widget.apply_feedback(eredmeny)

    def eredmeny_megjelenitese(self, elert_pont: int, ossz_pont: int) -> None:
        kategoria, szoveg, szazalek = QuizEvaluator.get_evaluation_summary(elert_pont, ossz_pont)
        self.eredmeny_cimke.setProperty("kategoria", kategoria)
        self.eredmeny_cimke.style().unpolish(self.eredmeny_cimke)
        self.eredmeny_cimke.style().polish(self.eredmeny_cimke)
        
        self.eredmeny_cimke.setText(f"Eredményed: {elert_pont} / {ossz_pont} ({szazalek:.0f}%)\n{szoveg}")
        self.eredmeny_cimke.show()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

class KvizFutarSzal(QThread):
    kviz_kesz = pyqtSignal(list)
    hiba_torent = pyqtSignal(str)

    def __init__(self, raw_folder: str, pdf_neve: str, max_kerdes: int) -> None:
        super().__init__()
        self.raw_folder = raw_folder
        self.pdf_neve = pdf_neve
        self.max_kerdes = max_kerdes

    def run(self) -> None:
        try:
            generator = QuizGenerator(self.raw_folder)
            kviz_json = generator.generalj_kvizt(self.pdf_neve, self.max_kerdes)
            self.kviz_kesz.emit(kviz_json)
        except ValueError as ve:
            self.hiba_torent.emit(f"Adathiba: {ve}")
        except json.JSONDecodeError:
            self.hiba_torent.emit("Hiba történt a generált kvíz feldolgozásakor.")
        except ConnectionError:
            self.hiba_torent.emit("Hálózati hiba: Nem sikerült kapcsolódni az AI szerveréhez.")