import time
import serial # Wir verwenden pyserial direkt
import paho.mqtt.client as mqtt
import traceback

# --- Konfiguration ---
SERIAL_PORT = "/dev/ttyUSB0"
MQTT_BROKER_HOST = "XZY"
MQTT_BROKER_PORT = 1883
MQTT_USERNAME = "XYZ"
MQTT_PASSWORD = "XZY" # Bitte stelle sicher, dass dies korrekt ist!
MQTT_TOPIC_PREFIX = "solardaten/laderegler"
PUBLISH_INTERVAL = 15 # Sekunden
# --- Ende Konfiguration ---

ve_data_dict = {} # Globales Dictionary für die zuletzt gelesenen, vollständigen VE.Direct Daten
ser = None      # Globale Variable für das Serial-Objekt

def publish_mqtt_data(client, data_dict):
    if not data_dict:
        return
    for original_key, value in data_dict.items():
        # Bereinige den Schlüssel für die Verwendung im MQTT-Topic
        safe_key = original_key.replace("#", "_").replace("+", "_")

        topic = f"{MQTT_TOPIC_PREFIX}/{safe_key}"
        try:
            payload = str(value)
            # Setze retain=True, damit der Broker die Nachricht speichert
            (rc, mid) = client.publish(topic, payload, qos=1, retain=True) # HIER IST DIE ÄNDERUNG
            if rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Gesendet (retained): {topic} -> {payload}")
            else:
                print(f"Fehler beim Senden an {topic} (Original Key: {original_key}): {mqtt.error_string(rc)}")
        except Exception as e:
            print(f"Fehler beim Verarbeiten/Senden von Daten für Key '{safe_key}' (Original: '{original_key}'): {e}")

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"Erfolgreich mit MQTT Broker {MQTT_BROKER_HOST} verbunden.")
    else:
        print(f"Verbindung zum MQTT Broker fehlgeschlagen, Code: {reason_code} ({mqtt.connack_string(reason_code)})")

def on_disconnect(client, userdata, reason_code, properties=None, legacy_rc_value=None):
    if reason_code == 0 and not legacy_rc_value :
         print(f"Verbindung zum MQTT Broker wurde normal getrennt.")
    elif reason_code and reason_code != 0:
        print(f"Unerwartet vom MQTT Broker getrennt. Grund: {reason_code}")
        if hasattr(reason_code, 'getName'):
             print(f"Disconnect Grund (Name): {reason_code.getName()}")
    elif legacy_rc_value and legacy_rc_value != 0:
        print(f"Unerwartet vom MQTT Broker getrennt. Legacy Grund: {legacy_rc_value}")
    else:
        print(f"Vom MQTT Broker getrennt (Code: {reason_code}, Legacy Code: {legacy_rc_value}).")

# --- Hauptprogramm ---
if __name__ == "__main__":
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if MQTT_USERNAME and MQTT_PASSWORD:
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect

    try:
        print(f"Versuche, mit MQTT Broker {MQTT_BROKER_HOST} zu verbinden...")
        mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"Kritischer Fehler beim Verbindungsaufbau zum MQTT Broker: {e}")
        traceback.print_exc()
        exit(1) # Skript beenden, wenn MQTT nicht verbinden kann

    current_block_data = {} # Temporäres Dictionary für den aktuellen Datenblock

    try:
        print(f"Initialisiere VE.Direct Verbindung zu {SERIAL_PORT}...")
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=19200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,  # Timeout für ser.readline() in Sekunden
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
        print(f"Serieller Port {SERIAL_PORT} geöffnet.")
        ser.flushInput() # Eingangs-Puffer zu Beginn leeren

        last_publish_time = time.time()

        while True:
            try:
                line_bytes = ser.readline()
                if not line_bytes: # Timeout beim Lesen der Zeile
                    if current_block_data:
                        print("Warnung: Timeout während des Lesens eines Blocks. Verwerfe unvollständigen Block.")
                        current_block_data = {}
                    time.sleep(0.1)
                    continue

                try:
                    line = line_bytes.decode('latin-1').strip()
                except UnicodeDecodeError:
                    print(f"UnicodeDecodeError bei Zeile: {line_bytes!r}, überspringe.")
                    continue

                if not line: # Leere Zeile überspringen
                    continue

                parts = line.split('\t', 1)
                if len(parts) == 2:
                    key, value = parts[0], parts[1]

                    if key == 'PID' and not current_block_data:
                        # print(f"Neuer VE.Direct Block gestartet mit PID: {value}") # Optionales Logging
                        pass # Nichts weiter zu tun hier, current_block_data ist bereits leer

                    current_block_data[key] = value

                    if key == 'Checksum':
                        # Block ist nominell komplett.
                        # Hier könnte man die Checksumme validieren (für dieses Skript optional).
                        # print(f"Block empfangen, endet mit Checksum. Daten: {current_block_data}") # Optionales Logging

                        ve_data_dict.update(current_block_data) # Globale Daten aktualisieren
                        current_block_data = {} # Für den nächsten Block zurücksetzen

                else:
                    if len(line) > 0:
                         print(f"Ignoriere Zeile ohne Tab-Separator: {line!r}")
                    if current_block_data:
                        print("Fehler: Unerwartetes Zeilenformat mitten im Block. Verwerfe Block.")
                        current_block_data = {}

            except serial.SerialException as e_read:
                print(f"Fehler beim Lesen vom seriellen Port: {e_read}")
                traceback.print_exc()
                if ser and ser.is_open:
                    ser.close()
                time.sleep(5)
                try:
                    ser.open() # Versuche Port neu zu öffnen
                    ser.flushInput()
                    print("Serieller Port neu geöffnet.")
                except Exception as e_reopen:
                    print(f"Konnte seriellen Port nicht neu öffnen: {e_reopen}. Beende Skript.")
                    break # Hauptschleife verlassen
            except Exception as e_loop:
                print(f"Unerwarteter Fehler in der Leseschleife: {e_loop}")
                traceback.print_exc()
                current_block_data = {} # Block zurücksetzen
                time.sleep(1) # Kurz warten


            # MQTT Sende-Logik
            current_time = time.time()
            if current_time - last_publish_time >= PUBLISH_INTERVAL:
                if ve_data_dict:
                    print("Veröffentliche gesammelte Daten per MQTT...")
                    publish_mqtt_data(mqtt_client, ve_data_dict.copy())
                    last_publish_time = current_time

    except serial.SerialException as e_serial_init:
        print(f"Kritischer serieller Fehler bei der Initialisierung: {e_serial_init}. Das Programm wird beendet.")
        traceback.print_exc()
    except KeyboardInterrupt:
        print("\nProgramm beendet durch Benutzer.")
    except Exception as e_main:
        print(f"Ein unerwarteter kritischer Fehler im Hauptprogramm ist aufgetreten: {e_main}")
        traceback.print_exc()
    finally:
        print("Räume auf...")

        print("Stoppe MQTT Netzwerk-Loop...")
        mqtt_client.loop_stop()
        print("Trenne MQTT Verbindung...")
        mqtt_client.disconnect()
        print("MQTT Aufräumarbeiten abgeschlossen.")

        if ser and ser.is_open:
            print(f"Schließe serielle Verbindung zu {SERIAL_PORT}...")
            ser.close()
            print("Serielle Verbindung geschlossen.")
        elif ser:
            print("Serielles Objekt 'ser' wurde erstellt, war aber nicht (mehr) geöffnet.")
        else:
            print("Serielles Objekt 'ser' wurde nicht erstellt.")

        print("Programm vollständig beendet.")
