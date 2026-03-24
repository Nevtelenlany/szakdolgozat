import random
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QRadioButton, QButtonGroup, QCheckBox, 
                             QLineEdit, QComboBox, QWidget)

class BaseQuestionWidget(QFrame):
    def __init__(self, kerdes_adat: dict, sorszam: int) -> None:
        super().__init__()
        self.kerdes_adat = kerdes_adat
        self.kerdes_id = kerdes_adat.get("id")
        self.setObjectName("QuestionFrame")
        
        self.layout = QVBoxLayout(self)
        self._setup_header(sorszam)
        self.setup_ui()

    def _setup_header(self, sorszam: int) -> None:
        kerdes_szoveg = self.kerdes_adat.get("question", self.kerdes_adat.get("instruction", "Kérdés?"))
        cimke = QLabel(f"<b>{sorszam}. {kerdes_szoveg}</b>")
        cimke.setObjectName("QuestionText")
        cimke.setWordWrap(True)
        self.layout.addWidget(cimke)

    def setup_ui(self) -> None:
        pass

    def get_user_answer(self) -> any:
        pass

    def apply_feedback(self, eredmeny_adat: dict) -> None:
        pass

    def set_feedback_style(self, widget: QWidget, status: str) -> None:
        widget.setProperty("feedback", status)
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _mutasd_a_magyarazatot(self, eredmeny_adat: dict) -> None:
        if not eredmeny_adat["helyes"]:
            magyarazat_szoveg = eredmeny_adat["feedback"].get("explanation", "")
            magyarazat_cimke = QLabel(f"<b>Magyarázat:</b> {magyarazat_szoveg}")
            magyarazat_cimke.setObjectName("EmptyText2")
            magyarazat_cimke.setWordWrap(True)
            self.layout.addWidget(magyarazat_cimke)

class SingleChoiceWidget(BaseQuestionWidget):
    def setup_ui(self) -> None:
        self.gomb_csoport = QButtonGroup(self)
        self.gombok = []
        for opcio in self.kerdes_adat.get("options", []):
            radio_btn = QRadioButton(opcio)
            self.layout.addWidget(radio_btn)
            self.gomb_csoport.addButton(radio_btn)
            self.gombok.append(radio_btn)

    def get_user_answer(self) -> str | None:
        return next((btn.text() for btn in self.gombok if btn.isChecked()), None)

    def apply_feedback(self, eredmeny_adat: dict) -> None:
        helyes_valasz = eredmeny_adat["feedback"]["correct_answer"]
        self._apply_styles_to_buttons(helyes_valasz)
        self._mutasd_a_magyarazatot(eredmeny_adat)

    def _apply_styles_to_buttons(self, helyes_valasz: str) -> None:
        for btn in self.gombok:
            if btn.text() == helyes_valasz:
                self.set_feedback_style(btn, "correct")
            elif btn.isChecked():
                self.set_feedback_style(btn, "wrong")

class MultipleChoiceWidget(BaseQuestionWidget):
    def setup_ui(self) -> None:
        self.dobozok = []
        for opcio in self.kerdes_adat.get("options", []):
            chk_btn = QCheckBox(opcio)
            self.layout.addWidget(chk_btn)
            self.dobozok.append(chk_btn)

    def get_user_answer(self) -> list[str]:
        return [chk.text() for chk in self.dobozok if chk.isChecked()]

    def apply_feedback(self, eredmeny_adat: dict) -> None:
        helyes_valaszok = eredmeny_adat["feedback"]["correct_answers"]
        self._apply_styles_to_checkboxes(helyes_valaszok)
        self._mutasd_a_magyarazatot(eredmeny_adat)

    def _apply_styles_to_checkboxes(self, helyes_valaszok: list[str]) -> None:
        for chk in self.dobozok:
            if chk.text() in helyes_valaszok:
                self.set_feedback_style(chk, "correct")
            elif chk.isChecked():
                self.set_feedback_style(chk, "wrong")


