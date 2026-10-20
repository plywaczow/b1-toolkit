# Decyzje projektowe

| # | Pytanie | Decyzja | Uzasadnienie |
|---|---------|---------|--------------|
| 1 | Co zwraca `$top=0`? | Pustą listę (`"value": []`) | Zgodnie ze znaczeniem „pobierz zero rekordów” oraz standardem OData. |
| 2 | Czy `$filter` rozróżnia wielkość liter w tekście? | Nie rozróżnia (case-insensitive) | Wygoda dla użytkownika wyszukującego np. kontrahenta lub miasto bez pamiętania wielkości liter. |
| 3 | Co ma zrobić POST, jeśli w ciele są pola spoza specyfikacji? | Ignorować nadmiarowe pola i zapisać tylko znane | Zasada tolerancji (Postel's law) – klient może przesyłać dodatkowe metadane bez psucia żądania. |
| 4 | Jaka jest struktura odpowiedzi dla list w GET (np. `/BusinessPartners`)? | Obiekt JSON z tablicą w kluczu `{"value": [...]}` | Format zgodny ze standardem OData oraz rzeczywistym SAP Business One Service Layer. |
| 5 | Czy pole `City` jest wymagane w API przy POST? | Jest opcjonalne w API, ale wymagane w pliku CSV | W punkcie 4 specyfikacji jako wymagane wskazano tylko `CardCode` i `CardName`; reguła z pkt 6 dotyczy jakości importu z CSV. |
| 6 | W jakiej jednostce wyrażony jest `SessionTimeout: 30`? | W minutach (30 minut) | Standardowa wartość wygasania sesji w SAP Service Layer. |

