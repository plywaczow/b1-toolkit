"""Warstwa danych: SQLite z tabelami podobnymi do SAP Business One (dane fikcyjne)."""
import os
import random
import sqlite3
DOMYSLNA_BAZA = "sklep_b1.db"
def sciezka_bazy():
    """Ścieżka do pliku bazy. Można ją zmienić zmienną środowiskową B1_DB."""
    return os.environ.get("B1_DB", DOMYSLNA_BAZA)
def polacz():
    """Nowe połączenie z bazą; wiersze dostępne po nazwach kolumn."""
    conn = sqlite3.connect(sciezka_bazy())
    conn.row_factory = sqlite3.Row
    return conn
def utworz_baze(sciezka):
    """Tworzy (od nowa) bazę z fikcyjnymi danymi. Poprzedni plik jest usuwany."""
    if os.path.exists(sciezka):
        os.remove(sciezka)
    los = random.Random(42) # stałe ziarno: za każdym razem te same dane
    conn = sqlite3.connect(sciezka)
    conn.executescript("""
    CREATE TABLE OCRD (CardCode TEXT PRIMARY KEY, CardName TEXT NOT NULL,
                    City TEXT, LicTradNum TEXT, E_Mail TEXT);
    CREATE TABLE OITM (ItemCode TEXT PRIMARY KEY, ItemName TEXT NOT NULL,
                    Price REAL);
    CREATE TABLE ORDR (DocEntry INTEGER PRIMARY KEY, CardCode TEXT, DocDate TEXT);
    CREATE TABLE RDR1 (DocEntry INTEGER, ItemCode TEXT, Quantity INTEGER,
                    LineTotal REAL);
        """)
    miasta = ["Wrocław", "Kraków", "Gdańsk", "Poznań"]
    for i in range(1, 9):
        conn.execute("INSERT INTO OCRD (CardCode, CardName, City) VALUES (?,?,?)",
                ("C%03d" % i, "Klient %d" % i, los.choice(miasta)))
    for i in range(1, 7):
        cena = round(los.uniform(10, 500), 2)
        conn.execute("INSERT INTO OITM VALUES (?,?,?)",
                ("A%03d" % i, "Towar %d" % i, cena))
    for nr in range(1, 21):
        kod = "C%03d" % los.randint(1, 8)
        data = "2026-%02d-%02d" % (los.randint(1, 9), los.randint(1, 28))
        conn.execute("INSERT INTO ORDR VALUES (?,?,?)", (nr, kod, data))
    for _ in range(los.randint(1, 3)):
        towar = "A%03d" % los.randint(1, 6)
        ilosc = los.randint(1, 10)
        cena = conn.execute("SELECT Price FROM OITM WHERE ItemCode=?",
                (towar,)).fetchone()[0]
        conn.execute("INSERT INTO RDR1 VALUES (?,?,?,?)",
            (nr, towar, ilosc, round(ilosc * cena, 2)))
    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    utworz_baze(sciezka_bazy())
    print("Utworzono bazę:", sciezka_bazy())