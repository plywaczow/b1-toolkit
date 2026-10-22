"""Atrapa SAP Business One Service Layer - uproszczona, tylko do nauki.
Uruchomienie (w folderze api): python -m uvicorn main:app --reload
Dokumentacja interaktywna: http://127.0.0.1:8000/docs
"""
# =========== czesc 1 =================
# ===== 1. Importy, konfiguracja i opis encji =====
import re
import secrets
import sqlite3
from typing import Optional

from fastapi import Body, Cookie, Depends, FastAPI, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import baza
app = FastAPI(title="Mini Service Layer (atrapa)", version="1.0")
# Dane logowania są FIKCYJNE i służą tylko do ćwiczeń.
UZYTKOWNICY = {"manager": "haslo-testowe"}
BAZY_FIRMY = {"SBODEMO_PL"}
SESJE = set() # identyfikatory aktywnych sesji (w pamięci serwera)
# Opis encji: nazwa w API -> tabela i kolumny w bazie.
ENCJE = {
    "BusinessPartners": {
        "tabela": "OCRD",
        "klucz": "CardCode",
        "pola": {"CardCode": "CardCode", "CardName": "CardName", "City": "City",
                 "FederalTaxID": "LicTradNum", "EmailAddress": "E_Mail"},
        "wymagane": ["CardCode", "CardName"],
        "dlugosci": {"CardCode": 15, "CardName": 100},
        "zapis": True,
    },
    "Items": {
        "tabela": "OITM",
        "klucz": "ItemCode",
        "pola": {"ItemCode": "ItemCode", "ItemName": "ItemName", "Price": "Price"},
        "wymagane": ["ItemCode", "ItemName"],
        "dlugosci": {"ItemCode": 20, "ItemName": 100},
        "zapis": True,
    },
    "Orders": {
        "tabela": "ORDR",
        "klucz": "DocEntry",
        "pola": {"DocEntry": "DocEntry", "CardCode": "CardCode", "DocDate": "DocDate"},
        "wymagane": [],
        "dlugosci": {},
        "zapis": False, # zamówienia tylko do odczytu
        "linie": True, # dołączamy DocumentLines z tabeli RDR1
    },
}

# część 2 (błędy w jednym, przewidywalnym formacie)

# ===== 2. Błędy w formacie zbliżonym do Service Layer =====
class BladB1(Exception):
    """Błąd, który zamieniamy na odpowiedź JSON w stylu Service Layer."""
    def __init__(self, status, kod, tekst):
        self.status = status
        self.kod = kod
        self.tekst = tekst
def odpowiedz_bledu(status, kod, tekst):
    return JSONResponse(status_code=status, content={
        "error": {"code": kod, "message": {"lang": "en-us", "value": tekst}}})
@app.exception_handler(BladB1)
async def obsluz_blad_b1(request, exc):
    return odpowiedz_bledu(exc.status, exc.kod, exc.tekst)
@app.exception_handler(RequestValidationError)
async def obsluz_blad_walidacji(request, exc):
    return odpowiedz_bledu(400, -1, "Invalid request: " + str(exc.errors()[0]["msg"]))
# cz 3 (sesja ilogowanie):
# ===== 3. Sesja i logowanie =====
def wymagaj_sesji(B1SESSION: Optional[str] = Cookie(None)):
    """Zależność: endpoint działa tylko z ciasteczkiem B1SESSION po zalogowaniu."""
    if B1SESSION not in SESJE:
        raise BladB1(401, -1, "Invalid session or session already timeout.")
@app.post("/b1s/v1/Login")
def logowanie(dane: dict = Body(...)):
    firma = dane.get("CompanyDB")
    uzytkownik = str(dane.get("UserName", ""))
    haslo = str(dane.get("Password", ""))
    oczekiwane = UZYTKOWNICY.get(uzytkownik, "")
    haslo_ok = secrets.compare_digest(oczekiwane, haslo) and uzytkownik in UZYTKOWNICY
    if firma not in BAZY_FIRMY or not haslo_ok:
        raise BladB1(401, -1, "Invalid login")
    sesja = secrets.token_hex(16)
    SESJE.add(sesja)
    odp = JSONResponse({"SessionId": sesja, "Version": "mock-1.0", "SessionTimeout": 30})
    odp.set_cookie("B1SESSION", sesja, httponly=True)
    return odp

# ===== 4. Funkcje pomocnicze: filtrowanie, wybór pól, lista =====
WZORZEC_WARUNKU = re.compile(
    r"^(\w+)\s+(eq|ne|gt|ge|lt|le)\s+('[^']*'|-?\d+(?:\.\d+)?)$")
OPERATORY = {"eq": "=", "ne": "<>", "gt": ">", "ge": ">=", "lt": "<", "le": "<="}
def pobierz_encje(nazwa):
    if nazwa not in ENCJE:
        raise BladB1(404, -1, "Resource not found for segment '%s'" % nazwa)
    return ENCJE[nazwa]
def zbuduj_where(konf, filtr):
    """Zamienia $filter (np. City eq 'Kraków') na fragment SQL i parametry.
    Nazwy kolumn bierzemy WYŁĄCZNIE z naszego słownika, a wartości przekazujemy
    jako parametry (znaki ?) - dzięki temu nie ma podatności na SQL injection.
    """
    if not filtr:
        return "", []
    warunki, parametry = [], []
    for kawalek in re.split(r"\s+and\s+", filtr.strip()):
        trafienie = WZORZEC_WARUNKU.match(kawalek.strip())
        if not trafienie:
            raise BladB1(400, -1, "Invalid $filter: " + kawalek)
        pole, operator, wartosc = trafienie.groups()
        if pole not in konf["pola"]:
            raise BladB1(400, -1, "Property '%s' is invalid" % pole)
        if wartosc.startswith("'"):
            wartosc = wartosc[1:-1]
        else:
            wartosc = float(wartosc)
        warunki.append("%s %s ?" % (konf["pola"][pole], OPERATORY[operator]))
        parametry.append(wartosc)
    return " WHERE " + " AND ".join(warunki), parametry
