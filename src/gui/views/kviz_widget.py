import random
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QRadioButton, QButtonGroup, QCheckBox, 
                             QLineEdit, QComboBox, QWidget)

class KvizWidget(QFrame):
    def __init__(self, kerdes_adat: dict, sorszam: int) -> None:
        # super().__init__() meghívja a szülőosztály (QFrame) inicializáló metódusát
        super().__init__()
        self.kerdes_adat = kerdes_adat
        self.kerdes_id = kerdes_adat.get("id")

        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.setObjectName("QuestionFrame")
        
        # QVBoxLayout: függőlegesen egymás alá rendezi a benne elhelyezett elemeket (widgeteket)
        self.elrendezes = QVBoxLayout(self)

        self._fejlec_beallitasa(sorszam)
        self._felulet_beallitasa()

    def _fejlec_beallitasa(self, sorszam: int) -> None:
        # lekéri a kérdés szövegét a JSON-ből.
        # a .get() először a "question" kulcsot keresi
        # ha az nincs (pl. párosítós feladatnál), akkor az "instruction" kulcsot, végső esetben pedig a "Kérdés?" szöveget adja vissza
        kerdes_szoveg = self.kerdes_adat.get("question", self.kerdes_adat.get("instruction", "Kérdés?"))
        
        # QLabel: megjeleníti a szöveget a felületen
        # <b> HTML tag segítségével vastagon jeleníti meg a sorszámot és a kérdést
        cimke = QLabel(f"<b>{sorszam}. {kerdes_szoveg}</b>")

        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        cimke.setObjectName("QuestionText")
        
        # setWordWrap(True): engedélyezi a szövegnek a sortörést, ha a kérdés túl hosszú lenne és nem férne ki egyetlen sorba
        cimke.setWordWrap(True)
        
        # hozzáadja a címkét az elrendezéshez
        self.elrendezes.addWidget(cimke)

    def _felulet_beallitasa(self) -> None:
        # alapértelmezett (üres) metódus, amit a leszármazott osztályok fognak felülírni (polimorfizmus)
        # minden feladattípus (pl. rádiógombos, párosítós) itt építi fel a saját gombjait
        pass

    def felhasznalo_valaszanak_lekerese(self) -> any:
        # üres metódus a válasz lekérésére. A leszármazottak felülírják, és visszaadják a beírt/kiválasztott értéket
        pass

    def visszajelzes_alkalmazasa(self, eredmeny_adat: dict) -> None:
        # üres metódus a kiértékelés utáni UI frissítésére (piros/zöld színezés). A leszármazottak felülírják
        pass

    def _visszajelzes_stilus_beallitasa(self, widget: QWidget, statusz: str) -> None:
        # setProperty: beállítja a felületi elem (widget) egyedi "feedback" tulajdonságát 
        # pontosan arra az értékre, amit a 'statusz' paraméterben megkapott (pl. "correct" vagy "wrong")
        # ez alapján fogja a QSS a megfelelő színeket (zöld vagy piros állapotot) alkalmazni
        widget.setProperty("feedback", statusz)
        # unpolish: eltávolítja a widgetről a jelenleg érvényes stíluslap (QSS) beállításait
        widget.style().unpolish(widget)
        # polish: újraalkalmazza a stíluslapot
        # beolvassa az új "feedback" értéket, és frissíti a widget megjelenését a képernyőn
        widget.style().polish(widget)

    def _magyarazat_megjelenitese(self, eredmeny_adat: dict) -> None:
        # ha a felhasználó válasza nem volt helyes (False)
        if not eredmeny_adat["helyes"]:
            # a kiértékelőtől kapott "feedback" egy belső szótár, ami a részleteket tartalmazza
            # ebből lekéri a magyarázatot ("explanation" kulcs), ha pedig nincs, egy üres stringet ("") ad vissza
            magyarazat_szoveg = eredmeny_adat["feedback"].get("explanation", "")
            # QLabel: megjeleníti a szöveget a felületen
            # a <b> HTML tag segítségével vastagon jeleníti meg a "Magyarázat:" szót
            magyarazat_cimke = QLabel(f"<b>Magyarázat:</b> {magyarazat_szoveg}")
            # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
            magyarazat_cimke.setObjectName("EmptyText2")
            # setWordWrap(True): engedélyezi a szövegnek a sortörést, ha a magyarázat túl hosszú lenne és nem férne ki egyetlen sorba
            magyarazat_cimke.setWordWrap(True)
            # hozzáadja a magyarázatot tartalmazó címkét az elrendezéshez
            self.elrendezes.addWidget(magyarazat_cimke)

