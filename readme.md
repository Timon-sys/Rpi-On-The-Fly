# Rpi-On-The-Fly 🔌

A little Python script I made to access my Raspberry Pi from everywhere with a simple GPIO switch.

## What it does

Flip a physical switch or Jumper connected to GPIO 25, and your Pi instantly becomes a WiFi hotspot. Flip it back, and it reconnects to your normal WiFi. Perfect for when you need quick access to your Pi without a monitor or keyboard!

## Features

- 🔄 Toggle between hotspot and normal WiFi with a physical switch
- 💡 Optional LED status indicator (WS2812B/NeoPixel)
- 🚀 Automatic startup on boot via systemd service
- 🔧 Simple configuration - just edit a few variables at the top of the script

## Hardware Requirements

- Raspberry Pi 😌
- Physical toggle switch or jumper wire
- Optional: WS2812B Neopixel for status indication

## Wiring

- **GPIO 25** - Connected to your switch (pulled down, switch connects to 3.3V)
- **GPIO 21** - Connected to LED strip data pin (optional, if `HAS_LED = True`)

## Quick Install

```bash
curl -sSL https://raw.githubusercontent.com/Timon-sys/Rpi-On-The-Fly/main/install.sh | sudo bash
```

Or manual installation:

```bash
git clone https://github.com/Timon-sys/Rpi-On-The-Fly.git
cd Rpi-On-The-Fly
sudo bash install.sh
```

## Configuration

Edit the script at `/opt/rpi-hotspot/pyhotspot.py`:

```python
# Configuration
PIN = 25  # GPIO pin for the switch
SSID = "PI-On-The-Fly"  # Your hotspot name
PASSWORD = "YourSecurePassword"  # Change this!
FALLBACK_CONNECTION = "your-wifi-name"  # Your normal WiFi Profile name in nmcli
HAS_LED = True  # Set to False if no LED strip
```

After editing, restart the service:
```bash
sudo systemctl restart pyhotspot.service
```

## Usage

### Control Commands
```bash
# Check status
sudo systemctl status pyhotspot.service

# View logs
sudo journalctl -u pyhotspot.service -f

# Restart service
sudo systemctl restart pyhotspot.service

# Test GPIO reading
sudo python3 /opt/rpi-hotspot/pyhotspot.py test
```

### LED Status (if enabled)
- 🟢 **Green** - Normal WiFi connected
- 🔵 **Blue** - Hotspot active
- 🟡 **Yellow** - Switching
- 🔴 **Red** - Error state

## How It Works

1. Script monitors GPIO (25) continuously
2. When Pin is **HIGH**: Disconnects from WiFi and starts hotspot
3. When Pin is **LOW**: Stops hotspot and reconnects to normal WiFi
4. LED provides visual feedback of current state (if enabled)
(the button polling is kept slow intentionally, so give it a good 5 seconds or so to actually see the LED change)

## Security Note

⚠️ **Important**: Change the default hotspot password in the configuration before using in production! The default password is just a placeholder.

## Troubleshooting

**Service won't start:**
```bash
sudo journalctl -u pyhotspot.service -n 50
```

**Hotspot not appearing:**
- Check that NetworkManager is installed
- Verify GPIO pin number matches your wiring
- Make sure WiFi interface is `wlan0` (or update in config)

**Can't reconnect to normal WiFi:**
- Ensure `FALLBACK_CONNECTION` matches your WiFi connection name exactly
- Check available connections: `nmcli connection show`

## Requirements

- Python 3
- NetworkManager
- RPi.GPIO
- rpi-ws281x

See `requirements.txt` for Python packages.

## License

MIT License - Do whatever you want with it!

## Contributing

Found a bug or want to add a feature? Pull requests are welcome!

---

Made with ❤️(and some 🤖) for those times when you just need to SSH into your Pi but it's tucked away somewhere without a monitor (or in your backpack😈)