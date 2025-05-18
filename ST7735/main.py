import time
import network
import rp2
import machine
import urequests as requests
import st7735
import utime
import re

#var
zastavka = "Beloruska" #jestli je v nazvu mezera tak misto ni pouzij + (Krivankovo+Namesti)
nastupiste = "1" #nastupiste (nech prazdy aby se ukazovali vsechny odjezdy)
ssid = "SSID"  # Zde zadejte název vaší Wi-Fi sítě
password = "Heslo"  # Zde zadejte heslo k vaší Wi-Fi síti

# Přidáno pro správné zobrazení češtiny v konzoli
machine.freq(133000000)  # Nastavení frekvence CPU na 133MHz (pokud je potřeba)
rp2.country('CZ')  # Nastavení země pro Wi-Fi
network.WLAN(network.STA_IF).active(True)  # Aktivace Wi-Fi
network.WLAN(network.STA_IF).connect(ssid, password)  # Připojení k Wi-Fi

# Připojení k Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
while not wlan.isconnected():
    time.sleep(1)

def parse_time(cas):
    # Povolit +, -, ± na začátku
    m = re.match(r"[+\-±]?(\d+)min", cas)
    if m:
        return int(m.group(1))
    m = re.match(r"(\d{1,2}):(\d{2})", cas)
    if m:
        now = utime.localtime()
        h, mi = int(m.group(1)), int(m.group(2))
        now_sec = now[3]*3600 + now[4]*60
        t_sec = h*3600 + mi*60
        if t_sec < now_sec:
            t_sec += 24*3600
        return (t_sec - now_sec) // 60
    if cas.strip() == "**":
        return -1
    return 9999

def clear():
    print("\n" * 20)
            
#nacist vsechen bordel
def fetch():
    url = "https://www.idsjmk.cz/api/departures/busstop-by-name?busStopName=" + str(zastavka) + "&place=" + str(nastupiste)
    response = requests.get(url)
    print(url)
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
        # Výpis na displej (příklad, uprav podle potřeby)
        tft.fill(0)
        y = 0
        for _, linka, konecna, vozik, cas in odjezdy[:12]:
            tft.text(f"{linka} {konecna} {vozik} {cas}", 0, y, 0xFFFF)
            y += 10
        # infotext na displej
        if isinstance(infotext, list):
            for info in infotext:
                tft.text(str(info)[:16], 0, y, 0xFFE0)
                y += 10
        else:
            tft.text(str(infotext)[:16], 0, y, 0xFFE0)
    else:
        tft.fill(0)
        tft.text("Skill issue", 0, 0, 0xF800)

while True:
    fetch()
    time.sleep(5)