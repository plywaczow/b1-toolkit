# Specyfikacja: Mini Service Layer (atrapa SAP Business One)
Adres bazowy: http://127.0.0.1:8000 (tylko komputer lokalny)

## 1. Logowanie
POST /b1s/v1/Login
Body (JSON): {"CompanyDB": "SBODEMO_PL", "UserName": "manager", "Password": "haslo-testowe"}
Sukces: 200, {"SessionId": "...", "Version": "mock-1.0", "SessionTimeout": 30}
oraz ciasteczko B1SESSION (klient odsyła je w kolejnych zapytaniach).
Błąd: 401, {"error": {"code": -1, "message": {"lang": "en-us", "value": "Invalid login"}}}

## 2. Endpointy (wymagają ciasteczka B1SESSION, inaczej 401)
| Metoda | Adres | Opis |
|--------|------------------------------------|-------------------------------|
| GET | /b1s/v1/BusinessPartners | lista klientów |
| GET | /b1s/v1/BusinessPartners('C001') | jeden klient po kodzie |
| POST | /b1s/v1/BusinessPartners | dodanie klienta (201) |
| GET | /b1s/v1/Items, /Items('A001') | towary |
| POST | /b1s/v1/Items | dodanie towaru (201) |
| GET | /b1s/v1/Orders, /Orders(5) | zamówienia z DocumentLines |

## 3. Parametry zapytań (GET na liście)
$top (domyślnie 20, max 1000), $skip, $select=Pole1,Pole2,
$filter=Pole eq 'tekst' lub Pole gt 100 (operatory: eq ne gt ge lt le; łączenie: and)

## 4. Pola encji
BusinessPartners: CardCode (max 15 znaków, wymagane), CardName (max 100, wymagane),
City, FederalTaxID (NIP), EmailAddress
Items: ItemCode (max 20, wymagane), ItemName (max 100, wymagane), Price
Orders (odczyt): DocEntry, CardCode, DocDate, DocumentLines[ItemCode, Quantity, LineTotal]

## 5. Format błędów (zawsze ten sam)
{"error": {"code": <liczba>, "message": {"lang": "en-us", "value": "<tekst>"}}}
Kody HTTP: 400 błędne dane, 401 brak sesji lub złe logowanie, 404 brak rekordu
lub encji, 405 niedozwolona metoda.
Duplikat klucza: 400 z kodem -2035. Brak rekordu: 404 z kodem -2028.

## 6. Plik CSV do importu klientów
Kolumny: CardCode;CardName;City;NIP;Email (NIP i Email opcjonalne)
Separator: średnik lub przecinek. Kodowanie: UTF-8 (z BOM lub bez) albo cp1250.
Reguły: CardCode, CardName i City niepuste; kod: litery, cyfry, myślnik, max 15 znaków;
nazwa max 100 znaków; NIP z poprawną sumą kontrolną; e-mail w poprawnym formacie;
kody nie mogą się powtarzać w pliku (bez względu na wielkość liter).
Mapowanie CSV -> API: NIP -> FederalTaxID, Email -> EmailAddress.

