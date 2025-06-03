import time
import network
import rp2
import machine
import urequests as requests
import utime
import re
import ntptime
import gc
import os

uart = machine.UART(0, baudrate=115200, tx=machine.Pin(0), rx=machine.Pin(1))

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

def delete_file(filename):
    try:
        os.remove(filename)
        print("Soubor smazán:", filename)
        return True
    except Exception as e:
        print("Chyba při mazání souboru:", e)
        return False

# nacteni configu
if file_exists("example.config.py"):
    if not file_exists("config.py"):
        rename_file("example.config.py", "config.py")
        from config import zastavka, nastupiste, ssid, password, WHITE, RED, YELLOW, spi, tft, scroll_speed, scroll_speed_info, fetch_interval, draw_interval, frekvence, cesko, time_offset, scroll_pause_interval
        print("Upozornění: nastav si config.py podle example.config.py!")
        time.sleep(5)
    else:
        delete_file("example.config.py")
        from config import zastavka, nastupiste, ssid, password, WHITE, RED, YELLOW, spi, tft, scroll_speed, scroll_speed_info, fetch_interval, draw_interval, frekvence, cesko, time_offset
elif file_exists("config.py"):
    from config import zastavka, nastupiste, ssid, password, WHITE, RED, YELLOW, spi, tft, scroll_speed, scroll_speed_info, fetch_interval, draw_interval, frekvence, cesko, time_offset, scroll_pause_interval
else:
    print("Chybí config.py! Zkopíruj si example.config.py a nastav ho.")
    exit("PEBKAC")

required_files = ["st7735.py", "pepega.bmp", "splash.bmp", "sysfont.py", "beznohy.py", "config.py"]
if not all(file_exists(f) for f in required_files):
    print("Chybí některé potřebné soubory! Stáhni je na zařízení.")
    exit("PEBKAC")

# nasaveni promenych
last_odjezdy = []
last_infotext = ""
last_error = ""
stopname = ""

# Splash screen (nahrazeno printem)
print("SPLASH SCREEN")
time.sleep(2)

# wifina
if ssid == "SSID" or password == "passwd" or zastavka == "":
    print("Musíš nastavit Wi-Fi a zastávku v config.py!")
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
    print("Připojuji Wi-Fi...", ssid)
    if utime.time() - start > timeout:
        print("Timeout při připojování Wi-Fi!")
        exit("Pepega")
    print("Cekam na Wi-Fi...")
    time.sleep(1)
print("Wi-Fi připojena, IP adresa:", wlan.ifconfig()[0])
time.sleep(2)

def sync_time():
    try:
        ntptime.host = "cz.pool.ntp.org"
        ntptime.settime()
        print("Čas synchronizován z NTP.")
    except Exception as e:
        print("NTP sync failed:", e)

def cesky_cas():
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

def parse_time(cas):
    cas = str(cas).strip()
    cas = cas.replace("♿", "")
    cas = cas.encode('ascii', 'ignore').decode()
    m = re.match(r"[+\-±]?(\d+)min", cas)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return 9999999
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

def draw_departures(odjezdy):
    global last_error, stopname
    print("="*40)
    if stopname:
        print("Zastávka:", stopname)
    now = cesky_cas()
    cas = "{:02d}:{:02d}:{:02d}".format(now[3], now[4], now[5])
    print("Čas:", cas)
    if last_error:
        print("Chyba sítě:", last_error)
        return
    if not odjezdy:
        print("Žádné odjezdy")
    else:
        print("Linka | Konečná | NP | Odjezd")
        for _, linka, konecna, vozik, cas in odjezdy[:10]:
            print("{:>5} | {:<20} | {} | {}".format(linka, konecna, vozik, cas))
            # Odeslání na Arduino přes UART
            msg = "LINE:{}\n".format(linka)
            uart.write(msg)
            msg = "TEXT:{}\n".format(konecna)
            uart.write(msg)
    if last_infotext:
        print("Info:", last_infotext)
    print("="*40)

def fetch():
    global last_odjezdy, last_infotext, last_error, stopname
    print("Fetching data...")
    url = "https://www.idsjmk.cz/api/departures/busstop-by-name?busStopName=" + str(zastavka) + "&place=" + str(nastupiste)
    try:
        response = requests.get(url)
        last_error = ""
    except Exception as e:
        print("Network error:", e)
        last_odjezdy = []
        last_infotext = ""
        stopname = ""
        last_error = str(e)
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
        stopname = stops[0].get('name', '')
        for stop in stops:
            signs = stop.get('signs', [])
            infotext = stop.get('infoText', "")
            for sign in signs:
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
                    odjezdy.append((parsed, linka, konecna, "o" if beznohy else " ", cas))
        odjezdy_valid = [o for o in odjezdy if o[0] >= 0]
        odjezdy_invalid = [o for o in odjezdy if o[0] < 0]
        odjezdy_valid.sort(key=lambda x: x[0])
        odjezdy = odjezdy_valid + odjezdy_invalid
        last_odjezdy = odjezdy
        last_infotext = infotext
        last_error = ""
    else:
        print("Skill issue: HTTP", response.status_code)
        last_odjezdy = []
        last_infotext = ""
        stopname = ""
        last_error = "HTTP " + str(response.status_code)
    gc.collect()

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
scroll_pause_until_info = 0
scroll_pause_until_global = 0

# main loop
while True:
    now = utime.time()
    visible_chars = 160 // 6
    if now - last_fetch > fetch_interval:
        fetch()
        last_fetch = now
    draw_departures(last_odjezdy, last_infotext, scroll_offset_global)
    gc.collect()