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
import gc
# jenom ochrana pred kokotama
import os

def file_exists(filename):
    try:
        os.stat(filename)
        return True
    except OSError:
        return False

def rename_file(old_name, new_name):
    try:
        os.rename(old_name, new_name)
        print("Soubor přejmenován:", old_name, "→", new_name)
        return True
    except Exception as e:
        print("Chyba při přejmenování:", e)
        return False
    
def draw_multiline_text(tft, x, y, text, color, font, max_width=160):
        chars_per_line = max_width // 6
        lines = [text[i:i+chars_per_line] for i in range(0, len(text), chars_per_line)]
        for idx, line in enumerate(lines):
            tft.fb_text(x, y + idx*12, line, color, font)

def delete_file(filename):
    try:
        os.remove(filename)
        print("Soubor smazán:", filename)
        return True
    except Exception as e:
        print("Chyba při mazání souboru:", e)
        return False
    
#nacteni configu
if file_exists("example.config.py"):
    if not file_exists("config.py"):
        rename_file("example.config.py", "config.py")
        from config import zastavka, nastupiste, ssid, password, WHITE, RED, YELLOW, spi,tft, scroll_speed, scroll_speed_info , fetch_interval, draw_interval, frekvence, cesko, time_offset
        tft.initr()
        tft.fill(0)
        tft.rotation(1)
        draw_multiline_text(
            tft, 0, 0,
            "prosimte, moc jasne bylo v navodu napsany ze si mas nakonfigurovat soubor config.py pomoci souboru example.config.py, tedka jsem ti to prejmenoval ale jestli sis to nenastavil tak ti to nepojede",
            0xF800, sysfont)
        tft.show()
        utime.sleep(5)
    else: 
        delete_file("example.config.py")
        from config import zastavka, nastupiste, ssid, password, WHITE, RED, YELLOW, spi,tft, scroll_speed, scroll_speed_info , fetch_interval, draw_interval, frekvence, cesko, time_offset
elif file_exists("config.py"):
    from config import zastavka, nastupiste, ssid, password, WHITE, RED, YELLOW, spi,tft, scroll_speed, scroll_speed_info , fetch_interval, draw_interval, frekvence, cesko, time_offset
else:
    spi = machine.SPI(1, baudrate=20000000, polarity=0, phase=0)
    tft = st7735.TFT(spi, 14, 15, 13)
    tft.initr()
    tft.fill(0)
    tft.rotation(1)
    draw_multiline_text(
        tft, 0, 0,
        "ty kokote, musis si nastavit soubor config.py, ten soubor proste nemuzu najit",
        0xF800, sysfont
    )
    draw_multiline_text(
        tft, 0, 60,
        "Error code: PEBKAC (problem exists between keyboard and chair)",
        0xF800, sysfont
    )
    tft.show()
    exit("PEBKAC")

required_files = ["st7735.py", "pepega.bmp", "splash.bmp", "sysfont.py"]
if all(file_exists(f) for f in required_files):
    print("vsechno mas stazeny")
else:
    spi = machine.SPI(1, baudrate=20000000, polarity=0, phase=0)
    tft = st7735.TFT(spi, 14, 15, 13)
    tft.initr()
    tft.fill(0)
    tft.rotation(1)
    tft.fb_fill(0)
    draw_multiline_text(
        tft, 0, 0,
        "ty kokote, musis si na to rpi stahnout vsechny soubory",
        0xF800, sysfont
    )
    draw_multiline_text(
        tft, 0, 60,
        "Error code: PEBKAC (problem exists between keyboard and chair)",
        0xF800, sysfont
    )
    tft.show()
    exit("PEBKAC")

#realnej zacatek kodu
# display init
tft.initr()
tft.fill(0)
tft.rotation(1)

#nasaveni promenych
last_odjezdy = []
last_infotext = ""
last_error = ""
stopname = ""

# Splash screen
tft.fb_fill(0)
tft.fb_bmp("splash.bmp", 0, 0)
tft.show()
utime.sleep(10)
scroll_offset = 0