class EgyvalaszosWidget(KvizWidget):
    def _felulet_beallitasa(self) -> None:
        # QButtonGroup: ez biztosítja, hogy a kérdésen belül egyszerre csak egyetlen válasz lehessen bejelölve
        self.gomb_csoport = QButtonGroup(self)
        self.gombok = []
        
        # végigmegy a kérdéshez tartozó lehetséges válaszlehetőségeken (opciókon) a JSON-ből
        for opcio in self.kerdes_adat.get("options", []):
            # QRadioButton: létrehoz egy kiválasztható, kör alakú rádiógombot a válasz szövegével
            radio_gomb = QRadioButton(opcio)
            
            # hozzáadja az aktuálisan létrehozott gombot az elrendezéshez
            self.elrendezes.addWidget(radio_gomb)
            # hozzáadja a csoporthoz is az egyedi kiválasztás biztosítása miatt
            self.gomb_csoport.addButton(radio_gomb)
            # eltárolja a gombot egy listában, hogy később a kiértékelésnél könnyen végig lehessen menni rajtuk
            self.gombok.append(radio_gomb)

    def felhasznalo_valaszanak_lekerese(self) -> str | None:
        # next(): végigmegy a listán, és azonnal visszaadja a legelső olyan elemet, ami megfelel a feltételnek
        # isChecked(): megnézi, hogy az adott rádiógomb be van-e jelölve a felületen
        # text(): ha megtalálta a bejelölt gombot, kiolvassa és visszaadja a rajta lévő feliratot (magát a választ)
        return next((gomb.text() for gomb in self.gombok if gomb.isChecked()), None)
    
    def visszajelzes_alkalmazasa(self, eredmeny_adat: dict) -> None:
        # kiolvassa a belső "feedback" szótárból a ténylegesen helyes választ
        helyes_valasz = eredmeny_adat["feedback"]["correct_answer"]
        self._gombok_stilusanak_beallitasa(helyes_valasz)
        self._magyarazat_megjelenitese(eredmeny_adat)

    def _gombok_stilusanak_beallitasa(self, helyes_valasz: str) -> None:
        # végigmegy a kérdéshez tartozó összes rádiógombon
        for gomb in self.gombok:
            # ha a gomb felirata megegyezik a helyes válasszal, zöldre ("correct") színezi
            # (ezt akkor is zöldre színezi, ha a felhasználó nem ezt jelölte be, hogy lássa, mi lett volna a jó)
            # text(): ha megtalálta a bejelölt gombot, kiolvassa és visszaadja a rajta lévő feliratot (magát a választ)
            if gomb.text() == helyes_valasz:
                self._visszajelzes_stilus_beallitasa(gomb, "correct")
            elif gomb.isChecked():
                self._visszajelzes_stilus_beallitasa(gomb, "wrong")

class TobbvalaszosWidget(KvizWidget):
    def _felulet_beallitasa(self) -> None:
        self.dobozok = []
        
        # végigmegy a kérdéshez tartozó lehetséges opciókon (válaszokon) a JSON-ből
        for opcio in self.kerdes_adat.get("options", []):
            # QCheckBox: olyan jelölőnégyzetet hoz létre, amiből a felhasználó többet is kiválaszthat egyszerre
            jelolo_negyzet = QCheckBox(opcio)
            # hozzáadja az aktuális jelölőnégyzetet a függőleges elrendezéshez
            self.elrendezes.addWidget(jelolo_negyzet)
            # eltárolja a jelölőnégyzetet a listában a későbbi kiértékeléshez
            self.dobozok.append(jelolo_negyzet)

    def felhasznalo_valaszanak_lekerese(self) -> list[str]:
        # ez a sor végigmegy az összes jelölőnégyzeten (self.dobozok)
        # ha a doboz be van jelölve (isChecked()), akkor a rajta lévő szöveget (text()) beteszi egy listába
        return [doboz.text() for doboz in self.dobozok if doboz.isChecked()]

    def visszajelzes_alkalmazasa(self, eredmeny_adat: dict) -> None:
        # kiolvassa a belső "feedback" szótárból a helyes válaszok listáját
        # (mivel több jó válasz is lehet, ez egy lista kulcsszavakkal/mondatokkal)
        helyes_valaszok = eredmeny_adat["feedback"]["correct_answers"]
        self._jelolonegyzetek_stilusanak_beallitasa(helyes_valaszok)
        self._magyarazat_megjelenitese(eredmeny_adat)

    def _jelolonegyzetek_stilusanak_beallitasa(self, helyes_valaszok: list[str]) -> None:
        # végigmegy a kérdéshez tartozó összes jelölőnégyzeten
        for doboz in self.dobozok:
            # megnézi, hogy az adott jelölőnégyzet szövege szerepel-e a helyes válaszok listájában
            if doboz.text() in helyes_valaszok:
                # ha igen, zöldre ("correct") színezi
                self._visszajelzes_stilus_beallitasa(doboz, "correct")
            # ha a doboz nincs a helyesek között, de a felhasználó bepipálta, pirosra ("wrong") színezi
            elif doboz.isChecked():
                self._visszajelzes_stilus_beallitasa(doboz, "wrong")

