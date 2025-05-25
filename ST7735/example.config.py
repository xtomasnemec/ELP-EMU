# ty importy jsou tady potreba, nehrab na to
import machine
import st7735

#var
zastavka = "" #jestli je v nazvu mezera tak misto ni pouzij "+" priklad:(Krivankovo+Namesti)
nastupiste = "" #nastupiste (nech prazdy aby se ukazovali vsechny odjezdy)
ssid = "SSID"  # Zde zadejte název vaší Wi-Fi sítě (deafult: SSID)
password = "passwd"  # Zde zadejte heslo k vaší Wi-Fi síti (deafult: passwd)

#barvicky
WHITE = 0xFFFF
RED = 0xF800
YELLOW = 0xFFE0

#konfigurace displeje
spi = machine.SPI(1, baudrate=40000000, polarity=0, phase=0) # SPI bus configuration
tft = st7735.TFT(spi, 14, 15, 13) # nastaveni pinu, 14 - CS, 15 - DC, 13 - RESET (jestli pouzivas ten pinout co mam na githubu tak do toho nedrbej)

#rychlost scrolovani textu
scroll_speed = 1 # rychlost scrolovani textu (default: 1)
scroll_speed_info = 3 # rychlost scrolovani vyluk (default: 3)
scroll_pause_interval = 2  # pauza mezi scrollovanim (default: 2) - v sekundach

#rychlost aktualizace
fetch_interval = 15  # sekund
draw_interval = 0.2  # sekund

#frekvence rpi pico
frekvence = 250_000_000 # frekvence rpi pico (default: 250_000_000) muze byt i mensi, ale pak se bude pomaleji aktualizovat displej

#čas
cesko = True # jestli chces cesky cas tak dej true, jinak false (default: true)
time_offset = 0 # casovy posun v hodinach (default: 0) jestli mas cesko = true tak dej 0, jinak dej cislo podle tvoji casove zony (napr. 1 pro stredoevropsky cas, 2 pro východoevropský čas atd.)