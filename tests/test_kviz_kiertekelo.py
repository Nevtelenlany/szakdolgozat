import pytest
from backend.kviz_kiertekelo import EgyvalaszosKiertekelo, RovidValaszKiertekelo

def test_egyvalaszos_kiertekelo_helyes_valasz():
    kiertekelo = EgyvalaszosKiertekelo()
    kerdes_adat = {
        "helyes_valasz": "Párizs",
        "magyarazat": "Franciaország fővárosa."
    }
    
    # helyes válasz kiértékelése
    helyes_e, visszajelzes = kiertekelo.kiertekel(kerdes_adat, "Párizs")
    
    assert helyes_e is True
    assert visszajelzes["helyes_valasz"] == "Párizs"
    assert visszajelzes["magyarazat"] == "Franciaország fővárosa."

def test_egyvalaszos_kiertekelo_hibas_valasz():
    kiertekelo = EgyvalaszosKiertekelo()
    kerdes_adat = {"helyes_valasz": "Párizs"}
    
    # rossz válasz kiértékelése
    helyes_e, _ = kiertekelo.kiertekel(kerdes_adat, "London")
    assert helyes_e is False

def test_rovid_valasz_kis_es_nagybetu_fuggetlenseg():
    kiertekelo = RovidValaszKiertekelo()
    kerdes_adat = {"elfogadott_kulcsszavak": ["DNS", "dezoxiribonukleinsav"]}
    
    # kezelnie kell a felesleges szóközöket és a kisbetűket is
    helyes_e, _ = kiertekelo.kiertekel(kerdes_adat, "   dNs   ")
    assert helyes_e is True