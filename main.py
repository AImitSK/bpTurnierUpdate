import os
import requests
from dotenv import load_dotenv
import json
from bs4 import BeautifulSoup
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)

load_dotenv()

api_url = os.getenv("ApiUrl").rstrip('/')
token = os.getenv("PersonalAccessToken")
table_id = os.getenv("TableId")
bot_id = os.getenv("BotId")

WEB_URL = "https://www.golfclub-rehburg-loccum.de/index.php?id=1"


def extract_status(soup, resource_name):
    """Hilfsfunktion, um den Status eines Platzes zu extrahieren."""
    try:
        status = soup.find(string=resource_name).find_next("div", class_="tx_gkmb_rs_pi1_statustext").text.strip()
        return status
    except AttributeError:
        logging.error(f"Konnte den Status für {resource_name} nicht finden.")
        return "-"


def get_data_from_web():
    # Webseite abrufen
    try:
        response = requests.get(WEB_URL)
        response.raise_for_status()  # Überprüfe auf Fehler
        soup = BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        logging.error(f"Fehler beim Abrufen der Webseite: {e}")
        return "-", "-", "-", "-", "-", "-"

    # Platzinformationen extrahieren
    status_18_loch = extract_status(soup, "18-Loch Platz")
    status_westwind = extract_status(soup, "WestWind-Kurzplatz")
    status_driving_range = extract_status(soup, "Driving-Range")
    status_uebungsgruens = extract_status(soup, "Übungsgrüns")
    status_trolleys = extract_status(soup, "Trolleys")
    status_e_carts = extract_status(soup, "E-Carts")

    # Rückgabe der Werte
    return status_18_loch, status_westwind, status_driving_range, status_uebungsgruens, status_trolleys, status_e_carts


def update_status(status_18_loch, status_westwind, status_driving_range, status_uebungsgruens, status_trolleys,
                  status_e_carts):
    url = f"{api_url}/tables/{table_id}/rows"

    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
        "content-type": "application/json",
        "x-bot-id": bot_id,
    }

    # Daten für die 6 Zeilen
    data = {
        "rows": [
            {"id": 1, "Status": status_18_loch},
            {"id": 2, "Status": status_westwind},
            {"id": 3, "Status": status_driving_range},
            {"id": 4, "Status": status_uebungsgruens},
            {"id": 5, "Status": status_trolleys},
            {"id": 6, "Status": status_e_carts},
        ]
    }

    try:
        response = requests.put(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        logging.info("Rows updated successfully")
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP Fehler: {http_err}")
        logging.error(f"Response: {response.text}")
    except Exception as err:
        logging.error(f"Anderer Fehler: {err}")


if __name__ == "__main__":
    # Hole die Daten von der Webseite
    status_18_loch, status_westwind, status_driving_range, status_uebungsgruens, status_trolleys, status_e_carts = get_data_from_web()

    # Aktualisiere die Tabelle mit den Werten
    update_status(status_18_loch, status_westwind, status_driving_range, status_uebungsgruens, status_trolleys,
                  status_e_carts)
