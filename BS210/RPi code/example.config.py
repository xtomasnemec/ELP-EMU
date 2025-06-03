#var
zastavka = "" #jestli je v nazvu mezera tak misto ni pouzij "+" priklad:(Krivankovo+Namesti)
nastupiste = "" #nastupiste (nech prazdy aby se ukazovali vsechny odjezdy)
ssid = "SSID"  # Zde zadejte název vaší Wi-Fi sítě (deafult: SSID)
password = "passwd"  # Zde zadejte heslo k vaší Wi-Fi síti (deafult: passwd)

#rychlost aktualizace
fetch_interval = 15  # sekund

#frekvence rpi pico
frekvence = 250_000_000 # frekvence rpi pico (default: 250_000_000) muze byt i mensi, ale pak se bude pomaleji aktualizovat displej

#čas
cesko = True # jestli chces cesky cas tak dej true, jinak false (default: true)
time_offset = 0 # casovy posun v hodinach (default: 0) jestli mas cesko = true tak dej 0, jinak dej cislo podle tvoji casove zony (napr. 1 pro stredoevropsky cas, 2 pro východoevropský čas atd.)