def wybierz_pola(konf, select):
    """Zwraca listę nazw pól do zwrócenia ($select lub wszystkie)."""
    if not select:
        return list(konf["pola"])
    wybrane = [p.strip() for p in select.split(",") if p.strip()]
    for pole in wybrane:
        if pole not in konf["pola"]:
            raise BladB1(400, -1, "Property '%s' is invalid" % pole)
    return wybrane
def dolacz_linie(conn, rekord):
    """Dla zamówienia dokłada listę pozycji DocumentLines."""
    wiersze = conn.execute(
        "SELECT ItemCode, Quantity, LineTotal FROM RDR1 WHERE DocEntry = ?",
        (rekord["DocEntry"],)).fetchall()
    rekord["DocumentLines"] = [dict(w) for w in wiersze]
def pobierz_liste(nazwa, top, skip, filtr, select):
    konf = pobierz_encje(nazwa)
    pola = wybierz_pola(konf, select)
    where, parametry = zbuduj_where(konf, filtr)
    kolumny = ", ".join("%s AS %s" % (konf["pola"][p], p) for p in pola)
    klucz_db = konf["pola"][konf["klucz"]]
    limit = 20 if top is None else top
    sql = "SELECT %s FROM %s%s ORDER BY %s LIMIT ? OFFSET ?" % (
        kolumny, konf["tabela"], where, klucz_db)
    conn = baza.polacz()

    # Projekt Mini B1 Toolkit · samodzielna praca · tydzień 3, październik 2026 Strona 17
    try:
        wiersze = conn.execute(sql, parametry + [limit, skip or 0]).fetchall()
        wynik = [dict(w) for w in wiersze]
        if konf.get("linie") and "DocEntry" in pola:
            for rekord in wynik:
                dolacz_linie(conn, rekord)
    finally:
        conn.close()
    return wynik
# ===== 5. Trasa: pobieranie jednego rekordu po kluczu (GET) =====
def pobierz_jeden(nazwa, klucz):
    konf = pobierz_encje(nazwa)
    kolumny = ", ".join("%s AS %s" % (kol, p) for p, kol in konf["pola"].items())
    sql = "SELECT %s FROM %s WHERE %s = ?" % (
    kolumny, konf["tabela"], konf["pola"][konf["klucz"]])
    conn = baza.polacz()
    try:
        wiersz = conn.execute(sql, (klucz,)).fetchone()
        if wiersz is None:
            raise BladB1(404, -2028, "No matching records found (ODBC -2028)")
        rekord = dict(wiersz)
        if konf.get("linie"):
            dolacz_linie(conn, rekord)
    finally:
        conn.close()
    return rekord
    # Adres w stylu Service Layer: /b1s/v1/BusinessPartners('C001') lub Orders(5)
@app.get("/b1s/v1/{encja}({klucz})", dependencies=[Depends(wymagaj_sesji)])
def jeden(encja: str, klucz: str):
    return pobierz_jeden(encja, klucz.strip("'"))
# ===== 6. Trasa: lista rekordów (GET) =====
@app.get("/b1s/v1/{encja}", dependencies=[Depends(wymagaj_sesji)])
def lista(encja: str,
          top: Optional[int] = Query(None, alias="$top", ge=0, le=1000),
          skip: Optional[int] = Query(None, alias="$skip", ge=0),
          filtr: Optional[str] = Query(None, alias="$filter"),
          select: Optional[str] = Query(None, alias="$select")):
    return {"value": pobierz_liste(encja, top, skip, filtr, select)}
# ===== 7. Trasa: dodawanie rekordu (POST) =====
def dodaj_rekord(nazwa, dane):
    konf = pobierz_encje(nazwa)
    if not konf["zapis"]:
        raise BladB1(405, -1, "Method not allowed for '%s'" % nazwa)
    for pole, wartosc in dane.items():
        if pole not in konf["pola"]:
            raise BladB1(400, -1, "Property '%s' of entity '%s' has invalid name"
    % (pole, nazwa))
    if not isinstance(wartosc, (str, int, float)):
        raise BladB1(400, -1, "Property '%s' has invalid value type" % pole)
    for pole in konf["wymagane"]:
        if not str(dane.get(pole, "")).strip():
            raise BladB1(400, -1, "Property '%s' is required" % pole)
    for pole, maksimum in konf["dlugosci"].items():
        if len(str(dane.get(pole, ""))) > maksimum:
            raise BladB1(400, -1, "Property '%s' is too long (max %d)" % (pole, maksimum))
    kolumny = [konf["pola"][p] for p in dane]
    sql = "INSERT INTO %s (%s) VALUES (%s)" % (
    konf["tabela"], ", ".join(kolumny), ", ".join(["?"] * len(kolumny)))
    conn = baza.polacz()
    try:
        conn.execute(sql, list(dane.values()))
        conn.commit()
    except sqlite3.IntegrityError:
        raise BladB1(400, -2035,
    "This entry already exists in the following tables (ODBC -2035)")
    finally:
        conn.close()
    return pobierz_jeden(nazwa, str(dane[konf["klucz"]]))
@app.post("/b1s/v1/{encja}", status_code=201, dependencies=[Depends(wymagaj_sesji)])
def dodaj(encja: str, dane: dict = Body(...)):
    return dodaj_rekord(encja, dane)

