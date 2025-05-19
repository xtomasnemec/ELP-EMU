import time
import network
import rp2
import machine
import urequests as requests
import utime
import re
import st7735
from sysfont import sysfont

#var
zastavka = "Privrat" #jestli je v nazvu mezera tak misto ni pouzij + (Krivankovo+Namesti)
nastupiste = "1" #nastupiste (nech prazdy aby se ukazovali vsechny odjezdy)
ssid = "ssid"  # Zde zadejte název vaší Wi-Fi sítě
password = "passwd"  # Zde zadejte heslo k vaší Wi-Fi síti

#barvicky
WHITE = 0xFFFF
RED = 0xF800

# Nastavení SPI a pinů
spi = machine.SPI(1, baudrate=20000000, polarity=0, phase=0)
tft = st7735.TFT(spi, 14, 15, 13)
tft.initr()
tft.fill(0)
tft.rotation(1)
scroll_offset = 0

#wifina
machine.freq(133000000)
rp2.country('CZ')
network.WLAN(network.STA_IF).active(True)
network.WLAN(network.STA_IF).connect(ssid, password)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
timeout = 30  # sekund
start = utime.time()
while not wlan.isconnected():
    if utime.time() - start > timeout:
        print("Wi-Fi se nepripojila, restartuji...")
        machine.reset()
    print("Cekam na Wi-Fi...")
    time.sleep(1)
print("Wi-Fi pripojena, IP adresa:", wlan.ifconfig()[0])

def strip_diacritics(text):
    # Ručně nahradí českou/slovenskou diakritiku za nejbližší ASCII znak
    replace = (
        ("á", "a"), ("č", "c"), ("ď", "d"), ("é", "e"), ("ě", "e"), ("í", "i"),
        ("ň", "n"), ("ó", "o"), ("ř", "r"), ("š", "s"), ("ť", "t"), ("ú", "u"),
        ("ů", "u"), ("ý", "y"), ("ž", "z"),
        ("Á", "A"), ("Č", "C"), ("Ď", "D"), ("É", "E"), ("Ě", "E"), ("Í", "I"),
        ("Ň", "N"), ("Ó", "O"), ("Ř", "R"), ("Š", "S"), ("Ť", "T"), ("Ú", "U"),
        ("Ů", "U"), ("Ý", "Y"), ("Ž", "Z"), ("±", "~")
    )
    for orig, repl in replace:
        text = text.replace(orig, repl)
    return text

def to_ascii(text):
    # Nejprve odstraní diakritiku, pak nahradí zbylé ne-ASCII znaky otazníkem
    text = strip_diacritics(text)
    return ''.join(c if 32 <= ord(c) <= 126 else '?' for c in text)

def parse_time(cas):
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
            
def clear_line(y, color=0, width=160, height=10):
    tft.fillrect((0, y), (width, height), color)

last_odjezdy = []
last_infotext = ""
scroll_offset = 0
last_error = ""  # Přidáno
stopname = ""

