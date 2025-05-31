from machine import UART, Pin
import utime as time

uart = None

def set_uart(uart_instance):
    global uart
    uart = uart_instance

def connect_panel(uart_id=0, tx_pin=0, rx_pin=1, baudrate=1200, bits=7, parity=0, stop=2):
    """
    Inicializuje UART pro komunikaci s panelem BS210.
    Vrací inicializovaný UART objekt.
    """
    from machine import UART, Pin
    uart = UART(0, baudrate=baudrate, bits=bits, parity=parity, stop=stop, tx=Pin(tx_pin), rx=Pin(rx_pin))
    time.sleep(0.3)  # počkej na stabilizaci UART
    return uart

def to_kamenicky(text):
    # Kompletní převodník Unicode → Kód Kamenických (KEYBCS2)
    tab = {
        "ě": 0x8A, "š": 0x9A, "č": 0x8C, "ř": 0x8D, "ž": 0x9E, "ý": 0x9D,
        "á": 0xA0, "í": 0xA1, "é": 0x82, "ú": 0xA3, "ů": 0xA5, "ť": 0x9F,
        "ď": 0x8E, "ň": 0xA4, "ó": 0xA2, "ú": 0xA3, "ě": 0x8A,
        "Ě": 0x8A, "Š": 0x9A, "Č": 0x8C, "Ř": 0x8D, "Ž": 0x9E, "Ý": 0x9D,
        "Á": 0xA0, "Í": 0xA1, "É": 0x82, "Ú": 0xA3, "Ů": 0xA5, "Ť": 0x9F,
        "Ď": 0x8E, "Ň": 0xA4, "Ó": 0xA2, "Ú": 0xA3,
        "ä": 0x84, "Ä": 0x8E, "ö": 0x94, "Ö": 0x99, "ü": 0x81, "Ü": 0x9A,
        "ß": 0xE1, "ô": 0xA4, "Ô": 0xA4, "ĺ": 0xA5, "Ĺ": 0xA5,
        "ľ": 0xA3, "Ľ": 0xA3, "ĺ": 0xA5, "Ĺ": 0xA5,
        "ě": 0x8A, "Ě": 0x8A, "č": 0x8C, "Č": 0x8C, "ř": 0x8D, "Ř": 0x8D,
        "ž": 0x9E, "Ž": 0x9E, "ý": 0x9D, "Ý": 0x9D, "á": 0xA0, "Á": 0xA0,
        "í": 0xA1, "Í": 0xA1, "é": 0x82, "É": 0x82, "ú": 0xA3, "Ú": 0xA3,
        "ů": 0xA5, "Ů": 0xA5, "ť": 0x9F, "Ť": 0x9F, "ď": 0x8E, "Ď": 0x8E,
        "ň": 0xA4, "Ň": 0xA4, "ó": 0xA2, "Ó": 0xA2, "ě": 0x8A, "Ě": 0x8A,
        "ô": 0xA4, "Ô": 0xA4, "ő": 0x99, "Ő": 0x99, "ű": 0x81, "Ű": 0x81,
        "ą": 0xB1, "Ą": 0xA5, "ć": 0x86, "Ć": 0xC6, "ę": 0xEA, "Ę": 0xCA,
        "ł": 0xB3, "Ł": 0xA3, "ń": 0xF1, "Ń": 0xD1, "ś": 0x9C, "Ś": 0x8C,
        "ź": 0x9F, "Ź": 0x8F, "ž": 0xBF, "Ż": 0xAF,
    }
    result = bytearray()
    for ch in text:
        if ch in tab:
            result.append(tab[ch])
        else:
            code = ord(ch)
            if code < 256:
                result.append(code)
            else:
                result.append(ord('?'))  # neznámý znak nahradí otazníkem
    return result

def send_panel_text(line, pos, text):
    # Sestaví zprávu ve formátu z2A2Hello World!\r a odešle ji na panel
    msg = f"z{line}{pos}{text}\r"
    uart.write(to_kamenicky(msg))

def set_line(linka):
    # nastaví linku
    msg = f"L{linka}\r"
    uart.write(to_kamenicky(msg))

def set_terminus(kod_cile):
    # nastaví kód cíle podle databáze v panelu
    msg = f"Z{kod_cile}\r"
    uart.write(to_kamenicky(msg))

def clear_panel():
    """
    Vyčistí (smaže) obsah panelu BS210 se standardním brněnským firmwarem.
    Obvykle funguje příkaz 'X\r'.
    """
    msg = "X\r"
    uart.write(to_kamenicky(msg))