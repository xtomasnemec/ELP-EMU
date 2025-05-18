import requests
import time
import network
import rp2
import machine
import urequests as requests

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

while not network.WLAN(network.STA_IF).isconnected():
    time.sleep(1)

# API 
url = "https://www.idsjmk.cz/api/departures/busstop-by-name?busStopName=" + str(zastavka) + "&place=" + str(nastupiste)
response = requests.get(url)
print(url)

#clear
def clear():
    # MicroPython nemá os.system, místo toho vypiš prázdné řádky
    print("\n" * 20)

#nacist vsechen bordel
def fetch():
    if response.status_code == 200:
        data = response.json()
        stops = data['stops']

        for stop in stops:
            signs = stop['signs']
            infotext = stop['infoText']

            for sign in signs:
                departures = sign['departures']
                for departure in departures:
                    # print vsech info
                    linka = departure['link']
                    konecna = departure['destinationStop']
                    cas = departure['time']
                    if "♿" in cas:
                        fixedcas = cas.replace("♿", "",)
                        beznohy = True
                    else:
                        beznohy = False
                        fixedcas = cas
                    if beznohy == True:
                        print(linka, konecna, "♿", fixedcas)
                    elif beznohy == False:
                        print(linka, konecna, fixedcas)
            print("--------------------------------------------------------------------")
            # Pokud infotext je seznam, vypiš každý řádek zvlášť
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