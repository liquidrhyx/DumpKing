#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║                        DUMPKING v3.1                          ║
║          Ultimate Memory Scanner & Editor for Android         ║
║             Automated Il2CppDumper Extraction Suite           ║
╚═══════════════════════════════════════════════════════════════╝
"""

import socket
import time
import os
import sys
import threading
import subprocess
from datetime import datetime

# ==================== CONFIGURATION ====================
METADATA_SIGNATURE_HEX = "af1bb1fa" # First 4 bytes of IL2CPP Metadata
IP = '127.0.0.1'
PORT = 12345
# =======================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class DumpKing:
    def __init__(self):
        self.host = IP
        self.port = PORT
        self.search_results = []
        self.saved_values = {}
        self.watch_thread = None
        self.watching = False
        self.watch_addresses = []
        
        # --- Folder Structure Setup ---
        self.ROOT_DUMP_FOLDER = "Dumped Memory Tools"
        self.METADATA_FOLDER = "Dumped MetaData"
        self.IL2CPP_FOLDER = "Pulled libil2cpp"
        self.DUMPER_FOLDER = "Il2CppDumper"

        # Ensure Root Folder exists for manual dumps
        if not os.path.exists(self.ROOT_DUMP_FOLDER):
            try: os.makedirs(self.ROOT_DUMP_FOLDER)
            except: pass

    def banner(self):
        print(f"{Colors.CYAN}")
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║                        DUMPKING v3.1                          ║")
        print("║          Ultimate Memory Scanner & Editor for Android         ║")
        print("║             Automated Il2CppDumper Extraction Suite           ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print(f"{Colors.END}")

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    # ==================== NETWORK CORE ====================

    def send_command(self, cmd, timeout=30):
        """Send command to memory spy server"""
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
                    if len(response) > 52428800: break # Safety Limit
                except socket.timeout:
                    break

            s.close()
            return response.decode('utf-8', errors='replace').strip('\x00')
        except Exception as e:
            return f"ERROR:{e}"

    def test_connection(self):
        """Test connection to memory spy"""
        print(f"{Colors.YELLOW}[*] Testing connection to memory spy...{Colors.END}")
        result = self.send_command("PING", timeout=5)
        if "PONG" in result:
            print(f"{Colors.GREEN}[✓] Connection successful!{Colors.END}")
            return True
        else:
            print(f"{Colors.RED}[✗] Connection failed: {result}{Colors.END}")
            print(f"{Colors.YELLOW}[!] Make sure the app is running and port forwarding is active:{Colors.END}")
            print("    adb forward tcp:12345 tcp:12345")
            return False

    # ==================== UTILITY FUNCTIONS ====================

    def int_to_hex_le(self, value):
        return value.to_bytes(4, byteorder='little').hex()

    def hex_le_to_int(self, hex_str):
        try:
            clean_hex = hex_str.strip()
            return int.from_bytes(bytes.fromhex(clean_hex), byteorder='little')
        except Exception:
            return None

    def parse_address_list(self, result):
        if result.startswith('ERROR'): return []
        clean_result = result.replace('[', '').replace(']', '')
        addresses = []
        for addr in clean_result.split(','):
            addr = addr.strip()
            try:
                if addr: addresses.append(int(addr))
            except Exception: pass
        return addresses

    def read_int(self, address):
        hex_addr = hex(address)
        result = self.send_command(f"READ:{hex_addr}:4", timeout=5)
        return self.hex_le_to_int(result)

    def write_int(self, address, value):
        hex_addr = hex(address)
        result = self.send_command(f"WRITE:{hex_addr}:{value}")
        return "WRITE_OK" in result

    def check_file_overwrite(self, filepath):
        if os.path.exists(filepath):
            print(f"\n{Colors.YELLOW}[!] File already exists: {filepath}{Colors.END}")
            choice = input(f"{Colors.CYAN}Overwrite? (y/n): {Colors.END}").lower()
            if choice == 'y':
                try:
                    os.remove(filepath)
                    time.sleep(0.5) # Wait for OS release
                    return True
                except Exception as e:
                    print(f"{Colors.RED}[✗] Could not delete file: {e}{Colors.END}")
                    return False
            else:
                print(f"{Colors.YELLOW}[-] Skipping dump.{Colors.END}")
                return False
        return True

    # ==================== CORE DUMPING ENGINE ====================

    def perform_smart_dump(self, start_addr, size, filename):
        CHUNK_SIZE = 8192
        total_read = 0
        
        folder = os.path.dirname(filename)
        if folder and not os.path.exists(folder):
            try: os.makedirs(folder)
            except: pass

        print(f"\n{Colors.YELLOW}[*] Initializing Smart Dump...{Colors.END}")
        print(f"Target: {hex(start_addr)} | Size: {size} bytes")
        print(f"Output: {filename}")
        
        start_time = time.time()
        
        try:
            with open(filename, 'wb') as f:
                while total_read < size:
                    bytes_to_read = min(CHUNK_SIZE, size - total_read)
                    current_addr = start_addr + total_read
                    
                    cmd = f"READ:{hex(current_addr)}:{bytes_to_read}"
                    hex_data = self.send_command(cmd, timeout=10)
                    
                    if "ERROR" in hex_data or not hex_data:
                        f.write(b'\x00' * bytes_to_read)
                    else:
                        try:
                            bin_data = bytes.fromhex(hex_data)
                            f.write(bin_data)
                        except ValueError:
                            f.write(b'\x00' * bytes_to_read)

                    total_read += bytes_to_read
                    
                    percent = (total_read / size) * 100
                    elapsed = time.time() - start_time
                    speed = (total_read / 1024) / (elapsed if elapsed > 0 else 1)
                    
                    sys.stdout.write(f"\r{Colors.CYAN}Progress: [{percent:.1f}%] {total_read}/{size} bytes | Speed: {speed:.1f} KB/s{Colors.END}")
                    sys.stdout.flush()

            print(f"\n\n{Colors.GREEN}[✓] Dump Complete! Saved to {filename}{Colors.END}")
            time.sleep(1) # CRITICAL: Wait for file unlock
            return True
            
        except KeyboardInterrupt:
            print(f"\n{Colors.RED}[!] Dump interrupted by user.{Colors.END}")
            return False
        except Exception as e:
            print(f"\n{Colors.RED}[!] Dump failed: {e}{Colors.END}")
            return False

    def get_parsed_maps(self):
        print(f"{Colors.YELLOW}[*] Fetching memory maps...{Colors.END}")
        raw = self.send_command("MAPS", timeout=60)
        if raw.startswith("ERROR"): return []

        lines = raw.replace('[', '').replace(']', '').split(',')
        if len(lines) < 2: lines = raw.split('\n')
             
        parsed_maps = []
        for line in lines:
            line = line.strip()
            parts = line.split()
            if len(parts) >= 1 and "-" in parts[0]:
                try:
                    range_parts = parts[0].split('-')
                    start = int(range_parts[0], 16)
                    end = int(range_parts[1], 16)
                    perms = parts[1] if len(parts) > 1 else ""
                    name = parts[-1] if len(parts) > 5 and not parts[-1].startswith('[') else "anon"
                    parsed_maps.append({'start': start, 'end': end, 'size': end-start, 'perms': perms, 'name': name})
                except: continue
        return parsed_maps

    # ==================== AUTOMATED DUMP.CS SUITE ====================

    def scan_metadata_region(self, start, size, sig_bytes):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((self.host, self.port))
        except: return None

        CHUNK_SIZE = 1024 * 1024 
        current_offset = 0
        overlap_size = len(sig_bytes)
        overlap = b"" 
        scan_limit = min(size, 32 * 1024 * 1024)

        while current_offset < scan_limit:
            read_len = min(CHUNK_SIZE, size - current_offset)
            addr = start + current_offset
            
            cmd = f"READ:{hex(addr)}:{read_len}"
            try: s.send(cmd.encode())
            except: 
                s.close()
                return None
            
            hex_data = b""
            expected_hex_len = read_len * 2
            retries = 0
            while len(hex_data) < expected_hex_len:
                try:
                    packet = s.recv(65536)
                    if not packet: break
                    if b"ERROR" in packet: 
                        s.close()
                        return None 
                    hex_data += packet
                except socket.timeout:
                    retries += 1
                    if retries > 3: break
                    continue
            
            if not hex_data: break

            try:
                chunk_bytes = bytes.fromhex(hex_data.decode('utf-8'))
            except:
                current_offset += read_len
                continue

            search_buffer = overlap + chunk_bytes
            found_idx = search_buffer.find(sig_bytes)
            
            if found_idx != -1:
                match_addr = addr - len(overlap) + found_idx
                s.close()
                return match_addr

            overlap = chunk_bytes[-overlap_size:]
            current_offset += read_len
            
        s.close()
        return None

    def auto_pull_metadata(self):
        print(f"\n{Colors.BOLD}=== PHASE 1: Pull Decrypted Metadata ==={Colors.END}")
        if not os.path.exists(self.METADATA_FOLDER):
            try: os.makedirs(self.METADATA_FOLDER)
            except: pass
            
        target_file = os.path.join(self.METADATA_FOLDER, "global-metadata.dat")
        if not self.check_file_overwrite(target_file):
            return True

        sig_bytes = bytes.fromhex(METADATA_SIGNATURE_HEX)
        maps = self.get_parsed_maps()
        
        candidates = []
        for m in maps:
            if 'rw' in m['perms'] and 10 * 1024 * 1024 <= m['size'] <= 128 * 1024 * 1024:
                candidates.append(m)
                
        print(f"[*] Found {len(candidates)} candidate regions for Metadata.")
        print(f"[*] Scanning memory for signature: {METADATA_SIGNATURE_HEX}...")
        
        found_addr = None
        for i, m in enumerate(candidates):
            mb = m['size'] / 1024 / 1024
            sys.stdout.write(f"\rScanning [{i+1}/{len(candidates)}] {m['name']} ({mb:.1f} MB)... ")
            sys.stdout.flush()
            
            found_addr = self.scan_metadata_region(m['start'], m['size'], sig_bytes)
            if found_addr:
                print(f"\n{Colors.GREEN}[!!!] FOUND METADATA HEADER at {hex(found_addr)} [!!!]{Colors.END}")
                break
        
        if found_addr:
            print(f"[*] Dumping 40MB from {hex(found_addr)}...")
            return self.perform_smart_dump(found_addr, 40000000, target_file)
        else:
            print(f"\n{Colors.RED}[-] Metadata signature not found.{Colors.END}")
            return False

    def auto_pull_libil2cpp(self):
        print(f"\n{Colors.BOLD}=== PHASE 2: Pull libil2cpp.so ==={Colors.END}")
        if not os.path.exists(self.IL2CPP_FOLDER):
            try: os.makedirs(self.IL2CPP_FOLDER)
            except: pass
            
        target_file = os.path.join(self.IL2CPP_FOLDER, "libil2cpp.so")
        if not self.check_file_overwrite(target_file):
            return True

        maps = self.get_parsed_maps()
        best_region = None
        max_size = 0
        
        for m in maps:
            if "libil2cpp.so" in m['name']:
                if m['size'] > max_size:
                    max_size = m['size']
                    best_region = m
        
        if best_region:
            print(f"{Colors.GREEN}[+] Found libil2cpp.so at {hex(best_region['start'])} ({max_size/1024/1024:.2f} MB){Colors.END}")
            return self.perform_smart_dump(best_region['start'], best_region['size'], target_file)
        else:
            print(f"{Colors.RED}[-] Could not find 'libil2cpp.so' by name in memory maps.{Colors.END}")
            return False

    def run_il2cpp_dumper(self):
        print(f"\n{Colors.BOLD}=== PHASE 3: Generate Dump.cs ==={Colors.END}")
        
        # Use Absolute Paths to ensure robust execution
        current_dir = os.getcwd()
        dumper_dir = os.path.join(current_dir, self.DUMPER_FOLDER)
        exe_path = os.path.join(dumper_dir, "Il2CppDumper.exe")
        
        if not os.path.exists(exe_path):
            print(f"{Colors.RED}[✗] Il2CppDumper.exe not found!{Colors.END}")
            print(f"Expected at: {exe_path}")
            return

        print(f"{Colors.GREEN}[+] Launching Il2CppDumper...{Colors.END}")
        print("1. Select 'libil2cpp.so' from 'Pulled libil2cpp' folder.")
        print("2. Select 'global-metadata.dat' from 'Dumped MetaData' folder.")
        
        try:
            # Popen with cwd set to the Dumper folder
            subprocess.Popen([exe_path], cwd=dumper_dir, shell=True)
        except Exception as e:
            print(f"{Colors.RED}[!] Failed to launch exe: {e}{Colors.END}")

    def create_dump_cs_menu(self):
        while True:
            self.clear_screen()
            print(f"{Colors.CYAN}{'='*65}{Colors.END}")
            print(f"{Colors.BOLD}                  CREATE DUMP.CS (AUTOMATION){Colors.END}")
            print(f"{Colors.CYAN}{'='*65}{Colors.END}\n")
            print(f"  {Colors.GREEN}[1]{Colors.END} Pull Decrypted Meta Data file")
            print(f"  {Colors.GREEN}[2]{Colors.END} Pull libil2cpp.so File")
            print(f"  {Colors.GREEN}[3]{Colors.END} Generate Dump.cs (Final)")
            print(f"  {Colors.GREEN}[4]{Colors.END} Run All One by One")
            print(f"  {Colors.YELLOW}[0]{Colors.END} Back to Main Menu\n")
            
            choice = input(f"{Colors.CYAN}Enter choice: {Colors.END}")
            
            if choice == '1':
                self.auto_pull_metadata()
                input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.END}")
            elif choice == '2':
                self.auto_pull_libil2cpp()
                input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.END}")
            elif choice == '3':
                self.run_il2cpp_dumper()
                input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.END}")
            elif choice == '4':
                print(f"\n{Colors.YELLOW}[*] Starting Full Automation Sequence...{Colors.END}")
                if self.auto_pull_metadata():
                    print("\n[+] Metadata Step Complete.")
                    time.sleep(2)
                    if self.auto_pull_libil2cpp():
                        print("\n[+] Binary Step Complete.")
                        time.sleep(2)
                        self.run_il2cpp_dumper()
                input(f"\n{Colors.CYAN}Sequence Complete. Press Enter...{Colors.END}")
            elif choice == '0':
                break

    # ==================== SEARCH MENU ====================

    def search_menu(self):
        while True:
            self.clear_screen()
            print(f"{Colors.BOLD}                        SEARCH MENU{Colors.END}")
            print(f"  {Colors.GREEN}[1]{Colors.END} Integer Search (DWORD)")
            print(f"  {Colors.GREEN}[2]{Colors.END} Hex Pattern Search")
            print(f"  {Colors.GREEN}[3]{Colors.END} String Search")
            print(f"  {Colors.GREEN}[4]{Colors.END} Refine Search (Filter Results)")
            print(f"  {Colors.GREEN}[5]{Colors.END} View Current Results ({len(self.search_results)} found)")
            print(f"  {Colors.GREEN}[6]{Colors.END} Clear Results")
            print(f"  {Colors.GREEN}[7]{Colors.END} Memory Region Filter")
            print(f"  {Colors.YELLOW}[0]{Colors.END} Back to Main Menu\n")
            choice = input(f"{Colors.CYAN}Enter choice: {Colors.END}")
            if choice == '1': self.integer_search()
            elif choice == '2': self.hex_search()
            elif choice == '3': self.string_search()
            elif choice == '4': self.refine_search()
            elif choice == '5': self.view_results()
            elif choice == '6':
                self.search_results = []
                print(f"{Colors.GREEN}[✓] Results cleared{Colors.END}")
                time.sleep(1)
            elif choice == '7': self.memory_region_menu()
            elif choice == '0': break

    def integer_search(self):
        self.clear_screen()
        print(f"{Colors.BOLD}=== INTEGER SEARCH ==={Colors.END}\n")
        try:
            value = int(input(f"{Colors.CYAN}Enter value to search: {Colors.END}"))
        except: return
        print(f"\n{Colors.YELLOW}[*] Searching...{Colors.END}")
        result = self.send_command(f"SCAN:{value}", timeout=120)
        if result.startswith('ERROR'): print(f"{Colors.RED}[✗] Failed{Colors.END}")
        else:
            self.search_results = self.parse_address_list(result)
            print(f"{Colors.GREEN}[✓] Found {len(self.search_results)} addresses{Colors.END}")
        input(f"\n{Colors.CYAN}Press Enter...{Colors.END}")

    def hex_search(self):
        self.clear_screen()
        print(f"{Colors.BOLD}=== HEX PATTERN SEARCH ==={Colors.END}\n")
        hex_pattern = input(f"{Colors.CYAN}Enter hex pattern: {Colors.END}").replace(" ", "").replace("0x", "")
        print(f"\n{Colors.YELLOW}[*] Searching...{Colors.END}")
        result = self.send_command(f"SEARCHHEX:{hex_pattern}", timeout=180)
        if "ERROR" in result: print(f"{Colors.RED}[✗] Failed{Colors.END}")
        else:
            self.search_results = self.parse_address_list(result)
            print(f"{Colors.GREEN}[✓] Found {len(self.search_results)} addresses{Colors.END}")
        input(f"\n{Colors.CYAN}Press Enter...{Colors.END}")

    def string_search(self):
        print(f"\n{Colors.YELLOW}[!] Use Hex Search for strings in this version.{Colors.END}")
        time.sleep(2)

    def refine_search(self):
        if not self.search_results: return
        self.clear_screen()
        print(f"{Colors.BOLD}=== REFINE SEARCH ==={Colors.END}\n")
        try:
            new_value = int(input(f"{Colors.CYAN}Enter new value: {Colors.END}"))
        except: return
        refined = []
        for addr in self.search_results:
            if self.read_int(addr) == new_value: refined.append(addr)
        print(f"\n{Colors.GREEN}[✓] Refined to {len(refined)} addresses{Colors.END}")
        self.search_results = refined
        input(f"\n{Colors.CYAN}Press Enter...{Colors.END}")

    def view_results(self):
        if not self.search_results: return
        self.clear_screen()
        print(f"{Colors.BOLD}=== RESULTS ==={Colors.END}\n")
        count = min(50, len(self.search_results))
        for i in range(count):
            addr = self.search_results[i]
            val = self.read_int(addr)
            print(f" {i+1}. {hex(addr)} = {val}")
        input(f"\n{Colors.CYAN}Press Enter...{Colors.END}")

    def memory_region_menu(self):
        print(f"{Colors.YELLOW}[!] Feature linked to Map Viewer.{Colors.END}")
        time.sleep(1)

    # ==================== MANUAL DUMP MENU ====================

    def dump_menu(self):
        while True:
            self.clear_screen()
            print(f"{Colors.BOLD}=== DUMP MEMORY TOOLS (MANUAL) ==={Colors.END}\n")
            print(f" [1] Dump Memory Region (Select from Map)")
            print(f" [2] Dump Specific Address Range")
            print(f" [3] Dump All Anonymous Regions")
            print(f" [4] Dump Search Results")
            print(f" [5] Export Search Results to File")
            print(f" [0] Back\n")
            choice = input("Choice: ")
            if choice == '1': self.dump_region_selector()
            elif choice == '2': self.dump_address_manual()
            elif choice == '3': self.dump_all_anon()
            elif choice == '4': self.dump_search_results()
            elif choice == '5': self.export_results()
            elif choice == '0': break

    def dump_region_selector(self):
        self.clear_screen()
        maps = self.get_parsed_maps()
        if not maps: return
        print(" [0] Show All | [1] RW Only | [2] Libraries Only")
        opt = input("Option: ")
        filtered = []
        for i, m in enumerate(maps):
            if opt == '1' and 'rw' not in m['perms']: continue
            if opt == '2' and '.so' not in m['name']: continue
            filtered.append(m)
        for i, m in enumerate(filtered):
            sz = m['size'] / 1024
            print(f" [{i}] {hex(m['start'])} ({sz:.0f} KB) {m['name']}")
        try:
            sel = int(input("ID: "))
            target = filtered[sel]
            name = target['name'].split('/')[-1] or "anon"
            name = "".join(c for c in name if c.isalnum() or c in '._')
            fname = os.path.join(self.ROOT_DUMP_FOLDER, f"dump_{name}_{hex(target['start'])}.bin")
            self.perform_smart_dump(target['start'], target['size'], fname)
        except: pass
        input("Press Enter...")

    def dump_address_manual(self):
        self.clear_screen()
        try:
            start = int(input("Start Address (hex): "), 16)
            size = int(input("Size (bytes): "))
            fname = os.path.join(self.ROOT_DUMP_FOLDER, f"dump_{hex(start)}_{datetime.now().strftime('%H%M%S')}.bin")
            self.perform_smart_dump(start, size, fname)
        except: pass
        input("Press Enter...")

    def dump_all_anon(self):
        print("Dumping all RW anonymous regions...")
        maps = self.get_parsed_maps()
        sub = os.path.join(self.ROOT_DUMP_FOLDER, f"Bulk_{datetime.now().strftime('%H%M')}")
        for m in maps:
            if 'rw' in m['perms'] and (m['name'] == '' or 'anon' in m['name']):
                fname = os.path.join(sub, f"anon_{hex(m['start'])}.bin")
                self.perform_smart_dump(m['start'], m['size'], fname)
        input("Press Enter...")

    def dump_search_results(self):
        if len(self.search_results) == 0:
            print(f"{Colors.RED}[✗] No search results to dump{Colors.END}")
            time.sleep(2)
            return
        self.clear_screen()
        print(f"{Colors.BOLD}=== DUMP SEARCH RESULTS ==={Colors.END}\n")
        filename = os.path.join(self.ROOT_DUMP_FOLDER, f"dump_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        print(f"{Colors.YELLOW}[*] Dumping {len(self.search_results)} addresses to {filename}...{Colors.END}")
        try:
            with open(filename, 'w') as f:
                f.write("DumpKing Memory Dump\n")
                for i, addr in enumerate(self.search_results):
                    value = self.read_int(addr)
                    f.write(f"{hex(addr)}\t{value}\n")
            print(f"\n{Colors.GREEN}[✓] Dump saved to {filename}{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}[✗] Dump failed: {e}{Colors.END}")
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.END}")

    def export_results(self):
        if len(self.search_results) == 0:
            print(f"{Colors.RED}[✗] No search results to export{Colors.END}")
            time.sleep(2)
            return
        filename = os.path.join(self.ROOT_DUMP_FOLDER, f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        print(f"\n{Colors.YELLOW}[*] Exporting to {filename}...{Colors.END}")
        try:
            with open(filename, 'w') as f:
                f.write("Address,Value\n")
                for addr in self.search_results:
                    value = self.read_int(addr)
                    f.write(f"{hex(addr)},{value}\n")
            print(f"{Colors.GREEN}[✓] Exported {len(self.search_results)} results to {filename}{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}[✗] Export failed: {e}{Colors.END}")
        time.sleep(2)

    # ==================== WRITE/EDIT MENU ====================

    def write_menu(self):
        while True:
            self.clear_screen()
            print(f"{Colors.BOLD}                        WRITE/EDIT MENU{Colors.END}")
            print(f"  {Colors.GREEN}[1]{Colors.END} Write Value (Single)")
            print(f"  {Colors.GREEN}[2]{Colors.END} Write to Search Results (Batch)")
            print(f"  {Colors.GREEN}[3]{Colors.END} Freeze Value")
            print(f"  {Colors.GREEN}[4]{Colors.END} Unfreeze All")
            print(f"  {Colors.GREEN}[5]{Colors.END} Save Address to List")
            print(f"  {Colors.GREEN}[6]{Colors.END} View Saved Addresses")
            print(f"  {Colors.GREEN}[7]{Colors.END} Edit Saved Address")
            print(f"  {Colors.YELLOW}[0]{Colors.END} Back to Main Menu\n")
            choice = input(f"{Colors.CYAN}Enter choice: {Colors.END}")
            if choice == '1': self.write_single()
            elif choice == '2': self.write_batch()
            elif choice == '3': self.freeze_value()
            elif choice == '4': self.unfreeze_all()
            elif choice == '5': self.save_address()
            elif choice == '6': self.view_saved()
            elif choice == '7': self.edit_saved()
            elif choice == '0': break

    def write_single(self):
        self.clear_screen()
        print(f"{Colors.BOLD}=== WRITE VALUE ==={Colors.END}\n")
        try:
            addr_str = input(f"{Colors.CYAN}Enter address (hex): {Colors.END}")
            address = int(addr_str, 16)
            current = self.read_int(address)
            print(f"\n  Current value at {hex(address)}: {Colors.GREEN}{current}{Colors.END}")
            new_value = int(input(f"\n{Colors.CYAN}Enter new value: {Colors.END}"))
            if self.write_int(address, new_value):
                print(f"{Colors.GREEN}[✓] Write successful!{Colors.END}")
            else:
                print(f"{Colors.RED}[✗] Write failed{Colors.END}")
        except: pass
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.END}")

    def write_batch(self):
        if len(self.search_results) == 0:
            print(f"{Colors.RED}[✗] No search results to write to{Colors.END}")
            time.sleep(2)
            return
        self.clear_screen()
        print(f"{Colors.BOLD}=== BATCH WRITE ==={Colors.END}\n")
        try:
            new_value = int(input(f"{Colors.CYAN}Enter value to write to ALL addresses: {Colors.END}"))
            print(f"\n{Colors.YELLOW}[*] Writing...{Colors.END}")
            success = 0
            for addr in self.search_results:
                if self.write_int(addr, new_value): success += 1
            print(f"\n{Colors.GREEN}[✓] Wrote to {success} addresses{Colors.END}")
        except: pass
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.END}")

    def freeze_value(self):
        self.clear_screen()
        print(f"{Colors.BOLD}=== FREEZE VALUE ==={Colors.END}\n")
        try:
            addr_str = input(f"{Colors.CYAN}Enter address (hex): {Colors.END}")
            address = int(addr_str, 16)
            current = self.read_int(address)
            print(f"\n  Current value: {Colors.GREEN}{current}{Colors.END}")
            freeze_val = input(f"\n{Colors.CYAN}Enter value (or Enter for current): {Colors.END}")
            value = int(freeze_val) if freeze_val else current
            result = self.send_command(f"FREEZE:{hex(address)}:{value}")
            if "FREEZE_OK" in result: print(f"{Colors.GREEN}[✓] Frozen!{Colors.END}")
            else: print(f"{Colors.RED}[✗] Failed{Colors.END}")
        except: pass
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.END}")

    def unfreeze_all(self):
        self.send_command("UNFREEZE")
        print(f"{Colors.GREEN}[✓] All unfrozen{Colors.END}")
        time.sleep(1)

    def save_address(self):
        if len(self.search_results) == 0: return
        self.clear_screen()
        print(f"{Colors.BOLD}=== SAVE ==={Colors.END}\n")
        for i in range(min(10, len(self.search_results))):
            print(f" {i+1}. {hex(self.search_results[i])}")
        try:
            idx = int(input(f"\n{Colors.CYAN}Number to save: {Colors.END}")) - 1
            name = input(f"{Colors.CYAN}Name: {Colors.END}")
            self.saved_values[name] = self.search_results[idx]
            print(f"{Colors.GREEN}[✓] Saved{Colors.END}")
        except: pass
        time.sleep(1)

    def view_saved(self):
        self.clear_screen()
        print(f"{Colors.BOLD}=== SAVED ==={Colors.END}\n")
        for name, addr in self.saved_values.items():
            print(f" {name}: {hex(addr)}")
        input("Press Enter...")

    def edit_saved(self):
        self.view_saved()

    # ==================== WATCH MENU ====================

    def watch_menu(self):
        while True:
            self.clear_screen()
            print(f"{Colors.BOLD}                        WATCH MENU{Colors.END}")
            status = f"{Colors.GREEN}RUNNING{Colors.END}" if self.watching else f"{Colors.RED}STOPPED{Colors.END}"
            print(f"  Status: {status}")
            print(f"  Watching: {len(self.watch_addresses)} addresses")
            print(f"  {Colors.GREEN}[1]{Colors.END} Add Watch")
            print(f"  {Colors.GREEN}[2]{Colors.END} Remove Watch")
            print(f"  {Colors.GREEN}[3]{Colors.END} Start")
            print(f"  {Colors.GREEN}[4]{Colors.END} Stop")
            print(f"  {Colors.GREEN}[5]{Colors.END} View List")
            print(f"  {Colors.GREEN}[6]{Colors.END} Clear")
            print(f"  {Colors.YELLOW}[0]{Colors.END} Back")
            choice = input(f"{Colors.CYAN}Enter choice: {Colors.END}")
            if choice == '1': self.add_watch()
            elif choice == '2': self.remove_watch()
            elif choice == '3': self.start_watch()
            elif choice == '4': self.stop_watch()
            elif choice == '5': self.view_watch()
            elif choice == '6':
                self.watch_addresses = []
                print(f"{Colors.GREEN}[✓] Cleared{Colors.END}")
                time.sleep(1)
            elif choice == '0':
                if self.watching: self.stop_watch()
                break

    def add_watch(self):
        try:
            addr_str = input(f"\n{Colors.CYAN}Enter address (hex): {Colors.END}")
            address = int(addr_str, 16)
            name = input(f"{Colors.CYAN}Enter name: {Colors.END}")
            self.watch_addresses.append({'addr': address, 'name': name})
            print(f"{Colors.GREEN}[✓] Added{Colors.END}")
        except: pass
        time.sleep(1)

    def remove_watch(self):
        if len(self.watch_addresses) == 0: return
        self.clear_screen()
        for i, item in enumerate(self.watch_addresses, 1):
            print(f" {i}. {item['name']}")
        try:
            idx = int(input("Remove #: ")) - 1
            if 0 <= idx < len(self.watch_addresses):
                self.watch_addresses.pop(idx)
                print("Removed")
        except: pass
        time.sleep(1)

    def start_watch(self):
        if len(self.watch_addresses) == 0: return
        if self.watching: return
        self.watching = True
        self.watch_thread = threading.Thread(target=self.watch_loop, daemon=True)
        self.watch_thread.start()
        print(f"{Colors.GREEN}[✓] Started{Colors.END}")
        time.sleep(1)

    def stop_watch(self):
        self.watching = False
        print(f"\n{Colors.YELLOW}[*] Stopped{Colors.END}")
        time.sleep(1)

    def view_watch(self):
        self.clear_screen()
        for item in self.watch_addresses:
            value = self.read_int(item['addr'])
            print(f" {item['name']}: {hex(item['addr'])} = {value}")
        input("Press Enter...")

    def watch_loop(self):
        prev = {}
        while self.watching:
            try:
                self.clear_screen()
                print(f"{Colors.BOLD}=== LIVE WATCH ==={Colors.END}")
                print("Ctrl+C to stop")
                for item in self.watch_addresses:
                    val = self.read_int(item['addr'])
                    change = "[CHANGED]" if item['addr'] in prev and val != prev[item['addr']] else ""
                    prev[item['addr']] = val
                    print(f" {item['name']}: {val} {change}")
                time.sleep(0.5)
            except: break

    # ==================== MAIN ====================

    def main_menu(self):
        while True:
            self.clear_screen()
            self.banner()
            print(f"{Colors.CYAN}{'='*65}{Colors.END}")
            print(f"{Colors.BOLD}                        MAIN MENU{Colors.END}")
            print(f"{Colors.CYAN}{'='*65}{Colors.END}\n")
            print(f"  {Colors.GREEN}[1]{Colors.END} Search/Scan Memory")
            print(f"  {Colors.GREEN}[2]{Colors.END} Write/Edit Values")
            print(f"  {Colors.GREEN}[3]{Colors.END} Dump Memory Tools")
            print(f"  {Colors.GREEN}[4]{Colors.END} Watch Values (Live Monitor)")
            print(f"  {Colors.GREEN}[5]{Colors.END} View Memory Maps")
            print(f"  {Colors.GREEN}[6]{Colors.END} Test Connection")
            print(f"  {Colors.YELLOW}[8]{Colors.END} Create Dump.cs (Automated)")
            print(f"  {Colors.YELLOW}[0]{Colors.END} Exit\n")
            print(f"{Colors.CYAN}{'='*65}{Colors.END}")
            choice = input(f"{Colors.CYAN}Enter choice: {Colors.END}")
            if choice == '1': self.search_menu()
            elif choice == '2': self.write_menu()
            elif choice == '3': self.dump_menu()
            elif choice == '4': self.watch_menu()
            elif choice == '5': self.viewmemorymaps()
            elif choice == '6':
                self.test_connection()
                time.sleep(1)
            elif choice == '8': self.create_dump_cs_menu()
            elif choice == '0':
                print(f"\n{Colors.CYAN}Thanks for using DumpKing!{Colors.END}\n")
                sys.exit(0)

    def run(self):
        self.clear_screen()
        self.banner()
        if not self.test_connection():
            print(f"\n{Colors.RED}[✗] Cannot connect to memory spy{Colors.END}")
            print(f"{Colors.YELLOW}[!] Make sure:{Colors.END}")
            print("    1. The app is running")
            print("    2. Run: adb forward tcp:12345 tcp:12345")
            input(f"\n{Colors.CYAN}Press Enter to exit...{Colors.END}")
            sys.exit(1)
        time.sleep(1)
        self.main_menu()

if __name__ == "__main__":
    try:
        dk = DumpKing()
        dk.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}[!] Interrupted by user{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}[✗] Fatal error: {e}{Colors.END}")
        sys.exit(1)