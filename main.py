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
    """Extrahiere Turnierdaten von der Webseite und konsolidiere die ersten 3 Einträge."""
    try:
        response = requests.get(WEB_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        logging.error(f"Fehler beim Abrufen der Webseite: {e}")
        return []

    tournament_data = []

    # Suche nach den Turnierdaten in den relevanten span-Tags
    events = soup.find_all("span", class_="tk-club")
    names = soup.find_all("span", class_="tk-public")

    # Maximal 3 Einträge erfassen
    for i in range(min(5, len(events))):
        datum = extract_clean_text(events[i])
        datum = clean_text(datum)  # Text bereinigen

        # Überprüfen, ob es genug Veranstaltungen gibt
        if i < len(names):
            veranstaltung = extract_clean_text(names[i], "Veranstaltung nicht gefunden")
            veranstaltung = clean_text(veranstaltung)  # Text bereinigen
        else:
            veranstaltung = "Veranstaltung nicht gefunden"

        logging.info(f"Datum: {datum}, Veranstaltung: {veranstaltung}")

        # Daten zur Liste hinzufügen
        tournament_data.append({
            "id": i + 1,  # ID zum Aktualisieren
            "Datum": datum,
            "Veranstaltung": veranstaltung,
            "Offen": "0"  # Platzhalter für die "Offen"-Spalte, kann später angepasst werden
        })

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

    # Daten für die Zeilen erstellen
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

if __name__ == "__main__":
    # Turnierdaten von der Webseite holen
    tournament_data = get_tournament_data()

    if tournament_data:
        # Aktualisiere die Tabelle mit den Turnierdaten
        update_tournament_data(tournament_data)
    else:
        logging.info("Keine Turnierdaten gefunden.")
