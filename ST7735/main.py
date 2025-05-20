import time
import network
import rp2
import machine
import urequests as requests
import utime
import re
import st7735
from sysfont import sysfont
import ntptime

#var
zastavka = "Beloruska" #jestli je v nazvu mezera tak misto ni pouzij + (Krivankovo+Namesti)
nastupiste = "" #nastupiste (nech prazdy aby se ukazovali vsechny odjezdy)
ssid = "SSID"  # Zde zadejte název vaší Wi-Fi sítě
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
tft.show_bmp("splash.bmp")
utime.sleep(10)
scroll_offset = 0

#wifina
if ssid == "SSID" or password == "passwd":
    tft.fill(0)
    def draw_multiline_text(tft, x, y, text, color, font, max_width=160):
        chars_per_line = max_width // 6
        lines = [text[i:i+chars_per_line] for i in range(0, len(text), chars_per_line)]
        for idx, line in enumerate(lines):
            tft.text((x, y + idx*12), line, color, font)

    draw_multiline_text(
        tft, 0, 0,
        "ty kokote, musis si nastavit v souboru main.py wifinu a zastavku",
        RED, sysfont
    )
    draw_multiline_text(
        tft, 0, 60,
        "Error code: PEBKAC (problem exists between keyboard and chair)",
        RED, sysfont
    )
    exit("PEBKAC")
else:
    machine.freq(133000000)
    rp2.country('CZ')
    network.WLAN(network.STA_IF).active(True)
    network.WLAN(network.STA_IF).connect(ssid, password)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
timeout = 30
start = utime.time()
while not wlan.isconnected():
    tft.fill(0)
    tft.text((0, 0), "Pripojuji Wi-Fi...", WHITE, sysfont)
    tft.text((0, 12), ssid, WHITE, sysfont)
    if utime.time() - start > timeout:
        tft.fill(0)
        tft.show_bmp("pepega.bmp")
        exit("Pepega")
    print("Cekam na Wi-Fi...")
    time.sleep(1)
tft.fill(0)
tft.text((0, 0), "Wi-Fi pripojena", WHITE, sysfont)
tft.text((0, 12), wlan.ifconfig()[0], WHITE, sysfont)
print("Wi-Fi pripojena, IP adresa:", wlan.ifconfig()[0])
time.sleep(2)  # <-- přidejte tuto řádku

def sync_time():
    try:
        ntptime.host = "pool.ntp.org"  # můžeš změnit na cz.pool.ntp.org
        ntptime.settime()
        print("Čas synchronizován z NTP.")
    except Exception as e:
        print("NTP sync failed:", e)

sync_time()  # <-- přidej tuto řádku

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
    cas = str(cas).strip()
    cas = cas.encode('ascii', 'ignore').decode()
    if ':' in cas:
        h, mi = cas.split(':')
        now = utime.localtime()
        h = int(h)
        mi = int(mi)
        now_sec = now[3]*3600 + now[4]*60
        t_sec = h*3600 + mi*60
        if t_sec < now_sec:
            t_sec += 24*3600
        return (t_sec - now_sec) // 60
    m = re.match(r"[+\-±]?(\d+)min", cas)
    if m:
        return int(m.group(1))
    if cas == "**":
        return -1
    return 999999

def clear():
    print("\n" * 20)
            
def clear_line(y, color=0, width=160, height=10):
    tft.fillrect((0, y), (width, height), color)

last_odjezdy = []
last_infotext = ""
scroll_offset = 0
last_error = "" 
stopname = ""

def draw_departures(odjezdy, infotext, scroll_offset):
    global last_error, stopname

    # První řádek: zobraz zastavka s nahrazením + za mezeru
    tft.fillrect((0, 0), (160, 10), 0)
    stopid = zastavka.replace("+", " ")[:20]
    now = utime.localtime()
    cas = "{:02d}:{:02d}:{:02d}".format(now[3], now[4], now[5])
    tft.text((0, 0), stopid + " " + nastupiste, WHITE, sysfont)
    tft.text((110, 0), cas, WHITE, sysfont)

    # Druhý řádek: hlavička
    tft.fillrect((0, 10), (160, 10), 0)
    tft.text((0, 10), "Linka", WHITE, sysfont)
    tft.text((60, 10), "Cil", WHITE, sysfont)
    tft.text((108, 10), "NP", WHITE, sysfont)
    tft.text((124, 10), "Odjezd", WHITE, sysfont)

    y = 20  # další řádky začínají až pod tímto


    if last_error:
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
            if str(cas).strip() == "**":
                if (scroll_offset % 2) == 0:
                    cas_text = "**"
                else:
                    cas_text = "  "
            else:
                cas_text = to_ascii(str(cas))
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
        # Pokud je infotext list, zobrazuj vždy jen jeden a cykli podle scroll_offset
        if isinstance(infotext, list) and len(infotext) > 0:
            visible_chars = 160 // 6  # 26 znaků na řádek
            # Vyber index infotextu podle toho, kolik už se odscrollovalo
            info_ascii_list = [to_ascii(str(info)) for info in infotext]
            # Spočítej, kolik scrollovacích kroků zabere každý infotext
            scroll_steps = [max(1, len(info_ascii) - visible_chars + 1) for info_ascii in info_ascii_list]
            total_steps = sum(scroll_steps)
            # Najdi, který infotext se má aktuálně zobrazit
            step = scroll_offset % total_steps
            acc = 0
            for idx, steps in enumerate(scroll_steps):
                if step < acc + steps:
                    info_ascii = info_ascii_list[idx]
                    local_offset = step - acc
                    info_visible = info_ascii[local_offset:local_offset+visible_chars]
                    clear_line(y, 0)
                    tft.text((0, y), info_visible, 0xFFE0, sysfont)
                    break
                acc += steps
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
                # Filtrování podle nastupiste (number v busStopSign)
                if nastupiste:
                    if str(sign.get('busStopSign', {}).get('number', '')) != str(nastupiste):
                        continue
                departures = sign.get('departures', [])
                for departure in departures:
                    linka = departure.get('link', '')
                    konecna = departure.get('destinationStop', '')
                    cas = departure.get('time', '')
                    beznohy = "♿" in cas
                    fixedcas = re.sub(r"[^\d:]", "", cas)
                    print("API cas:", repr(cas))
                    print("FIXED cas:", repr(fixedcas))
                    parsed = parse_time(fixedcas)
                    print("PARSED:", parsed)
                    odjezdy.append((parsed, linka, konecna, "o" if beznohy else "", fixedcas))
        odjezdy_valid = [o for o in odjezdy if o[0] >= 0]
        odjezdy_invalid = [o for o in odjezdy if o[0] < 0]
        odjezdy_valid.sort(key=lambda x: x[0])
        odjezdy = odjezdy_valid + odjezdy_invalid
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
    for o in odjezdy:
        print("DEBUG:", o)
        print("API cas:", repr(cas))
        print("FIXED cas:", repr(fixedcas))

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