class RovidValaszWidget(KvizWidget):
    def _felulet_beallitasa(self) -> None:
        # QLineEdit: egyetlen soros szövegbeviteli mezőt hoz létre a rövid válasznak
        self.beviteli_mezo = QLineEdit()
        # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
        self.beviteli_mezo.setObjectName("ShortAnswerInput")
        # setPlaceholderText: halvány szürke szöveg, ami eltűnik, amint a felhasználó gépelni kezd
        self.beviteli_mezo.setPlaceholderText("Írd ide a választ...")
        # hozzáadja a beviteli mezőt a függőleges elrendezéshez
        self.elrendezes.addWidget(self.beviteli_mezo)

    def felhasznalo_valaszanak_lekerese(self) -> str:
        # visszaadja azt a szöveget, amit a felhasználó beírt a mezőbe
        return self.beviteli_mezo.text()

    def visszajelzes_alkalmazasa(self, eredmeny_adat: dict) -> None:
        self._beviteli_mezo_frissitese(eredmeny_adat)
        self._magyarazat_megjelenitese(eredmeny_adat)
        
    def _beviteli_mezo_frissitese(self, eredmeny_adat: dict) -> None:
        if eredmeny_adat["helyes"]:
            self._visszajelzes_stilus_beallitasa(self.beviteli_mezo, "correct")
        else:
            self._visszajelzes_stilus_beallitasa(self.beviteli_mezo, "wrong")
            # .join() egy vesszővel elválasztott szöveggé fűzi össze a listát
            # eredmeny_adat szótárból kiveszi a "feedback" kulcshoz tartozó értéket (ami szintén egy szótár)
            # majd ebből kiveszi az "accepted_keywords" kulcshoz tartozó értéket, de ha az nem létezik, akkor egy üres listát ([]) ad vissza
            kulcsszavak = ", ".join(eredmeny_adat["feedback"].get("accepted_keywords", []))
            self.beviteli_mezo.setText(self.beviteli_mezo.text() + f" (Helyes: {kulcsszavak})")

