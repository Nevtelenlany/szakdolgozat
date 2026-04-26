import pytest
from backend.temakor_kezelo import TemakorKezelo

def test_nev_validalasa_helyes():
    kezelo = TemakorKezelo()
    siker, uzenet = kezelo._nev_validalasa("Algoritmusok_es_Adatszerkezetek")
    assert siker is True
    assert uzenet == ""

def test_nev_validalasa_tiltott_karakter():
    kezelo = TemakorKezelo()
    # tiltott karakterek tesztelése
    siker, uzenet = kezelo._nev_validalasa("Szoftverfejlesztes/Alapok")
    assert siker is False
    assert "nem tartalmazhatja" in uzenet

def test_nev_validalasa_fenntartott_nev():
    kezelo = TemakorKezelo()
    # rendszer által fenntartott nevek tesztelése
    siker, uzenet = kezelo._nev_validalasa("CON")
    assert siker is False
    assert "operációs rendszer által fenntartott" in uzenet