"""Reguły walidacji danych klientów przed importem do SAP Business One."""
import re

KOLUMNY_WYMAGANE = ["CardCode", "CardName", "City"]
KOLUMNY_OPCJONALNE = ["NIP", "Email"]

WZORZEC_KODU = re.compile(r"^[A-Za-z0-9\-]{1,15}$")
WZORZEC_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
WAGI_NIP = (6, 5, 7, 2, 3, 4, 5, 6, 7)
MAKS_NAZWA = 100


def nip_poprawny(nip):
    """Sprawdza NIP: 10 cyfr (myślniki i spacje ignorujemy) i suma kontrolna."""
    cyfry = nip.replace("-", "").replace(" ", "")
    if not re.fullmatch(r"[0-9]{10}", cyfry):
        return False
    suma = sum(int(c) * w for c, w in zip(cyfry[:9], WAGI_NIP))
    kontrolna = suma % 11
    return kontrolna != 10 and kontrolna == int(cyfry[9])


def sprawdz_naglowki(kolumny):
    """Zwraca listę brakujących, wymaganych kolumn (pusta lista = wszystko OK)."""
    obecne = [k.strip() for k in (kolumny or [])]
    return [k for k in KOLUMNY_WYMAGANE if k not in obecne]


def oczysc_wiersz(wiersz):
    """Usuwa zbędne spacje z początku i końca każdej wartości."""
    return {klucz: (wartosc or "").strip() for klucz, wartosc in wiersz.items()}


def waliduj_wiersz(wiersz):
    """Zwraca listę błędów jednego wiersza jako krotki (pole, komunikat)."""
    bledy = []
    for pole in KOLUMNY_WYMAGANE:
        if not wiersz.get(pole, ""):
            bledy.append((pole, "pole jest puste"))
    kod = wiersz.get("CardCode", "")
    if kod and not WZORZEC_KODU.match(kod):
        bledy.append(("CardCode", "kod: tylko litery, cyfry i myślnik, max 15 znaków"))
    if kod and not kod.upper().startswith("C"):
        bledy.append(("CardCode", "kod klienta musi zaczynać się od litery C"))
    if len(wiersz.get("CardName", "")) > MAKS_NAZWA:
        bledy.append(("CardName", "nazwa dłuższa niż %d znaków" % MAKS_NAZWA))
    nip = wiersz.get("NIP", "")
    if nip and not nip_poprawny(nip):
        bledy.append(("NIP", "niepoprawny NIP (długość lub suma kontrolna)"))
    email = wiersz.get("Email", "")
    if email and not WZORZEC_EMAIL.match(email):
        bledy.append(("Email", "niepoprawny adres e-mail"))
    return bledy


def waliduj_plik(wiersze):
    """Waliduje wszystkie wiersze i wykrywa duplikaty kodów w pliku.

    Zwraca (poprawne, bledy):
        poprawne - lista oczyszczonych wierszy, każdy z kluczem "_nr" (numer wiersza)
        bledy    - lista słowników: {"wiersz": nr, "pole": ..., "komunikat": ...}

    Numer wiersza liczymy tak jak w Excelu: nagłówek to wiersz 1, dane od 2.
    """
    poprawne, bledy = [], []
    widziane = {}  # kod (małymi literami) -> numer pierwszego wiersza
    for indeks, surowy in enumerate(wiersze):
        nr = indeks + 2
        wiersz = oczysc_wiersz(surowy)
        problemy = waliduj_wiersz(wiersz)
        kod = wiersz.get("CardCode", "").lower()
        if kod:
            if kod in widziane:
                problemy.append(("CardCode",
                                 "duplikat kodu z wiersza %d" % widziane[kod]))
            else:
                widziane[kod] = nr
        if problemy:
            for pole, komunikat in problemy:
                bledy.append({"wiersz": nr, "pole": pole, "komunikat": komunikat})
        else:
            wiersz["_nr"] = nr
            poprawne.append(wiersz)
    return poprawne, bledy
