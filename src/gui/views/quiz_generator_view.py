import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QSlider, QScrollArea,
    QFrame, QButtonGroup, QRadioButton, QCheckBox, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import random

from backend.quiz_generator import quiz_generator

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

class quiz_generator_view(QWidget):
    def __init__(self, temakor_neve):
        super().__init__()
        self.temakor_neve = temakor_neve
        self.mappa_utvonal = f"./data/subjects/{temakor_neve}/raw/"

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.hiba_cimke = QLabel("Nincs PDF feltöltve. Tölts fel egyet, mielőtt kvízt kérnél!")
        self.hiba_cimke.setStyleSheet("color: red; font-size: 16px; font-weight: bold;")
        self.hiba_cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hiba_cimke.hide()
        self.main_layout.addWidget(self.hiba_cimke)

        self.vezerlo_widget = QWidget()
        self.vezerlo_layout = QVBoxLayout(self.vezerlo_widget)

        pdf_sor = QHBoxLayout()
        pdf_sor.addWidget(QLabel("Válaszd ki a tananyagot (PDF):"))
        self.pdf_valaszto = QComboBox()
        self.pdf_valaszto.setStyleSheet("padding: 5px;")
        pdf_sor.addWidget(self.pdf_valaszto)
        pdf_sor.addStretch()
        self.vezerlo_layout.addLayout(pdf_sor)

        csuszka_sor = QHBoxLayout()
        csuszka_sor.addWidget(QLabel("Kérdések maximális száma:"))
        
        self.csuszka = QSlider(Qt.Orientation.Horizontal)
        self.csuszka.setMinimum(1)
        self.csuszka.setMaximum(50) # Max 50 kérdés
        self.csuszka.setValue(10)    # Alapból 10-esen áll
        self.csuszka.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.csuszka.setTickInterval(1)
        
        self.csuszka_ertek_cimke = QLabel("5")
        self.csuszka_ertek_cimke.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.csuszka.valueChanged.connect(lambda val: self.csuszka_ertek_cimke.setText(str(val)))

        csuszka_sor.addWidget(self.csuszka)
        csuszka_sor.addWidget(self.csuszka_ertek_cimke)
        csuszka_sor.addWidget(QLabel("db"))
        self.vezerlo_layout.addLayout(csuszka_sor)

        self.generalas_gomb = QPushButton("Kvíz Generálása a Geminivel")
        self.generalas_gomb.setStyleSheet("padding: 10px; background-color: #28a745; color: white; font-weight: bold; font-size: 14px; border-radius: 5px;")
        self.generalas_gomb.clicked.connect(self.kviz_inditasa)
        self.vezerlo_layout.addWidget(self.generalas_gomb)

        self.main_layout.addWidget(self.vezerlo_widget)

        self.info_cimke = QLabel()
        self.info_cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.info_cimke)
        self.info_cimke.hide()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: 1px solid #ccc; background-color: #fafafa; border-radius: 5px;")
        
        self.kviz_tartalom_widget = QWidget()
        self.kviz_tartalom_layout = QVBoxLayout(self.kviz_tartalom_widget)
        self.kviz_tartalom_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.kviz_tartalom_widget)
        self.main_layout.addWidget(self.scroll_area)
        self.scroll_area.hide()


    def showEvent(self, event):
        super().showEvent(event)
        
        self.pdf_valaszto.clear()
        van_pdf = False
        
        if os.path.exists(self.mappa_utvonal):
            for fajl in os.listdir(self.mappa_utvonal):
                if fajl.lower().endswith(".pdf"):
                    self.pdf_valaszto.addItem(fajl)
                    van_pdf = True

        if not van_pdf:
            self.hiba_cimke.show()
            self.vezerlo_widget.hide()
        else:
            self.hiba_cimke.hide()
            self.vezerlo_widget.show()

    def kviz_inditasa(self):
        kivalasztott_pdf = self.pdf_valaszto.currentText()
        if not kivalasztott_pdf:
            return
            
        max_k = self.csuszka.value()
        
        self.generalas_gomb.setEnabled(False)
        self.pdf_valaszto.setEnabled(False)
        self.csuszka.setEnabled(False)
        
        self.info_cimke.setText(f"A(z) {kivalasztott_pdf} elemzése folyamatban... Ez eltarthat egy darabig.")
        self.info_cimke.setStyleSheet("color: #0078D7; font-style: italic; font-size: 14px;")
        self.info_cimke.show()
        self.scroll_area.hide()
        
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
        self.info_cimke.setStyleSheet("color: red; font-weight: bold;")

    def kviz_megerkezett(self, kviz_json):
        self.ui_visszakapcsolasa()
        self.info_cimke.hide()
        self.scroll_area.show()
        
        self.kviz_kirajzolasa(kviz_json)

    def ui_visszakapcsolasa(self):
        """Visszakapcsolja a gombokat és csúszkákat."""
        self.generalas_gomb.setEnabled(True)
        self.pdf_valaszto.setEnabled(True)
        self.csuszka.setEnabled(True)

    def kviz_kirajzolasa(self, kviz_lista):
        self.jelenlegi_kviz_adatok = kviz_lista 
        
        self.valasz_vezerlok = {} 

        kerdes_szamlalo = 1

        for kerdes_adat in kviz_lista:
            tipus = kerdes_adat.get("type")
            kerdes_id = kerdes_adat.get("id", kerdes_szamlalo)

            kerdes_doboz = QFrame()
            kerdes_doboz.setStyleSheet("background-color: white; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 10px; padding: 15px;")
            kerdes_layout = QVBoxLayout(kerdes_doboz)

            kerdes_szoveg = kerdes_adat.get("question", kerdes_adat.get("instruction", "Kérdés?"))
            cimke = QLabel(f"<b>{kerdes_szamlalo}. {kerdes_szoveg}</b>")
            cimke.setStyleSheet("font-size: 16px; border: none;") 
            cimke.setWordWrap(True)
            kerdes_layout.addWidget(cimke)

            #egyvalasztos
            if tipus == "single_choice":
                gomb_csoport = QButtonGroup(self)
                gomb_lista = []

                for opcio in kerdes_adat.get("options", []):
                    radio_btn = QRadioButton(opcio)
                    radio_btn.setStyleSheet("font-size: 14px; border: none; padding: 5px;")
                    kerdes_layout.addWidget(radio_btn)
                    gomb_csoport.addButton(radio_btn)
                    gomb_lista.append(radio_btn)

                self.valasz_vezerlok[kerdes_id] = {"tipus": "single_choice", "gombok": gomb_lista}

            #tobbvalasztos
            elif tipus == "multiple_choice":
                checkbox_lista = []
                for opcio in kerdes_adat.get("options", []):
                    chk_btn = QCheckBox(opcio)
                    chk_btn.setStyleSheet("font-size: 14px; border: none; padding: 5px;")
                    kerdes_layout.addWidget(chk_btn)
                    checkbox_lista.append(chk_btn)

                self.valasz_vezerlok[kerdes_id] = {"tipus": "multiple_choice", "dobozok": checkbox_lista}
                
            #rovidvalasz
            elif tipus == "short_answer":
                beviteli_mezo = QLineEdit()
                beviteli_mezo.setPlaceholderText("Írd ide a választ...")
                beviteli_mezo.setStyleSheet("font-size: 14px; border: 1px solid #ccc; padding: 5px; border-radius: 4px;")
                kerdes_layout.addWidget(beviteli_mezo)
                
                self.valasz_vezerlok[kerdes_id] = {"tipus": "short_answer", "mezo": beviteli_mezo}
                
            #parositos
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
                    combo.addItem("--- Válassz párt ---")
                    combo.addItems(jobb_oldal_kevert)
                    combo.setStyleSheet("font-size: 14px; padding: 5px;")
                    sor_layout.addWidget(combo)
                    
                    kerdes_layout.addLayout(sor_layout)
                    sorok_lista.append({"bal_szoveg": bal_szo, "combo": combo})
                    
                self.valasz_vezerlok[kerdes_id] = {"tipus": "matching", "sorok": sorok_lista}

            #sorba rendezos
            elif tipus == "ordering":
                helyes_sorrend = kerdes_adat.get("ordered_items", [])
                kevert_sorrend = helyes_sorrend.copy()
                random.shuffle(kevert_sorrend)
                
                combo_lista = []
                for i in range(len(helyes_sorrend)):
                    sor_layout = QHBoxLayout()
                    sor_layout.addWidget(QLabel(f"<b>{i+1}. hely:</b>"))
                    
                    combo = QComboBox()
                    combo.addItem("--- Melyik jön ide? ---")
                    combo.addItems(kevert_sorrend)
                    combo.setStyleSheet("font-size: 14px; padding: 5px;")
                    sor_layout.addWidget(combo)
                    
                    kerdes_layout.addLayout(sor_layout)
                    combo_lista.append(combo)
                    
                self.valasz_vezerlok[kerdes_id] = {"tipus": "ordering", "combok": combo_lista}
            else:
                hibajel = QLabel(f"<i>(Ismeretlen feladattípus: '{tipus}')</i>")
                kerdes_layout.addWidget(hibajel)

            self.kviz_tartalom_layout.addWidget(kerdes_doboz)
            kerdes_szamlalo += 1

        self.kiertekel_gomb = QPushButton("Kvíz Beküldése és Értékelése")
        self.kiertekel_gomb.setStyleSheet("padding: 12px; background-color: #007bff; color: white; font-weight: bold; font-size: 16px; border-radius: 5px; margin-top: 20px;")
        self.kiertekel_gomb.clicked.connect(self.kviz_kiertekelese)
        self.kviz_tartalom_layout.addWidget(self.kiertekel_gomb)
        
        self.eredmeny_cimke = QLabel()
        self.eredmeny_cimke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.eredmeny_cimke.hide()
        self.kviz_tartalom_layout.addWidget(self.eredmeny_cimke)
        
        self.kviz_tartalom_layout.addStretch()

    def kviz_kiertekelese(self):
        """Végigmegy a kitöltött UI elemeken, és összeveti a JSON eredeti adataival."""
        ossz_pont = len(self.jelenlegi_kviz_adatok)
        elert_pont = 0
        
        self.kiertekel_gomb.setEnabled(False)

        for kerdes_adat in self.jelenlegi_kviz_adatok:
            kerdes_id = kerdes_adat.get("id")
            tipus = kerdes_adat.get("type")
            vezerlo_adat = self.valasz_vezerlok.get(kerdes_id)
            
            if not vezerlo_adat:
                continue

            if tipus == "single_choice":
                helyes_valasz = kerdes_adat.get("correct_answer")
                kivalasztva = None
                
                for btn in vezerlo_adat["gombok"]:
                    if btn.isChecked():
                        kivalasztva = btn.text()
                        
                    if btn.text() == helyes_valasz:
                        btn.setStyleSheet("font-size: 14px; border: none; padding: 5px; color: green; font-weight: bold;")
                    elif btn.isChecked() and btn.text() != helyes_valasz:
                        btn.setStyleSheet("font-size: 14px; border: none; padding: 5px; color: red; font-weight: bold; text-decoration: line-through;")
                
                if kivalasztva == helyes_valasz:
                    elert_pont += 1

            elif tipus == "multiple_choice":
                helyes_valaszok = set(kerdes_adat.get("correct_answers", []))
                kivalasztott_valaszok = set()
                
                for chk in vezerlo_adat["dobozok"]:
                    if chk.isChecked():
                        kivalasztott_valaszok.add(chk.text())
                        
                    if chk.text() in helyes_valaszok:
                        chk.setStyleSheet("font-size: 14px; border: none; padding: 5px; color: green; font-weight: bold;")
                    elif chk.isChecked() and chk.text() not in helyes_valaszok:
                        chk.setStyleSheet("font-size: 14px; border: none; padding: 5px; color: red; font-weight: bold; text-decoration: line-through;")

                if kivalasztott_valaszok == helyes_valaszok:
                    elert_pont += 1
                    
            elif tipus == "short_answer":
                elfogadott_kulcsszavak = [k.lower() for k in kerdes_adat.get("accepted_keywords", [])]
                beirt_szoveg = vezerlo_adat["mezo"].text().strip().lower()
                
                helyes = False
                for kulcsszo in elfogadott_kulcsszavak:
                    if kulcsszo in beirt_szoveg:
                        helyes = True
                        break
                        
                if helyes:
                    elert_pont += 1
                    vezerlo_adat["mezo"].setStyleSheet("font-size: 14px; border: 2px solid green; padding: 5px; border-radius: 4px; background-color: #e8f5e9;")
                else:
                    vezerlo_adat["mezo"].setStyleSheet("font-size: 14px; border: 2px solid red; padding: 5px; border-radius: 4px; background-color: #ffebee;")
                    vezerlo_adat["mezo"].setText(vezerlo_adat["mezo"].text() + f" (Helyes kulcsszavak: {', '.join(elfogadott_kulcsszavak)})")

            elif tipus == "matching":
                eredeti_parok = kerdes_adat.get("pairs", {})
                minden_jo = True
                
                for sor in vezerlo_adat["sorok"]:
                    bal_szo = sor["bal_szoveg"]
                    combo = sor["combo"]
                    valasztott = combo.currentText()
                    helyes_par = eredeti_parok.get(bal_szo)
                    
                    if valasztott == helyes_par:
                        combo.setStyleSheet("font-size: 14px; padding: 5px; border: 2px solid green; background-color: #e8f5e9;")
                    else:
                        minden_jo = False
                        combo.setStyleSheet("font-size: 14px; padding: 5px; border: 2px solid red; background-color: #ffebee;")

                        if valasztott != "--- Válassz párt ---":
                            combo.setItemText(combo.currentIndex(), f"Rossz! A jó: {helyes_par}")
                        
                if minden_jo:
                    elert_pont += 1

            elif tipus == "ordering":
                eredeti_sorrend = kerdes_adat.get("ordered_items", [])
                minden_jo = True
                
                for i, combo in enumerate(vezerlo_adat["combok"]):
                    valasztott = combo.currentText()
                    helyes_elem = eredeti_sorrend[i]
                    
                    if valasztott == helyes_elem:
                        combo.setStyleSheet("font-size: 14px; padding: 5px; border: 2px solid green; background-color: #e8f5e9;")
                    else:
                        minden_jo = False
                        combo.setStyleSheet("font-size: 14px; padding: 5px; border: 2px solid red; background-color: #ffebee;")
                        if valasztott != "--- Melyik jön ide? ---":
                            combo.setItemText(combo.currentIndex(), f"Rossz! Ide ez jött volna: {helyes_elem}")
                        
                if minden_jo:
                    elert_pont += 1

        szazalek = (elert_pont / ossz_pont) * 100 if ossz_pont > 0 else 0
        
        if szazalek == 100:
            szin = "green"
            szoveg = "Hibátlan munka!"
        elif szazalek >= 60:
            szin = "orange"
            szoveg = "Szép eredmény, de van még mit tanulni!"
        else:
            szin = "red"
            szoveg = "Ezt még át kell ismételned!"

        self.eredmeny_cimke.setText(f"<h1>Eredményed: {elert_pont} / {ossz_pont} ({szazalek:.0f}%)</h1><h2 style='color: {szin};'>{szoveg}</h2>")
        self.eredmeny_cimke.show()
        
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())