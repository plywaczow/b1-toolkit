"""Testy walidatora. Uruchomienie (w folderze migrator): python -m unittest"""
import unittest
import walidator as w


def dobry(**zmiany):
    wiersz = {"CardCode": "C100", "CardName": "Firma Testowa", "City": "Poznań",
              "NIP": "", "Email": ""}
    wiersz.update(zmiany)
    return wiersz


class TestNip(unittest.TestCase):
    def test_poprawny_nip(self):
        self.assertTrue(w.nip_poprawny("1234563218"))

    def test_nip_z_myslnikami(self):
        self.assertTrue(w.nip_poprawny("123-456-32-18"))

    def test_zla_suma_kontrolna(self):
        self.assertFalse(w.nip_poprawny("1234563219"))

    def test_zla_dlugosc(self):
        self.assertFalse(w.nip_poprawny("12345"))

    def test_litery(self):
        self.assertFalse(w.nip_poprawny("12345A3218"))


class TestWiersz(unittest.TestCase):
    def test_poprawny_wiersz_nie_ma_bledow(self):
        self.assertEqual(w.waliduj_wiersz(dobry()), [])

    def test_puste_pola_wymagane(self):
        bledy = w.waliduj_wiersz(dobry(CardName="", City=""))
        pola = [pole for pole, _ in bledy]
        self.assertEqual(sorted(pola), ["CardName", "City"])

    def test_zly_kod(self):
        bledy = w.waliduj_wiersz(dobry(CardCode="C 100!"))
        self.assertEqual([pole for pole, _ in bledy], ["CardCode"])

    def test_za_dlugi_kod(self):
        self.assertTrue(w.waliduj_wiersz(dobry(CardCode="C" * 16)))

    def test_zly_email(self):
        bledy = w.waliduj_wiersz(dobry(Email="to-nie-email"))
        self.assertEqual([pole for pole, _ in bledy], ["Email"])

    def test_zly_nip(self):
        bledy = w.waliduj_wiersz(dobry(NIP="1234563219"))
        self.assertEqual([pole for pole, _ in bledy], ["NIP"])

    def test_kod_nie_zaczyna_sie_od_c(self):
        """Kod klienta musi zaczynać się od litery C (reguła biznesowa)."""
        bledy = w.waliduj_wiersz(dobry(CardCode="V100"))
        pola = [pole for pole, _ in bledy]
        self.assertIn("CardCode", pola)


class TestPlik(unittest.TestCase):
    def test_duplikat_kodu_niezaleznie_od_wielkosci_liter(self):
        wiersze = [dobry(CardCode="C100"), dobry(CardCode="c100")]
        poprawne, bledy = w.waliduj_plik(wiersze)
        self.assertEqual(len(poprawne), 1)
        self.assertEqual(bledy[0]["wiersz"], 3)
        self.assertIn("duplikat", bledy[0]["komunikat"])

    def test_numery_wierszy_licza_naglowek(self):
        poprawne, bledy = w.waliduj_plik([dobry(), dobry(CardCode="", CardName="")])
        self.assertEqual(poprawne[0]["_nr"], 2)
        self.assertEqual({b["wiersz"] for b in bledy}, {3})

    def test_spacje_na_brzegach_sa_usuwane(self):
        poprawne, bledy = w.waliduj_plik([dobry(CardName=" Firma ")])
        self.assertEqual(poprawne[0]["CardName"], "Firma")
        self.assertEqual(bledy, [])

    def test_brakujace_naglowki(self):
        self.assertEqual(w.sprawdz_naglowki(["CardCode", "City"]), ["CardName"])
        self.assertEqual(w.sprawdz_naglowki(None), ["CardCode", "CardName", "City"])


if __name__ == "__main__":
    unittest.main()
