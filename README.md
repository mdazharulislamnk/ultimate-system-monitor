# System Monitor Pro — By Azhar

A high-performance, fully customizable, professional system resource monitor for the command-line. Designed for engineers, developers, and power users who need real-time, low-latency visibility into hardware performance. Transform your terminal into a futuristic "Command Center" dashboard tracking CPU cores, RAM, Swap, storage partitions, and network traffic with precision.

![Preview](./assets/preview.png)

Highlights
- Real-time, low-latency monitoring with configurable refresh rate
- Per-core CPU graphs and current clock speed
- Detailed RAM and Swap statistics
- Auto-discovered storage partitions with visual usage bars
- Live upload/download speeds and TCP-based ping latency
- Optional CSV data logging for later analysis
- Cross-platform: Windows, macOS, Linux

Technologies
- Language: Python 3.6+
- Core library: psutil (Process and System Utilities)
- Standard libraries used: socket, time, datetime, os, sys, platform, json, csv, ctypes (Windows-only)

Features & Metrics
1. Smart Window Management
   - Auto-resize: Resizes terminal to fit the dashboard for a tidy display.
   - Auto-position (Windows): Moves the terminal window to a preset screen position (default 500px left, 100px top).

2. Advanced CPU Analytics
   - Total CPU usage percentage
   - Current CPU frequency in MHz
   - Per-core usage bars for every logical processor

3. Detailed Memory Stats
   - Physical RAM: total, used, free, usage %
   - Swap (virtual memory): monitor usage to detect memory pressure

4. Storage Intelligence
   - Auto-discovers connected drives (HDD, SSD, USB)
   - Visual capacity bars with used/total numbers

5. Real-Time Network
   - Upload and download speeds calculated between updates (KB/s or MB/s)
   - TCP-based ping latency to a configurable target (default: 8.8.8.8)

6. Data Logging
   - Optional CSV logging (system_metrics.csv) recorded every second for offline analysis

Installation

Prerequisites
- Python 3.6+ installed. Download from https://www.python.org/

Clone the repo
```bash
git clone https://github.com/mdazharulislamnk/ultimate-system-monitor.git
cd ultimate-system-monitor
```

Install dependencies
```bash
pip install psutil
```

Usage

Basic
```bash
python monitor.py
```

Enable logging
```bash
python monitor.py --log
```
This creates system_metrics.csv in the script folder.

Exit
- Press Ctrl + C to safely stop the monitor.

Configuration

1) In-script user settings (layout & window position)
Open monitor.py and edit the top USER SETTINGS block to control layout and positioning:
```python
# --- USER SETTINGS ---
W = 66              # Dashboard width
PADDING_TOP = 2     # Vertical padding above dashboard
PADDING_LEFT = 4    # Horizontal padding from left
WINDOW_X = 500      # Window position: pixels from LEFT (Windows)
WINDOW_Y = 100      # Window position: pixels from TOP (Windows)
```

2) Optional config.json (monitoring logic)
Create or edit config.json to change runtime behavior without modifying code:
```json
{
  "refresh_rate": 0.5,
  "ping_target": "1.1.1.1",
  "ping_port": 53,
  "show_cpu_per_core": true,
  "logging_enabled": false,
  "thresholds": {
    "mid": 60,
    "high": 90
  },
  "colors": {
    "label": "blue",
    "value_high": "red"
  }
}
```

CSV Logging Format
- Timestamp, cpu_total_pct, cpu_core_0_pct, ..., ram_used_mb, ram_total_mb, swap_used_mb, swap_total_mb, net_up_bps, net_down_bps, ping_ms

Troubleshooting

1) Broken dashboard / weird characters
Cause: Terminal font or encoding does not support box-drawing characters.
Fix:
- On Windows, the script attempts to set UTF-8 (chcp 65001).
- Use Windows Terminal, or switch to a font like Consolas / DejaVu Sans Mono.
- Ensure your terminal uses UTF-8 encoding.

2) Window moves to wrong place (multi-monitor or DPI)
Cause: Multiple monitors with different DPI or scaling.
Fix:
- Adjust WINDOW_X / WINDOW_Y in monitor.py until it sits where you want.
- Consider disabling auto-positioning on multi-monitor setups.

3) ModuleNotFoundError: No module named 'psutil'
Fix:
```bash
pip install psutil
```

4) Permission errors fetching specific metrics
Fix:
- On some OSes, elevated privileges may be required. Re-run with appropriate permissions.

Tips & Notes
- Reduce refresh_rate in config.json to lower CPU overhead.
- Disable per-core view on machines with many logical processors for a compact view.
- Logged CSV can be opened with Excel or Google Sheets for visual analysis.

Roadmap / Improvements
- Config file schema validation and CLI flags for quick overrides
- Optional JSON or InfluxDB output for integration into dashboards
- More granular per-core history graphs and exportable PNG snapshots
- Theming support and user presets for different terminals

Contributing
Contributions, bug reports, and feature requests are welcome.
1. Fork the repo
2. Create a branch (feature/your-feature)
3. Make changes and add tests where applicable
4. Open a PR with a clear description

Author
Md. Azharul Islam  
GitHub: [@mdazharulislamnk](https://github.com/mdazharulislamnk)  
LinkedIn: Md. Azharul Islam

License
This project is open-source under the MIT License — see LICENSE for details.