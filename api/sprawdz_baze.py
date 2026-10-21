"""Szybkie sprawdzenie bazy: wypisuje liczbę klientów w tabeli OCRD."""
import sqlite3

conn = sqlite3.connect("sklep_b1.db")
print(conn.execute("SELECT COUNT(*) FROM OCRD").fetchone())
conn.close()