#wifina
if ssid == "SSID" or password == "passwd" or zastavka == "":
    tft.fb_fill(0)
    draw_multiline_text(
        tft, 0, 0,
        "ty kokote, musis si nastavit v souboru config.py wifinu a zastavku",
        RED, sysfont
    )
    draw_multiline_text(
        tft, 0, 60,
        "Error code: PEBKAC (problem exists between keyboard and chair)",
        RED, sysfont
    )
    tft.show()
    exit("PEBKAC")
else:
    machine.freq(frekvence)
    rp2.country('CZ')
    network.WLAN(network.STA_IF).active(True)
    network.WLAN(network.STA_IF).connect(ssid, password)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
timeout = 30
start = utime.time()
while not wlan.isconnected():
    tft.fb_fill(0)
    tft.fb_text(0, 0, "Pripojuji Wi-Fi...", WHITE, sysfont)
    tft.fb_text(0, 12, ssid, WHITE, sysfont)
    tft.show()
    if utime.time() - start > timeout:
        tft.fb_fill(0)
        tft.fb_bmp("pepega.bmp", 0, 0)
        tft.show()
        exit("Pepega")
    print("Cekam na Wi-Fi...")
    time.sleep(1)
tft.fb_fill(0)
tft.fb_text(0, 0, "Wi-Fi pripojena", WHITE, sysfont)
tft.fb_text(0, 12, wlan.ifconfig()[0], WHITE, sysfont)
tft.show()
print("Wi-Fi pripojena, IP adresa:", wlan.ifconfig()[0])
time.sleep(2)  # <-- přidejte tuto řádku

#píčoviny co něco dělaj s časem
def sync_time():
    try:
        ntptime.host = "cz.pool.ntp.org"
        ntptime.settime()
        print("Čas synchronizován z NTP.")
    except Exception as e:
        print("NTP sync failed:", e)
   
def cesky_cas():
     # ceskej cas
    t = utime.localtime(utime.time())
    year, month, mday, hour, minute, second, weekday, yearday = t
    def last_sunday(year, month):
        for day in range(31, 24, -1):
            try:
                if utime.localtime(utime.mktime((year, month, day, 0, 0, 0, 0, 0)))[6] == 6:
                    return day
            except:
                continue
        return 31

    start_dst = last_sunday(year, 3)
    end_dst = last_sunday(year, 10)

    if (month > 3 and month < 10) or \
       (month == 3 and (mday > start_dst or (mday == start_dst and hour >= 2))) or \
       (month == 10 and (mday < end_dst or (mday == end_dst and hour < 3))):
        offset = 2  # CEST
    else:
        offset = 1  # CET

    cesky_cas = utime.localtime(utime.time() + offset * 3600)
    return cesky_cas

sync_time()

def strip_diacritics(text):
    # ascii znaky
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
    text = strip_diacritics(text)
    return ''.join(c if 32 <= ord(c) <= 126 else ' ' for c in text)

def parse_time(cas):
    cas = str(cas).strip()
    cas = cas.replace("♿", "")  # Odstraň emoji vozíčkáře
    cas = cas.encode('ascii', 'ignore').decode()
    m = re.match(r"[+\-±]?(\d+)min", cas)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return 999999
    if ':' in cas:
        try:
            h, mi = cas.split(':')
            now = cesky_cas()
            h = int(h)
            mi = int(mi)
            now_sec = now[3]*3600 + now[4]*60
            t_sec = h*3600 + mi*60
            if t_sec < now_sec:
                t_sec += 24*3600
            return (t_sec - now_sec) // 60
        except Exception:
            return 999999
    if cas == "**":
        return 0
    return 999999

def clear():
    print("\n" * 20)
            
def clear_line(y, color=0, width=160, height=10):
    hi = color >> 8
    lo = color & 0xFF
    fb = tft.framebuf
    for row in range(y, min(y + height, tft._size[1])):
        idx = 2 * (row * tft._size[0])
        fb[idx:idx + width*2] = bytes([hi, lo]) * width

