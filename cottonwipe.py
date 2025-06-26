#!/usr/bin/python3
#! coding: utf-8
"""Coded By Br3noAraujo"""

import os
import sys
import subprocess
import time
import argparse
import signal
import shutil
import random
import datetime
import logging
import locale
import json
from typing import List, Dict, Optional

banner = """

  ,--,  .---.  _______  _______  .---.  .-. .-..-.  .-.,-.,---.  ,---.   
.' .'\033[1;94m)\033[0m / .-. \033[1;94m)\033[0m|__   __||__   __|/ .-. \033[1;94m)\033[0m |  \| || |/\| ||\033[1;94m(\033[0m|| .-.\ | .-'   
|  |\033[1;94m(_)\033[0m| | |\033[1;94m(_)\033[0m \033[1;94m)\033[0m| |     \033[1;94m)\033[0m| |   | | |\033[1;94m(_)\033[0m|   | || /  \ |\033[1;94m(_)\033[0m| |-' )| `-.   
\  \   | | | | \033[1;94m(_)\033[0m |    \033[1;94m(_)\033[0m |   | | | | | |\  ||  /\  || || |--' | .-'   
 \  `-.\ `-' /   | |      | |   \ `-' / | | |\033[1;94m)\033[0m||(/  \ || || |    |  `--. 
  \____\)---'    `-'      `-'    )---'  /(  (_)(_)   \|`-'/(     /( __.' 
       \033[1;94m(_)                      \033[1;94m(_)    \033[1;94m(__)              \033[1;94m(__)   \033[1;94m(__)     
        \033[1;96mAn ZeroFill Python tool — gentle as\033[3m\033[97m Cotton\033[0m\033[1;96m, final as \033[1;31mDEATH\033[1;96m.\033[0m

  \033[1;94mAuthor: Br3noAraujo   |   GitHub: github.com/Br3noAraujo   |   License: MIT\033[0m
  \033[1;31mDANGER: This tool will IRREVERSIBLY destroy all data on the selected device!\033[0m
"""

about = """
CottonWipe is a robust, open source Python tool for secure data destruction (ZeroFill/RandomFill) on block devices (HDD, SSD, USB, SD, partitions).

Features:
- Lists all disks and partitions, with clear warnings for mounted and encrypted devices.
- Double confirmation (unless --dangerous).
- Progress bar, logging, verification, and performance throttle.
- Compatible with Linux/UNIX terminals. 100% Python 3, open source.

USE WITH EXTREME CAUTION: This tool is designed for irreversible data destruction!
"""

# ========== Internationalization (gettext) ==========
try:
    import gettext
    locale.setlocale(locale.LC_ALL, '')
    lang = os.environ.get('LANG', 'en_US')
    t = gettext.translation('cottonwipe', localedir='locales', languages=[lang], fallback=True)
    _ = t.gettext
except Exception:
    _ = lambda s: s
import builtins
builtins._ = _

# ========== Progress bar ==========
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    tqdm = None
class DummyProgress:
    def update(self, n): pass
    def close(self): pass

# ========== Configurable logging with color ==========
class ColorFormatter(logging.Formatter):
    COLORS = {
        'CRITICAL': '\033[1;31m',   # Dark Red (bold)
        'ERROR':    '\033[1;91m',   # Light Red (bold)
        'WARNING':  '\033[1;93m',   # Yellow (bold)
        'SUCCESS':  '\033[1;92m',   # Green (bold)
        'INFO':     '\033[1;96m',   # Light Blue (bold)
        'DEBUG':    '\033[1;94m',   # Blue (bold)
        'RESET':    '\033[0m',
    }
    EMOJIS = {
        'CRITICAL': ' 🛑',
        'ERROR':    ' ❌',
        'WARNING':  ' ⚠️',
        'SUCCESS':  ' ✅',
        'INFO':     ' 🔍',
        'DEBUG':    ' 🔵',
    }
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        emoji = self.EMOJIS.get(record.levelname, '')
        bold = '\033[1m'
        msg = super().format(record)
        # Always bold + color
        msg = f"{bold}{color}{msg}{reset}{emoji}"
        return msg

