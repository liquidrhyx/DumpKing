#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║                        DUMPKING v4.3                          ║
║          Ultimate Memory Scanner & Editor for Android         ║
║             Automated Il2CppDumper Extraction Suite           ║
║            ENHANCED: Multi-Type Search + Watchpoints          ║
╚═══════════════════════════════════════════════════════════════╝
"""


import socket
import time
import os
import sys
import mmap
import threading
import subprocess
import struct
import select
import tkinter as tk
from tkinter import filedialog
from datetime import datetime


# ==================== CONFIGURATION ====================
METADATA_SIGNATURE_HEX = "af1bb1fa" 
IP = '127.0.0.1'
PORT = 12345
# =======================================================


# Enable ANSI colors in Windows CMD
os.system('color')


class UI:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    MAGENTA = '\033[95m'

    @staticmethod
    def box(text, color=CYAN):
        lines = text.split('\n')
        width = max(len(line) for line in lines) + 2
        print(f"{color}╔{'═'*width}╗")
        for line in lines:
            print(f"║ {line.center(width-2)} ║")
        print(f"╚{'═'*width}╝{UI.END}")


    @staticmethod
    def print_item(index, text, info=""):
        idx_str = f"[{index}]".ljust(5)
        print(f" {UI.GREEN}{idx_str}{UI.END} {UI.BOLD}{text.ljust(30)}{UI.END} {UI.BLUE}{info}{UI.END}")


    @staticmethod
    def header(text):
        print(f"\n{UI.CYAN}>> {text.upper()} <<{UI.END}")
        print(f"{UI.BLUE}{'-'*40}{UI.END}")


class ADBHelper:
    @staticmethod
    def run(cmd):
        try:
            return subprocess.check_output(f"adb {cmd}", shell=True).decode('utf-8').strip()
        except: return None


    @staticmethod
    def is_device_connected():
        out = ADBHelper.run("devices")
        return "device" in out and len(out.split('\n')) > 1


    @staticmethod
    def get_current_package():
        try:
            out = ADBHelper.run("shell dumpsys activity activities")
            if not out: return None

            for line in out.splitlines():
                if "mResumedActivity" in line:
                    parts = line.split()
                    for part in parts:
                        if "/" in part and "ActivityRecord" not in part:
                            return part.split("/")[0]
        except: pass
        return None


    @staticmethod
    def get_install_path(package):
        out = ADBHelper.run(f"shell pm path {package}")
        if out and "package:" in out:
            full_path = out.replace("package:", "").strip()
            return os.path.dirname(full_path)
        return None


    @staticmethod
    def launch_app(package):
        ADBHelper.run(f"shell monkey -p {package} -c android.intent.category.LAUNCHER 1")


    @staticmethod
    def kill_app(package):
        ADBHelper.run(f"shell am force-stop {package}")


class DumpKing:
    def __init__(self):
        self.host = IP
        self.port = PORT
        self.saved_values = {}
        self.watch_thread = None
        self.watching = False
        self.watch_addresses = []
        self.memory_cache = [] 
        self.cancel_requested = False
        self.active_snapshot = None
        self.snapshot_regions = None
        self.active_disk_snapshot = None
        self.disk_regions = None
        self.search_mode = None
        self.freeze_active = False
        self.freeze_thread = None
        self.freeze_targets = []


        # NEW: Watchpoint tracking
        self.watchpoint_active = False
        self.watchpoint_thread = None
        self.watchpoint_address = 0
        self.watchpoint_log = []

        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.ROOT_DUMP_FOLDER = os.path.join(self.BASE_DIR, "Dumped Memory Tools")
        self.METADATA_FOLDER = os.path.join(self.BASE_DIR, "Dumped MetaData")
        self.IL2CPP_FOLDER = os.path.join(self.BASE_DIR, "Pulled libil2cpp")
        self.DUMPER_FOLDER = os.path.join(self.BASE_DIR, "Il2CppDumper")


        for folder in [self.ROOT_DUMP_FOLDER, self.METADATA_FOLDER, self.IL2CPP_FOLDER]:
            if not os.path.exists(folder):
                try: os.makedirs(folder)
                except: pass


    def banner(self):
        print(f"{UI.CYAN}")
        print(r"""
  ____  _   _ __  __ ____  _  _____ _   _  ____ 
 |  _ \| | | |  \/  |  _ \| |/ /_ _| \ | |/ ___|
 | | | | | | | |\/| | |_) | ' / | ||  \| | |  _ 
 | |_| | |_| | |  | |  __/| . \ | || |\  | |_| |
 |____/ \___/|_|  |_|_|   |_|\_\___|_| \_|\____| v4.3
        """)
        print(f"{UI.END}")
        print(f" {UI.YELLOW}[*] Root Path: {self.BASE_DIR}{UI.END}")
        print(f" {UI.GREEN}[*] Output:    {self.ROOT_DUMP_FOLDER}{UI.END}\n")


    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')


    # ==================== STARTUP MENU ====================


    def startup(self):
        self.clear_screen()
        self.banner()
        UI.box("SELECT MODE", UI.GREEN)
        print("")
        UI.print_item("1", "File Replacement", "Static Hack (ADB Root)")
        UI.print_item("2", "Memory Spy", "Runtime Hack (Internal Server)")
        print("")
        UI.print_item("0", "Exit")

        c = input(f"\n{UI.CYAN}dumpking@start:~$ {UI.END}")

        if c == '1':
            self.file_replacement_mode()
        elif c == '2':
            self.connect_internal_server()
        elif c == '0':
            sys.exit(0)
        else:
            self.startup()


    # ==================== FEATURE 1: FILE REPLACEMENT ====================


    def file_replacement_mode(self):
        self.clear_screen()
        UI.header("SMART FILE REPLACER (ROOT)")

        if not ADBHelper.is_device_connected():
            print(f"{UI.RED}[!] No ADB Device connected.{UI.END}")
            input("Press Enter..."); self.startup()


        print(f"{UI.YELLOW}[*] Scanning for running game...{UI.END}")
        pkg = ADBHelper.get_current_package()

        if not pkg or pkg in ["com.android.launcher3", "com.android.systemui", "com.google.android.inputmethod.latin"]:
            print(f"{UI.RED}[!] No active game detected.{UI.END}")
            pkg = input(f"{UI.CYAN}Please enter the Package Name manually (e.g., com.example.game): {UI.END}")
            if not pkg: self.startup()
            print(f"{UI.YELLOW}[*] Launching {pkg} to verify install...{UI.END}")
            ADBHelper.launch_app(pkg)
            time.sleep(3)
        else:
            print(f"{UI.GREEN}[+] Detected Active App: {pkg}{UI.END}")


        print(f"{UI.YELLOW}[*] Fetching installation path...{UI.END}")
        install_path = ADBHelper.get_install_path(pkg)
        if not install_path:
            print(f"{UI.RED}[!] Could not find installation path. Is the app installed?{UI.END}")
            input("Enter to return..."); self.startup()

        print(f"{UI.GREEN}[+] Installation Path: {install_path}{UI.END}")


        print(f"\n{UI.RED}[!] Force Closing {pkg} to ensure safe replacement...{UI.END}")
        ADBHelper.kill_app(pkg)
        time.sleep(1)
        print(f"{UI.GREEN}[✓] App Killed.{UI.END}")


        print(f"\n{UI.BOLD}Select file to replace:{UI.END}")
        print(f" [1] libil2cpp.so (ARM64) - {UI.YELLOW}Most Common{UI.END}")
        print(f" [2] global-metadata.dat")
        print(f" [3] Custom Path")

        choice = input(f"{UI.CYAN}Choice: {UI.END}")

        target_path = ""
        header_check = None

        if choice == '1':
            target_path = f"{install_path}/lib/arm64/libil2cpp.so"
            header_check = b'\x7fELF'
        elif choice == '2':
            target_path = f"/data/data/{pkg}/files/il2cpp/Metadata/global-metadata.dat"
            header_check = b'\xaf\x1b\xb1\xfa'
        elif choice == '3':
            target_path = input(f"{UI.CYAN}Enter full device path: {UI.END}")
        else: self.startup()


        print(f"\n{UI.YELLOW}[*] Select your MODIFIED file from PC...{UI.END}")

        root = tk.Tk()
        root.withdraw()
        local_file = filedialog.askopenfilename(title="Select Hacked File")
        root.destroy()


        if not local_file:
            print(f"{UI.RED}[!] No file selected.{UI.END}")
            time.sleep(1); self.startup()


        if header_check:
            try:
                with open(local_file, 'rb') as f:
                    head = f.read(4)
                    if head != header_check:
                        print(f"\n{UI.RED}[WARNING] File Header Mismatch!{UI.END}")
                        print(f"Expected: {header_check.hex()} | Found: {head.hex()}")
                        print(f"You might be replacing the wrong file type.")
                        c = input("Continue anyway? (y/n): ")
                        if c.lower() != 'y': self.startup()
            except Exception:
                pass


        print(f"\n{UI.CYAN}Transferring file to secure storage...{UI.END}")

        temp_remote = "/sdcard/dk_temp_file"

        os.system(f'adb push "{local_file}" {temp_remote}')

        cmd = f'su -c "cp {temp_remote} {target_path}"'
        res = ADBHelper.run(f"shell {cmd}")

        perm_cmd = f'su -c "chmod 755 {target_path}"'
        ADBHelper.run(f"shell {perm_cmd}")

        ADBHelper.run(f"shell rm {temp_remote}")


        print(f"\n{UI.GREEN}[✓] SUCCESS! File replaced successfully.{UI.END}")
        print(f"{UI.YELLOW}[!] You can now launch the game.{UI.END}")
        input("Press Enter to return to menu...")
        self.startup()


    # ==================== FEATURE 2: INTERNAL SERVER ====================


    def connect_internal_server(self):
        self.clear_screen()
        UI.header("CONNECTING TO MEMORY SPY")

        ADBHelper.run(f"forward tcp:{PORT} tcp:{PORT}")

        print(f"{UI.YELLOW}[*] Attempting connection... (15s timeout){UI.END}")

        connected = False
        start_t = time.time()

        while time.time() - start_t < 15:
            res = self.send_command("PING", timeout=2)
            if "PONG" in res:
                connected = True
                break
            time.sleep(1)
            sys.stdout.write(".")
            sys.stdout.flush()

        if not connected:
            print(f"\n\n{UI.RED}[✗] Connection Failed.{UI.END}")
            print(f"{UI.YELLOW}[!] Troubleshooting Steps:{UI.END}")
            print(" 1. The game must be OPEN.")
            print(" 2. The DumpKing payload must be running inside the app.")
            print(" 3. Try restarting the game.")

            c = input(f"\n{UI.CYAN}[1] Retry  [2] Launch App via ADB  [0] Menu: {UI.END}")
            if c == '1': self.connect_internal_server()
            elif c == '2': 
                pkg = input("Enter Package Name: ")
                ADBHelper.launch_app(pkg)
                self.connect_internal_server()
            else: self.startup()
        else:
            print(f"\n{UI.GREEN}[✓] Connected to Internal Server.{UI.END}")
            time.sleep(1)
            self.get_parsed_maps()
            self.main_menu()
    
    def _check_cancel(self):
        """
        Non-blocking cancel check.
        - On Windows: disabled (no select on stdin)
        - On Unix: allows 'q' + Enter
        """
        if os.name == 'nt':
            # Windows: cannot select() on stdin safely
            return False

        try:
            r, _, _ = select.select([sys.stdin], [], [], 0)
            if r:
                cmd = sys.stdin.readline().strip().lower()
                if cmd in ('q', 'quit', 'cancel'):
                    self.cancel_requested = True
                    return True
        except:
            return False
        return False

    def start_freeze(self, result_dict, value):
        candidates = self._build_candidates_from_input(value)
        if not candidates:
            print(f"{UI.RED}[!] Invalid freeze value{UI.END}")
            return

        targets = []

        for stype, addrs in result_dict.items():
            if stype not in candidates:
                continue
            data_hex = candidates[stype].hex()

            for a in addrs:
                if self.search_mode == 'safe':
                    addr = a
                    region = self._get_region_for_address(addr)
                else:
                    addr = self.file_offset_to_address(a)
                    region = self._get_region_for_file_offset(a)

                if not addr or not region:
                    continue

                if 'w' not in region['perms']:
                    print(f"{UI.YELLOW}[RO] Cannot freeze {hex(addr)}{UI.END}")
                    continue

                targets.append((addr, data_hex))

        if not targets:
            print(f"{UI.RED}[!] Nothing writable to freeze{UI.END}")
            return

        self.freeze_targets = targets
        self.freeze_active = True
        self.freeze_thread = threading.Thread(
            target=self._freeze_worker,
            daemon=True
        )
        self.freeze_thread.start()

        print(f"{UI.GREEN}[✓] Freeze active ({len(targets)} addresses){UI.END}")

    def _freeze_worker(self, interval=0.25):
        while self.freeze_active:
            for addr, data_hex in self.freeze_targets:
                if self.search_mode == 'safe':
                    region = self._get_region_for_address(addr)
                else:
                    region = next(
                        (r for r in self.disk_regions if r['mem_start'] <= addr < r['mem_end']),
                        None
                    )
                if not region or 'w' not in region['perms']:
                    print(f"{UI.RED}[!] Freeze stopped: RO at {hex(addr)}{UI.END}")
                    self.freeze_active = False
                    return

                self.send_command(
                    f"WRITE_HEX:{hex(addr)}:{data_hex}",
                    timeout=2
                )
            time.sleep(interval)

    def stop_freeze(self):
        if not self.freeze_active:
            print(f"{UI.YELLOW}[!] No active freeze{UI.END}")
            return
        self.freeze_active = False
        self.freeze_targets = []
        print(f"{UI.GREEN}[✓] Freeze stopped{UI.END}")


    # ==================== NETWORK & UTILS ====================


    def send_command(self, cmd, timeout=30):
        """Enhanced send_command with crash detection and auto-reconnect"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((self.host, self.port))
            s.send(cmd.encode())
            response = b''
            while True:
                try:
                    chunk = s.recv(65536)
                    if not chunk: break
                    response += chunk
                    if len(response) > 52428800: break 
                except socket.timeout: break
            s.close()

            decoded = response.decode('utf-8', errors='replace').strip('\x00')

            # Check if server is still alive
            if not decoded or len(decoded) == 0:
                # Empty response = possible crash
                if cmd == "PING":
                    return "ERROR:SERVER_DEAD"
                # Try ping to confirm
                ping_result = self.send_command("PING", timeout=2)
                if "PONG" not in ping_result:
                    print(f"\n{UI.RED}[!] SERVER CRASHED OR DISCONNECTED{UI.END}")
                    self.handle_server_crash()
                    return "ERROR:SERVER_CRASHED"

            return decoded

        except ConnectionRefusedError:
            print(f"\n{UI.RED}[!] CONNECTION REFUSED - Server not running{UI.END}")
            self.handle_server_crash()
            return "ERROR:CONNECTION_REFUSED"
        except socket.timeout:
            print(f"\n{UI.YELLOW}[!] TIMEOUT - Server might be overloaded{UI.END}")
            return "ERROR:TIMEOUT"
        except Exception as e:
            print(f"\n{UI.RED}[!] NETWORK ERROR: {e}{UI.END}")
            return f"ERROR:{e}"


    def handle_server_crash(self):
        """Handle server crash - notify user and attempt recovery"""
        print(f"\n{UI.RED}╔════════════════════════════════════════╗{UI.END}")
        print(f"{UI.RED}║     SERVER CRASH DETECTED!             ║{UI.END}")
        print(f"{UI.RED}╚════════════════════════════════════════╝{UI.END}")

        print(f"\n{UI.YELLOW}Possible causes:{UI.END}")
        print(f" 1. Memory scanner hit device limits")
        print(f" 2. Game crashed or was closed")
        print(f" 3. ADB port forwarding reset")
        print(f" 4. Out of memory on device")

        print(f"\n{UI.CYAN}[*] Attempting auto-recovery...{UI.END}")

        # Wait a moment
        time.sleep(2)

        # Re-establish ADB forward
        print(f"{UI.YELLOW}[1/3] Re-establishing ADB port forward...{UI.END}")
        ADBHelper.run(f"forward tcp:{self.port} tcp:{self.port}")
        time.sleep(1)

        # Test connection
        print(f"{UI.YELLOW}[2/3] Testing connection...{UI.END}")
        retry_count = 0
        max_retries = 5

        while retry_count < max_retries:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect((self.host, self.port))
                s.send(b"PING")
                resp = s.recv(1024).decode()
                s.close()

                if "PONG" in resp:
                    print(f"{UI.GREEN}[3/3] ✓ Connection restored!{UI.END}")
                    print(f"\n{UI.GREEN}[+] Server is back online.{UI.END}")
                    time.sleep(1)
                    return True
            except:
                pass

            retry_count += 1
            print(f"{UI.YELLOW}    Retry {retry_count}/{max_retries}...{UI.END}")
            time.sleep(2)

        # Failed to reconnect
        print(f"\n{UI.RED}[✗] Auto-recovery failed.{UI.END}")
        print(f"\n{UI.YELLOW}MANUAL RECOVERY STEPS:{UI.END}")
        print(f" 1. Check if game is still running")
        print(f" 2. Restart the game")
        print(f" 3. Return to main menu and reconnect")

        input(f"\n{UI.CYAN}Press Enter to return to menu...{UI.END}")
        self.main_menu()
        return False
    
    def _build_candidates_from_input(self, raw_value):
        """
        Accepts int, hex string (0x...), or text string.
        Returns a candidates dict mapping search_name -> bytes (little-endian where applicable).
        This is used by smart_search only (keeps existing generate_search_candidates untouched).
        """
        candidates = {}

        # If it's already bytes, just use it
        if isinstance(raw_value, (bytes, bytearray)):
            candidates['bytes'] = bytes(raw_value)
            return candidates

        # If it's an int (or numeric-like), use existing integer flows
        if isinstance(raw_value, (int, float)):
            try:
                # prefer int path for integer-like inputs
                int_val = int(raw_value)
                # reuse your existing integer/float/double/xor logic by temporarily calling generate_search_candidates
                try:
                    candidates.update(self.generate_search_candidates(int_val))
                except Exception:
                    pass
                # also include raw binary representation of stringified hex
                try:
                    candidates['raw_int_le'] = int_val.to_bytes(4, byteorder='little', signed=True)
                except:
                    pass
                return candidates
            except:
                    pass
        # If string:
        s = str(raw_value).strip()

        # Detect hex strings: starting with 0x or only hex chars and even length
        if s.startswith("0x") or all(c in "0123456789abcdefABCDEF" for c in s.replace(" ", "")) and len(s.replace(" ", "")) % 2 == 0:
            try:
                # strip 0x and spaces
                hs = s[2:] if s.startswith("0x") else s
                hs = hs.replace(" ", "")
                b = bytes.fromhex(hs)
                candidates['hex_bytes'] = b
            except:
                pass

            # Also try interpreting as integer if 0xNNNN
            try:
                int_val = int(s, 16)
                try:
                    candidates.update(self.generate_search_candidates(int_val))
                except:
                    pass
            except:
                pass

            return candidates

        # Otherwise treat as plain string -> bytes (UTF-8) plus NULL-terminated and uppercase/lowercase variants.
        try:
            b = s.encode('utf-8')
            candidates['utf8'] = b
            # common variations
            candidates['utf8_null'] = b + b'\x00'
            candidates['utf16le'] = s.encode('utf-16le')
            candidates['hex_string'] = b.hex().encode('utf-8')
        except:
            pass

        # fallback: try numeric parsing
        try:
            iv = int(s)
            try:
                candidates.update(self.generate_search_candidates(iv))
            except:
                pass
        except:
            pass

        return candidates

    def smart_search(self, value, mode='safe'):
        """
        Smart search using:
        - SAFE  -> RAM snapshot (fast, small)
        - ENTIRE -> FAST dump engine + mmap (very fast scan)
        """
        self.search_mode = mode
        if mode == 'entire' and self.active_disk_snapshot:
            self.cleanup_disk_snapshot()
            self.active_disk_snapshot = None
            self.disk_regions = None
        UI.header(f"SMART SEARCH: {value}")
        print(f"{UI.YELLOW}[*] Generating search candidates...{UI.END}")

        # Sanity ping
        if "PONG" not in self.send_command("PING", timeout=2):
            print(f"{UI.RED}[!] Server not responding{UI.END}")
            return {}

        candidates = self._build_candidates_from_input(value)
        if not candidates:
            print(f"{UI.RED}[!] Invalid search input{UI.END}")
            return {}

        maps = self.get_parsed_maps()
        if not maps:
            print(f"{UI.RED}[!] No memory maps{UI.END}")
            return {}

        # ---------------- REGION SELECTION ----------------

        if mode == 'entire':
            regions = [m for m in maps if 'r' in m['perms']]
        else:
            regions = [
                m for m in maps
                if 'rw-' in m['perms'] and m['size'] <= 8 * 1024 * 1024
            ]

        total_bytes = sum(r['size'] for r in regions)
        if total_bytes == 0:
            print(f"{UI.RED}[!] Nothing to scan{UI.END}")
            return {}

        # ---------------- SNAPSHOT / DUMP ----------------

        snapshot = None
        dump_file = None

        if mode == 'safe':
            snapshot = self._build_memory_snapshot(regions)
            if not snapshot:
                return {}

        else:
            # ENTIRE MEMORY → FAST DUMP ENGINE
            dump_file = os.path.join(
                self.ROOT_DUMP_FOLDER,
                f"entire_memory_dump_{int(time.time())}.bin"
            )

            UI.header("DUMPING ENTIRE MEMORY (FAST MODE)")
            print(f"{UI.YELLOW}[!] Using fast dump engine (~3 MB/s){UI.END}")

            self.disk_regions = []
            file_offset = 0

            with open(dump_file, 'wb') as f:
                for r in regions:
                    self.disk_regions.append({
                        'file_start': file_offset,
                        'file_end': file_offset + r['size'],
                        'mem_start': r['start'],
                        'mem_end': r['end'],
                        'perms': r['perms']
                    })

                    ok = self.perform_smart_dump(
                        r['start'],
                        r['size'],
                        f,
                        base_offset=file_offset
                    )

                    if not ok:
                        print(f"{UI.RED}[!] Dump aborted{UI.END}")
                        return {}

                    file_offset += r['size']

            self.active_disk_snapshot = dump_file

        # ---------------- SCAN ----------------

        mode_label = "ENTIRE MEMORY (DUMP)" if mode == 'entire' else "SAFE SNAPSHOT"
        print(f"{UI.CYAN}[*] Scanning {len(candidates)} value types ({mode_label}){UI.END}")

        all_results = {}
        total_found = 0

        # ===== ENTIRE MEMORY (DISK + MMAP) =====
        if mode == 'entire':
            with open(self.active_disk_snapshot, 'rb') as f:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

                for name, needle in candidates.items():
                    print(f"{UI.YELLOW}>> Trying: {name.ljust(20)}{UI.END}", end=" ")

                    found = []
                    idx = mm.find(needle)
                    while idx != -1:
                        found.append(idx)
                        idx = mm.find(needle, idx + 1)

                    if found:
                        all_results[name] = found
                        total_found += len(found)
                        print(f"{UI.GREEN}✓ Found {len(found)}{UI.END}")
                    else:
                        print(f"{UI.RED}✗ None{UI.END}")

                mm.close()

        # ===== SAFE SEARCH (RAM SNAPSHOT) =====
        else:
            for name, needle in candidates.items():
                print(f"{UI.YELLOW}>> Trying: {name.ljust(20)}{UI.END}", end=" ")

                found = []
                for block in snapshot:
                    base = block['start']
                    data = block['data']

                    idx = data.find(needle)
                    while idx != -1:
                        found.append(base + idx)
                        idx = data.find(needle, idx + 1)

                if found:
                    all_results[name] = found
                    total_found += len(found)
                    print(f"{UI.GREEN}✓ Found {len(found)}{UI.END}")
                else:
                    print(f"{UI.RED}✗ None{UI.END}")
        print(f"\n{UI.GREEN}[+] Total Results: {total_found} across {len(all_results)} types{UI.END}")

        self.active_snapshot = snapshot
        return all_results

    
    def diagnose_scan(self):
        """Show what memory regions will be scanned"""
        maps = self.get_parsed_maps()
        
        # Filter same way as smali scanner
        scannable = []
        for m in maps:
            if ('rw-' in m['perms'] or 'r--' in m['perms']) and m['size'] <= 8*1024*1024:
                scannable.append(m)
        
        print(f"\n{UI.CYAN}SCAN COVERAGE ANALYSIS{UI.END}")
        print(f"Total regions: {len(maps)}")
        print(f"Scannable regions: {len(scannable)}")
        
        total_size = sum(m['size'] for m in scannable)
        print(f"Total scan size: {total_size/1024/1024:.1f} MB")
        
        print(f"\n{UI.YELLOW}Sample scannable regions:{UI.END}")
        for m in scannable[:20]:  # Show first 20
            print(f"  {hex(m['start'])} | {m['size']/1024:.0f}KB | {m['perms']} | {m['name']}")
        
        input("\nPress Enter to continue...")

    def smart_region_filter(self):
        """Show which regions likely contain game data"""
        maps = self.get_parsed_maps()
    
        # Prioritize regions
        priority_regions = []
    
        for m in maps:
            if 'rw-' not in m['perms'] and 'r--' not in m['perms']:
                continue
            if m['size'] > 8*1024*1024:
                continue
            
            # Calculate priority score
            score = 0
            name = m['name'].lower()
        
            if 'anon' in name or name == '':
                score = 100  # Highest - heap data
            elif 'libil2cpp' in name:
                score = 90
            elif 'libunity' in name:
                score = 80
            elif 'heap' in name:
                score = 95
            elif name.startswith('/system'):
                score = 10  # Lowest - system libs
            else:
                score = 50
        
            priority_regions.append((score, m))
    
        # Sort by priority
        priority_regions.sort(reverse=True, key=lambda x: x[0])
    
        print(f"\nTOP 20 PRIORITY REGIONS:")
        for score, m in priority_regions[:20]:
            print(f"  [{score}] {hex(m['start'])} | {m['size']/1024:.0f}KB | {m['name']}")

    def _build_memory_snapshot(self, regions):
        """
        Reads memory ONCE and stores it in RAM.
        Returns list of dicts: {start, data}
        """
        snapshot = []
        total = sum(r['size'] for r in regions)
        read = 0
        self.cancel_requested = False
        print(f"{UI.YELLOW}[!] Press 'q' + Enter to cancel{UI.END}")

        CHUNK = 4096
        last_print = time.time()

        UI.header("BUILDING MEMORY SNAPSHOT")

        for r in regions:
            buf = bytearray()
            offset = 0

            while offset < r['size']:
                if self._check_cancel():
                    print(f"\n{UI.RED}[!] Operation cancelled by user{UI.END}")
                    return None
            
                size = min(CHUNK, r['size'] - offset)
                addr = r['start'] + offset
                res = self.send_command(f"READ:{hex(addr)}:{size}", timeout=5)

                if self.cancel_requested:
                    print(f"\n{UI.RED}[!] Snapshot cancelled by user{UI.END}")
                    return None

                if res and not res.startswith("ERROR"):
                    try:
                        chunk = bytes.fromhex(res)
                    except:
                        chunk = b'\x00' * size
                else:
                    chunk = b'\x00' * size

                buf.extend(chunk)
                offset += size
                read += size

                # Progress + cyberpunk bytes
                now = time.time()
                if now - last_print > 0.15:
                    percent = (read / total) * 100 if total else 100.0
                    stream = chunk[:32].hex().upper()
                    sys.stdout.write(
                        f"\r{UI.CYAN}[*] Snapshot: "
                        f"{read // 1024 // 1024}MB / "
                        f"{total // 1024 // 1024}MB "
                        f"({percent:.1f}%) | "
                        f"READING: {stream}{UI.END}"
                    )
                    sys.stdout.flush()
                    last_print = now

            snapshot.append({
                'start': r['start'],
                'data': bytes(buf)
            })

        # ---- FORCE FINAL SNAPSHOT DISPLAY (AFTER ALL REGIONS) ----
        sys.stdout.write(
            f"\r{UI.CYAN}[*] Snapshot: "
            f"{total // 1024 // 1024}MB / "
            f"{total // 1024 // 1024}MB "
            f"(100.0%){UI.END}\n"
        )
        sys.stdout.flush()
        print(UI.GREEN + "[✓] Snapshot complete" + UI.END)
        # ---------------------------------------------------------

        return snapshot


    def int_to_hex_le(self, value):
        return value.to_bytes(4, byteorder='little').hex()


    def hex_le_to_int(self, hex_str):
        try: return int.from_bytes(bytes.fromhex(hex_str.strip()), byteorder='little')
        except: return None


    def parse_address_list(self, result):
        if result.startswith('ERROR'): return []
        return [int(x.strip()) for x in result.replace('[', '').replace(']', '').split(',') if x.strip()]


    def read_int(self, address):
        return self.hex_le_to_int(self.send_command(f"READ:{hex(address)}:4", timeout=5))


    def write_int(self, address, value):
        is_writable = False
        found_region = False

        for m in self.memory_cache:
            if m['start'] <= address < m['end']:
                found_region = True
                if 'w' in m['perms']: is_writable = True
                break

        res = self.send_command(f"WRITE:{hex(address)}:{value}")

        if "WRITE_OK" in res:
            return True
        else:
            if found_region and not is_writable:
                print(f"\n{UI.RED}[!] ⚠ WRITE FAILED: READ-ONLY MEMORY DETECTED.{UI.END}")
                print(f"{UI.YELLOW}    You are trying to write to a 'Code' region (r-xp or r--p).{UI.END}")
                print(f"{UI.YELLOW}    Runtime patching of Code is blocked by Android OS.{UI.END}")
                print(f"{UI.GREEN}    SOLUTION: Use 'File Replacement' mode in the startup menu.{UI.END}")
                input("Press Enter to continue...")
            return False


    def check_file_overwrite(self, filepath):
        if os.path.exists(filepath):
            print(f"\n{UI.YELLOW}[!] File exists: {os.path.basename(filepath)}{UI.END}")
            if input(f"{UI.CYAN}Overwrite? (y/n): {UI.END}").lower() == 'y':
                try: os.remove(filepath); time.sleep(0.5); return True
                except: return False
            return False
        return True


    # ==================== NEW: MEMORY WATCHPOINT SYSTEM ====================


    def watchpoint_worker(self, address, poll_interval=0.05):
        """
        Background thread that monitors memory address for changes.
        When value changes, captures timestamp and new value.
        """
        last_value = self.read_int(address)
        change_count = 0

        print(f"\n{UI.MAGENTA}[WATCHPOINT] Monitoring 0x{address:X} | Initial: {last_value}{UI.END}")
        print(f"{UI.YELLOW}[*] Press Ctrl+C to stop monitoring...{UI.END}\n")

        while self.watchpoint_active:
            try:
                current_value = self.read_int(address)

                if current_value != last_value and current_value is not None:
                    change_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

                    log_entry = {
                        'time': timestamp,
                        'address': address,
                        'old_value': last_value,
                        'new_value': current_value,
                        'change_id': change_count
                    }

                    self.watchpoint_log.append(log_entry)

                    # Display real-time
                    print(f"{UI.GREEN}[{timestamp}] CHANGE #{change_count}{UI.END}")
                    print(f"  Address:  0x{address:X}")
                    print(f"  Old:      {last_value}")
                    print(f"  New:      {UI.BOLD}{current_value}{UI.END}")
                    print(f"  Delta:    {current_value - last_value:+d}\n")

                    last_value = current_value

                time.sleep(poll_interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"{UI.RED}[!] Watchpoint error: {e}{UI.END}")
                break

        print(f"\n{UI.YELLOW}[WATCHPOINT] Stopped. Total changes detected: {change_count}{UI.END}")


    def start_watchpoint(self, address):
        """Start monitoring an address for changes"""
        if self.watchpoint_active:
            print(f"{UI.RED}[!] Watchpoint already active! Stop it first.{UI.END}")
            return

        self.watchpoint_address = address
        self.watchpoint_log = []
        self.watchpoint_active = True

        self.watchpoint_thread = threading.Thread(
            target=self.watchpoint_worker,
            args=(address,),
            daemon=True
        )
        self.watchpoint_thread.start()


    def stop_watchpoint(self):
        """Stop active watchpoint"""
        if not self.watchpoint_active:
            print(f"{UI.YELLOW}[!] No active watchpoint.{UI.END}")
            return

        self.watchpoint_active = False
        if self.watchpoint_thread:
            self.watchpoint_thread.join(timeout=2)

        print(f"{UI.GREEN}[✓] Watchpoint stopped.{UI.END}")


    def view_watchpoint_log(self):
        """Display captured changes"""
        if not self.watchpoint_log:
            print(f"{UI.YELLOW}[!] No changes recorded.{UI.END}")
            return

        print(f"\n{UI.CYAN}╔══════════════════════════════════════════════════════╗{UI.END}")
        print(f"{UI.CYAN}║           MEMORY CHANGE LOG                          ║{UI.END}")
        print(f"{UI.CYAN}╚══════════════════════════════════════════════════════╝{UI.END}\n")

        print(f"{UI.BOLD}{'#'.ljust(5)} {'TIME'.ljust(15)} {'ADDRESS'.ljust(12)} {'OLD'.ljust(10)} {'NEW'.ljust(10)} {'DELTA'}{UI.END}")
        print("-" * 70)

        for entry in self.watchpoint_log[-50:]:  # Show last 50
            delta = entry['new_value'] - entry['old_value']
            delta_str = f"{delta:+d}" if delta != 0 else "0"

            print(f"{str(entry['change_id']).ljust(5)} "
                  f"{entry['time'].ljust(15)} "
                  f"0x{entry['address']:X}".ljust(12) + " "
                  f"{str(entry['old_value']).ljust(10)} "
                  f"{str(entry['new_value']).ljust(10)} "
                  f"{delta_str}")


    def export_watchpoint_log(self):
        """Export log to file"""
        if not self.watchpoint_log:
            print(f"{UI.YELLOW}[!] No changes to export.{UI.END}")
            return

        filename = f"watchpoint_log_{int(time.time())}.txt"
        try:
            with open(filename, 'w') as f:
                f.write("DUMPKING MEMORY WATCHPOINT LOG\n")
                f.write(f"Address: 0x{self.watchpoint_address:X}\n")
                f.write(f"Total Changes: {len(self.watchpoint_log)}\n")
                f.write("="*70 + "\n\n")

                for entry in self.watchpoint_log:
                    f.write(f"[{entry['time']}] Change #{entry['change_id']}\n")
                    f.write(f"  Address: 0x{entry['address']:X}\n")
                    f.write(f"  Old Value: {entry['old_value']}\n")
                    f.write(f"  New Value: {entry['new_value']}\n")
                    f.write(f"  Delta: {entry['new_value'] - entry['old_value']:+d}\n\n")

            print(f"{UI.GREEN}[✓] Exported to: {filename}{UI.END}")
        except Exception as e:
            print(f"{UI.RED}[!] Export failed: {e}{UI.END}")


    def watchpoint_menu(self):
        """Menu for memory watchpoint features"""
        while True:
            self.clear_screen()
            UI.box("MEMORY WATCHPOINT", UI.MAGENTA)
            print("")

            status = f"{UI.GREEN}ACTIVE{UI.END}" if self.watchpoint_active else f"{UI.RED}INACTIVE{UI.END}"
            log_count = len(self.watchpoint_log)

            print(f" Status: {status}")
            if self.watchpoint_active:
                print(f" Address: {UI.CYAN}0x{self.watchpoint_address:X}{UI.END}")
            print(f" Changes Logged: {UI.YELLOW}{log_count}{UI.END}\n")

            UI.print_item("1", "Start Watchpoint", "Monitor address for changes")
            UI.print_item("2", "Stop Watchpoint")
            UI.print_item("3", "View Change Log", f"({log_count} entries)")
            UI.print_item("4", "Export Log to File")
            UI.print_item("5", "Clear Log")
            UI.print_item("0", "Back")

            c = input(f"\n{UI.CYAN}root@android:~/watchpoint# {UI.END}")

            if c == '1':
                if self.watchpoint_active:
                    print(f"{UI.RED}[!] Stop current watchpoint first!{UI.END}")
                    time.sleep(1)
                else:
                    try:
                        addr_str = input(f"{UI.YELLOW}Enter address (hex, e.g., 0x12345678): {UI.END}")
                        address = int(addr_str, 16)
                        print(f"\n{UI.YELLOW}[*] Starting watchpoint... (monitoring in background){UI.END}")
                        self.start_watchpoint(address)
                        time.sleep(2)
                    except Exception as e:
                        print(f"{UI.RED}[!] Error: {e}{UI.END}")
                        time.sleep(1)

            elif c == '2':
                self.stop_watchpoint()
                time.sleep(1)

            elif c == '3':
                self.view_watchpoint_log()
                input("\nPress Enter to continue...")

            elif c == '4':
                self.export_watchpoint_log()
                time.sleep(1)

            elif c == '5':
                self.watchpoint_log = []
                print(f"{UI.GREEN}[✓] Log cleared.{UI.END}")
                time.sleep(0.5)

            elif c == '0':
                if self.watchpoint_active:
                    print(f"{UI.YELLOW}[!] Stopping active watchpoint...{UI.END}")
                    self.stop_watchpoint()
                    time.sleep(1)
                break


    # ==================== ENHANCED SEARCH ENGINE ====================


    def generate_search_candidates(self, value):
        """
        Generate all possible representations of a value for comprehensive searching.
        Mimics Game Guardian's multi-type encrypted search capability.
        """
        candidates = {}
        if not isinstance(value, int):
            return {}
        # 1. DIRECT INTEGER (DWORD - 4 bytes)
        try:
            candidates['int32'] = value.to_bytes(4, byteorder='little', signed=True)
        except: pass

        try:
            candidates['uint32'] = value.to_bytes(4, byteorder='little', signed=False)
        except: pass

        # 2. FLOAT (Single Precision - 4 bytes)
        try:
            candidates['float'] = struct.pack('<f', float(value))
        except: pass

        # 3. DOUBLE (Double Precision - 8 bytes)
        try:
            candidates['double'] = struct.pack('<d', float(value))
        except: pass

        # 4. XOR ENCRYPTED (Common encryption method)
        xor_keys = [0x12345678, 0xDEADBEEF, 0xCAFEBABE, 0x87654321, 0xAAAAAAAA, 0x55555555]
        for key in xor_keys:
            try:
                encrypted = value ^ key
                candidates[f'xor_{hex(key)}'] = encrypted.to_bytes(4, byteorder='little', signed=False)
            except: pass

        # 5. INVERTED VALUE (Negative representation)
        try:
            candidates['negative'] = (-value).to_bytes(4, byteorder='little', signed=True)
        except: pass

        # 6. SCALED VALUES (Common in Unity games)
        for scale in [10, 100, 1000, 10000]:
            try:
                scaled = value * scale
                candidates[f'scaled_x{scale}'] = scaled.to_bytes(4, byteorder='little', signed=True)
            except: pass

        # 7. HEX STRING REPRESENTATION
        try:
            hex_str = hex(value)[2:].encode('utf-8')
            candidates['hex_string'] = hex_str
        except: pass

        return candidates

    def refine_smart_results(self, result_dict, new_value):

        if self.search_mode == 'entire':
            return self._refine_disk_results(result_dict, new_value)
        UI.header(f"REFINING TO: {new_value}")

        if not self.active_snapshot:
            print(f"{UI.RED}[!] No snapshot available. Run Smart Search again.{UI.END}")
            return result_dict

        new_candidates = self._build_candidates_from_input(new_value)
        refined = {}

        for search_type, addresses in result_dict.items():
            if search_type not in new_candidates:
                continue

            needle = new_candidates[search_type]
            nlen = len(needle)
            matched = []

            for block in self.active_snapshot:
                base = block['start']
                data = block['data']

                for addr in addresses:
                    if base <= addr < base + len(data):
                        offset = addr - base
                        if data[offset:offset+nlen] == needle:
                            matched.append(addr)
            if matched:
                refined[search_type] = matched
                print(f"{UI.GREEN}✓ {search_type}: {len(matched)} remain{UI.END}")
            else:
                print(f"{UI.RED}✗ {search_type}: none{UI.END}")
        total = sum(len(v) for v in refined.values())
        print(f"\n{UI.GREEN}[+] Refined to {total} addresses{UI.END}")
        return refined

    def _refine_disk_results(self, result_dict, new_value):
        UI.header(f"REFINING (DISK SNAPSHOT): {new_value}")

        if not self.active_disk_snapshot or not self.disk_regions:
            print(f"{UI.RED}[!] No disk snapshot available{UI.END}")
            return result_dict

        candidates = self._build_candidates_from_input(new_value)
        refined = {}

        with open(self.active_disk_snapshot, 'rb') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

            for stype, offsets in result_dict.items():
                if stype not in candidates:
                    continue

                needle = candidates[stype]
                nlen = len(needle)
                kept = []

                for off in offsets:
                    if mm[off:off+nlen] == needle:
                        kept.append(off)

                if kept:
                    refined[stype] = kept
                    print(f"{UI.GREEN}✓ {stype}: {len(kept)} remain{UI.END}")
                else:
                    print(f"{UI.RED}✗ {stype}: none{UI.END}")

            mm.close()

        print(f"\n{UI.GREEN}[+] Disk refine complete{UI.END}")
        return refined

    def file_offset_to_address(self, offset):
        for r in self.disk_regions:
            if r['file_start'] <= offset < r['file_end']:
                return r['mem_start'] + (offset - r['file_start'])
        return None

    def display_smart_results(self, result_dict, limit=50):
        """
        Display results grouped by value type with current values.
        """
        print(f"\n{UI.BOLD}{'TYPE'.ljust(20)} {'ADDRESS'.ljust(14)} {'CURRENT VALUE'}{UI.END}")
        print("-" * 60)

        count = 0
        for search_type, addresses in result_dict.items():
            for addr in addresses[:min(10, len(addresses))]:
                if self.search_mode == 'entire':
                    real = self.file_offset_to_address(addr)
                    print(f"{search_type.ljust(20)} {hex(real) if real else 'N/A'}")
                    current = self.read_int(real) if real else None
                else:
                    current = self.read_int(addr)
                    print(f"{search_type.ljust(20)} {hex(addr).ljust(14)} {current}")
                count += 1
                if count >= limit:
                    print(f"\n{UI.YELLOW}[...] Showing first {limit} results{UI.END}")
                    return
            if addresses:
                print("")


    def write_smart_results(self, result_dict, new_value):
        candidates = self._build_candidates_from_input(new_value)
        if not candidates:
            print(f"{UI.RED}[!] Invalid value{UI.END}")
            return False

        success = 0
        failed = 0
        blocked = 0

        for stype, addrs in result_dict.items():
            if stype not in candidates:
                continue

            data_hex = candidates[stype].hex()

            for a in addrs:
                if self.search_mode == 'safe':
                    addr = a
                    region = self._get_region_for_address(addr)
                else:
                    addr = self.file_offset_to_address(a)
                    region = self._get_region_for_file_offset(a)

                if not addr or not region:
                    failed += 1
                    continue

                if 'w' not in region['perms']:
                    print(f"{UI.YELLOW}[RO] {hex(addr)} ({region['perms']}){UI.END}")
                    blocked += 1
                    continue

                res = self.send_command(
                    f"WRITE_HEX:{hex(addr)}:{data_hex}",
                    timeout=3
                )

                if "WRITE_OK" in res:
                    success += 1
                else:
                    failed += 1

        print(
            f"{UI.GREEN}[+] Written: {success}{UI.END} | "
            f"{UI.YELLOW}Blocked: {blocked}{UI.END} | "
            f"{UI.RED}Failed: {failed}{UI.END}"
        )
        return success > 0

    def _write_disk_results(self, result_dict, new_value):
        print(f"{UI.YELLOW}[!] Writing via disk snapshot mapping{UI.END}")

        candidates = self._build_candidates_from_input(new_value)
        success = 0
        failed = 0

        for stype, offsets in result_dict.items():
            if stype not in candidates:
                continue

            data = candidates[stype]

            for off in offsets:
                addr = self.file_offset_to_address(off)
                if addr is None:
                    failed += 1
                    continue

                # Check permissions
                region = next(
                    (r for r in self.disk_regions if r['mem_start'] <= addr < r['mem_end']),
                    None
                )
                if not region or 'w' not in region['perms']:
                    print(f"{UI.RED}[!] READ-ONLY: {hex(addr)}{UI.END}")
                    failed += 1
                    continue

                res = self.send_command(
                    f"WRITE_HEX:{hex(addr)}:{data.hex()}",
                    timeout=5
                )
                if "WRITE_OK" in res:
                    success += 1
                else:
                    failed += 1

        print(f"{UI.GREEN}[+] Written: {success} | Failed: {failed}{UI.END}")
        return success > 0
    
    def _get_region_for_address(self, addr):
        for r in self.memory_cache:
            if r['start'] <= addr < r['end']:
             return r
        return None
    
    def _get_region_for_file_offset(self, offset):
        for r in self.disk_regions:
            if r['file_start'] <= offset < r['file_end']:
                return r
        return None

    def enhanced_search_menu(self):
        """
        New search menu with smart multi-type capabilities.
        """
        smart_results = {}
        if not smart_results:
            self.freeze_active = False
            self.freeze_targets = []

        while True:
            self.clear_screen()
            UI.box("SMART SEARCH ENGINE", UI.GREEN)
            print("")

            result_count = sum(len(v) for v in smart_results.values()) if smart_results else 0

            UI.print_item("1", "Smart Search", f"({result_count} results)")
            UI.print_item("2", "Refine Results")
            UI.print_item("3", "View Results")
            UI.print_item("4", "Export Addresses")
            UI.print_item("5", "Clear Results")
            UI.print_item("6", "Write Values")
            UI.print_item("7", "Freeze Values")
            UI.print_item("8", "Stop Freeze")
            UI.print_item("0", "Back")

            c = input(f"\n{UI.CYAN}root@android:~/smart-search# {UI.END}")

            if c == '1':
                self.clear_screen()
                UI.header("SMART SEARCH MODE")

                print(f"{UI.GREEN}[1]{UI.END} Safe Search (FAST, RECOMMENDED)")
                print(f"{UI.RED}  - Scans safe RW memory only")
                print(f"{UI.GREEN}[2]{UI.END} Entire Memory (VERY SLOW)")
                print(f"{UI.RED}  - Reads ALL readable memory once")
                print(f"{UI.GREEN}[0]{UI.END} Cancel\n")

                mode_choice = input(f"{UI.CYAN}Select mode: {UI.END}").strip()

                if mode_choice == '0':
                    continue

                if mode_choice == '1':
                    mode = 'safe'
                    throttle = None
                elif mode_choice == '2':
                    mode = 'entire'
                else:
                    print(f"{UI.RED}Invalid option{UI.END}")
                    time.sleep(1)
                    continue

                val = input(f"{UI.YELLOW}Enter value (int / hex / string): {UI.END}")

                smart_results = self.smart_search(val, mode=mode)

                input("\nPress Enter to continue...")

            elif c == '2':
                if not smart_results:
                    print(f"{UI.RED}No results to refine!{UI.END}")
                    time.sleep(1)
                else:
                    try:
                        val = input(f"{UI.YELLOW}New value (int / hex / string): {UI.END}").strip()
                        smart_results = self.refine_smart_results(smart_results, val)
                        input("\nPress Enter to continue...")
                    except Exception as e:
                        print(f"{UI.RED}Error: {e}{UI.END}")
                        input("Enter...")

            elif c == '3':
                if smart_results:
                    self.display_smart_results(smart_results)
                    input("\nPress Enter to continue...")
                else:
                    print(f"{UI.RED}No results!{UI.END}")
                    time.sleep(1)

            elif c == '4':
                if smart_results:
                    filename = f"addresses_{int(time.time())}.txt"
                    with open(filename, 'w') as f:
                        for stype, addrs in smart_results.items():
                            f.write(f"\n=== {stype} ===\n")
                            for a in addrs:
                                if self.search_mode == 'entire':
                                    real = self.file_offset_to_address(a)
                                    f.write(f"{hex(real) if real else 'N/A'}\n")
                                else:
                                    f.write(f"{hex(a)}\n")
                    print(f"{UI.GREEN}Exported to {filename}{UI.END}")
                    time.sleep(1)
                else:
                    print(f"{UI.RED}No results!{UI.END}")
                    time.sleep(1)

            elif c == '5':
                smart_results = {}
                print(f"{UI.GREEN}Cleared.{UI.END}")
                time.sleep(0.5)

            elif c == '6':
                if smart_results:
                    val = input(f"{UI.YELLOW}Write value: {UI.END}")
                    self.write_smart_results(smart_results, val)
                    input("Enter...")
                else:
                    print("No results")
                    time.sleep(1)

            elif c == '7':
                if smart_results:
                    val = input(f"{UI.YELLOW}Freeze value: {UI.END}")
                    self.start_freeze(smart_results, val)
                    time.sleep(1)
                else:
                    print("No results")
                    time.sleep(1)

            elif c == '8':
                self.stop_freeze()
                time.sleep(1)

            elif c == '0':
                break


    # ==================== DUMP ENGINE ====================


    def draw_progress_bar(self, current, total, speed, width=30):
        percent = current / total
        filled = int(width * percent)
        bar = '█' * filled + '░' * (width - filled)
        sys.stdout.write(f"\r {UI.CYAN}[{bar}] {percent*100:.1f}% | {speed:.1f} KB/s{UI.END}")
        sys.stdout.flush()


    def perform_smart_dump(self, start_addr, size, file_or_path, base_offset=0):
        """
        Dump memory region using fast reader.

        - file_or_path: str (path) OR open file handle
        - base_offset: write offset inside file (used for multi-region dumps)
        """
        CHUNK_SIZE = 16384
        total_read = 0
        start_time = time.time()

        # Decide file mode
        close_after = False
        if isinstance(file_or_path, str):
            filename = file_or_path
            if not os.path.isabs(filename):
                filename = os.path.join(self.ROOT_DUMP_FOLDER, filename)

            folder = os.path.dirname(filename)
            if folder and not os.path.exists(folder):
                try:
                    os.makedirs(folder)
                except:
                    pass

            f = open(filename, 'ab')
            close_after = True
        else:
            f = file_or_path
            f.seek(base_offset)

        UI.header("INITIATING MEMORY DUMP")
        print(f" {UI.BOLD}Target:{UI.END} {hex(start_addr)}")
        print(f" {UI.BOLD}Size:{UI.END}   {size:,} bytes")
        if isinstance(file_or_path, str):
            print(f" {UI.BOLD}File:{UI.END}   {file_or_path}")
        else:
            print(f" {UI.BOLD}File:{UI.END}   <stream>")

        try:
            while total_read < size:
                bytes_to_read = min(CHUNK_SIZE, size - total_read)
                cmd = f"READ:{hex(start_addr + total_read)}:{bytes_to_read}"
                hex_data = self.send_command(cmd, timeout=10)

                if not hex_data or "ERROR" in hex_data:
                    data = b'\x00' * bytes_to_read
                else:
                    try:
                        data = bytes.fromhex(hex_data)
                    except:
                        data = b'\x00' * bytes_to_read

                f.write(data)
                total_read += bytes_to_read

                elapsed = time.time() - start_time
                speed = (total_read / 1024) / (elapsed if elapsed > 0 else 1)
                self.draw_progress_bar(total_read, size, speed)

            if close_after:
                f.close()

            print(f"\n\n{UI.GREEN}[✓] DUMP SUCCESSFUL{UI.END}")
            return True

        except KeyboardInterrupt:
            print(f"\n{UI.RED}[!] Dump interrupted{UI.END}")
            if close_after:
                f.close()
            return False



    def get_parsed_maps(self):
        raw = self.send_command("MAPS", timeout=60)
        if raw.startswith("ERROR"): return []
        lines = raw.replace('[', '').replace(']', '').split(',')
        if len(lines) < 2: lines = raw.split('\n')
        parsed = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 1 and "-" in parts[0]:
                try:
                    s, e = [int(x, 16) for x in parts[0].split('-')]
                    perms = parts[1] if len(parts) > 1 else ""
                    name = parts[-1] if len(parts) > 5 and not parts[-1].startswith('[') else "anon"
                    parsed.append({'start': s, 'end': e, 'size': e-s, 'perms': perms, 'name': name})
                except: pass
        self.memory_cache = parsed
        return parsed


    def scan_metadata_region(self, start, size, sig_bytes):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((self.host, self.port))
        except:
            return None
        CHUNK = 1024 * 1024; curr = 0; overlap = b""; limit = min(size, 32 * 1024 * 1024) 
        while curr < limit:
            read_len = min(CHUNK, size - curr)
            s.send(f"READ:{hex(start+curr)}:{read_len}".encode())
            hex_data = b""; expected = read_len * 2
            while len(hex_data) < expected:
                try:
                    p = s.recv(65536)
                    if not p or b"ERROR" in p: s.close(); return None
                    hex_data += p
                except: break
            try: chunk = bytes.fromhex(hex_data.decode())
            except: curr += read_len; continue
            buf = overlap + chunk; idx = buf.find(sig_bytes)
            if idx != -1: s.close(); return start + curr - len(overlap) + idx
            overlap = chunk[-len(sig_bytes):]; curr += read_len
        s.close(); return None


    def auto_pull_metadata(self):
        UI.header("PHASE 1: METADATA HUNT")
        target = os.path.join(self.METADATA_FOLDER, "global-metadata.dat")
        if not self.check_file_overwrite(target): return True
        maps = self.get_parsed_maps()
        cands = [m for m in maps if 'rw' in m['perms'] and 10*1024*1024 <= m['size'] <= 128*1024*1024]
        print(f"[*] Scanning {len(cands)} candidate regions...")
        sig = bytes.fromhex(METADATA_SIGNATURE_HEX); found = None
        for i, m in enumerate(cands):
            sys.stdout.write(f"\r {UI.YELLOW}>> Scanning {i+1}/{len(cands)}: {m['name']} ({m['size']//1024//1024}MB){UI.END}   ")
            found = self.scan_metadata_region(m['start'], m['size'], sig)
            if found: break
        if found:
            print(f"\n{UI.GREEN}[!!!] SIGNATURE FOUND AT {hex(found)} [!!!]{UI.END}")
            return self.perform_smart_dump(found, 40000000, target)
        return False


    def auto_pull_libil2cpp(self):
        UI.header("PHASE 2: BINARY PULL")
        target = os.path.join(self.IL2CPP_FOLDER, "libil2cpp.so")
        if not self.check_file_overwrite(target): return True
        maps = self.get_parsed_maps(); best = None; max_s = 0
        for m in maps:
            if "libil2cpp.so" in m['name'] and m['size'] > max_s: max_s = m['size']; best = m
        if best:
            print(f"{UI.GREEN}[+] Located libil2cpp.so at {hex(best['start'])}{UI.END}")
            return self.perform_smart_dump(best['start'], best['size'], target)
        return False


    def run_dumper(self):
        UI.header("PHASE 3: GENERATE DUMP.CS")
        exe = os.path.join(self.DUMPER_FOLDER, "Il2CppDumper.exe")
        if not os.path.exists(exe): return
        try: subprocess.Popen([exe], cwd=self.DUMPER_FOLDER, shell=True)
        except Exception as e: print(f"{UI.RED}Error: {e}{UI.END}")


    def automated_menu(self):
        while True:
            self.clear_screen(); UI.box("AUTOMATED DUMP SUITE", UI.YELLOW); print("")
            UI.print_item("1", "Pull Metadata"); UI.print_item("2", "Pull Binary"); UI.print_item("3", "Run Dumper"); UI.print_item("4", "FULL SEQUENCE"); UI.print_item("0", "Back")
            c = input(f"\n{UI.CYAN}root@android:~/auto# {UI.END}")
            if c == '1': self.auto_pull_metadata(); input("Enter...")
            elif c == '2': self.auto_pull_libil2cpp(); input("Enter...")
            elif c == '3': self.run_dumper(); input("Enter...")
            elif c == '4': 
                if self.auto_pull_metadata(): time.sleep(1); 
                if self.auto_pull_libil2cpp(): time.sleep(1); self.run_dumper()
                input("Enter...")
            elif c == '0': break


    # ==================== MAIN MENUS ====================


    def dump_menu(self):
        while True:
            self.clear_screen(); UI.box("MANUAL DUMP TOOLS", UI.RED); print("")
            UI.print_item("1", "Region Dump"); UI.print_item("2", "Manual Dump"); UI.print_item("3", "Dump Anon"); UI.print_item("0", "Back")
            c = input(f"\n{UI.CYAN}root@android:~/dump# {UI.END}")
            if c == '1': self.dump_region_selector()
            elif c == '2': self.dump_address_manual()
            elif c == '3': self.dump_all_anon()
            elif c == '0': break


    def dump_region_selector(self):
        maps = self.get_parsed_maps()
        if not maps: return
        print(f"\n{UI.YELLOW}[1] RW Only  [2] Libraries Only  [0] All{UI.END}"); opt = input("Filter: ")
        filtered = [m for m in maps if not ((opt=='1' and 'rw' not in m['perms']) or (opt=='2' and '.so' not in m['name']))]
        print("\n   ID   |    ADDRESS    |   SIZE   | NAME"); print("-" * 50)
        size_kb = f"{m['size']//1024} KB"
        for i, m in enumerate(filtered): print(f" [{str(i).rjust(3)}] | {hex(m['start']).ljust(12)} | {size_kb.ljust(8)} | {m['name']}")
        try:
            t = filtered[int(input(f"\n{UI.CYAN}ID to Dump: {UI.END}"))]
            name = "".join(c for c in t['name'].split('/')[-1] if c.isalnum() or c in '._') or "anon"
            self.perform_smart_dump(t['start'], t['size'], f"dump_{name}_{hex(t['start'])}.bin")
        except: pass
        input("Enter...")


    def dump_address_manual(self):
        try: self.perform_smart_dump(int(input("Start (hex): "), 16), int(input("Size: ")), f"dump_manual.bin")
        except: pass
        input("Enter...")


    def dump_all_anon(self):
        print("Bulk dumping..."); maps = self.get_parsed_maps(); sub = os.path.join(self.ROOT_DUMP_FOLDER, f"Bulk_{datetime.now().strftime('%H%M')}")
        if not os.path.exists(sub): os.makedirs(sub)
        for i, m in enumerate([m for m in maps if 'rw' in m['perms'] and (m['name'] == '' or 'anon' in m['name'])]):
            print(f"Processing {i}..."); self.perform_smart_dump(m['start'], m['size'], os.path.join(sub, f"anon_{hex(m['start'])}.bin"))
        input("Enter...")


    def view_memory_maps(self):
        maps = self.get_parsed_maps(); print(f"\n{UI.YELLOW}[Enter] for All, or type filter{UI.END}"); f_str = input("Filter: ").lower().strip()
        if f_str: maps = [m for m in maps if f_str in m['name'].lower()]
        print(f"\n{UI.GREEN}Total Regions: {len(maps)}{UI.END}"); print(f" {UI.BOLD}{'START'.ljust(14)} {'END'.ljust(14)} {'SIZE'.ljust(10)} {'PERMS'.ljust(6)} {'NAME'}{UI.END}"); print("-" * 60)
        for m in maps:
             sz_str = f"{m['size']//1024} KB" if m['size'] < 1024*1024 else f"{m['size']/1024/1024:.1f} MB"
             print(f" {hex(m['start']).ljust(14)} {hex(m['end']).ljust(14)} {sz_str.ljust(10)} {m['perms'].ljust(6)} {m['name']}")
        input("\nPress Enter to return...")


    def check_connection(self):
        print(f"\n{UI.YELLOW}[*] Pinging...{UI.END}")
        res = self.send_command("PING", 2)
        if "PONG" in res: print(f"{UI.GREEN}[✓] STILL CONNECTED{UI.END}")
        else: print(f"{UI.RED}[✗] DISCONNECTED{UI.END}")
        time.sleep(1)


    def main_menu(self):
        while True:
            self.clear_screen(); self.banner()
            print(f" {UI.YELLOW}SCANNER TOOLS{UI.END}                 {UI.YELLOW}DUMPER TOOLS{UI.END}")
            print(f" {UI.BLUE}-------------{UI.END}                 {UI.BLUE}------------{UI.END}")
            print(f" {UI.GREEN}[1]{UI.END} {UI.RED}★ Smart Search (NEW){UI.END}     {UI.GREEN}[3]{UI.END} Manual Dump")
            print(f" {UI.GREEN}[W]{UI.END} {UI.MAGENTA}★ Watchpoint (NEW){UI.END}   {UI.GREEN}[8]{UI.END} {UI.RED}AUTO-EXTRACT (DUMP.CS){UI.END}")
            print(""); print(f" {UI.YELLOW}UTILS{UI.END}"); print(f" {UI.BLUE}-----{UI.END}")
            print(f" {UI.GREEN}[4]{UI.END} Watch List"); 
            print(f" {UI.GREEN}[5]{UI.END} View Maps"); 
            print(f" {UI.GREEN}[D]{UI.END} {UI.CYAN}★ Diagnose Scanner{UI.END}")  # ADD THIS LINE
            print(f" {UI.GREEN}[6]{UI.END} Reconnect"); 
            print(f" {UI.GREEN}[7]{UI.END} Check Connection"); 
            print(f" {UI.GREEN}[R]{UI.END} Raw Command Console"); 
            print(f" {UI.GREEN}[0]{UI.END} Back to Mode Select")
            c = input(f"\n{UI.CYAN}root@android:~# {UI.END}").lower()
            if c == '1': self.enhanced_search_menu()
            elif c == '3': self.dump_menu()
            elif c == '4': print("Watch list empty."); time.sleep(1)
            elif c == '5': self.view_memory_maps()
            elif c == 'd': 
                self.diagnose_scan() 
                self.smart_region_filter()
            elif c == '6': self.connect_internal_server()
            elif c == '7': self.check_connection()
            elif c == '8': self.automated_menu()
            elif c == 'r': self.raw_command_console()
            elif c == 'w': self.watchpoint_menu()
            elif c == '0': self.startup()

    def cleanup_disk_snapshot(self):
        if self.active_disk_snapshot and os.path.exists(self.active_disk_snapshot):
            try:
                os.remove(self.active_disk_snapshot)
                print(f"{UI.YELLOW}[i] Removed disk snapshot{UI.END}")
            except:
                pass

    def run(self):
        try:
            self.startup()
        finally:
            self.cleanup_disk_snapshot()

    def raw_command_console(self):
        """
        Interactive console to send raw commands to the internal server.
        """
        self.clear_screen()
        UI.box("RAW COMMAND CONSOLE", UI.CYAN)
        print(f"{UI.YELLOW}Type raw commands exactly as sent to the server.{UI.END}")
        print(f"{UI.GREEN}Examples:{UI.END}")
        print("  MAPS")
        print("  READ:0x7a12340000:4")
        print("  PING")
        print("")
        print(f"{UI.RED}Type 'exit' to return to menu.{UI.END}\n")

        while True:
            cmd = input(f"{UI.CYAN}raw@android:~# {UI.END}").strip()
            if not cmd:
                continue
            if cmd.lower() in ("exit", "quit", "back"):
                break

            res = self.send_command(cmd, timeout=10)

            print(f"\n{UI.GREEN}--- RESPONSE ---{UI.END}")
            print(res if res else "(empty)")
            print(f"{UI.GREEN}----------------{UI.END}\n")

            if "SERVER_CRASHED" in res or "CONNECTION_REFUSED" in res:
                input("Press Enter to return...")
                break


if __name__ == "__main__":
    try:
        dk = DumpKing()
        dk.run()
    except KeyboardInterrupt:
        dk.cleanup_disk_snapshot()
        print(f"\n{UI.YELLOW}Session Terminated.{UI.END}")
        sys.exit(0)
