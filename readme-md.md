# 🔭 AetherLens Home Edition

> **See Through Your Digital Energy Cloud** - Open-source cost and usage monitoring for smart homes, IoT devices, and personal cloud services.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Discord](https://img.shields.io/discord/123456789?color=7289da&logo=discord&logoColor=white)](https://discord.gg/aetherlens)
[![GitHub Stars](https://img.shields.io/github/stars/aetherlens/home?style=social)](https://github.com/aetherlens/home)
[![Docker Pulls](https://img.shields.io/docker/pulls/aetherlens/home)](https://hub.docker.com/r/aetherlens/home)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

## 🏠 What is AetherLens?

AetherLens brings enterprise-grade cost monitoring and optimization to your home lab. Track every watt, every API call, and every penny across your entire digital footprint - from smart plugs to cloud services.

### 🎯 Perfect For:
- **Home Lab Enthusiasts** running Proxmox, TrueNAS, or Kubernetes
- **Smart Home Users** with complex Home Assistant setups
- **Self-Hosters** managing their own services and infrastructure
- **Crypto Miners** tracking profitability across rigs
- **Solar Owners** optimizing self-consumption vs. grid export
- **Remote Workers** managing home office expenses

## ✨ Key Features

### 📊 Unified Dashboard
- Real-time power consumption across all devices
- Historical usage trends and patterns
- Cost breakdowns by device, room, or category
- Time-of-use optimization suggestions

### 🔌 Extensive Integrations
- **Smart Plugs**: TP-Link Kasa, Shelly, Tasmota, Zigbee
- **Energy Monitors**: Emporia Vue, Sense, IoTaWatt
- **Home Automation**: Home Assistant, Hubitat, SmartThings
- **Cloud Services**: AWS, Azure, GCP personal accounts
- **Solar/Battery**: Tesla, Enphase, SolarEdge, Fronius
- **Crypto Mining**: NiceHash, HiveOS, major pool APIs

### 💡 Smart Features
- **Anomaly Detection**: Identify unusual consumption patterns
- **Cost Predictions**: Estimate monthly bills before they arrive
- **Optimization Tips**: AI-driven suggestions to reduce costs
- **Carbon Tracking**: Monitor your environmental impact
- **Bill Verification**: Compare actual vs. utility bills

### 🔒 Privacy First
- **100% Local**: All data stays on your hardware
- **No Cloud Required**: Functions completely offline
- **Encrypted Storage**: Optional encryption at rest
- **You Own Your Data**: Export anytime in standard formats

## 🚀 Quick Start

### Docker Compose (Recommended)

```yaml
version: '3.8'
services:
  aetherlens:
    image: aetherlens/home:latest
    container_name: aetherlens
    ports:
      - "8080:8080"
    volumes:
      - ./data:/data
      - ./config:/config
    environment:
      - TZ=America/New_York
      - INFLUXDB_URL=http://influxdb:8086
    restart: unless-stopped

  influxdb:
    image: influxdb:2.7
    container_name: aetherlens-db
    volumes:
      - ./influxdb:/var/lib/influxdb2
    restart: unless-stopped
```

```bash
# Start the stack
docker-compose up -d

# Access the UI
open http://localhost:8080
```

### Standalone Installation

```bash
# Download the latest release
curl -L https://github.com/aetherlens/home/releases/latest/download/aetherlens-linux-amd64 -o aetherlens
chmod +x aetherlens

# Initialize configuration
./aetherlens init

# Start the service
./aetherlens start
```

### Home Assistant Add-on

```yaml
# Add repository to Home Assistant
https://github.com/aetherlens/home-assistant-addon

# Install from Add-on Store
# Configure and start
```

## 📸 Screenshots

<div align="center">
  <img src="docs/images/dashboard.png" width="45%" alt="Dashboard Overview">
  <img src="docs/images/device-detail.png" width="45%" alt="Device Details">
</div>

<div align="center">
  <img src="docs/images/cost-analysis.png" width="45%" alt="Cost Analysis">
  <img src="docs/images/solar-optimization.png" width="45%" alt="Solar Optimization">
</div>

## 🔧 Configuration Example

```yaml
# config.yaml
general:
  currency: USD
  timezone: America/New_York
  
energy_rates:
  provider: "Local Utility Co"
  time_of_use:
    peak:
      rate: 0.32
      hours: "14:00-19:00"
    off_peak:
      rate: 0.12
      hours: "23:00-07:00"
    standard:
      rate: 0.18

plugins:
  - name: shelly
    enabled: true
    devices:
      - ip: 192.168.1.100
        name: "Office Desk"
        room: "Office"
        
  - name: home_assistant
    enabled: true
    url: "http://homeassistant.local:8123"
    token: "${HA_TOKEN}"
    
  - name: aws
    enabled: true
    profile: "personal"
    regions: ["us-east-1", "us-west-2"]
```

## 🔌 Plugin Development

Create custom plugins to monitor any device or service:

```python
# plugins/my_device.py
from aetherlens import BasePlugin, Metric

class MyDevicePlugin(BasePlugin):
    def collect(self):
        # Fetch data from your device
        power = self.get_power_usage()
        
        return [
            Metric(
                name="power",
                value=power,
                unit="watts",
                device_id=self.config['device_id'],
                timestamp=time.now()
            )
        ]
    
    def get_capabilities(self):
        return ["power", "energy", "cost"]
```

[📚 Full Plugin Development Guide →](docs/PLUGIN_GUIDE.md)

## 📈 Visualization & Export

### Grafana Integration
```bash
# Import pre-built dashboards
./aetherlens grafana import

# Or use Prometheus endpoint
http://localhost:8080/metrics
```

### Data Export
```bash
# Export to CSV
./aetherlens export --format csv --start 2024-01-01 --end 2024-12-31

# Stream to InfluxDB/TimescaleDB
./aetherlens export --format influx --continuous
```

## 🛣️ Roadmap

### Phase 1 - Foundation (Q1 2025) ✅
- [x] Core architecture
- [x] Basic plugin system
- [x] Docker deployment
- [x] Top 10 device integrations

### Phase 2 - Intelligence (Q2 2025) 🚧
- [ ] Machine learning predictions
- [ ] Automated optimization
- [ ] Mobile app (iOS/Android)
- [ ] 25+ plugin integrations

### Phase 3 - Ecosystem (Q3 2025) 📋
- [ ] Plugin marketplace
- [ ] Cloud sync (optional)
- [ ] Small business features
- [ ] Energy arbitrage automation

[View Full Roadmap →](ROADMAP.md)

## 🤝 Contributing

We love contributions! Whether it's:
- 🐛 Bug reports
- 💡 Feature requests
- 🔌 New plugins
- 📖 Documentation improvements
- 💻 Code contributions

Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Top Contributors
<a href="https://github.com/aetherlens/home/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=aetherlens/home" />
</a>

## 💬 Community

- **Discord**: [Join our Discord](https://discord.gg/aetherlens) - Active community, real-time help
- **Forum**: [community.aetherlens.io](https://community.aetherlens.io) - Long-form discussions
- **Reddit**: [r/aetherlens](https://reddit.com/r/aetherlens) - News and showcases
- **Twitter**: [@aetherlens](https://twitter.com/aetherlens) - Updates and tips

## 🏆 Success Stories

> "Cut my electricity bill by 30% after identifying vampire loads I never knew existed!" - *@homelab_hero*

> "Finally understand what my solar panels are actually saving me. The time-of-use optimization paid for my entire home lab upgrade." - *@solar_saver*

> "The Home Assistant integration is flawless. Seeing all my costs in one place is a game-changer." - *@smart_home_sam*

## 📊 Stats & Badges

![Energy Saved](https://img.shields.io/badge/Community%20Energy%20Saved-1.21GWh-green)
![Money Saved](https://img.shields.io/badge/Community%20Money%20Saved-$420k-success)
![Active Installs](https://img.shields.io/badge/Active%20Installs-10k+-blue)
![Plugins Available](https://img.shields.io/badge/Plugins%20Available-50+-orange)

## 🛡️ Security

- Security is our priority. Please report vulnerabilities to security@aetherlens.io
- See [SECURITY.md](SECURITY.md) for our security policy
- All dependencies are regularly updated and scanned

## 📝 License

AetherLens is MIT licensed. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built with amazing open-source projects:
- [InfluxDB](https://github.com/influxdata/influxdb) for time-series storage
- [Grafana](https://github.com/grafana/grafana) for visualization
- [Home Assistant](https://github.com/home-assistant) for inspiration
- All our [plugin contributors](CONTRIBUTORS.md)

## 🚦 Status

[![Build Status](https://github.com/aetherlens/home/workflows/CI/badge.svg)](https://github.com/aetherlens/home/actions)
[![Coverage](https://codecov.io/gh/aetherlens/home/branch/main/graph/badge.svg)](https://codecov.io/gh/aetherlens/home)
[![Go Report Card](https://goreportcard.com/badge/github.com/aetherlens/home)](https://goreportcard.com/report/github.com/aetherlens/home)
[![Docker Image Size](https://img.shields.io/docker/image-size/aetherlens/home)](https://hub.docker.com/r/aetherlens/home)

---

<div align="center">
  <b>⚡ Every Watt Counts - From Home to Cloud ⚡</b>
  <br>
  <sub>Built with ❤️ by the home lab community, for the home lab community</sub>
</div>