import sys
import requests
import time
import os
import re
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')  # Přidáno pro správné zobrazování znaků


#var
zastavka = "Hlavni+Nadrazi" #jestli je v nazvu mezera tak misto ni pouzij + (Krivankovo+Namesti)
nastupiste = "78" #nastupiste (nech prazdy aby se ukazovali vsechny odjezdy)


# API 
url = "https://www.idsjmk.cz/api/departures/busstop-by-name?busStopName=" + str(zastavka) + "&place=" + str(nastupiste)
response = requests.get(url)
print(url)

#clear
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def parse_time(cas):
    # Povolit +, -, ± na začátku
    m = re.match(r"[+\-±]?(\d+)min", cas)
    if m:
        return int(m.group(1))
    m = re.match(r"(\d{1,2}):(\d{2})", cas)
    if m:
        now = datetime.now()
        h, mi = int(m.group(1)), int(m.group(2))
        t = now.replace(hour=h, minute=mi, second=0, microsecond=0)
        if t < now:
            t += timedelta(days=1)  # Přes půlnoc
        return int((t - now).total_seconds() // 60)
    if cas.strip() == "**":
        return -1
    return 9999

#nacist vsechen bordel
def fetch():
    if response.status_code == 200:
        data = response.json()
        stops = data['stops']
        odjezdy = []

        for stop in stops:
            signs = stop['signs']
            infotext = stop['infoText']

            for sign in signs:
                departures = sign['departures']
                for departure in departures:
                    linka = departure['link']
                    konecna = departure['destinationStop']
                    cas = departure['time']
                    beznohy = "♿" in cas
                    fixedcas = cas.replace("♿", "").strip()
                    odjezdy.append((parse_time(fixedcas), linka, konecna, "♿" if beznohy else "", fixedcas))

        # Seřadit podle času
        odjezdy.sort(key=lambda x: x[0])

        for _, linka, konecna, vozik, cas in odjezdy:
            print(linka, konecna, vozik, cas)

        print("--------------------------------------------------------------------")
        # infotext výpis
        if isinstance(infotext, list):
            for info in infotext:
                print(info)
        else:
            print(infotext)
    else:
        print("Skill issue, nenačetlo se to. Status code:", response.status_code)


loop = True
while loop:
    clear()
    fetch()
    time.sleep(5)