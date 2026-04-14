import json
from PyQt6.QtCore import QThread, pyqtSignal

from backend.chatbot import ChatBot
from backend.kviz_generator import KvizGenerator


# QThread: a PyQt6 beépített szálkezelője
# generálás idejére (ami az internetes API miatt több másodperc is lehet) leválasztja a folyamatot a főszálról
# ezzel biztosítja, hogy a grafikus felület ne fagyjon le a betöltés alatt
class KvizHatterszal(QThread):
    # pyqtSignal: kommunikációs csatornák (jelek), amelyeken keresztül a háttérszál üzeneteket tud küldeni a grafikus felületnek
    # kviz_kesz: egy listát (a kész JSON kvízt) fog küldeni, ha sikeres a generálás
    kviz_kesz = pyqtSignal(list)
    # hiba_tortent: egy szöveget (a hibaüzenetet) fog küldeni, ha valami elromlik
    hiba_tortent = pyqtSignal(str)

    def __init__(self, temakor_neve: str, pdf_neve: str, max_kerdes: int) -> None:
        # super().__init__() meghívja a szülőosztály (QThread) inicializáló metódusát
        super().__init__()
        
        # eltárolja a megkapott paramétereket a példányban (self)
        self.temakor_neve = temakor_neve
        self.pdf_neve = pdf_neve
        self.max_kerdes = max_kerdes
        
    # run() a QThread beépített metódusa
    # amikor a főprogram meghívja a .start() parancsot, ez a függvény automatikusan, egy külön háttérszálon fog elindulni
    def run(self) -> None:
        try:
            generator = KvizGenerator()
            kviz_json = generator.generalj_kvizt(self.temakor_neve, self.pdf_neve, self.max_kerdes)
            
            # .emit(): ha minden sikeres volt, elküldi a kviz_kesz jelet a grafikus felület felé, és átadja benne a legenerált kvíz adatait
            self.kviz_kesz.emit(kviz_json)

        except ValueError as hiba:
            # ha a megadott adatokkal volt gond, elküldi a hiba_tortent jelet a hibaüzenettel
            self.hiba_tortent.emit(f"Adathiba: {hiba}")
            
        except json.JSONDecodeError:
            # ha a Gemini API nem érvényes JSON formátumot adott vissza
            self.hiba_tortent.emit("Hiba történt a generált kvíz feldolgozásakor.")
        except ConnectionError:
            # ha nincs internet, vagy nem elérhető a Google szervere
            self.hiba_tortent.emit("Hálózati hiba: Nem sikerült kapcsolódni az AI szerveréhez.")
        except Exception as e:
            # általános hibafogó: minden egyéb, nem várt futási hibát elkap, megakadályozva a program összeomlását
            self.hiba_tortent.emit(f"Ismeretlen hiba történt a kvíz generálása során: {e}")

# QThread: a PyQt6 beépített szálkezelője
# generálás idejére (ami az internetes API miatt több másodperc is lehet) leválasztja a folyamatot a főszálról
# ezzel biztosítja, hogy a grafikus felület ne fagyjon le a betöltés alatt
class ChatbotHatterszal(QThread):
    # pyqtSignal: kommunikációs csatornák (jelek), amelyeken keresztül a háttérszál üzeneteket tud küldeni a grafikus felületnek
    valasz_megerkezett = pyqtSignal(str)
    # hiba_tortent: egy szöveget (a hibaüzenetet) fog küldeni, ha valami elromlik
    hiba_tortent = pyqtSignal(str)

    # inicializálja a szálat a szükséges adatokkal
    def __init__(self, kerdes: str, adatbazis_utvonal: str) -> None:
        # super().__init__() meghívja a szülőosztály (QThread) inicializáló metódusát
        super().__init__()
        # eltárolja a megkapott paramétereket a példányban (self)
        self.kerdes = kerdes
        self.adatbazis_utvonal = adatbazis_utvonal

    # run() a QThread beépített metódusa
    # amikor a főprogram meghívja a .start() parancsot, ez a függvény automatikusan, egy külön háttérszálon fog elindulni
    def run(self) -> None:
        try:
            bot = ChatBot(adatbazis_utvonal=self.adatbazis_utvonal)
            valasz = bot.kerdes_feltevese(self.kerdes)
            self.valasz_megerkezett.emit(valasz)
            
        except ValueError as ve:
            self.hiba_tortent.emit(f"Konfigurációs vagy adathiba: {ve}")
        except ConnectionError:
            self.hiba_tortent.emit("Hálózati hiba: Nem sikerült kapcsolódni a Google Gemini szervereihez.")
        except Exception as e:
            self.hiba_tortent.emit(f"Futási hiba történt a háttérfolyamatban: {e}")

# QThread: a PyQt6 beépített szálkezelője
# PDF-ek feldolgozása és vektorizálása idejére leválasztja a folyamatot a főszálról
# ezzel biztosítja, hogy a grafikus felület ne fagyjon le a betöltés alatt
class PdfHatterszal(QThread):
    # pyqtSignal: kommunikációs csatornák (jelek), amelyeken keresztül a háttérszál üzeneteket tud küldeni a grafikus felületnek
    # feldolgozas_kesz: egy jelzés, ami akkor fut le, ha a PDF beolvasása és mentése sikeresen befejeződött
    feldolgozas_kesz = pyqtSignal()
    # hiba_tortent: egy szöveget (a hibaüzenetet) fog küldeni, ha valami elromlik
    hiba_tortent = pyqtSignal(str)

    def __init__(self, backend, utvonal: str) -> None:
        # super().__init__() meghívja a szülőosztály (QThread) inicializáló metódusát
        super().__init__()
        # eltárolja a megkapott paramétereket a példányban (self)
        self.backend = backend
        self.utvonal = utvonal

    # run() a QThread beépített metódusa
    # amikor a főprogram meghívja a .start() parancsot, ez a függvény automatikusan, egy külön háttérszálon fog elindulni
    def run(self) -> None:
        try:
            self.backend.pdf_hozzadasa(self.utvonal)
            # .emit(): ha minden sikeres volt, elküldi a feldolgozas_kesz jelet a grafikus felület felé
            self.feldolgozas_kesz.emit()
        except Exception as e:
            # általános hibafogó: minden nem várt futási hibát elkap, és visszaküldi a hibaüzenetet a felületnek
            self.hiba_tortent.emit(f"Hiba a PDF feldolgozása során: {str(e)}")