class ParositosWidget(KvizWidget):
    def _felulet_beallitasa(self) -> None:
        # lekéri a JSON-ből a "pairs" (párok) szótárat, ha nincs, üres szótárat ad vissza
        parok = self.kerdes_adat.get("pairs", {})
        # a szótár kulcsai alkotják a bal oldalt (pl. fogalmak), ezek fix sorrendben maradnak
        bal_oldal = list(parok.keys())
        # a szótár értékei alkotják a jobb oldalt (pl. definíciók), ezek kerülnek a legördülő menübe
        jobb_oldal_kevert = list(parok.values())
        # a random.shuffle() összekeveri a listát, hogy a helyes válaszok ne mindig ugyanabban a sorrendben legyenek a menüben
        random.shuffle(jobb_oldal_kevert)
        # ez a lista fogja tárolni az egyes sorok adatait a későbbi kiértékeléshez
        self.sorok = []
        
        for bal_szo in bal_oldal:
            # QHBoxLayout: vízszintesen egymás mellé helyezi a bal oldali szöveget és a legördülő menüt
            sor_elrendezes = QHBoxLayout()
            # QLabel: megjeleníti a szöveget a felületen
            # a <b> HTML tag segítségével vastagon jeleníti meg a szót
            # addWidget: hozzáadja a vastagított bal oldali szöveget az adott sor elrendezéséhez
            sor_elrendezes.addWidget(QLabel(f"<b>{bal_szo}</b>"))
            # QComboBox: legördülő menüt hoz létre a jobb oldali (kevert) válaszlehetőségeknek
            legordulo_menu = QComboBox()
            # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
            legordulo_menu.setObjectName("MatchingCombo")
            # addItem: betesz egy alapértelmezett szöveget a menü legtetejére
            legordulo_menu.addItem("--- Válassz párt ---")
            # addItems: hozzáadja a teljes összekevert válaszlistát a menühöz
            legordulo_menu.addItems(jobb_oldal_kevert)
            # addWidget: hozzáadja a kész legördülő menüt a sor vízszintes elrendezéséhez
            sor_elrendezes.addWidget(legordulo_menu)
            # a vízszintes sort (szöveg + menü) hozzáadja az ősosztály fő, függőleges elrendezéséhez
            self.elrendezes.addLayout(sor_elrendezes)
            # eltárolja a bal oldali szöveget és a hozzá tartozó menü objektumot a listában
            self.sorok.append({"bal_szoveg": bal_szo, "legordulo_menu": legordulo_menu})

    def felhasznalo_valaszanak_lekerese(self) -> dict:
        # visszaad egy szótárat (dictionary), ami összeköti a fogalmakat a felhasználó által kiválasztott elemekkel
        # végigmegy a self.sorok listán (amiben a bal oldali szövegeket és a legördülő menüket tároltuk)
        # és kulcs-érték párokat hoz létre: a kulcs a bal oldali szöveg, az érték pedig a legördülő menüben kiválasztott szöveg (.currentText())
        return {sor["bal_szoveg"]: sor["legordulo_menu"].currentText() for sor in self.sorok}

    def visszajelzes_alkalmazasa(self, eredmeny_adat: dict) -> None:
        # kiolvassa a belső "feedback" szótárból az eredeti, helyes párosításokat
        eredeti_parok = eredmeny_adat["feedback"]["pairs"]
        # meghívja az alatta lévő segédmetódust, ami zöldre vagy pirosra színezi a menüket az eredmény alapján
        self._legordulo_menuk_frissitese(eredeti_parok)
        # meghívja az ősosztályból örökölt metódust, ami kiírja a magyarázatot a felületre, ha hibás volt a válasz
        self._magyarazat_megjelenitese(eredmeny_adat)
        
    def _legordulo_menuk_frissitese(self, eredeti_parok: dict) -> None:
        # végigmegy a felületen létrehozott sorokon (ahol a fogalmak és a menük vannak)
        for sor in self.sorok:
            # kiveszi az aktuális sorhoz tartozó legördülő menüt a szótárból
            legordulo_menu = sor["legordulo_menu"]
            # lekéri a kiértékelőtől kapott szótárból (eredeti_parok), hogy ehhez a bal oldali szöveghez mi a helyes pár
            helyes_par = eredeti_parok.get(sor["bal_szoveg"])
            
            # ellenőrzi, hogy a felhasználó által kiválasztott szöveg megegyezik-e a helyessel
            # a .currentText() visszaadja azt, amit a felhasználó kiválasztott
            if legordulo_menu.currentText() == helyes_par:
                # ha igen, zöldre ("correct") színezi a menüt az ősosztály metódusával
                self._visszajelzes_stilus_beallitasa(legordulo_menu, "correct")
            else:
                # ha nem, pirosra ("wrong") színezi a menüt
                self._visszajelzes_stilus_beallitasa(legordulo_menu, "wrong")
                # ha a felhasználó választott valamit (tehát nem az alapértelmezett "--- Válassz párt ---" maradt bent),
                # akkor a kiválasztott elem szövegét átírja úgy, hogy mutassa a helyes választ is
                # a .currentText() visszaadja azt, amit a felhasználó kiválasztott
                if legordulo_menu.currentText() != "--- Válassz párt ---":
                    legordulo_menu.setItemText(legordulo_menu.currentIndex(), f"Rossz! A helyes: {helyes_par}")

