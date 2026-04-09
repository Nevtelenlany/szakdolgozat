import chromadb
from chromadb.config import Settings
import multiprocessing

def _kollekcio_lekerese(adatbazis_utvonal: str):
    # inicializálja a ChromaDB klienst a megadott útvonalon
    # PersistentClient biztosítja, hogy az adatok fizikailag a mappába legyenek mentve, ne csak a memóriába
    # anonymized_telemetry=False kikapcsolja a névtelen adatgyűjtést (nem küld adatokat a készítőknek)
    kliens = chromadb.PersistentClient(path=adatbazis_utvonal, settings=Settings(anonymized_telemetry=False))
    
    # lekéri a 'my-collection' nevű táblát, vagy automatikusan létrehozza, ha még nem létezik
    return kliens.get_or_create_collection(name="my-collection")

def hatter_mentes(adatbazis_utvonal: str, darab_azonositok: list[str], vektorok: list[list[float]], darabok: list[str], metaadatok: list[dict]) -> None:
    kollekcio = _kollekcio_lekerese(adatbazis_utvonal)
    
    # hozzáadja az adatokat a vektoradatbázishoz
    kollekcio.add(
        ids=darab_azonositok,
        embeddings=vektorok,
        documents=darabok,    # chunkok
        metadatas=metaadatok  # kiegészítő adatok, itt ez a forrásfájl neve 
    )

def hatter_torles(adatbazis_utvonal: str, fajl_neve: str) -> None:
    kollekcio = _kollekcio_lekerese(adatbazis_utvonal)
    try:
        # lekéri a teljes adatbázis tartalmát
        minden_adat = kollekcio.get()

        # teljes adatbázis tartalmán végigmegy
        # startswith megvizsgálja, hogy az azonosító a megadott fájlnévvel kezdődik-e
        torlendo_id_k = [egyedi_azonosito for egyedi_azonosito in minden_adat['ids'] if egyedi_azonosito.startswith(f"{fajl_neve}_chunk_")]
        
        # ha talált törlendő elemet a listában, akkor végrehajtja a törlést
        if torlendo_id_k:
            # delete a chromaDB könyvtár beépített metódusa
            kollekcio.delete(ids=torlendo_id_k)
    except ValueError:
        pass

def _elszigetelt_kereses(adatbazis_utvonal: str, vektorok: list[list[float]], eredmeny_sor: multiprocessing.Queue) -> None:
    try:
        kollekcio = _kollekcio_lekerese(adatbazis_utvonal)
        
        # lekérdezi a 3 leginkább hasonló dokumentumdarabot a megadott vektor alapján
        # beépített query metódus megkeresi a paraméterek alapján a legközelebb álló vektorokat
        # query_embeddings paraméterben kapja meg azt a vektort, amihez a hasonlót keresi
        # n_results=3: a 3 legjobb találatot adja vissza a ChromaDB-ből
        eredmeny = kollekcio.query(query_embeddings=vektorok, n_results=3)
        
        # ha nincs találat, vagy üres a dokumentumlista, egy üres kontextust küld vissza
        if not eredmeny.get('documents') or not eredmeny['documents'][0]:
            # put() metódus ráteszi az eredménysorra (Queue) az üres kontextust és a sikeres ("ok") státuszt a főprogram számára
            eredmeny_sor.put({"status": "ok", "kontextus": ""})
            return
        
        # összefűzi a talált dokumentumokat a forrás megjelölésével egy formázott listába
        kontextus_lista = [
            # meta.get() kikeresi a 'forras' kulcsot a szótárból (hibatűrés: ha nincs, 'Ismeretlen forrás' lesz)
            # {doc} pedig maga a szövegdarab (chunk), ami a sortörés (\n) után kerül beillesztésre
            f"[Forrás: {meta.get('forras', 'Ismeretlen forrás')}]\n{doc}"
            
            # [0]-ás index: mivel ez egy lista a listában (beágyazott lista), és a külső listában csak 1 db belső lista van (aminek persze több eleme is van)
            # zip(): párhuzamosan megy végig a szövegek és a metaadatok listáján, a háttérben 2 elemű párokat (doc, meta) hozva létre
            # ezeket a párokat azonnal be is helyettesíti a fenti f-string sablonba
            for doc, meta in zip(eredmeny['documents'][0], eredmeny['metadatas'][0])
        ]

        # találatokat elküldi az eredménysorba (Queue), \n\n---\n\n (dupla sortörés és vonal) elválasztással
        eredmeny_sor.put({"status": "ok", "kontextus": "\n\n---\n\n".join(kontextus_lista)})
    except Exception as hiba:
        # hiba esetén a hibaüzenetet küldi vissza a sornak szótárként
        eredmeny_sor.put({"status": "hiba", "kontextus": str(hiba)})

