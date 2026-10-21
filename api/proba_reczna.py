"""Ręczna próba API: loguje się i wypisuje kilku klientów (serwer musi działać)."""
import requests

URL = "http://127.0.0.1:8000"
sesja = requests.Session()  # Session pamięta ciasteczko B1SESSION
odp = sesja.post(
    URL + "/b1s/v1/Login",
    json={
        "CompanyDB": "SBODEMO_PL",
        "UserName": "manager",
        "Password": "haslo-testowe",
    },
)
print("Logowanie:", odp.status_code, odp.json())

odp = sesja.get(URL + "/b1s/v1/BusinessPartners", params={"$top": 3})
print("Lista:", odp.status_code)
for klient in odp.json()["value"]:
    print(" ", klient)

