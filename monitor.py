import psutil       # Library to fetch system information (CPU, RAM, Disk, etc.)
import time         # Library to handle time delays (sleep) and timing (ping)
import os           # Library to interact with the operating system (clear screen, file paths)
import sys          # Library for system-specific parameters
import platform     # Library to get the computer's network name (Hostname)
import socket       # Library to create network connections (used for Ping)
import json         # Library to read/write settings files
import csv          # Library to save data logs (Comma Separated Values)
import argparse     # Library to handle command-line arguments (like --log)
import re           # Library for Regular Expressions (used to strip color codes for length calc)
from datetime import datetime # Library to handle dates and timestamps

# ==========================================
# ⚙️ USER SETTINGS (LAYOUT & CONTROL)
# ==========================================

# 1. DASHBOARD SIZE
# This sets the width of the internal content boxes (excluding padding).
W = 66              

# 2. INTERNAL TERMINAL SPACING (MARGINS)
# Increase these numbers to push the box away from the edges of the window.
PADDING_TOP = 2     # How many empty lines at the top
PADDING_LEFT = 4    # How many spaces to the left of the box
PADDING_BOTTOM = 2  # Extra space at the bottom (for window height calc)

# 3. WINDOW POSITION (SCREEN COORDINATES)
# Change these to move the window on your screen automatically.
WINDOW_X = 500      # Pixels from LEFT of screen
WINDOW_Y = 100      # Pixels from TOP of screen

# ==========================================
# 🛠️ DEFAULT CONFIGURATION
# ==========================================
# These settings act as a backup if 'config.json' is deleted or missing.
DEFAULT_CONFIG = {
    "refresh_rate": 0.5,        # How often to update the screen (0.5s = 2 times/sec)
    "ping_target": "8.8.8.8",   # The IP address to check internet connection (Google DNS)
    "ping_port": 53,            # The port used for the connection check
    "show_cpu_per_core": True,  # Toggle to show/hide individual CPU core bars
    "logging_enabled": False,   # Default setting for logging (False = off)
    "log_file": "system_metrics.csv", # Name of the file where logs are saved
    "thresholds": {
        "mid": 50,  # If usage > 50%, color turns Yellow
        "high": 80  # If usage > 80%, color turns Red
    },
    "colors": {
        "label": "red",         # Color for text labels (e.g. "Usage:")
        "value_low": "green",   # Color for low numbers
        "value_mid": "yellow",  # Color for medium numbers
        "value_high": "red",    # Color for high numbers
        "alert": "red"          # Color for errors or offline status
    }
}

# ==========================================
# 🎨 ANSI COLORS
# ==========================================
# These special strings tell the terminal to change text color.
# Example: Printing "\033[31mHello" prints "Hello" in Red.
COLORS = {
    "reset": "\033[0m",     # Resets color back to default white/gray
    "cyan": "\033[36m",     # Cyan color (used for Borders)
    "green": "\033[32m",    # Green color
    "yellow": "\033[33m",   # Yellow color
    "red": "\033[31m",      # Red color
    "blue": "\033[34m",     # Blue color
    "magenta": "\033[35m",  # Magenta/Purple color (used for Title)
    "white": "\033[37m",    # White color
    "bold": "\033[1m"       # Bold text style
}

# Global variable to store loaded configuration
cfg = {}

# ==========================================
# 🔧 HELPER FUNCTIONS
# ==========================================

def load_config():
    """
    Tries to load settings from 'config.json'.
    If the file is not found or has errors, it falls back to DEFAULT_CONFIG.
    """
    global cfg
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                loaded = json.load(f)
                # Merge: Take defaults, then overwrite with what we found in the file.
                cfg = {**DEFAULT_CONFIG, **loaded}
                
                # Safety check: Ensure the color structure exists to prevent crashes
                if "colors" not in loaded or "label" not in loaded["colors"]:
                     cfg["colors"]["label"] = "red"
        except:
            # If JSON is broken, ignore it and use defaults
            cfg = DEFAULT_CONFIG
    else:
        # If file doesn't exist, use defaults
        cfg = DEFAULT_CONFIG

