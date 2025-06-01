#include <Arduino.h>
#include <SoftwareSerial.h>

// UART nastavení
#define PANEL_BAUD 1200
SoftwareSerial PANEL_SERIAL(10, 11); // RX, TX pro panel (zvol správné piny)

// Pomocné funkce pro IBIS komunikaci
uint8_t ibis_checksum(const uint8_t *data, size_t len) {
  uint8_t cs = 0;
  for (size_t i = 0; i < len; ++i) cs ^= data[i];
  return cs;
}

// Převod na Kamenických (zde pouze ASCII, pro plnou podporu doplň mapování)
void to_kamenicky(const char *src, uint8_t *dst, size_t maxlen) {
  size_t i = 0;
  while (src[i] && i < maxlen - 1) {
    dst[i] = (uint8_t)src[i]; // pouze ASCII
    i++;
  }
  dst[i] = 0;
}

// Odeslání zprávy na panel s IBIS kontrolním součtem
void send_ibis(const char *msg) {
  uint8_t buf[64];
  to_kamenicky(msg, buf, sizeof(buf) - 1);
  size_t len = strlen((char*)buf);
  uint8_t cs = ibis_checksum(buf, len);
  PANEL_SERIAL.write(buf, len);
  PANEL_SERIAL.write(cs);

  // Poslat i do USB (Serial Monitor)
  Serial.print("SEND: ");
  Serial.write(buf, len);
  Serial.print(" [CS=");
  Serial.print(cs, HEX);
  Serial.println("]");
}

// Ovládací funkce
void send_panel_text(const char *line, const char *pos, const char *text) {
  char msg[64];
  snprintf(msg, sizeof(msg), "z%s%s%s\r", line, pos, text);
  send_ibis(msg);
}

void set_line(const char *linka) {
  char msg[16];
  snprintf(msg, sizeof(msg), "L%s\r", linka);
  send_ibis(msg);
}

void set_terminus(const char *kod_cile) {
  char msg[16];
  snprintf(msg, sizeof(msg), "Z%s\r", kod_cile);
  send_ibis(msg);
}

void clear_panel() {
  send_ibis("X\r");
}

void setup() {
  Serial.begin(9600); // USB pro ladění
  PANEL_SERIAL.begin(PANEL_BAUD); // pouze 8N1!
  delay(300); // počkej na stabilizaci UART
}

void loop() {
  set_line("069");
  send_panel_text("2", "A2", "HELLO WORLD!");
  delay(5000);
  clear_panel();
}