def hatter_kereses(adatbazis_utvonal: str, vektorok: list[list[float]]) -> str:
    # létrehoz egy csatornát (Queue), amin keresztül a háttérfolyamat és a főprogram kommunikálni tud
    eredmeny_sor = multiprocessing.Queue()
    # target megmondja, melyik függvényt futtassa, az args pedig átadja neki a szükséges paramétereket
    folyamat = multiprocessing.Process(target=_elszigetelt_kereses, args=(adatbazis_utvonal, vektorok, eredmeny_sor))
    folyamat.start() # elindítja a háttérfolyamatot
    # főprogram itt megáll, és megvárja, amíg a háttérfolyamat betesz egy eredményt a sorba, majd kiveszi azt
    valasz = eredmeny_sor.get()
    # join() biztosítja, hogy a főprogram megvárja a háttérfolyamat biztonságos és teljes leállását (memória felszabadítása)
    folyamat.join()
    
    # ha a háttérfolyamat hibát jelzett (pl. megsérült az adatbázis), a program dob egy kivételt (RuntimeError)
    if valasz["status"] == "hiba":
        raise RuntimeError(f"ChromaDB hiba a keresésnél: {valasz['kontextus']}")
        
    # ha minden sikeres volt, visszaadja a formázott szövegeket tartalmazó kontextust
    return valasz["kontextus"]


def _elszigetelt_kviz_kereses(adatbazis_utvonal: str, vektorok: list[list[float]], fajl_neve: str, eredmeny_sor: multiprocessing.Queue) -> None:
    try:
        kollekcio = _kollekcio_lekerese(adatbazis_utvonal)
        
        # query() metódussal keresi meg a kvízkérdésekhez tartozó releváns tananyagot
        # beépített query metódus megkeresi a paraméterek alapján a legközelebb álló vektorokat
        eredmeny = kollekcio.query(
            # query_embeddings paraméterben kapja meg azt a vektort, amihez a hasonlót keresi
            query_embeddings=vektorok,
            # n_results=3: a 3 legjobb találatot adja vissza a ChromaDB-ből
            n_results=3,
            # 'where' paraméterrel biztosítja, hogy a keresés kizárólag a kiválasztott fájlra korlátozódjon
            where={"forras": fajl_neve}
        )
        
        # {} itt egy halmazt (Set) hoz létre, hogy az esetleges redundanciát elkerülje, mert egy elem nem szerepelhet benne többször
        # eredmeny.get('documents', []) lekéri a dokumentumokat, de ha valami hiba történne, egy üres listát [] ad vissza
        # 'for dokumentum_lista in eredmeny.get(...)' végigmegy a nagy listán, és kiveszi a belső listákat
        # 'for szoveg in dokumentum_lista' végigmegy az éppen kivett belső listán, és megfogja az egyes szövegeket
        kontextus_halmaz = {szoveg for dokumentum_lista in eredmeny.get('documents', []) for szoveg in dokumentum_lista}

        # találatokat elküldi az eredménysorba (Queue), \n\n---\n\n (dupla sortörés és vonal) elválasztással
        eredmeny_sor.put({"status": "ok", "kontextus": "\n\n---\n\n".join(kontextus_halmaz)})
        
    except Exception as hiba:
        # hiba esetén a hibaüzenetet küldi vissza az eredménysorba
        eredmeny_sor.put({"status": "hiba", "kontextus": str(hiba)})