def get_ansi(color_name):
    """
    Looks up the color code (e.g. \033[31m) for a simple name (e.g. 'red').
    """
    return COLORS.get(color_name, COLORS['white'])

def get_color_by_percent(percent):
    """
    Decides which color to use based on how high a number is.
    < 50% -> Green
    < 80% -> Yellow
    > 80% -> Red
    """
    if percent < cfg['thresholds']['mid']:
        return get_ansi(cfg['colors']['value_low'])  # Green
    if percent < cfg['thresholds']['high']:
        return get_ansi(cfg['colors']['value_mid'])  # Yellow
    return get_ansi(cfg['colors']['value_high'])     # Red

def get_size(bytes, suffix="B"):
    """
    Converts a huge number of bytes (e.g. 1073741824) into readable text (e.g. "1.00 GB").
    It divides by 1024 repeatedly until the number is small enough to read.
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def clear_screen():
    """
    Wipes the terminal text so we can draw the new frame.
    Uses 'cls' for Windows and 'clear' for Mac/Linux.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

def move_window(x, y):
    """
    Moves the console window to the specific screen coordinates (x, y).
    Uses the Windows API (ctypes) to forcefully reposition the window.
    """
    if os.name == 'nt':
        try:
            import ctypes
            # Get the unique ID (handle) of the console window
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                # 0x0005 = SWP_NOSIZE (don't resize) | SWP_NOZORDER (don't change layer)
                ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, 0, 0, 0x0005)
        except Exception:
            pass

def setup_terminal():
    """
    Sets up the terminal size and position based on your PADDING settings.
    1. Fixes encoding for correct line drawing.
    2. Resizes window to fit box + padding.
    3. Moves window to desired X/Y coordinates.
    """
    if os.name == 'nt':
        os.system('chcp 65001 >nul') # Force UTF-8 encoding
        
        # CALCULATE TOTAL WINDOW SIZE
        # Width = Box Width (W) + Left Padding + Right Buffer (4)
        total_cols = W + PADDING_LEFT + 4
        # Height = Estimate (50) + Top Padding + Bottom Padding
        total_lines = 50 + PADDING_TOP + PADDING_BOTTOM
        
        # Apply size
        os.system(f'mode con: cols={total_cols} lines={total_lines}')
        
        # Move to user defined X/Y
        move_window(WINDOW_X, WINDOW_Y)
    
    clear_screen()

def draw_bar(percent, length=15):
    """
    Creates a visual loading bar: [████------]
    Args:
        percent: The current usage (0-100)
        length: How many characters wide the bar should be
    """
    length = int(length)
    # Calculate how many '█' blocks we need
    filled = int(length * percent // 100)
    
    # 'min' and 'max' ensure the bar never goes below 0 or exceeds the length limit
    # This fixes visual glitches if percent is > 100 or < 0.
    filled = min(length, max(0, filled))
    
    color = get_color_by_percent(percent)
    
    # Construct the string: Colored Blocks + Dashes
    bar = '█' * filled + '-' * (length - filled)
    return f"[{color}{bar}{COLORS['reset']}]"

def get_uptime():
    """
    Calculates how long the PC has been turned on.
    """
    boot = datetime.fromtimestamp(psutil.boot_time())
    return str(datetime.now() - boot).split('.')[0] # Removes microseconds

def get_ping():
    """
    Checks internet speed (latency).
    Uses a standard Socket connection (TCP) instead of 'ping.exe'.
    This is faster and doesn't require Administrator permissions.
    """
    try:
        st = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5) 
        s.connect((cfg['ping_target'], cfg['ping_port']))
        s.close()
        return (time.time() - st) * 1000 # Convert to milliseconds
    except:
        return None

def log_metrics(cpu, ram, disk, down, up, ping):
    """
    Saves the current stats to a CSV file if logging is ON.
    """
    if not cfg['logging_enabled']: return
    mode = 'a' if os.path.isfile(cfg['log_file']) else 'w'
    with open(cfg['log_file'], mode, newline='') as f:
        wr = csv.writer(f)
        if mode == 'w':
            wr.writerow(["Time", "CPU", "RAM", "Disk", "Down", "Up", "Ping"])
        wr.writerow([
            datetime.now().strftime("%H:%M:%S"),
            cpu, ram, disk, down, up, ping or 0
        ])

