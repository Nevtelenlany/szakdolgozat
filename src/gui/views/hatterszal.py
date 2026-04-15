import json
import threading
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

        except RuntimeError as e:
            # ezt a hibát dobja a generátor, ha a modellek elérhetetlenek, vagy kimerült a napi API kvóta
            self.hiba_tortent.emit(str(e))

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
            # csupa kisbetűssé alakítjuk a biztonságosabb keresés érdekében
            hiba_uzenet = str(e).lower() 
            
            # kiszűri az érvénytelen API kulcs miatti hibákat
            if "api key" in hiba_uzenet or "api_key" in hiba_uzenet or "400" in hiba_uzenet or "403" in hiba_uzenet:
                self.hiba_tortent.emit("Érvénytelen API kulcs! Kérlek, ellenőrizd a megadott GOOGLE_API_KEY-t a .env fájlban.")
            # kiszűri a nyers hálózati hibákat
            elif "11001" in hiba_uzenet or "getaddrinfo" in hiba_uzenet or "nameresolutionerror" in hiba_uzenet:
                self.hiba_tortent.emit("Nincs internetkapcsolat! Kérlek, ellenőrizd a hálózatot, majd próbáld újra.")      
            # minden egyéb, nem várt futási hibát elkap
            else:
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
            # ha nincs internet, vagy nem elérhető a Google szervere
            self.hiba_tortent.emit("Hálózati hiba: Nem sikerült kapcsolódni az AI szerveréhez.")
        except Exception as e:
            # csupa kisbetűssé alakítjuk a biztonságosabb keresés érdekében
            hiba_uzenet = str(e).lower() 
            
            # kiszűri az érvénytelen API kulcs miatti hibákat
            if "api key" in hiba_uzenet or "api_key" in hiba_uzenet or "400" in hiba_uzenet or "403" in hiba_uzenet:
                self.hiba_tortent.emit("Érvénytelen API kulcs! Kérlek, ellenőrizd a megadott GOOGLE_API_KEY-t a .env fájlban.")
            # kiszűri a nyers hálózati hibákat
            elif "11001" in hiba_uzenet or "getaddrinfo" in hiba_uzenet or "nameresolutionerror" in hiba_uzenet:
                self.hiba_tortent.emit("Nincs internetkapcsolat! Kérlek, ellenőrizd a hálózatot, majd próbáld újra.")      
            # minden egyéb, nem várt futási hibát elkap
            else:
                self.hiba_tortent.emit(f"Ismeretlen hiba történt a kvíz generálása során: {e}")

# QThread: a PyQt6 beépített szálkezelője
# PDF-ek feldolgozása és vektorizálása idejére leválasztja a folyamatot a főszálról
# ezzel biztosítja, hogy a grafikus felület ne fagyjon le a betöltés alatt
class PdfHatterszal(QThread):
    # pyqtSignal: kommunikációs csatornák (jelek), amelyeken keresztül a háttérszál üzeneteket tud küldeni a grafikus felületnek
    # feldolgozas_kesz: egy jelzés, ami akkor fut le, ha a PDF beolvasása és mentése sikeresen befejeződött
    feldolgozas_kesz = pyqtSignal()
    # hiba_tortent: egy szöveget (a hibaüzenetet) fog küldeni, ha valami elromlik
    hiba_tortent = pyqtSignal(str)
    # kvota_kerdes: egy jelzés, ami akkor fut le, ha a program eléri az API percenkénti limitjét
    # jelezve a főszálnak, hogy kérdezze meg a felhasználót a lassított folytatásról
    kvota_kerdes = pyqtSignal()
    # allapot_frissites: egy szöveget (az aktuális feldolgozási állapotot) fog küldeni a felületnek
    # hogy a hosszú várakozási idők alatt is folyamatosan nyomon követhető legyen a haladás
    allapot_frissites = pyqtSignal(str)

    def __init__(self, backend, utvonal: str) -> None:
        # super().__init__() meghívja a szülőosztály (QThread) inicializáló metódusát
        super().__init__()
        # eltárolja a megkapott paramétereket a példányban (self)
        self.backend = backend
        self.utvonal = utvonal
        # háttérszál megállításáért és újraindításáért felelős szinkronizációs eszköz 
        self.valasz_megerkezett = threading.Event()
        # eltárolja a felhasználó döntését (True/False), hogy folytatódhat-e a feldolgozás lassított módban
        self.folytatas_engedelyezve = False

    # run() a QThread beépített metódusa
    # amikor a főprogram meghívja a .start() parancsot, ez a függvény automatikusan, egy külön háttérszálon fog elindulni
    def run(self) -> None:
        try:
            self.backend.pdf_hozzadasa(self.utvonal, kerdes_callback=self._kerdes_kezelo, allapot_callback=self.allapot_frissites.emit)
            # .emit(): ha minden sikeres volt, elküldi a feldolgozas_kesz jelet a grafikus felület felé
            self.feldolgozas_kesz.emit()
        except RuntimeError as e:
            # hibát dob, ha a felhasználó a "Nem"-re nyomott
            self.hiba_tortent.emit(str(e))
        except ConnectionError:
            # ha nincs internet, vagy nem elérhető a Google szervere
            self.hiba_tortent.emit("Hálózati hiba: Nem sikerült kapcsolódni az AI szerveréhez.")
        except Exception as e:
            # csupa kisbetűssé alakítjuk a biztonságosabb keresés érdekében
            hiba_uzenet = str(e).lower() 
            
            # kiszűri az érvénytelen API kulcs miatti hibákat
            if "api key" in hiba_uzenet or "api_key" in hiba_uzenet or "400" in hiba_uzenet or "403" in hiba_uzenet:
                self.hiba_tortent.emit("Érvénytelen API kulcs! Kérlek, ellenőrizd a megadott GOOGLE_API_KEY-t a .env fájlban.")
            # kiszűri a nyers hálózati hibákat
            elif "11001" in hiba_uzenet or "getaddrinfo" in hiba_uzenet or "nameresolutionerror" in hiba_uzenet:
                self.hiba_tortent.emit("Nincs internetkapcsolat! Kérlek, ellenőrizd a hálózatot, majd próbáld újra.")      
            # minden egyéb, nem várt futási hibát elkap
            else:
                self.hiba_tortent.emit(f"Ismeretlen hiba történt a kvíz generálása során: {e}")
                
    # ezt a függvényt hívja meg a PDF feldolgozó, amikor eléri az API limitet
    def _kerdes_kezelo(self) -> bool:
        self.valasz_megerkezett.clear() # alapállapotba állítja a jelzőeseményt
        self.kvota_kerdes.emit() # szól a főszálnak (ablaknak), hogy jelenítse meg a felugró ablakot
        self.valasz_megerkezett.wait() # a háttérszál itt megáll és várakozik, amíg a felhasználó nem választ
        return self.folytatas_engedelyezve

    # ezt a függvényt a grafikus felület (GUI) hívja meg, miután a felhasználó választott
    def valasz_adas(self, folytassa: bool) -> None:
        self.folytatas_engedelyezve = folytassa
        self.valasz_megerkezett.set() # jelzést ad, ami újraindítja a várakozó háttérszálat