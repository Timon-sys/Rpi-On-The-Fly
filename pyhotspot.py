#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import subprocess
import sys
import os

from rpi_ws281x import PixelStrip, Color

# Configuration
PIN = 25 # GPIO pin connected to the switch
SSID = "PI-On-The-Fly"  # Hotspot SSID
PASSWORD = "SecurePassword123"  # Hotspot password (change as needed)

WIFI_INTERFACE = "wlan0" # WiFi interface name
FALLBACK_CONNECTION = "preconfigured"  # Name of your normal WiFi connection (see in nmtui)
HAS_LED = True  # Set to True if an LED strip is connected
#under the hood the wifi profile name is "Pi-Hotspot"

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

if HAS_LED:
    LED_COUNT      = 1       # Number of LEDs in the strip
    LED_PIN        = 21       # GPIO pin number used to control the LEDs
    LED_FREQ_HZ    = 800000   # LED signal frequency in Hz (WS2812 uses 800 kHz)
    LED_DMA        = 10       # DMA channel to use for signal generation
    LED_BRIGHTNESS = 255      # Brightness (0–255)
    LED_INVERT     = False    # True if signal should be inverted (for some driver circuits)
    LED_CHANNEL    = 0        # Channel (0 for GPIOs 10–31, 1 for GPIOs 0–9)

    try:
        strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        strip.begin()
    except Exception as e:
        print(f"{RED}LED initialization failed: {e}{RESET}")
        HAS_LED = False

def run_cmd(cmd):
    #Execute command and print errors.#
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
        return True
    except Exception as e:
        print(f"{RED}ERROR with '{' '.join(cmd)}': {e}{RESET}")
        return False
    
def connection_exists(conn_name):
    #Check if a NetworkManager connection exists.#
    try:
        result = subprocess.run(["nmcli", "-t", "-f", "NAME", "connection", "show"], 
                              capture_output=True, text=True, timeout=10)
        return conn_name in result.stdout
    except:
        return False

def is_hotspot_active():
    #Check if hotspot is running.#
    try:
        result = subprocess.run(["nmcli", "-t", "connection", "show", "--active"], 
                              capture_output=True, text=True, timeout=10)
        return "Pi-Hotspot" in result.stdout
    except:
        return False

def start_hotspot():
    #Start hotspot.#
    if is_hotspot_active():
        print(f"{BLUE}Hotspot already running{RESET}")
        return
    
    print(f"{BLUE}Starting hotspot...{RESET}")
    # Stop normal WiFi connection
    run_cmd(["nmcli", "connection", "down", FALLBACK_CONNECTION])
    # Delete old hotspot if exists
    run_cmd(["nmcli", "connection", "delete", "Pi-Hotspot"])
    # Start new hotspot
    if run_cmd(["nmcli", "dev", "wifi", "hotspot", "ifname", WIFI_INTERFACE, 
                "con-name", "Pi-Hotspot", "ssid", SSID, "password", PASSWORD]):
        print(f"{GREEN}Hotspot started{RESET}")
        
        if HAS_LED:
            strip.setPixelColor(0, Color(0, 0, 10))  # Blue to indicate hotspot is active
            strip.show()

    else:
        print(f"{RED}ERROR: Hotspot start failed!{RESET}")
        if HAS_LED:
            strip.setPixelColor(0, Color(10, 0, 0))   # Red to indicate error
            strip.show()

def stop_hotspot():
    #Stop hotspot and activate normal WiFi.#
    print(f"{BLUE}Stopping hotspot...{RESET}")
    run_cmd(["nmcli", "connection", "down", "Pi-Hotspot"])
    time.sleep(1)
    
    if not connection_exists(FALLBACK_CONNECTION):
        print(f"{YELLOW}WARNING: '{FALLBACK_CONNECTION}' connection not found! Cannot restore WiFi.{RESET}")
        if HAS_LED:
            strip.setPixelColor(0, Color(10, 0, 0))  # Red to indicate error
            strip.show()
        return
    
    if run_cmd(["nmcli", "connection", "up", FALLBACK_CONNECTION]):
        print(f"{GREEN}Normal WiFi activated{RESET}")

        if HAS_LED:
            strip.setPixelColor(0, Color(0, 10, 0))  # Green to indicate normal WiFi
            strip.show()
    else:
        print(f"{RED}ERROR: Normal WiFi could not be activated!{RESET}")
        if HAS_LED:
            strip.setPixelColor(0, Color(10, 0, 0))   # Red to indicate error
            strip.show()

def sync_state(pin_state):
    #Sync network state with switch position.#
    hotspot_running = is_hotspot_active()
    
    if pin_state and not hotspot_running:
        start_hotspot()
    elif not pin_state and hotspot_running:
        stop_hotspot()

def main():
    print(f"{GREEN}=== Pi Hotspot Switch started ==={RESET}")
    
    # Check if running as root
    if os.geteuid() != 0:
        print(f"{RED}ERROR: This script must be run as root!{RESET}")
        print(f"{YELLOW}Please run with: sudo python3 {sys.argv[0]}{RESET}")
        sys.exit(1)
    
    if not connection_exists(FALLBACK_CONNECTION):
        print(f"{YELLOW}WARNING: '{FALLBACK_CONNECTION}' connection not found!{RESET}")
        print(f"{YELLOW}The switch will start the hotspot but cannot restore normal WiFi.{RESET}")
        print("")

    if HAS_LED:
        strip.setPixelColor(0, Color(0, 10, 0))  # Green to indicate service is running
        strip.show()
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    # Initial state: sync with switch position
    current_state = GPIO.input(PIN)
    print(f"Switch position: {GREEN + 'ON' if current_state else RED + 'OFF'}{RESET}")
    sync_state(current_state)
    
    try:
        while True:
            pin_state = GPIO.input(PIN)
            
            if pin_state != current_state:
                # Simple debouncing

                if HAS_LED:
                    strip.setPixelColor(0, Color(10, 10, 0))  #yellow for state change
                    strip.show()

                time.sleep(0.1)
                if GPIO.input(PIN) == pin_state:  # Confirm state
                    print(f"Switch changed to: {GREEN + 'ON' if pin_state else RED + 'OFF'}{RESET}")
                    
                    if pin_state:
                        start_hotspot()
                    else:
                        stop_hotspot()
                    
                    current_state = pin_state
            
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        print(f"{YELLOW}Service stopped{RESET}")

    finally:
        GPIO.cleanup()
        if HAS_LED:
            strip.setPixelColor(0, Color(0, 0, 0))  #turn off LED at the end
            strip.show()
            
def test_gpio():
    #GPIO test.
    print(f"{BLUE}GPIO test (CTRL-C to stop)...{RESET}")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    try:
        while True:
            state = GPIO.input(PIN)
            color = GREEN if state else RED
            print(f"GPIO {PIN} = {color}{'HIGH' if state else 'LOW'}{RESET}")
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"{YELLOW}Test ended{RESET}")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_gpio()
    else:
        main()