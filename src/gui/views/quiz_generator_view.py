import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSlider, QScrollArea,
                             QFrame, QButtonGroup, QRadioButton, QCheckBox, QLineEdit, QSpinBox, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from backend.quiz_generator import quiz_generator
from backend.quiz_logic import QuizEvaluator, QuizFileManager

class quiz_generator_view(QWidget):
    def __init__(self, temakor_neve):
        super().__init__()
        self.temakor_neve = temakor_neve
        self.mappa_utvonal = f"./data/subjects/{temakor_neve}/raw/"

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

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

        self.vezerlo_widget = QWidget()
        self.vezerlo_layout = QVBoxLayout(self.vezerlo_widget)

        pdf_sor = QHBoxLayout()
        pdf_cimke = QLabel("Válaszd ki a tananyagot (PDF):")
        pdf_cimke.setObjectName("EmptyText2")
        pdf_sor.addWidget(pdf_cimke)

        self.pdf_valaszto = QComboBox()
        self.pdf_valaszto.setObjectName("PdfSelector")
        pdf_sor.addWidget(self.pdf_valaszto)
        pdf_sor.addStretch()
        self.vezerlo_layout.addLayout(pdf_sor)

        csuszka_sor = QHBoxLayout()
        csuszka_cimke = QLabel("Kérdések maximális száma:")
        csuszka_cimke.setObjectName("EmptyText2")
        csuszka_sor.addWidget(csuszka_cimke)
        
        self.csuszka = QSlider(Qt.Orientation.Horizontal)
        self.csuszka.setObjectName("QuizSlider")
        self.csuszka.setMinimum(1)
        self.csuszka.setMaximum(50)
        self.csuszka.setValue(10)
        self.csuszka.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.csuszka.setTickInterval(1)
        
        self.csuszka_ertek_cimke = QSpinBox()
        self.csuszka_ertek_cimke.setObjectName("SliderValueBadge")
        self.csuszka_ertek_cimke.setMinimum(1)
        self.csuszka_ertek_cimke.setMaximum(50)
        self.csuszka_ertek_cimke.setValue(10)
        self.csuszka_ertek_cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.csuszka_ertek_cimke.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)

        self.csuszka.valueChanged.connect(self.csuszka_ertek_cimke.setValue)
        self.csuszka_ertek_cimke.textChanged.connect(
            lambda text: self.csuszka.setValue(int(text)) if text.isdigit() else None
        )

        csuszka_sor.addWidget(self.csuszka)
        csuszka_sor.addWidget(self.csuszka_ertek_cimke)
        self.vezerlo_layout.addLayout(csuszka_sor)

        self.generalas_gomb = QPushButton("Kvíz generálása")
        self.generalas_gomb.setObjectName("GenerateButton")
        self.generalas_gomb.clicked.connect(self.kviz_inditasa)
        self.vezerlo_layout.addWidget(self.generalas_gomb)

        self.main_layout.addWidget(self.vezerlo_widget)

        self.info_cimke = QLabel()
        self.info_cimke.setObjectName("InfoLabel")
        self.info_cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.info_cimke)
        self.info_cimke.hide()

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("QuizScrollArea")
        self.scroll_area.setWidgetResizable(True)
        
        self.kviz_tartalom_widget = QWidget()
        self.kviz_tartalom_widget.setObjectName("QuizContentWidget")
        self.kviz_tartalom_layout = QVBoxLayout(self.kviz_tartalom_widget)
        self.kviz_tartalom_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.kviz_tartalom_widget)
        self.main_layout.addWidget(self.scroll_area)
        self.scroll_area.hide()

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

    def showEvent(self, event):
        super().showEvent(event)
        self.pdf_valaszto.clear()
        
        pdf_lista = QuizFileManager.get_available_pdfs(self.mappa_utvonal)
        
        if not pdf_lista:

            self.hiba_widget.show()
            self.vezerlo_widget.hide()
            self.ures_ter.hide()
        else:

            self.pdf_valaszto.addItems(pdf_lista)
            self.hiba_widget.hide()
            self.vezerlo_widget.show()
            self.ures_ter.show()

    def kviz_kiertekelese(self):
        self.kiertekel_gomb.setEnabled(False)
        user_answers = {}

        for kerdes_adat in self.jelenlegi_kviz_adatok:
            k_id = kerdes_adat.get("id")
            tipus = kerdes_adat.get("type")
            vezerlo_adat = self.valasz_vezerlok.get(k_id)

            if not vezerlo_adat: continue

            if tipus == "single_choice":
                valasztott = None
                for btn in vezerlo_adat["gombok"]:
                    if btn.isChecked(): valasztott = btn.text()
                user_answers[k_id] = valasztott

            elif tipus == "multiple_choice":
                valasztottak = [chk.text() for chk in vezerlo_adat["dobozok"] if chk.isChecked()]
                user_answers[k_id] = valasztottak

            elif tipus == "short_answer":
                user_answers[k_id] = vezerlo_adat["mezo"].text()

            elif tipus == "matching":
                valasz_dict = {}
                for sor in vezerlo_adat["sorok"]:
                    valasz_dict[sor["bal_szoveg"]] = sor["combo"].currentText()
                user_answers[k_id] = valasz_dict

            elif tipus == "ordering":
                valasz_lista = [combo.currentText() for combo in vezerlo_adat["combok"]]
                user_answers[k_id] = valasz_lista

        kivalasztott_pdf = self.pdf_valaszto.currentText()
        elert_pont, ossz_pont, eredmenyek = QuizEvaluator.evaluate_quiz(
            self.jelenlegi_kviz_adatok, 
            user_answers,
            raw_folder_path=self.mappa_utvonal, 
            pdf_neve=kivalasztott_pdf
        )
        
        self.szinezd_ki_a_kvizt(eredmenyek)
        self.eredmeny_megjelenitese(elert_pont, ossz_pont)

    def set_feedback_style(self, widget, status):
        widget.setProperty("feedback", status)
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def szinezd_ki_a_kvizt(self, eredmenyek):
        for k_id, eredmeny in eredmenyek.items():
            vezerlo_adat = self.valasz_vezerlok.get(k_id)
            if not vezerlo_adat: continue
            
            tipus = vezerlo_adat["tipus"]
            feedback = eredmeny["feedback"]

            if tipus == "single_choice":
                helyes_valasz = feedback["correct_answer"]
                for btn in vezerlo_adat["gombok"]:
                    if btn.text() == helyes_valasz:
                        self.set_feedback_style(btn, "correct")
                    elif btn.isChecked():
                        self.set_feedback_style(btn, "wrong")

            elif tipus == "multiple_choice":
                helyes_valaszok = feedback["correct_answers"]
                for chk in vezerlo_adat["dobozok"]:
                    if chk.text() in helyes_valaszok:
                        self.set_feedback_style(chk, "correct")
                    elif chk.isChecked():
                        self.set_feedback_style(chk, "wrong")

            elif tipus == "short_answer":
                mezo = vezerlo_adat["mezo"]
                if eredmeny["helyes"]:
                    self.set_feedback_style(mezo, "correct")
                else:
                    self.set_feedback_style(mezo, "wrong")
                    kulcsszavak = ", ".join(feedback["accepted_keywords"])
                    mezo.setText(mezo.text() + f" (Helyes: {kulcsszavak})")

            elif tipus == "matching":
                eredeti_parok = feedback["pairs"]
                for sor in vezerlo_adat["sorok"]:
                    combo = sor["combo"]
                    helyes_par = eredeti_parok.get(sor["bal_szoveg"])
                    if combo.currentText() == helyes_par:
                        self.set_feedback_style(combo, "correct")
                    else:
                        self.set_feedback_style(combo, "wrong")
                        if combo.currentText() != "--- Válassz párt ---":
                            combo.setItemText(combo.currentIndex(), f"Rossz! A helyes: {helyes_par}")

            elif tipus == "ordering":
                eredeti_sorrend = feedback["ordered_items"]
                for i, combo in enumerate(vezerlo_adat["combok"]):
                    helyes_elem = eredeti_sorrend[i]
                    if combo.currentText() == helyes_elem:
                        self.set_feedback_style(combo, "correct")
                    else:
                        self.set_feedback_style(combo, "wrong")
                        if combo.currentText() != "--- Melyik jön ide? ---":
                            combo.setItemText(combo.currentIndex(), f"Rossz! Ide ez jött volna: {helyes_elem}")

    def eredmeny_megjelenitese(self, elert_pont, ossz_pont):
        kategoria, szoveg, szazalek = QuizEvaluator.get_evaluation_summary(elert_pont, ossz_pont)
        
        self.eredmeny_cimke.setProperty("kategoria", kategoria)
        self.eredmeny_cimke.style().unpolish(self.eredmeny_cimke)
        self.eredmeny_cimke.style().polish(self.eredmeny_cimke)
        
        self.eredmeny_cimke.setText(f"Eredményed: {elert_pont} / {ossz_pont} ({szazalek:.0f}%)\n{szoveg}")
        self.eredmeny_cimke.show()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())
    
    def kviz_inditasa(self):
        kivalasztott_pdf = self.pdf_valaszto.currentText()
        if not kivalasztott_pdf: return
            
        max_k = self.csuszka.value()
        
        self.generalas_gomb.setEnabled(False)
        self.pdf_valaszto.setEnabled(False)
        self.csuszka.setEnabled(False)
        self.csuszka_ertek_cimke.setEnabled(False)
        
        self.info_cimke.setText(f"A(z) {kivalasztott_pdf} elemzése folyamatban... Ez eltarthat egy darabig.")
        self.info_cimke.setProperty("feedback", "")
        self.info_cimke.style().unpolish(self.info_cimke)
        self.info_cimke.style().polish(self.info_cimke)
        self.info_cimke.show()
        
        self.scroll_area.hide()
        self.ures_ter.show()
        
        while self.kviz_tartalom_layout.count():
            item = self.kviz_tartalom_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        self.futar = KvizFutarSzal(self.mappa_utvonal, kivalasztott_pdf, max_k)
        self.futar.kviz_kesz.connect(self.kviz_megerkezett)
        self.futar.hiba_torent.connect(self.kviz_hiba)
        self.futar.start()

    def kviz_hiba(self, hiba_uzenet):
        self.ui_visszakapcsolasa()
        self.info_cimke.setText(f"Hiba történt a generálás során:\n{hiba_uzenet}")
        self.set_feedback_style(self.info_cimke, "wrong")
        self.ures_ter.show()

    def kviz_megerkezett(self, kviz_json):
        self.ui_visszakapcsolasa()
        self.info_cimke.hide()
        
        self.ures_ter.hide()
        self.scroll_area.show()
        
        self.kviz_kirajzolasa(kviz_json)

    def ui_visszakapcsolasa(self):
        self.generalas_gomb.setEnabled(True)
        self.pdf_valaszto.setEnabled(True)
        self.csuszka.setEnabled(True)
        self.csuszka_ertek_cimke.setEnabled(True)

    def kviz_kirajzolasa(self, kviz_lista):
        self.jelenlegi_kviz_adatok = kviz_lista 
        self.valasz_vezerlok = {} 
        kerdes_szamlalo = 1

        for kerdes_adat in kviz_lista:
            tipus = kerdes_adat.get("type")
            kerdes_id = kerdes_adat.get("id", kerdes_szamlalo)

            kerdes_doboz = QFrame()
            kerdes_doboz.setObjectName("QuestionFrame")
            kerdes_layout = QVBoxLayout(kerdes_doboz)

            kerdes_szoveg = kerdes_adat.get("question", kerdes_adat.get("instruction", "Kérdés?"))
            cimke = QLabel(f"<b>{kerdes_szamlalo}. {kerdes_szoveg}</b>")
            cimke.setObjectName("QuestionText")
            cimke.setWordWrap(True)
            kerdes_layout.addWidget(cimke)

            if tipus == "single_choice":
                gomb_csoport = QButtonGroup(self)
                gomb_lista = []
                for opcio in kerdes_adat.get("options", []):
                    radio_btn = QRadioButton(opcio)
                    kerdes_layout.addWidget(radio_btn)
                    gomb_csoport.addButton(radio_btn)
                    gomb_lista.append(radio_btn)
                self.valasz_vezerlok[kerdes_id] = {"tipus": "single_choice", "gombok": gomb_lista}

            elif tipus == "multiple_choice":
                checkbox_lista = []
                for opcio in kerdes_adat.get("options", []):
                    chk_btn = QCheckBox(opcio)
                    kerdes_layout.addWidget(chk_btn)
                    checkbox_lista.append(chk_btn)
                self.valasz_vezerlok[kerdes_id] = {"tipus": "multiple_choice", "dobozok": checkbox_lista}
                
            elif tipus == "short_answer":
                beviteli_mezo = QLineEdit()
                beviteli_mezo.setObjectName("ShortAnswerInput")
                beviteli_mezo.setPlaceholderText("Írd ide a választ...")
                kerdes_layout.addWidget(beviteli_mezo)
                self.valasz_vezerlok[kerdes_id] = {"tipus": "short_answer", "mezo": beviteli_mezo}
                
            elif tipus == "matching":
                parok = kerdes_adat.get("pairs", {})
                bal_oldal = list(parok.keys())
                jobb_oldal_kevert = list(parok.values())
                random.shuffle(jobb_oldal_kevert)

                sorok_lista = []
                for bal_szo in bal_oldal:
                    sor_layout = QHBoxLayout()
                    sor_layout.addWidget(QLabel(f"<b>{bal_szo}</b>"))
                    combo = QComboBox()
                    combo.setObjectName("MatchingCombo")
                    combo.addItem("--- Válassz párt ---")
                    combo.addItems(jobb_oldal_kevert)
                    sor_layout.addWidget(combo)
                    kerdes_layout.addLayout(sor_layout)
                    sorok_lista.append({"bal_szoveg": bal_szo, "combo": combo})
                self.valasz_vezerlok[kerdes_id] = {"tipus": "matching", "sorok": sorok_lista}

            elif tipus == "ordering":
                helyes_sorrend = kerdes_adat.get("ordered_items", [])
                kevert_sorrend = helyes_sorrend.copy()
                random.shuffle(kevert_sorrend)
                
                combo_lista = []
                for i in range(len(helyes_sorrend)):
                    sor_layout = QHBoxLayout()
                    sor_layout.addWidget(QLabel(f"<b>{i+1}. hely:</b>"))
                    combo = QComboBox()
                    combo.setObjectName("OrderingCombo")
                    combo.addItem("--- Melyik jön ide? ---")
                    combo.addItems(kevert_sorrend)
                    sor_layout.addWidget(combo)
                    kerdes_layout.addLayout(sor_layout)
                    combo_lista.append(combo)
                self.valasz_vezerlok[kerdes_id] = {"tipus": "ordering", "combok": combo_lista}
            else:
                hibajel = QLabel(f"<i>(Ismeretlen feladattípus: '{tipus}')</i>")
                kerdes_layout.addWidget(hibajel)

            self.kviz_tartalom_layout.addWidget(kerdes_doboz)
            kerdes_szamlalo += 1
            
        self.kiertekel_gomb.setEnabled(True)
        self.kiertekel_gomb.show()
        self.eredmeny_cimke.hide()
        self.kviz_tartalom_layout.addStretch()

class KvizFutarSzal(QThread):
    kviz_kesz = pyqtSignal(list)
    hiba_torent = pyqtSignal(str)

    def __init__(self, raw_folder, pdf_neve, max_kerdes):
        super().__init__()
        self.raw_folder = raw_folder
        self.pdf_neve = pdf_neve
        self.max_kerdes = max_kerdes

    def run(self):
        try:
            generator = quiz_generator(self.raw_folder)
            kviz_json = generator.generalj_kvizt(self.pdf_neve, self.max_kerdes)
            self.kviz_kesz.emit(kviz_json)
        except Exception as e:
            self.hiba_torent.emit(str(e))