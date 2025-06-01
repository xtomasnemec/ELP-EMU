from machine import UART, Pin
import utime as time
from libIBIS import connect_panel, set_uart, send_panel_text, set_line, set_terminus, clear_panel, to_kamenicky, ibis_checksum, log_comm

uart = connect_panel()
set_uart(uart)

last_blink = time.ticks_ms()
blink_interval = 500  # ms

while True:
    # Ovládání panelu (každých 5 s)
    set_line("69")
    send_panel_text("2", "A2", "HELLO WORLD!")
    time.sleep(5)
    clear_panel()
    print("vsechno jede")