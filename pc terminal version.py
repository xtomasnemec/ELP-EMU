import sys
import requests
import time
import os

sys.stdout.reconfigure(encoding='utf-8')  # Přidáno pro správné zobrazování znaků


#var
zastavka = "Beloruska" #jestli je v nazvu mezera tak misto ni pouzij + (Krivankovo+Namesti)
nastupiste = "1" #nastupiste (nech prazdy aby se ukazovali vsechny odjezdy)


# API 
url = "https://www.idsjmk.cz/api/departures/busstop-by-name?busStopName=" + str(zastavka) + "&place=" + str(nastupiste)
response = requests.get(url)
print(url)

#clear
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

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