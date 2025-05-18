import time
import network
import rp2
import machine
import urequests as requests
import re
import utime

#var
zastavka = "Beloruska" #jestli je v nazvu mezera tak misto ni pouzij + (Krivankovo+Namesti)
nastupiste = "1" #nastupiste (nech prazdy aby se ukazovali vsechny odjezdy)
ssid = "ssid"
password = "passwd"

machine.freq(133000000)
rp2.country('CZ')
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while not wlan.isconnected():
    time.sleep(1)

def parse_time(cas):
    m = re.match(r"(\d+)min", cas)
    if m:
        return int(m.group(1))
    m = re.match(r"(\d{1,2}):(\d{2})", cas)
    if m:
        now = utime.localtime()
        h, mi = int(m.group(1)), int(m.group(2))
        # Dnešní čas v sekundách od půlnoci
        now_sec = now[3]*3600 + now[4]*60
        t_sec = h*3600 + mi*60
        # Pokud je čas v minulosti, je to zítra
        if t_sec < now_sec:
            t_sec += 24*3600
        return (t_sec - now_sec) // 60
    if cas.strip() == "**":
        return -1
    return 9999

def clear():
    print("\n" * 20)

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
        for _, linka, konecna, vozik, cas in odjezdy:
            print(linka, konecna, vozik, cas)
        print("--------------------------------------------------------------------")
        if isinstance(infotext, list):
            for info in infotext:
                print(info)
        else:
            print(infotext)
    else:
        print("Skill issue, nenačetlo se to. Status code:", response.status_code)

while True:
    clear()
    fetch()
    time.sleep(5)