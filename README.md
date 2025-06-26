
# CottonWipe
<p align="center">
  <img src="https://i.imgur.com/HjcAJrI.png" alt="CottonWipe Banner" width="600"/>
</p>

<b>ZeroFill & RandomFill for Linux block devices — gentle as cotton, final as death.</b>

---

## ⚠️ DANGER: IRREVERSIBLE DATA DESTRUCTION! ⚠️

> **CottonWipe** is a professional, open source Python tool for secure, irreversible data destruction on block devices (HDD, SSD, USB, SD, partitions).
> 
> **USE AT YOUR OWN RISK!**
> 
> **All data on the selected device will be permanently destroyed. There is NO UNDO.**
> 
> **Author:** Br3noAraujo | **License:** MIT | **GitHub:** [Br3noAraujo](https://github.com/Br3noAraujo)

---

## ✨ Features

- 🔍 Lists all disks and partitions, with clear warnings for mounted and encrypted devices.
- ⚠️ Double confirmation (unless `--dangerous`).
- 📊 Progress bar, logging, verification, and performance throttle.
- 🎨 Colorful, modern CLI with banner and themed messages.
- 🧩 Compatible with Linux/UNIX terminals. 100% Python 3, open source.

---

## 🚀 Quick Start

```bash
git clone https://github.com/Br3noAraujo/CottonWipe.git
cd CottonWipe
sudo python3 cottonwipe.py
```

Or make it executable:
```bash
chmod +x cottonwipe.py
sudo ./cottonwipe.py
```

---

## 🛡️ Usage Example

```bash
sudo ./cottonwipe.py -l                # List all block devices
sudo ./cottonwipe.py -d sdb            # Wipe /dev/sdb (with double confirmation)
sudo ./cottonwipe.py -d sdb -D         # Wipe /dev/sdb (DANGEROUS: no confirmation)
sudo ./cottonwipe.py -d sdb -p 3 -r    # 3 passes, random data
sudo ./cottonwipe.py -d sdb -V         # Verify after wipe
sudo ./cottonwipe.py -d sdb -t 50      # Throttle to 50 MB/s
sudo ./cottonwipe.py -h                # Show help and banner
```

---

## 📝 Command Line Options

| Short | Long         | Description                                      |
|-------|--------------|--------------------------------------------------|
| -b    | --block-size | Block size in bytes (default: 1048576)           |
| -p    | --passes     | Number of overwrite passes (default: 1)          |
| -d    | --device     | Device name to wipe (e.g., sdb)                  |
| -D    | --dangerous  | Automatic mode: no confirmation prompts          |
| -r    | --random     | Fill with random data instead of zeros           |
| -q    | --quiet      | Suppress most output (only errors)               |
| -v    | --verbose    | Show more detailed logs (debug level)            |
| -l    | --list       | List block devices and exit                      |
| -s    | --sha256     | Show SHA256 of this script and exit              |
| -V    | --verify     | Verify device after wipe                         |
| -t    | --throttle   | Throttle write speed (MB/s)                      |
| -n    | --no-mounted | Do not allow wiping mounted devices              |
| -f    | --log-file   | Save logs to file                                |
| -T    | --test       | Run internal unit tests and exit                 |

---

## 🧑‍💻 Legal & Safety

- **This tool is provided AS IS, without warranty of any kind.**
- **You are solely responsible for any data loss or hardware damage.**
- **Always double-check the device you are wiping.**
- **Never run on a device containing important data unless you are absolutely sure.**
- **For professional use, audit the code and test in a safe environment first.**

---

## ❤️ Contributing

Pull requests, issues and suggestions are welcome!  
Let's make secure data destruction accessible, beautiful and open source.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>Gentle as cotton, final as death. Use wisely! 🧨</b>
</p> 