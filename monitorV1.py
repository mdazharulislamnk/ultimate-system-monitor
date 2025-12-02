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
# ⚙️ USER SETTINGS
# ==========================================
# This determines the visual width of the dashboard box.
# If the text wraps or looks broken, try increasing or decreasing this number.
# 66 is the standard width calculated to fit the 64 dashes + 2 borders.
W = 66  

# ==========================================
# 🛠️ DEFAULT CONFIGURATION
# ==========================================
# These settings act as a backup if 'config.json' is deleted or missing.
DEFAULT_CONFIG = {
    "refresh_rate": 0.5,        # How often to update the screen (0.5 = twice per second)
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

# This global variable will hold the active settings during runtime.
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
    Looks up the weird code (e.g. \033[31m) for a simple name (e.g. 'red').
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
    x: Pixels from the left.
    y: Pixels from the top.
    """
    if os.name == 'nt':
        try:
            import ctypes
            # Get the ID (Handle) of the current console window
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            
            if hwnd:
                # These are special Windows codes (Flags)
                # SWP_NOSIZE (0x0001) -> Keeps the current width/height
                # SWP_NOZORDER (0x0004) -> Keeps the window layer (doesn't force it to top)
                # We combine them: 0x0001 + 0x0004 = 0x0005
                FLAGS = 0x0005
                
                # SetWindowPos(ID, InsertAfter, X, Y, Width, Height, Flags)
                # We set InsertAfter to 0, Width to 0, Height to 0 (because flags ignore them)
                ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, 0, 0, FLAGS)
        except Exception:
            # If this fails (e.g., on Mac/Linux or restricted systems), do nothing
            pass

def setup_terminal():
    """
    Prepares the command prompt window for the dashboard.
    1. Fixes character encoding (UTF-8) so box lines connect properly on Windows.
    2. Resizes the window so lines don't wrap around and break the layout.
    3. Moves the window to the desired position.
    """
    if os.name == 'nt':
        # 'chcp 65001' sets Windows CMD to UTF-8 mode
        os.system('chcp 65001 >nul')
        # 'mode con' resizes the window. We add +4 for padding.
        os.system(f'mode con: cols={W + 4} lines=50')
        
        # --- MOVE WINDOW HERE ---
        # Change 10, 10 to whatever position you want (x, y)
        move_window(500, 100)
    
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
    # This fixes the "extra bar" glitch.
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
    # Current time - Boot time = Uptime duration
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
        s.settimeout(0.5) # Wait max 0.5 seconds
        s.connect((cfg['ping_target'], cfg['ping_port']))
        s.close()
        # Latency = End Time - Start Time
        return (time.time() - st) * 1000
    except:
        return None # Return None if offline

def log_metrics(cpu, ram, disk, down, up, ping):
    """
    Saves the current stats to a CSV file if logging is ON.
    This allows you to open the data in Excel later.
    """
    if not cfg['logging_enabled']: return
    
    # Check if file exists (to know if we need to write the header row)
    mode = 'a' if os.path.isfile(cfg['log_file']) else 'w'
    
    with open(cfg['log_file'], mode, newline='') as f:
        wr = csv.writer(f)
        # Write headers only if creating a new file
        if mode == 'w':
            wr.writerow(["Time", "CPU", "RAM", "Disk", "Down", "Up", "Ping"])
        # Write the data row
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
    Without this, the box borders would break because Python counts the 
    invisible color characters as part of the length.
    """
    # Regex pattern to find ANSI codes like \033[31m
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    # Remove them and count the remaining visible text
    return len(ansi_escape.sub('', s))

def draw_row(content, border_color=COLORS['cyan']):
    """
    Prints a single line inside the box borders.
    It automatically calculates how many spaces are needed on the right
    to make the right border line up perfectly.
    
    Format: ║ Content spaces ║
    """
    v_len = visible_len(content)
    
    # Math: Total Width - Left Border - Text Length - Right Border - 2 spaces padding
    padding = W - 2 - v_len - 2 
    
    # Safety: Ensure padding never goes negative
    if padding < 0: padding = 0
    
    # Print the constructed line
    print(f"{border_color}║{COLORS['reset']} {content}{' ' * padding} {border_color}║{COLORS['reset']}")

# ==========================================
# 🚀 MAIN PROGRAM
# ==========================================

def main():
    # 1. Check for command line flags (like --log)
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", action="store_true", help="Start logging immediately")
    args = parser.parse_args()

    # 2. Run Setup (Fix size AND position)
    setup_terminal()
    load_config()
    
    # Enable logging if user ran with --log
    if args.log: cfg['logging_enabled'] = True

    # Shortcuts for colors to keep code clean
    C_LBL = get_ansi(cfg['colors']['label'])   # Label Color (Red)
    C_RST = COLORS['reset']
    C_CYN = COLORS['cyan']
    C_YLW = COLORS['yellow']
    
    # ==========================================
    # 📦 BOX HEADER VARIABLES
    # ==========================================
    # We pre-calculate these strings so we don't have to rebuild them every second.
    # We use string multiplication ('═'*64) to create perfect lines.
    
    # 1. Main Header (Simple full width)
    MAIN_TOP = f"{C_CYN}╔{'═'*64}╗{C_RST}"
    MAIN_BOT = f"{C_CYN}╚{'═'*64}╝{C_RST}"

    # 2. Uptime Box (Calculated to center the text "UPTIME")
    UPTIME_TOP = f"{C_CYN}╔{'═'*28} {C_YLW}UPTIME{C_CYN} {'═'*28}╗{C_RST}"
    UPTIME_BOT = f"{C_CYN}╚{'═'*64}╝{C_RST}"

    # 3. CPU Box
    CPU_TOP = f"{C_CYN}╔{'═'*27} {C_YLW}CPU INFO{C_CYN} {'═'*27}╗{C_RST}"
    CPU_BOT = f"{C_CYN}╚{'═'*64}╝{C_RST}"

    # 4. RAM Box
    RAM_TOP = f"{C_CYN}╔{'═'*28} {C_YLW}MEMORY{C_CYN} {'═'*28}╗{C_RST}"
    RAM_BOT = f"{C_CYN}╚{'═'*64}╝{C_RST}"

    # 5. Storage Box
    STO_TOP = f"{C_CYN}╔{'═'*27} {C_YLW}STORAGE{C_CYN} {'═'*28}╗{C_RST}"
    STO_BOT = f"{C_CYN}╚{'═'*64}╝{C_RST}"

    # 6. Network Box
    NET_TOP = f"{C_CYN}╔{'═'*27} {C_YLW}NETWORK{C_CYN} {'═'*28}╗{C_RST}"
    NET_BOT = f"{C_CYN}╚{'═'*64}╝{C_RST}"

    print("Starting System Monitor...")
    
    # Get initial network stats to calculate speed later
    old_net = psutil.net_io_counters()

    try:
        # Start the Infinite Loop
        while True:
            # --- 1. GATHER DATA ---
            
            # CPU Data
            cpu = psutil.cpu_percent(interval=cfg['refresh_rate'])
            cpu_freq = psutil.cpu_freq()
            cores = psutil.cpu_percent(percpu=True) if cfg['show_cpu_per_core'] else []
            
            # Memory Data
            mem = psutil.virtual_memory() # Physical RAM
            swap = psutil.swap_memory()   # Virtual Memory (Pagefile)
            
            # Network Data
            net = psutil.net_io_counters()
            disk = psutil.disk_usage(os.path.abspath(os.sep))
            ping = get_ping()
            
            # Calculate Download/Upload Speed
            # (Current Bytes - Old Bytes) / Time Interval
            sent = (net.bytes_sent - old_net.bytes_sent) / cfg['refresh_rate']
            recv = (net.bytes_recv - old_net.bytes_recv) / cfg['refresh_rate']
            old_net = net
            
            # Save to file if logging is on
            log_metrics(cpu, mem.percent, disk.percent, recv, sent, ping)

            # --- 2. RENDER DASHBOARD ---
            
            clear_screen() # Wipe previous frame
            
            # --- MAIN HEADER SECTION ---
            print(MAIN_TOP)
            # Title row with Yellow color
            draw_row(f"{COLORS['yellow']}System Monitor Pro By Azhar        |  {platform.node():<20}")
            if cfg['logging_enabled']:
                draw_row(f"{COLORS['red']} [REC] LOGGING ENABLED{C_RST}")
            print(MAIN_BOT)
            print("") # Empty line for visual spacing

            # --- UPTIME SECTION ---
            print(UPTIME_TOP)
            draw_row(f"  {C_LBL}System Up :{C_RST} {get_uptime()}")
            print(UPTIME_BOT)
            print("")

            # --- CPU SECTION ---
            print(CPU_TOP)
            draw_row(f"  {C_LBL}Usage     :{C_RST} {draw_bar(cpu, 15)} {cpu:>5.1f}%")
            if cpu_freq:
                draw_row(f"  {C_LBL}Speed     :{C_RST} {cpu_freq.current:.0f} MHz")
            
            # Draw per-core bars if enabled
            if cores:
                for i in range(0, len(cores), 2):
                    c1 = cores[i]
                    # Check if there is a second core for this row
                    c2 = cores[i+1] if i+1 < len(cores) else None
                    
                    # Left Column
                    b1 = draw_bar(c1, 5)
                    row = f" #{i+1:02} {b1} {c1:>3.0f}%"
                    
                    # Right Column (if exists)
                    if c2 is not None:
                        b2 = draw_bar(c2, 5)
                        row += f"   #{i+2:02} {b2} {c2:>3.0f}%"
                    
                    draw_row(row)
            print(CPU_BOT)
            print("")

            # --- MEMORY SECTION ---
            print(RAM_TOP)
            
            # Physical RAM Details
            draw_row(f"  {C_YLW}--- Physical RAM ---{C_RST}")
            draw_row(f"  {C_LBL}Total     :{C_RST} {get_size(mem.total)}")
            draw_row(f"  {C_LBL}Used      :{C_RST} {get_size(mem.used)} ({mem.percent}%)")
            draw_row(f"  {C_LBL}Free/Avail:{C_RST} {get_size(mem.available)}")
            draw_row(f"  {C_LBL}Progress  :{C_RST} {draw_bar(mem.percent, 25)}")
            
            # Visual Separator
            draw_row(f"  {C_CYN}{'-'*60}{C_RST}") 
            
            # Swap Memory Details (Virtual Memory on Disk)
            draw_row(f"  {C_YLW}--- Swap (Virtual Mem) ---{C_RST}")
            draw_row(f"  {C_LBL}Total     :{C_RST} {get_size(swap.total)}")
            draw_row(f"  {C_LBL}Used      :{C_RST} {get_size(swap.used)} ({swap.percent}%)")
            draw_row(f"  {C_LBL}Free      :{C_RST} {get_size(swap.free)}")
            draw_row(f"  {C_LBL}Progress  :{C_RST} {draw_bar(swap.percent, 25)}")
            print(RAM_BOT)
            print("")

            # --- STORAGE SECTION ---
            print(STO_TOP)
            for p in psutil.disk_partitions():
                try:
                    # Skip CD-ROMs to avoid errors
                    if 'cdrom' in p.opts or p.fstype == '': continue
                    u = psutil.disk_usage(p.mountpoint)
                    
                    # Format: C:\ [BAR] 50% 50GB/100GB
                    # p.device[:5] limits the name length to 5 chars to fit nicely
                    draw_row(f"  {C_LBL}{p.device[:5]:<5}     :{C_RST} {draw_bar(u.percent, 10)} {u.percent:>5.1f}% {get_size(u.used)}/{get_size(u.total)}")
                except: continue
            print(STO_BOT)
            print("")

            # --- NETWORK SECTION ---
            print(NET_TOP)
            if ping:
                # Color code the ping (Green < 100ms, else Red)
                pc = COLORS['green'] if ping < 100 else COLORS['red']
                draw_row(f"  {C_LBL}Ping      :{C_RST} {pc}{ping:.0f} ms{C_RST}")
            else:
                draw_row(f"  {C_LBL}Ping      :{C_RST} {COLORS['red']}Offline{C_RST}")
            
            draw_row(f"  {C_LBL}Down      :{C_RST} {COLORS['green']}{get_size(recv)}/s{C_RST}")
            draw_row(f"  {C_LBL}Up        :{C_RST} {COLORS['yellow']}{get_size(sent)}/s{C_RST}")
            print(NET_BOT)

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nStopped.")
        sys.exit()

if __name__ == "__main__":
    main()