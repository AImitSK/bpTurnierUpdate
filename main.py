import os
import requests
import json
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import logging
import re  # Modul für reguläre Ausdrücke

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)

# .env Datei laden
load_dotenv()

# API- und Tabellendaten aus der .env Datei laden
api_url = os.getenv("ApiUrl").rstrip('/')
token = os.getenv("PersonalAccessToken")
table_id = os.getenv("TableId")
bot_id = os.getenv("BotId")

# Webseite mit Turnierdaten
WEB_URL = "https://www.pccaddie.net/clubs/0493347/app.php?cat=ts_calendar"

def extract_clean_text(element, fallback=""):
    """Hilfsfunktion zur Bereinigung des Textes."""
    return element.get_text(strip=True) if element else fallback

def clean_text(text):
    """Hilfsfunktion, um Mehrfach-Leerzeichen zu entfernen und die Daten einzeilig zu halten."""
    # Entferne alle mehrfachen Leerzeichen und formatiere den Text einzeilig
    text = re.sub(r'\s+', ' ', text)  # Ersetze mehrere Leerzeichen durch eins
    text = text.strip()  # Entferne führende und nachfolgende Leerzeichen
    return text


def get_tournament_data():
    """Extrahiere Turnierdaten von der Webseite und konsolidiere die ersten 5 Einträge."""
    try:
        response = requests.get(WEB_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        logging.error(f"Fehler beim Abrufen der Webseite: {e}")
        return []

    tournament_data = []
    events = soup.find_all("tr", class_="pcco-xcal-list-item")

    for idx, event in enumerate(events):
        # Alle Zeiträume für den Tag sammeln und zusammenfügen
        times = [clean_text(span.get_text()) for span in event.find_all("span", class_="tk-club")]
        datum = " und ".join(times) if times else "Datum nicht gefunden"

        # Turniername extrahieren
        name_container = event.find("span", class_="tk-turnier")
        veranstaltung = clean_text(name_container.get_text()) if name_container else "Veranstaltung nicht gefunden"

        # Offen-Status prüfen und Beschriftung setzen
        is_open = "offenes Turnier" if event.find("i", class_="fa-check") else "geschlossenes Turnier"

        # Daten hinzufügen im erwarteten Format
        entry = {
            "id": idx + 1,  # Eindeutige ID für jeden Eintrag
            "Datum": datum,
            "Veranstaltung": veranstaltung,
            "Offen": is_open
        }
        tournament_data.append(entry)

        # Debugging-Ausgabe für jedes Turnier
        print(f"Eintrag {idx + 1}: {entry}")

    return tournament_data


def update_tournament_data(tournament_data):
    """Aktualisiere die Turnierdaten über die API."""
    url = f"{api_url}/tables/{table_id}/rows"

    headers = {
        "x-bot-id": bot_id,
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
        "content-type": "application/json"
    }

    # Daten im geforderten Format übergeben
    data = {"rows": tournament_data}

    try:
        response = requests.put(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        logging.info("Turnierdaten erfolgreich aktualisiert")
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP Fehler: {http_err} (Code: {response.status_code})")
        logging.error(f"Response: {response.text}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request Fehler: {req_err}")
    except Exception as err:
        logging.error(f"Unbekannter Fehler: {err}")


# Hauptprogramm für den Aufruf der Funktionen
if __name__ == "__main__":
    # Turnierdaten von der Webseite holen
    tournament_data = get_tournament_data()

    # Debugging-Ausgabe der gesamten Liste
    print("\nGesammelte Turnierdaten:")
    for entry in tournament_data:
        print(entry)

    if tournament_data:
        # Aktualisiere die Tabelle mit den Turnierdaten
        update_tournament_data(tournament_data)
    else:
        logging.info("Keine Turnierdaten gefunden.")