# Add custom SUCCESS level
SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, 'SUCCESS')
def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)
logging.Logger.success = success

def setup_logging(quiet: bool, log_file: Optional[str] = None, level=logging.INFO):
    handlers = []
    if not quiet:
        color_formatter = ColorFormatter('%(asctime)s %(levelname)s: %(message)s')
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(color_formatter)
        handlers.append(stream_handler)
    else:
        handlers.append(logging.StreamHandler(sys.stderr))
    if log_file:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(log_file, maxBytes=2*1024*1024, backupCount=3)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        handlers.append(file_handler)
    logging.basicConfig(
        level=level,
        handlers=handlers,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

# ========== Signal handling ==========
def setup_signal_handlers():
    def handle_signal(signum, frame):
        print()  # Garante quebra de linha antes do log
        logging.error(_("\n[ABORTED] Received signal %s. Exiting cleanly.") % signum)
        sys.exit(130)
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

# ========== Dependency checks ==========
def require_root() -> None:
    if os.geteuid() != 0:
        logging.critical(_("This script must be run as root."))
        sys.exit(1)
def check_dependencies() -> None:
    for dep in ("lsblk", "blockdev"):
        if shutil.which(dep) is None:
            logging.critical(_("'%s' is not available on this system. Please install it.") % dep)
            sys.exit(1)

# ========== Device listing ==========
def list_block_devices(include_partitions=True) -> List[Dict[str, str]]:
    try:
        result = subprocess.run([
            "lsblk", "-o", "NAME,SIZE,TYPE,MODEL,MOUNTPOINT,FSTYPE,RM", "-J"
        ], capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        devices = []
        for block in data.get("blockdevices", []):
            if block["type"] == "disk":
                devices.append({
                    "name": block["name"],
                    "size": block["size"],
                    "type": block["type"],
                    "model": block.get("model", "-"),
                    "mountpoint": block.get("mountpoint", "") or "-",
                    "mounted": bool(block.get("mountpoint")),
                    "fstype": block.get("fstype", "-"),
                    "is_partition": False,
                    "removable": str(block.get("rm", "0")) == "1"
                })
                if include_partitions:
                    for part in block.get("children", []):
                        devices.append({
                            "name": part["name"],
                            "size": part["size"],
                            "type": part["type"],
                            "model": block.get("model", "-"),
                            "mountpoint": part.get("mountpoint", "") or "-",
                            "mounted": bool(part.get("mountpoint")),
                            "fstype": part.get("fstype", "-"),
                            "is_partition": True,
                            "removable": str(part.get("rm", "0")) == "1"
                        })
        return devices
    except Exception as e:
        logging.critical(_("Failed to list devices: %s") % e)
        sys.exit(1)

def show_devices(devices: List[Dict[str, str]]):
    logging.info(_("\nDetected block devices:"))
    print("{:<3} {:<15} {:<10} {:<8} {:<20} {:<15} {:<10} {:<10} {:<10}".format(
        "#", "Device", "Size", "Type", "Model", "Mountpoint", "Mounted?", "FSTYPE", "Removable"))
    print("-"*125)
    for idx, d in enumerate(devices):
        print("{:<3} /dev/{:<12} {:<10} {:<8} {:<20} {:<15} {:<10} {:<10} {:<10}".format(
            idx,
            str(d.get("name", "-")),
            str(d.get("size", "-")),
            str(d.get("type", "-")),
            str(d.get("model", "-") or "-"),
            str(d.get("mountpoint", "-") or "-"),
            "YES" if d.get("mounted") else "NO",
            str(d.get("fstype", "-") or "-"),
            "YES" if d.get("removable") else "NO"
        ))
    print()
    for d in devices:
        fstype = str(d.get("fstype", "-") or "-")
        if d.get("mounted"):
            logging.warning(_("/dev/%s is mounted at %s.") % (d.get("name", "-"), d.get("mountpoint", "-")))
        if fstype.lower().startswith("crypto_luks"):
            logging.warning(_("/dev/%s appears to be a LUKS encrypted device.") % d.get("name", "-"))
        if d.get("is_partition"):
            logging.info(_("/dev/%s is a partition.") % d.get("name", "-"))

# ========== Root and confirmation ==========
def get_root_device() -> Optional[str]:
    try:
        result = subprocess.run([
            "lsblk", "-o", "NAME,MOUNTPOINT", "-J"
        ], capture_output=True, text=True, check=True)
        import json
        data = json.loads(result.stdout)
        for block in data.get("blockdevices", []):
            if block.get("mountpoint") == "/":
                return block["name"]
            for part in block.get("children", []):
                if part.get("mountpoint") == "/":
                    return block["name"]
        return None
    except Exception:
        return None

def double_confirm(device: str, size_bytes: Optional[int] = None, passes: int = 1, block_size: int = 1048576) -> None:
    est_time = None
    if size_bytes:
        # Estimativa grosseira: 100MB/s
        est_time = str(datetime.timedelta(seconds=int((size_bytes * passes) / (100*1024*1024))))
    msg = _("\nWARNING: You are about to destroy ALL data on /dev/%s!" % device)
    if size_bytes:
        msg += _("\nTarget size: %s bytes (%s)" % (size_bytes, human_readable_size(size_bytes)))
    msg += _("\nBlock size: %d bytes, Passes: %d" % (block_size, passes))
    if est_time:
        msg += _("\nEstimated time (at 100MB/s): %s" % est_time)
    logging.warning(msg)
    confirm1 = input(_("Type 'DESTROY' to confirm: "))
    if confirm1.strip() != "DESTROY":
        logging.error(_("Confirmation failed."))
        sys.exit(1)
    confirm2 = input(_("Type the device name (%s) to confirm: ") % device)
    if confirm2.strip() != device:
        logging.error(_("Second confirmation failed."))
        sys.exit(1)

def human_readable_size(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)

# ========== Wipe, Throttle, mmap, Verification ==========
def wipe_device(device: str, block_size: int, passes: int, random_fill: bool = False, use_mmap: bool = False, throttle: Optional[float] = None, verify: bool = False) -> None:
    global _
    size_bytes = get_device_size_bytes(device)
    total_written = 0
    start_time = time.time()
    try:
        for p in range(passes):
            logging.info(_("\nPass %d/%d - Writing %s to /dev/%s...") % (p+1, passes, _('random data') if random_fill else _('zeros'), device))
            written = 0
            n_blocks = size_bytes // block_size
            remainder = size_bytes % block_size
            progress = tqdm(total=size_bytes, unit='B', unit_scale=True, leave=True) if TQDM_AVAILABLE else DummyProgress()
            with open(f"/dev/{device}", "wb") as f:
                mm = None
                if use_mmap:
                    try:
                        import mmap
                        mm = mmap.mmap(f.fileno(), 0)
                    except Exception:
                        mm = None
                try:
                    for __ in range(n_blocks):
                        buf = os.urandom(block_size) if random_fill else b"\x00" * block_size
                        if mm:
                            mm.write(buf)
                        else:
                            f.write(buf)
                        written += block_size
                        progress.update(block_size)
                        if throttle:
                            time.sleep(block_size / (throttle * 1024 * 1024))
                    if remainder:
                        buf = os.urandom(remainder) if random_fill else b"\x00" * remainder
                        if mm:
                            mm.write(buf)
                        else:
                            f.write(buf)
                        written += remainder
                        progress.update(remainder)
                    f.flush()
                    os.fsync(f.fileno())
                except KeyboardInterrupt:
                    progress.close()
                    logging.error(_("\n[ABORTED] Interrupted by user. Exiting cleanly."))
                    sys.exit(130)
            progress.close()
            total_written += written
        elapsed = time.time() - start_time
        logging.info(_("\n[OK] Device /dev/%s wiped successfully.") % device)
        logging.info(_("Total written: %d bytes in %s.") % (total_written, datetime.timedelta(seconds=elapsed)))
        if verify:
            if verify_device(device, block_size, random_fill):
                logging.info(_("[VERIFY] Device /dev/%s verified successfully.") % device)
            else:
                logging.error(_("[VERIFY] Verification failed for /dev/%s!") % device)
    except KeyboardInterrupt:
        logging.error(_("\n[ABORTED] Interrupted by user. Exiting cleanly."))
        sys.exit(130)
    except PermissionError:
        logging.critical(_("Permission denied to write to /dev/%s.") % device)
        sys.exit(1)
    except FileNotFoundError:
        logging.critical(_("Device /dev/%s does not exist.") % device)
        sys.exit(1)
    except OSError as e:
        logging.critical(_("OS error: %s") % e)
        sys.exit(1)
    except Exception as e:
        logging.critical(_("Unexpected error: %s") % e)
        sys.exit(1)

def verify_device(device: str, block_size: int, random_fill: bool = False, sample_blocks: int = 8) -> bool:
    global _
    try:
        with open(f"/dev/{device}", "rb") as f:
            for __ in range(sample_blocks):
                data = f.read(block_size)
                if not data:
                    break
                if random_fill:
                    if all(b == 0 for b in data):
                        return False
                else:
                    if any(b != 0 for b in data):
                        return False
        return True
    except Exception as e:
        logging.error(_("[VERIFY] Error reading device: %s") % e)
        return False

def get_device_size_bytes(device: str) -> int:
    try:
        result = subprocess.run([
            "blockdev", "--getsize64", f"/dev/{device}"
        ], capture_output=True, text=True, check=True)
        return int(result.stdout.strip())
    except Exception as e:
        logging.critical(_("Could not get device size: %s") % e)
        sys.exit(1)

def sha256_self(path=None) -> str:
    import hashlib
    if path is None:
        path = os.path.abspath(__file__)
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

# ========== Main CLI ==========
def main() -> None:
    global _
    parser = argparse.ArgumentParser(
        description="\033[1m" + banner + "\033[0m" + "\n" + about,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
  Project: github.com/Br3noAraujo/CottonWipe
  Author: Br3noAraujo | License: MIT | Python 3.x only
  Coded with care, but USE AT YOUR OWN RISK!
        """
    )
    parser.add_argument("-b", "--block-size", type=int, default=1048576, help=_("Block size in bytes (default: 1048576)"))
    parser.add_argument("-p", "--passes", type=int, default=1, help=_("Number of overwrite passes (default: 1)"))
    parser.add_argument("-d", "--device", type=str, help=_("Device name to wipe (e.g., sdb)"))
    parser.add_argument("-D", "--dangerous", action="store_true", help=_("Automatic mode: no confirmation prompts"))
    parser.add_argument("-r", "--random", action="store_true", help=_("Fill with random data instead of zeros"))
    parser.add_argument("-q", "--quiet", action="store_true", help=_("Suppress most output (only errors)"))
    parser.add_argument("-v", "--verbose", action="store_true", help=_("Show more detailed logs (debug level)"))
    parser.add_argument("-l", "--list", action="store_true", help=_("List block devices and exit"))
    parser.add_argument("-s", "--sha256", action="store_true", help=_("Show SHA256 of this script and exit"))
    parser.add_argument("-V", "--verify", action="store_true", help=_("Verify device after wipe"))
    parser.add_argument("-t", "--throttle", type=float, help=_("Throttle write speed (MB/s)"))
    parser.add_argument("-n", "--no-mounted", action="store_true", help=_("Do not allow wiping mounted devices"))
    parser.add_argument("-f", "--log-file", type=str, help=_("Save logs to file"))
    parser.add_argument("-T", "--test", action="store_true", help=_("Run internal unit tests and exit"))
    args = parser.parse_args()

    # Print banner unless in quiet, list, sha256, or test mode
    if not (args.quiet or args.list or args.sha256 or args.test):
        print("\033[1m" + banner + "\033[0m")

    if args.test:
        run_internal_tests()
        sys.exit(0)

    log_level = logging.DEBUG if args.verbose else (logging.ERROR if args.quiet else logging.INFO)
    setup_logging(args.quiet, args.log_file, level=log_level)
    setup_signal_handlers()
    require_root()
    check_dependencies()

    if args.sha256:
        print(sha256_self())
        sys.exit(0)

    if args.list:
        devices = list_block_devices()
        show_devices(devices)
        sys.exit(0)

    if args.block_size < 512:
        logging.critical(_("Block size too small. Must be >= 512 bytes."))
        sys.exit(1)

    devices = list_block_devices()
    show_devices(devices)
    if not devices:
        logging.critical(_("No block devices found."))
        sys.exit(1)

    # Filtro de montados
    if args.no_mounted:
        devices = [d for d in devices if not d["mounted"]]
        if not devices:
            logging.critical(_("No unmounted devices available."))
            sys.exit(1)
        show_devices(devices)

    # Seleção de dispositivo
    device = None
    if args.device:
        if not any(d["name"] == args.device for d in devices):
            logging.critical(_("Device /dev/%s not found in detected block devices.") % args.device)
            sys.exit(1)
        device = args.device
    else:
        try:
            idx = int(input(_("Select the device number to wipe (e.g., 0): ")))
            if idx < 0 or idx >= len(devices):
                raise ValueError
        except ValueError:
            logging.critical(_("Invalid selection."))
            sys.exit(1)
        device = devices[idx]["name"]

    # Proteção do root
    rootdev = get_root_device()
    if rootdev and device == rootdev:
        logging.critical(_("/dev/%s is the root device (mounted as /). Refusing to wipe.") % device)
        sys.exit(1)

    # Proteção de montados
    devinfo = next((d for d in devices if d["name"] == device), None)
    if devinfo and devinfo["mounted"] and args.no_mounted:
        logging.critical(_("/dev/%s is mounted. Refusing to wipe due to --no-mounted." ) % device)
        sys.exit(1)

    # Confirmação
    if not args.dangerous:
        double_confirm(device, get_device_size_bytes(device), args.passes, args.block_size)
    else:
        logging.warning(_("[DANGEROUS MODE] Skipping confirmation prompts!"))

    logging.info(_("\nStarting wipe of /dev/%s with block size %d bytes, %d pass(es), mode: %s...") % (device, args.block_size, args.passes, _('random') if args.random else _('zero-fill')))
    wipe_device(device, args.block_size, args.passes, random_fill=args.random, use_mmap=True, throttle=args.throttle, verify=args.verify)

# ========== Internal unit tests ==========
def run_internal_tests():
    import unittest
    from unittest.mock import patch
    class TestCottonWipe(unittest.TestCase):
        @patch('subprocess.run')
        def test_list_block_devices_parsing(self, mock_run):
            mock_run.return_value.stdout = '''
            {"blockdevices": [
                {"name": "sda", "size": "100G", "type": "disk", "model": "TestDisk", "mountpoint": null, "fstype": null, "children": [
                    {"name": "sda1", "size": "100G", "type": "part", "model": "TestDisk", "mountpoint": "/", "fstype": "ext4"}
                ]}
            ]}
            '''
            mock_run.return_value.returncode = 0
            devices = list_block_devices()
            self.assertEqual(devices[0]['name'], 'sda')
            self.assertEqual(devices[0]['type'], 'disk')
            self.assertFalse(devices[0]['is_partition'])
            self.assertEqual(devices[1]['name'], 'sda1')
            self.assertEqual(devices[1]['type'], 'part')
            self.assertTrue(devices[1]['is_partition'])
        @patch('builtins.input', side_effect=['DESTROY', 'sda'])
        def test_double_confirm(self, mock_input):
            double_confirm('sda')
        @patch('builtins.input', side_effect=['NOPE', 'sda'])
        def test_double_confirm_fail(self, mock_input):
            with self.assertRaises(SystemExit):
                double_confirm('sda')
        def test_sha256_self(self):
            hash_val = sha256_self(__file__)
            self.assertEqual(len(hash_val), 64)
            self.assertTrue(all(c in '0123456789abcdef' for c in hash_val.lower()))
    unittest.main(argv=['ignored', '-v'], exit=False)

if __name__ == "__main__":
    main()