def draw_departures(odjezdy, infotext, scroll_offset):
    global last_error, stopname, scroll_offset_info

    # ... horní lišta a záhlaví ...
    tft.fb_fill(0)
    stopid = zastavka.replace("+", " ")[:20]
    now = cesky_cas()
    cas = "{:02d}:{:02d}:{:02d}".format(now[3], now[4], now[5])
    tft.fb_text(0, 0, stopid + " " + nastupiste, WHITE, sysfont)
    tft.fb_text(110, 0, cas, WHITE, sysfont)
    for xx in range(0, 160):
        tft.fb_pixel(xx, 8, WHITE)
    tft.fb_text(0, 10, "Linka", WHITE, sysfont)
    tft.fb_text(60, 10, "Smer", WHITE, sysfont)
    tft.fb_text(108, 10, "NP", WHITE, sysfont)
    tft.fb_text(124, 10, "Odjezd", WHITE, sysfont)
    for xx in range(0, 160):
        tft.fb_pixel(xx, 18, WHITE)
    tft.show_partial(0, 0, 160, 20)  # překresli pouze záhlaví

    y = 20

    if last_error:
        tft.fb_text(0, y, "Chyba site", RED, sysfont)
        err = to_ascii(str(last_error))
        for i in range(3):
            part = err[i*22:(i+1)*22]
            if part:
                tft.fb_text(0, y + 12 + i*12, part, RED, sysfont)
        tft.show_partial(0, y, 160, 48)
        return

    if not odjezdy:
        clear_line(y, 0)
        tft.fb_text(0, y, "Zadne odjezdy", RED, sysfont)
        tft.show_partial(0, y, 160, 10)
        y += 10
    else:
        for _, linka, konecna, vozik, cas in odjezdy[:10]:
            clear_line(y, 0)
            linka_ascii = to_ascii(f"{linka}")
            linka_px = len(linka_ascii) * 6
            konecna_ascii = to_ascii(f"{konecna}")
            konecna_px = len(konecna_ascii) * 6
            konecna_visible_chars = (110 - 25) // 6

            # Pro linka
            if linka_px > 120:
                visible_chars = 120 // 6
                start = scroll_offset_global % (len(linka_ascii) - visible_chars + 1)
                linka_visible = linka_ascii[start:start+visible_chars]
            else:
                linka_visible = linka_ascii

            # Pro konecna
            if konecna_px > konecna_visible_chars * 6:
                start_k = scroll_offset_global % (len(konecna_ascii) - konecna_visible_chars + 1)
                konecna_visible = konecna_ascii[start_k:start_k+konecna_visible_chars]
            else:
                konecna_visible = konecna_ascii
            if str(cas).replace("♿", "").strip() == "**":
                if ((scroll_offset // blikani_hvezdicek) % 2) == 0:
                    cas_text = "**"
                else:
                    cas_text = "  "
            else:
                cas_clean = str(cas).replace("♿", "")
                cas_text = to_ascii(cas_clean)

            x_cas = 159 - len(cas_text) * 6

            tft.fb_text(0, y, linka_visible, RED, sysfont)
            tft.fb_text(25, y, konecna_visible, RED, sysfont)
            tft.fb_text(112, y, to_ascii(f"{vozik}"), RED, sysfont)
            tft.fb_text(x_cas, y, cas_text, RED, sysfont)
            y += 10

    if infotext:
        if isinstance(infotext, list) and len(infotext) > 0:
            visible_chars = 160 // 6 + 1
            info_ascii_list = [to_ascii(str(info)) for info in infotext]
            scroll_steps = [max(1, len(info_ascii) - visible_chars + 1) for info_ascii in info_ascii_list]
            total_steps = sum(scroll_steps)
            step = scroll_offset_info % total_steps
            acc = 0
            for idx, steps in enumerate(scroll_steps):
                if step < acc + steps:
                    info_ascii = info_ascii_list[idx]
                    local_offset = step - acc
                    info_visible = info_ascii[local_offset:local_offset+visible_chars]
                    clear_line(y, 0)
                    tft.fb_text(0, y, info_visible, YELLOW, sysfont)
                    break
                acc += steps
        else:
            clear_line(y, 0)
            info_ascii = to_ascii(str(infotext))
            visible_chars = 160 // 6
            # Pro infotext
            if len(info_ascii) > visible_chars:
                start = scroll_offset_global % (len(info_ascii) - visible_chars + 1)
                info_visible = info_ascii[start:start+visible_chars]
            else:
                info_visible = info_ascii
            tft.fb_text(0, y, info_visible, YELLOW, sysfont)

    tft.show()

def fetch():
    global last_odjezdy, last_infotext, last_error, stopname
    print("Fetching data...")
    url = "https://www.idsjmk.cz/api/departures/busstop-by-name?busStopName=" + str(zastavka) + "&place=" + str(nastupiste)
    try:
        response = requests.get(url)
        last_error = ""  # Vynuluj chybu při úspěchu
    except Exception as e:
        tft.fb_fill(0)
        tft.fb_text(0, 0, "Chyba site (jestli to sviti uz dlouho tak to zkus restartovat)", RED, sysfont)
        tft.fb_text(0, 12, to_ascii(str(e)), RED, sysfont)
        tft.show()
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
                if not departures:
                    last_odjezdy = []
                    last_infotext = infotext
                    stopname = stop.get('name', '')
                    return
                for departure in departures:
                    linka = departure.get('link', '')
                    konecna = departure.get('destinationStop', '')
                    cas = departure.get('time', '')
                    beznohy = "♿" in cas
                    parsed = parse_time(cas)
                    odjezdy.append((parsed, linka, konecna, "o" if beznohy else "", cas))
        odjezdy_valid = [o for o in odjezdy if o[0] >= 0]
        odjezdy_invalid = [o for o in odjezdy if o[0] < 0]
        odjezdy_valid.sort(key=lambda x: x[0])
        odjezdy = odjezdy_valid + odjezdy_invalid
        last_odjezdy = odjezdy
        last_infotext = infotext
        last_error = ""  # Vynuluj chybu při úspěchu
    else:
        tft.fb_fill(0)
        tft.fb_text(0, 0, "Skill issue", RED, sysfont)
        tft.show()
        last_odjezdy = []
        last_infotext = ""
        stopname = ""
        last_error = "HTTP " + str(response.status_code)
    gc.collect()

# Hlavní smyčka
last_fetch = utime.time()
scroll_offset_info = 0
blikani_hvezdicek = 1

if cesko == True:
    now = cesky_cas()
elif cesko == False:
    now = utime.localtime(utime.time() + int(time_offset) * 3600)

cas = "{:02d}:{:02d}:{:02d}".format(now[3], now[4], now[5])

last_info_hash = ""
scroll_pause_until = 0
scroll_offset_global = 0

while True:
    now = utime.time()
    # Pauza scrollu infotextu
    info_hash = str(last_infotext)

    # Změna infotextu = reset scrollu a pauza
    if info_hash != last_info_hash:
        scroll_offset_global = 0
        scroll_pause_until = now + 2
        last_info_hash = info_hash

    # Zastavení na konci infotextu
    visible_chars = 160 // 6
    if isinstance(last_infotext, list) and len(last_infotext) > 0:
        info_ascii_list = [to_ascii(str(info)) for info in last_infotext]
        scroll_steps = [max(1, len(info_ascii) - visible_chars + 1) for info_ascii in info_ascii_list]
        total_steps = sum(scroll_steps)
        step = scroll_offset_global % total_steps
        acc = 0
        for idx, steps in enumerate(scroll_steps):
            if step < acc + steps:
                if step == acc + steps - 1 and scroll_pause_until < now:
                    scroll_pause_until = now + 2
                break
            acc += steps
    else:
        info_ascii = to_ascii(str(last_infotext))
        if len(info_ascii) > visible_chars:
            max_step = len(info_ascii) - visible_chars
            if (scroll_offset_global % (max_step + 1)) == max_step and scroll_pause_until < now:
                scroll_pause_until = now + 2

    if now - last_fetch > fetch_interval:
        fetch()
        last_fetch = now

    draw_departures(last_odjezdy, last_infotext, scroll_offset_global)

    if utime.time() >= scroll_pause_until:
        scroll_offset_global += scroll_speed 
        scroll_offset_info += scroll_speed_info 

    gc.collect()
    utime.sleep(draw_interval)