# ==========================================
# 🖼️ DISPLAY HELPERS (THE BOX LOGIC)
# ==========================================

def visible_len(s):
    """
    Calculates the REAL length of a string by ignoring hidden color codes.
    Without this, box borders break because Python counts invisible codes as length.
    """
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return len(ansi_escape.sub('', s))

def pr(text):
    """
    CUSTOM PRINT FUNCTION
    Automatically adds the LEFT PADDING to every line printed.
    """
    padding_str = " " * PADDING_LEFT
    print(f"{padding_str}{text}")

def draw_row(content, border_color=COLORS['cyan']):
    """
    Prints a single line inside the box borders.
    It automatically calculates right-side padding to align the border.
    Format: ║ Content spaces ║
    """
    v_len = visible_len(content)
    padding = W - 2 - v_len - 2 
    if padding < 0: padding = 0
    # Use 'pr' instead of 'print' to handle left margin
    pr(f"{border_color}║{COLORS['reset']} {content}{' ' * padding} {border_color}║{COLORS['reset']}")

# ==========================================
# 🚀 MAIN PROGRAM
# ==========================================

def main():
    # 1. Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", action="store_true", help="Start logging immediately")
    args = parser.parse_args()

    # 2. Setup Terminal (Size & Position)
    setup_terminal()
    load_config()
    
    if args.log: cfg['logging_enabled'] = True

    # Color shortcuts
    C_LBL = get_ansi(cfg['colors']['label'])
    C_RST = COLORS['reset']
    C_CYN = COLORS['cyan']
    C_YLW = COLORS['yellow']
    
    # --- BOX HEADERS ---
    # Pre-calculated strings for box tops and bottoms
    MAIN_TOP = f"{C_CYN}╔{'═'*64}╗{C_RST}"
    MAIN_BOT = f"{C_CYN}╚{'═'*64}╝{C_RST}"
    UPTIME_TOP = f"{C_CYN}╔{'═'*28} {C_YLW}UPTIME{C_CYN} {'═'*28}╗{C_RST}"
    UPTIME_BOT = f"{C_CYN}╚{'═'*64}╝{C_RST}"
    CPU_TOP = f"{C_CYN}╔{'═'*27} {C_YLW}CPU INFO{C_CYN} {'═'*27}╗{C_RST}"
    CPU_BOT = f"{C_CYN}╚{'═'*64}╝{C_RST}"
    RAM_TOP = f"{C_CYN}╔{'═'*28} {C_YLW}MEMORY{C_CYN} {'═'*28}╗{C_RST}"
    RAM_BOT = f"{C_CYN}╚{'═'*64}╝{C_RST}"
    STO_TOP = f"{C_CYN}╔{'═'*27} {C_YLW}STORAGE{C_CYN} {'═'*28}╗{C_RST}"
    STO_BOT = f"{C_CYN}╚{'═'*64}╝{C_RST}"
    NET_TOP = f"{C_CYN}╔{'═'*27} {C_YLW}NETWORK{C_CYN} {'═'*28}╗{C_RST}"
    NET_BOT = f"{C_CYN}╚{'═'*64}╝{C_RST}"

    print("Starting System Monitor...")
    old_net = psutil.net_io_counters()

    try:
        while True:
            # --- GATHER DATA ---
            cpu = psutil.cpu_percent(interval=cfg['refresh_rate'])
            cpu_freq = psutil.cpu_freq()
            cores = psutil.cpu_percent(percpu=True) if cfg['show_cpu_per_core'] else []
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            net = psutil.net_io_counters()
            disk = psutil.disk_usage(os.path.abspath(os.sep))
            ping = get_ping()
            
            sent = (net.bytes_sent - old_net.bytes_sent) / cfg['refresh_rate']
            recv = (net.bytes_recv - old_net.bytes_recv) / cfg['refresh_rate']
            old_net = net
            
            log_metrics(cpu, mem.percent, disk.percent, recv, sent, ping)

            # --- RENDER ---
            clear_screen()
            
            # Print Top Padding (Empty lines)
            print("\n" * PADDING_TOP)
            
            # 1. HEADER (Use 'pr' for left padding)
            pr(MAIN_TOP)
            draw_row(f"{COLORS['yellow']}System Monitor Pro By Azhar        |  {platform.node():<20}")
            if cfg['logging_enabled']: draw_row(f"{COLORS['red']} [REC] LOGGING ENABLED{C_RST}")
            pr(MAIN_BOT)
            print("")

            # 2. UPTIME
            pr(UPTIME_TOP)
            draw_row(f"  {C_LBL}System Up :{C_RST} {get_uptime()}")
            pr(UPTIME_BOT)
            print("")

            # 3. CPU
            pr(CPU_TOP)
            draw_row(f"  {C_LBL}Usage     :{C_RST} {draw_bar(cpu, 15)} {cpu:>5.1f}%")
            if cpu_freq: draw_row(f"  {C_LBL}Speed     :{C_RST} {cpu_freq.current:.0f} MHz")
            
            if cores:
                for i in range(0, len(cores), 2):
                    c1 = cores[i]
                    c2 = cores[i+1] if i+1 < len(cores) else None
                    b1 = draw_bar(c1, 5)
                    row = f" #{i+1:02} {b1} {c1:>3.0f}%"
                    if c2 is not None:
                        b2 = draw_bar(c2, 5)
                        row += f"   #{i+2:02} {b2} {c2:>3.0f}%"
                    draw_row(row)
            pr(CPU_BOT)
            print("")

            # 4. MEMORY
            pr(RAM_TOP)
            draw_row(f"  {C_YLW}--- Physical RAM ---{C_RST}")
            draw_row(f"  {C_LBL}Total     :{C_RST} {get_size(mem.total)}")
            draw_row(f"  {C_LBL}Used      :{C_RST} {get_size(mem.used)} ({mem.percent}%)")
            draw_row(f"  {C_LBL}Free/Avail:{C_RST} {get_size(mem.available)}")
            draw_row(f"  {C_LBL}Progress  :{C_RST} {draw_bar(mem.percent, 25)}")
            draw_row(f"  {C_CYN}{'-'*60}{C_RST}") 
            draw_row(f"  {C_YLW}--- Swap (Virtual Mem) ---{C_RST}")
            draw_row(f"  {C_LBL}Total     :{C_RST} {get_size(swap.total)}")
            draw_row(f"  {C_LBL}Used      :{C_RST} {get_size(swap.used)} ({swap.percent}%)")
            draw_row(f"  {C_LBL}Free      :{C_RST} {get_size(swap.free)}")
            draw_row(f"  {C_LBL}Progress  :{C_RST} {draw_bar(swap.percent, 25)}")
            pr(RAM_BOT)
            print("")

            # 5. STORAGE
            pr(STO_TOP)
            for p in psutil.disk_partitions():
                try:
                    if 'cdrom' in p.opts or p.fstype == '': continue
                    u = psutil.disk_usage(p.mountpoint)
                    draw_row(f"  {C_LBL}{p.device[:5]:<5}     :{C_RST} {draw_bar(u.percent, 10)} {u.percent:>5.1f}% {get_size(u.used)}/{get_size(u.total)}")
                except: continue
            pr(STO_BOT)
            print("")

            # 6. NETWORK
            pr(NET_TOP)
            if ping:
                pc = COLORS['green'] if ping < 100 else COLORS['red']
                draw_row(f"  {C_LBL}Ping      :{C_RST} {pc}{ping:.0f} ms{C_RST}")
            else: draw_row(f"  {C_LBL}Ping      :{C_RST} {COLORS['red']}Offline{C_RST}")
            
            draw_row(f"  {C_LBL}Down      :{C_RST} {COLORS['green']}{get_size(recv)}/s{C_RST}")
            draw_row(f"  {C_LBL}Up        :{C_RST} {COLORS['yellow']}{get_size(sent)}/s{C_RST}")
            pr(NET_BOT)

    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit()

if __name__ == "__main__":
    main()