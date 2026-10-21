"""Testy atrapy Service Layer. Uruchomienie (w folderze api): python -m unittest"""
# ===== Testy 0. Przygotowanie =====
import os
import tempfile
import unittest
from fastapi.testclient import TestClient
import baza
import main

LOGIN = {"CompanyDB": "SBODEMO_PL", "UserName": "manager", "Password": "haslo-testowe"}


class TestApi(unittest.TestCase):
    def setUp(self):
        # Każdy test dostaje świeżą, tymczasową bazę z danymi fikcyjnymi.
        self.folder = tempfile.TemporaryDirectory()
        sciezka = os.path.join(self.folder.name, "test.db")
        baza.utworz_baze(sciezka)
        os.environ["B1_DB"] = sciezka
        main.SESJE.clear()
        self.klient = TestClient(main.app)

    def tearDown(self):
        self.klient.close()
        os.environ.pop("B1_DB", None)
        self.folder.cleanup()

    def zaloguj(self):
        odp = self.klient.post("/b1s/v1/Login", json=LOGIN)
        self.assertEqual(odp.status_code, 200)

    # ===== Testy 1. Logowanie i lista (dzień 2) =====
    def test_logowanie_poprawne_zwraca_sesje(self):
        odp = self.klient.post("/b1s/v1/Login", json=LOGIN)
        self.assertEqual(odp.status_code, 200)
        self.assertIn("SessionId", odp.json())

    def test_logowanie_zle_haslo(self):
        zle = dict(LOGIN, Password="zle")
        odp = self.klient.post("/b1s/v1/Login", json=zle)
        self.assertEqual(odp.status_code, 401)
        self.assertEqual(odp.json()["error"]["message"]["value"], "Invalid login")

    def test_lista_bez_logowania_jest_odrzucona(self):
        odp = self.klient.get("/b1s/v1/BusinessPartners")
        self.assertEqual(odp.status_code, 401)

    def test_lista_domyslnie_zwraca_8_klientow(self):
        self.zaloguj()
        odp = self.klient.get("/b1s/v1/BusinessPartners")
        self.assertEqual(odp.status_code, 200)
        self.assertEqual(len(odp.json()["value"]), 8)

    def test_top_i_skip(self):
        self.zaloguj()
        odp = self.klient.get("/b1s/v1/BusinessPartners",
                              params={"$top": 2, "$skip": 1})
        kody = [k["CardCode"] for k in odp.json()["value"]]
        self.assertEqual(kody, ["C002", "C003"])

    def test_filter_po_kodzie(self):
        self.zaloguj()
        odp = self.klient.get("/b1s/v1/BusinessPartners",
                              params={"$filter": "CardCode eq 'C001'"})
        self.assertEqual([k["CardCode"] for k in odp.json()["value"]], ["C001"])

    def test_filter_z_wartoscia_liczbowa(self):
        self.zaloguj()
        odp = self.klient.get("/b1s/v1/Items", params={"$filter": "Price gt 0"})
        self.assertEqual(len(odp.json()["value"]), 6)

    def test_select_ogranicza_pola(self):
        self.zaloguj()
        odp = self.klient.get("/b1s/v1/BusinessPartners",
                              params={"$top": 1, "$select": "CardCode,City"})
        self.assertEqual(sorted(odp.json()["value"][0]), ["CardCode", "City"])

    def test_filter_z_nieznanym_polem_to_blad_400(self):
        self.zaloguj()
        odp = self.klient.get("/b1s/v1/BusinessPartners",
                              params={"$filter": "Haslo eq 'x'"})
        self.assertEqual(odp.status_code, 400)

    def test_proba_sql_injection_nie_dziala(self):
        self.zaloguj()
        zlosliwy = "CardCode eq 'x' OR 1=1 --'"
        odp = self.klient.get("/b1s/v1/BusinessPartners", params={"$filter": zlosliwy})
        self.assertEqual(odp.status_code, 400)

    def test_nieznana_encja_to_404(self):
        self.zaloguj()
        odp = self.klient.get("/b1s/v1/Nieistnieje")
        self.assertEqual(odp.status_code, 404)

    def test_zamowienia_maja_pozycje(self):
        self.zaloguj()
        odp = self.klient.get("/b1s/v1/Orders", params={"$top": 1})
        zamowienie = odp.json()["value"][0]
        self.assertGreaterEqual(len(zamowienie["DocumentLines"]), 1)

    def test_filter_ne(self):
        self.zaloguj()
        odp = self.klient.get("/b1s/v1/BusinessPartners",
                              params={"$filter": "CardCode ne 'C001'"})
        self.assertEqual(odp.status_code, 200)
        self.assertEqual(len(odp.json()["value"]), 7)


if __name__ == "__main__":
    unittest.main()