def hatter_kviz_kereses(adatbazis_utvonal: str, vektorok: list[list[float]], fajl_neve: str) -> str:
    # létrehoz egy csatornát (Queue), amin keresztül a háttérfolyamat és a főprogram kommunikálni tud
    eredmeny_sor = multiprocessing.Queue()
    # target megmondja, melyik függvényt futtassa, az args pedig átadja neki a szükséges paramétereket
    folyamat = multiprocessing.Process(target=_elszigetelt_kviz_kereses, args=(adatbazis_utvonal, vektorok, fajl_neve, eredmeny_sor))
    folyamat.start() # elindítja a háttérfolyamatot
    # főprogram itt megáll, és megvárja, amíg a háttérfolyamat betesz egy eredményt a sorba, majd kiveszi azt
    valasz = eredmeny_sor.get()
    # join() biztosítja, hogy a főprogram megvárja a háttérfolyamat biztonságos és teljes leállását (memória felszabadítása)
    folyamat.join()
    
    # ha a háttérfolyamat hibát jelzett, a program dob egy kivételt (RuntimeError)
    if valasz["status"] == "hiba":
        raise RuntimeError(f"ChromaDB hiba a kvíznél: {valasz['kontextus']}")
        
    # ha minden sikeres volt, visszaadja a formázott szövegeket tartalmazó kontextust
    return valasz["kontextus"]


def _elszigetelt_teljes_szoveg(adatbazis_utvonal: str, fajl_neve: str, eredmeny_sor: multiprocessing.Queue) -> None:
    try:
        kollekcio = _kollekcio_lekerese(adatbazis_utvonal)
        # lekérdezi az adatbázisból az összes olyan dokumentumot (chunkot), ami ehhez a fájlhoz tartozik
        # 'where' paraméterrel biztosítja, hogy a keresés kizárólag a kiválasztott fájlra korlátozódjon
        minden_adat = kollekcio.get(where={"forras": fajl_neve})
        
        # kettős ellenőrzésre azért van szükség, mert ha egyáltalán nem kap adatot (None), a .get() parancs azonnal összeomlasztaná a programot
        # minden_adat: megnézi, hogy egyáltalán kapott-e bármilyen választ (nem None-e)
        # minden_adat.get("documents"): megnézi, hogy a kapott válaszban vannak-e tényleges dokumentumok (nem üres-e)
        if not (minden_adat and minden_adat.get("documents")):
            eredmeny_sor.put({"status": "hiba", "uzenet": f"Nincs adat az adatbázisban a(z) {fajl_neve} fájlhoz!"})
            return
            
        # összefűzi a chunkokat, és sortöréssel elválasztja őket egymástól
        teljes_szoveg = "\n".join(minden_adat["documents"])
        
        # sikeres találatot (a teljes szöveget) elküldi az eredménysorba (Queue)
        eredmeny_sor.put({"status": "ok", "szoveg": teljes_szoveg})
    
    except Exception as hiba:
        # hiba esetén a hibaüzenetet küldi vissza az eredménysorba
        eredmeny_sor.put({"status": "hiba", "uzenet": str(hiba)})

def hatter_teljes_szoveg_lekeres(adatbazis_utvonal: str, fajl_neve: str) -> dict:
    # létrehoz egy csatornát (Queue), amin keresztül a háttérfolyamat és a főprogram kommunikálni tud
    eredmeny_sor = multiprocessing.Queue()
    # target megmondja, melyik függvényt futtassa, az args pedig átadja neki a szükséges paramétereket
    folyamat = multiprocessing.Process(target=_elszigetelt_teljes_szoveg, args=(adatbazis_utvonal, fajl_neve, eredmeny_sor))
    folyamat.start() # elindítja a háttérfolyamatot
    # főprogram itt megáll, és megvárja, amíg a háttérfolyamat betesz egy eredményt a sorba, majd kiveszi azt
    valasz = eredmeny_sor.get()
    # join() biztosítja, hogy a főprogram megvárja a háttérfolyamat biztonságos és teljes leállását (memória felszabadítása)
    folyamat.join()
    
    return valasz