class SorbarendezosWidget(KvizWidget):
    def _felulet_beallitasa(self) -> None:
        # lekéri a JSON-ből a helyes sorrendet tartalmazó listát, ha nincs, egy üres listát ad vissza
        helyes_sorrend = self.kerdes_adat.get("ordered_items", [])
        # a .copy() másolatot készít a listáról, hogy az összekeverés során az eredeti (helyes) sorrend ne vesszen el
        kevert_sorrend = helyes_sorrend.copy()
        # a random.shuffle() összekeveri a másolt lista elemeit
        random.shuffle(kevert_sorrend)
        # ez a lista fogja tárolni a felületen létrehozott legördülő menüket a későbbi kiértékeléshez
        self.menuk = []
        # a range(len(...)) segítségével pontosan annyiszor fut le a ciklus, ahány elem van a sorrendben
        # az 'i' a ciklusváltozó, ami 0-tól indul
        for i in range(len(helyes_sorrend)):
            # QHBoxLayout: vízszintesen egymás mellé helyezi a sorszámot és a legördülő menüt
            sor_elrendezes = QHBoxLayout()
            # QLabel: megjeleníti a sorszámot a felületen
            # a <b> HTML tag segítségével vastagon jeleníti meg a szöveget
            # addWidget: hozzáadja a címkét a vízszintes elrendezéshez
            sor_elrendezes.addWidget(QLabel(f"<b>{i+1}. hely:</b>"))

            # QComboBox: legördülő menüt hoz létre az összekevert válaszlehetőségeknek
            legordulo_menu = QComboBox()
            # setObjectName: ez alapján lehet hivatkozni rá a stíluslapokban (QSS)
            legordulo_menu.setObjectName("OrderingCombo")
            # addItem: betesz egy alapértelmezett szöveget a menü legtetejére
            legordulo_menu.addItem("--- Melyik jön ide? ---")
            # addItems: hozzáadja a teljes összekevert válaszlistát a menühöz
            legordulo_menu.addItems(kevert_sorrend)
            
            # addWidget: hozzáadja a legördülő menüt a sor vízszintes elrendezéséhez
            sor_elrendezes.addWidget(legordulo_menu)
            # addLayout: a vízszintes sort hozzáadja az ősosztály fő, függőleges elrendezéséhez
            self.elrendezes.addLayout(sor_elrendezes)
            
            # eltárolja a legördülő menü objektumot a listában a későbbi kiértékeléshez
            self.menuk.append(legordulo_menu)

    def felhasznalo_valaszanak_lekerese(self) -> list[str]:
        # visszaadja sorrendben a felhasználó által kiválasztott elemeket egy listában
        # végigmegy a felületen létrehozott legördülő menükön (amiket a self.menuk listában tároltunk),
        # és a .currentText() segítségével kiolvassa belőlük az éppen kiválasztott szöveget
        return [legordulo_menu.currentText() for legordulo_menu in self.menuk]

    def visszajelzes_alkalmazasa(self, eredmeny_adat: dict) -> None:
        # kiolvassa a belső "feedback" szótárból az eredeti, helyes sorrendet tartalmazó listát
        eredeti_sorrend = eredmeny_adat["feedback"]["ordered_items"]
        self._legordulo_menuk_frissitese(eredeti_sorrend)
        self._magyarazat_megjelenitese(eredmeny_adat)
        
    def _legordulo_menuk_frissitese(self, eredeti_sorrend: list[str]) -> None:
        # enumerate: végigmegy a listán, és egyszerre adja vissza a sorszámot (i) és magát a legördülő menüt
        for i, legordulo_menu in enumerate(self.menuk):
            # az eredeti_sorrend listából a sorszám (i) alapján kikeresi, hogy mi lett volna a helyes elem az adott helyre
            helyes_elem = eredeti_sorrend[i]
            
            # ellenőrzi, hogy a felhasználó által kiválasztott szöveg megegyezik-e a helyessel
            # a .currentText() visszaadja azt, amit a felhasználó kiválasztott
            if legordulo_menu.currentText() == helyes_elem:
                # ha igen, zöldre ("correct") színezi a menüt az ősosztály metódusával
                self._visszajelzes_stilus_beallitasa(legordulo_menu, "correct")
            else:
                # ha nem, pirosra ("wrong") színezi a menüt
                self._visszajelzes_stilus_beallitasa(legordulo_menu, "wrong")
                # ha a felhasználó választott valamit (tehát nem az alapértelmezett "--- Melyik jön ide? ---" maradt bent),
                # akkor a kiválasztott elem szövegét átírja úgy, hogy mutassa a helyes választ is
                if legordulo_menu.currentText() != "--- Melyik jön ide? ---":
                    legordulo_menu.setItemText(legordulo_menu.currentIndex(), f"Rossz! Ide ez jött volna: {helyes_elem}")

# szótár, ami összeköti a JSON-ben kapott angol kérdéstípusokat a megfelelő widget (felületi elem) osztályokkal
WIDGET_REGISZTER = {
    "single_choice": EgyvalaszosWidget,
    "multiple_choice": TobbvalaszosWidget,
    "short_answer": RovidValaszWidget,
    "matching": ParositosWidget,
    "ordering": SorbarendezosWidget
}