class ShortAnswerWidget(BaseQuestionWidget):
    def setup_ui(self) -> None:
        self.beviteli_mezo = QLineEdit()
        self.beviteli_mezo.setObjectName("ShortAnswerInput")
        self.beviteli_mezo.setPlaceholderText("Írd ide a választ...")
        self.layout.addWidget(self.beviteli_mezo)

    def get_user_answer(self) -> str:
        return self.beviteli_mezo.text()

    def apply_feedback(self, eredmeny_adat: dict) -> None:
        self._update_input_field(eredmeny_adat)
        self._mutasd_a_magyarazatot(eredmeny_adat)

    def _update_input_field(self, eredmeny_adat: dict) -> None:
        if eredmeny_adat["helyes"]:
            self.set_feedback_style(self.beviteli_mezo, "correct")
        else:
            self.set_feedback_style(self.beviteli_mezo, "wrong")
            kulcsszavak = ", ".join(eredmeny_adat["feedback"].get("accepted_keywords", []))
            self.beviteli_mezo.setText(self.beviteli_mezo.text() + f" (Helyes: {kulcsszavak})")

class MatchingWidget(BaseQuestionWidget):
    def setup_ui(self) -> None:
        parok = self.kerdes_adat.get("pairs", {})
        bal_oldal = list(parok.keys())
        jobb_oldal_kevert = list(parok.values())
        random.shuffle(jobb_oldal_kevert)

        self.sorok = []
        for bal_szo in bal_oldal:
            sor_layout = QHBoxLayout()
            sor_layout.addWidget(QLabel(f"<b>{bal_szo}</b>"))
            
            combo = QComboBox()
            combo.setObjectName("MatchingCombo")
            combo.addItem("--- Válassz párt ---")
            combo.addItems(jobb_oldal_kevert)
            
            sor_layout.addWidget(combo)
            self.layout.addLayout(sor_layout)
            self.sorok.append({"bal_szoveg": bal_szo, "combo": combo})

    def get_user_answer(self) -> dict:
        return {sor["bal_szoveg"]: sor["combo"].currentText() for sor in self.sorok}

    def apply_feedback(self, eredmeny_adat: dict) -> None:
        eredeti_parok = eredmeny_adat["feedback"]["pairs"]
        self._update_comboboxes(eredeti_parok)
        self._mutasd_a_magyarazatot(eredmeny_adat)

    def _update_comboboxes(self, eredeti_parok: dict) -> None:
        for sor in self.sorok:
            combo = sor["combo"]
            helyes_par = eredeti_parok.get(sor["bal_szoveg"])
            
            if combo.currentText() == helyes_par:
                self.set_feedback_style(combo, "correct")
            else:
                self.set_feedback_style(combo, "wrong")
                if combo.currentText() != "--- Válassz párt ---":
                    combo.setItemText(combo.currentIndex(), f"Rossz! A helyes: {helyes_par}")

class OrderingWidget(BaseQuestionWidget):
    def setup_ui(self) -> None:
        helyes_sorrend = self.kerdes_adat.get("ordered_items", [])
        kevert_sorrend = helyes_sorrend.copy()
        random.shuffle(kevert_sorrend)
        
        self.combok = []
        for i in range(len(helyes_sorrend)):
            sor_layout = QHBoxLayout()
            sor_layout.addWidget(QLabel(f"<b>{i+1}. hely:</b>"))
            
            combo = QComboBox()
            combo.setObjectName("OrderingCombo")
            combo.addItem("--- Melyik jön ide? ---")
            combo.addItems(kevert_sorrend)
            
            sor_layout.addWidget(combo)
            self.layout.addLayout(sor_layout)
            self.combok.append(combo)

    def get_user_answer(self) -> list[str]:
        return [combo.currentText() for combo in self.combok]

    def apply_feedback(self, eredmeny_adat: dict) -> None:
        eredeti_sorrend = eredmeny_adat["feedback"]["ordered_items"]
        self._update_comboboxes(eredeti_sorrend)
        self._mutasd_a_magyarazatot(eredmeny_adat)

    def _update_comboboxes(self, eredeti_sorrend: list[str]) -> None:
        for i, combo in enumerate(self.combok):
            helyes_elem = eredeti_sorrend[i]
            if combo.currentText() == helyes_elem:
                self.set_feedback_style(combo, "correct")
            else:
                self.set_feedback_style(combo, "wrong")
                if combo.currentText() != "--- Melyik jön ide? ---":
                    combo.setItemText(combo.currentIndex(), f"Rossz! Ide ez jött volna: {helyes_elem}")

WIDGET_REGISTRY = {
    "single_choice": SingleChoiceWidget,
    "multiple_choice": MultipleChoiceWidget,
    "short_answer": ShortAnswerWidget,
    "matching": MatchingWidget,
    "ordering": OrderingWidget
}