def draw_departures(odjezdy, infotext, scroll_offset):
    global last_error, stopname

    # První řádek: zobraz zastavka s nahrazením + za mezeru
    tft.fillrect((0, 0), (160, 10), 0)
    stopid = zastavka.replace("+", " ")[:20]
    now = utime.localtime()
    cas = "{:02d}:{:02d}:{:02d}".format(now[3], now[4], now[5])
    tft.text((0, 0), stopid, WHITE, sysfont)
    tft.text((110, 0), cas, WHITE, sysfont)

    # Druhý řádek: hlavička
    tft.fillrect((0, 10), (160, 10), 0)
    tft.text((0, 10), "Linka", WHITE, sysfont)
    tft.text((60, 10), "Cil", WHITE, sysfont)
    tft.text((108, 10), "NP", WHITE, sysfont)
    tft.text((124, 10), "Odjezd", WHITE, sysfont)

    y = 20  # další řádky začínají až pod tímto

    if last_error:
        # Chybová hláška až pod hlavičkou
        tft.text((0, y), "Chyba site", RED, sysfont)
        err = to_ascii(str(last_error))
        for i in range(3):
            part = err[i*22:(i+1)*22]
            if part:
                tft.text((0, y + 12 + i*12), part, RED, sysfont)
        return

    if odjezdy:
        for _, linka, konecna, vozik, cas in odjezdy[:6]:
            clear_line(y, 0)
            linka_ascii = to_ascii(f"{linka}")
            linka_px = len(linka_ascii) * 6
            if linka_px > 120:
                visible_chars = 120 // 6
                start = scroll_offset % (len(linka_ascii) - visible_chars + 1)
                linka_visible = linka_ascii[start:start+visible_chars]
            else:
                linka_visible = linka_ascii

            konecna_ascii = to_ascii(f"{konecna}")
            konecna_px = len(konecna_ascii) * 6
            konecna_visible_chars = (110 - 25) // 6  # prostor pro konečnou
            if konecna_px > konecna_visible_chars * 6:
                start_k = scroll_offset % (len(konecna_ascii) - konecna_visible_chars + 1)
                konecna_visible = konecna_ascii[start_k:start_k+konecna_visible_chars]
            else:
                konecna_visible = konecna_ascii

            cas_text = to_ascii(f"{cas}")
            x_cas = 159 - len(cas_text) * 6

            tft.text((0, y), linka_visible, RED, sysfont)
            tft.text((25, y), konecna_visible, RED, sysfont)
            tft.text((112, y), to_ascii(f"{vozik}"), RED, sysfont)
            tft.text((x_cas, y), cas_text, RED, sysfont)
            y += 10
    else:
        tft.text((0, y), "Zadne odjezdy", RED, sysfont)
        y += 10
    if infotext:
        if isinstance(infotext, list):
            for info in infotext:
                clear_line(y, 0)
                info_ascii = to_ascii(str(info))
                visible_chars = 160 // 6  # 26 znaků na řádek
                if len(info_ascii) > visible_chars:
                    start = scroll_offset % (len(info_ascii) - visible_chars + 1)
                    info_visible = info_ascii[start:start+visible_chars]
                else:
                    info_visible = info_ascii
                tft.text((0, y), info_visible, 0xFFE0, sysfont)
                y += 10
        else:
            clear_line(y, 0)
            info_ascii = to_ascii(str(infotext))
            visible_chars = 160 // 6  # 26 znaků na řádek
            if len(info_ascii) > visible_chars:
                start = scroll_offset % (len(info_ascii) - visible_chars + 1)
                info_visible = info_ascii[start:start+visible_chars]
            else:
                info_visible = info_ascii
            tft.text((0, y), info_visible, 0xFFE0, sysfont)

def fetch():
    global last_odjezdy, last_infotext, last_error, stopname
    print("Fetching data...")
    url = "https://www.idsjmk.cz/api/departures/busstop-by-name?busStopName=" + str(zastavka) + "&place=" + str(nastupiste)
    try:
        response = requests.get(url)
        last_error = ""  # Vynuluj chybu při úspěchu
    except Exception as e:
        tft.fill(0)
        tft.text((0, 0), "Chyba site (jestli to sviti uz dlouho tak to zkus restartovat)", RED, sysfont)
        tft.text((0, 12), to_ascii(str(e)), RED, sysfont)
        print("Network error:", e)
        last_odjezdy = []
        last_infotext = ""
        stopname = ""
        last_error = str(e)  # Ulož chybu
        return

    print("fetched from", url)
    if response.status_code == 200:
        data = response.json()
        stops = data.get('stops', [])
        odjezdy = []
        infotext = ""
        if not stops:
            last_odjezdy = []
            last_infotext = ""
            stopname = ""
            return
        stopname = stops[0].get('name', '')  # Ulož název zastávky
        for stop in stops:
            signs = stop.get('signs', [])
            infotext = stop.get('infoText', "")
            for sign in signs:
                departures = sign.get('departures', [])
                for departure in departures:
                    linka = departure.get('link', '')
                    konecna = departure.get('destinationStop', '')
                    cas = departure.get('time', '')
                    beznohy = "♿" in cas
                    fixedcas = cas.replace("♿", "").strip()
                    odjezdy.append((parse_time(fixedcas), linka, konecna, "o" if beznohy else "", fixedcas))
        odjezdy.sort(key=lambda x: x[0])
        last_odjezdy = odjezdy
        last_infotext = infotext
        last_error = ""  # Vynuluj chybu při úspěchu
    else:
        tft.fill(0)
        tft.text((0, 0), "Skill issue", RED, sysfont)
        last_odjezdy = []
        last_infotext = ""
        stopname = ""
        last_error = "HTTP " + str(response.status_code)

# Hlavní smyčka
fetch_interval = 15  # sekund
draw_interval = 0.5  # sekund
last_fetch = utime.time()
scroll_offset = 0

while True:
    now = utime.time()
    if now - last_fetch >= fetch_interval:
        fetch()
        last_fetch = now

    draw_departures(last_odjezdy, last_infotext, scroll_offset)
    scroll_offset += 1
    utime.sleep(0.1)