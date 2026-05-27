# 🟢 GoGreen — Keep Microsoft Teams Status Green & Available (Always)

### The #1 open-source tool to keep your Microsoft Teams status "Available" — without installing anything.

<p align="center">
  <img src="https://img.shields.io/badge/Teams_Status-Always_Green_🟢-00e676?style=for-the-badge&logo=microsoftteams&logoColor=white" alt="Keep Microsoft Teams Status Green Always Available">
  <img src="https://img.shields.io/badge/Install-ZERO_Dependencies-blueviolet?style=for-the-badge" alt="Zero Install No Dependencies No Pip No Admin">
  <img src="https://img.shields.io/badge/Platform-macOS_|_Windows-lightgrey?style=for-the-badge&logo=apple&logoColor=white" alt="Works on macOS and Windows">
  <img src="https://img.shields.io/badge/Python-3.7+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.7+ Required">
  <img src="https://img.shields.io/github/stars/SuperShary/GoGreen?style=for-the-badge&color=yellow&logo=github" alt="GitHub Stars">
  <img src="https://img.shields.io/github/license/SuperShary/GoGreen?style=for-the-badge" alt="MIT License">
</p>

<p align="center">
  <strong>Tired of Microsoft Teams showing you as "Away" after 5 minutes?</strong><br>
  GoGreen keeps your Teams status green <em>permanently</em> — no software to install, no admin password, no pip packages.<br>
  <strong>Just copy → run → stay green. Works on corporate laptops.</strong>
</p>

---

## 📖 Table of Contents

- [The Problem](#-the-problem)
- [The Solution](#-the-solution--gogreen)
- [Quick Start (30 Seconds)](#-quick-start--30-seconds)
- [Features](#-features)
- [How It Works](#-how-it-works)
- [Supported Platforms](#-supported-platforms)
- [Requirements](#-requirements)
- [Screenshots](#-screenshots)
- [FAQ](#-frequently-asked-questions)
- [Comparison with Other Tools](#-comparison-with-other-tools)
- [Contributing](#-contributing)
- [License](#-license)

---

## 😤 The Problem

Microsoft Teams automatically changes your status to **"Away"** after just **5 minutes of inactivity**. This happens when you:

- 🚶 Step away to grab coffee
- 📱 Switch to your phone for a call
- 📖 Read a document on paper
- 🍽️ Take a lunch break
- 🧠 Think deeply without touching the mouse

Your manager, your team, and your entire organization can see that yellow "Away" badge. It creates the impression you're not working — even when you are.

**There's no built-in way to disable this behavior in Microsoft Teams.**

---

## 💡 The Solution — GoGreen

**GoGreen** is a lightweight, open-source Python application that keeps your Microsoft Teams status set to **"Available" (green)** at all times.

It works by simulating tiny, imperceptible mouse movements and keyboard presses at regular intervals — just enough to prevent Teams from detecting you as idle.

### ✅ What makes GoGreen different?

| | GoGreen | Mouse Jigglers | Other Scripts | Browser Extensions |
|---|:---:|:---:|:---:|:---:|
| **Zero install** (no pip, no brew, no admin) | ✅ | ❌ | ❌ | ❌ |
| **Works on locked corporate laptops** | ✅ | ❌ | ❌ | ⚠️ |
| **Cross-platform** (macOS + Windows) | ✅ | ⚠️ | ⚠️ | ✅ |
| **Beautiful GUI with dark theme** | ✅ | ❌ | ❌ | ❌ |
| **Customizable duration** (2h–∞) | ✅ | ❌ | ❌ | ❌ |
| **Schedule mode** (auto start/stop) | ✅ | ❌ | ❌ | ❌ |
| **Prevents laptop sleep** | ✅ | ✅ | ❌ | ❌ |
| **Activity log** | ✅ | ❌ | ❌ | ❌ |
| **Open source & free** | ✅ | ❌ | ✅ | ⚠️ |
| **No USB device needed** | ✅ | ❌ | ✅ | ✅ |

---

## 🚀 Quick Start — 30 Seconds

### Option A: Download ZIP (Easiest — No Git Required)

1. Click the green **"Code"** button above → **"Download ZIP"**
2. Extract the ZIP folder anywhere on your computer
3. Open **Terminal** (macOS) or **Command Prompt** (Windows)
4. Navigate to the folder:
   ```bash
   cd path/to/gogreen
   ```
5. Run it:
   ```bash
   python3 main.py
   ```

### Option B: Git Clone

```bash
git clone https://github.com/SuperShary/GoGreen.git
cd GoGreen
python3 main.py
```

> **Windows users:** Use `python main.py` instead of `python3 main.py`

### That's it. No `pip install`. No virtual environment. No admin password.

The GoGreen window will open with a beautiful dark-themed interface. Click **▶ START** and your Teams status will stay green.

---

## 🎛️ Features

### ⏱️ Duration Control
Choose exactly how long to keep your status green:
- **Presets**: 2 hours, 4 hours, 8 hours, 12 hours
- **Custom**: Enter any number of hours
- **Infinite mode**: Runs until you stop it manually

### 🔄 Adjustable Activity Interval
Control how frequently GoGreen simulates activity:
- Slide between **30 seconds** and **5 minutes**
- Lower interval = more reliable, higher = more subtle
- Default: 60 seconds (recommended)

### 📅 Schedule Mode (Set It & Forget It)
Automate your green status on a weekly schedule:
- Set **start time** (e.g., 09:00 AM) and **stop time** (e.g., 06:00 PM)
- Choose **active days** (Monday through Sunday)
- GoGreen auto-starts and auto-stops — no manual intervention needed
- Perfect for standard work hours

### 📋 Live Activity Log
Real-time log showing every action GoGreen takes:
- Timestamped entries for each mouse wiggle and key press
- Engine start/stop/pause events
- Schedule trigger notifications

### 🎨 Premium Dark Theme GUI
No ugly terminal scripts. GoGreen has a polished desktop interface with:
- Animated pulsing status indicator (green / amber / gray)
- Live countdown timer
- Intuitive controls (Start, Pause, Stop)
- Clean card-based layout

### 💾 Persistent Settings
Your preferences are saved automatically:
- Duration, interval, schedule — everything persists between sessions
- Settings stored locally at `~/.gogreen/settings.json`
- No cloud, no accounts, no telemetry

### 😴 Sleep Prevention
GoGreen prevents your laptop from going to sleep:
- **macOS**: Uses built-in `caffeinate` command
- **Windows**: Uses `kernel32.dll` `SetThreadExecutionState` API
- No third-party sleep prevention tools needed

---

## ⚙️ How It Works

GoGreen uses a **triple-layer approach** to keep Microsoft Teams status green:

```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║  Layer 1: 🖱️  MOUSE WIGGLE                               ║
║  → Moves cursor 1 pixel right, then 1 pixel back        ║
║  → Completely invisible to the user                      ║
║  → macOS: CoreGraphics via osascript                     ║
║  → Windows: user32.dll SetCursorPos via ctypes           ║
║                                                          ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Layer 2: ⌨️  SHIFT KEY PRESS                             ║
║  → Presses and releases the Shift key                    ║
║  → Harmless — produces no visible output                 ║
║  → macOS: System Events via osascript                    ║
║  → Windows: user32.dll keybd_event via ctypes            ║
║                                                          ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Layer 3: 😴  SLEEP PREVENTION                            ║
║  → Prevents display and system idle sleep                ║
║  → macOS: caffeinate -di (built-in command)              ║
║  → Windows: SetThreadExecutionState (built-in API)       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

**Important:** GoGreen does **NOT**:
- Access the Microsoft Teams API
- Modify any Teams settings or files
- Send any data anywhere
- Require internet access
- Install any software or drivers

It simply simulates keyboard and mouse input at the OS level — indistinguishable from you actually using your computer.

---

## 🖥️ Supported Platforms

| Platform | Status | Simulation Method |
|---|:---:|---|
| **macOS** (Intel & Apple Silicon) | ✅ Fully supported | `osascript` (CoreGraphics + System Events) + `caffeinate` |
| **Windows 10/11** | ✅ Fully supported | `ctypes` → `user32.dll` + `kernel32.dll` |
| **Linux** | 🔜 Coming soon | PRs welcome! |

---

## 📋 Requirements

| Requirement | Details |
|---|---|
| **Python** | 3.7 or later |
| **pip packages** | ❌ None — zero external dependencies |
| **Admin rights** | ❌ Not required |
| **Internet** | ❌ Not required (works offline) |
| **External tools** | ❌ None — uses only OS built-in tools |

### Where to get Python

| Platform | How to check | How to install |
|---|---|---|
| **macOS** | Open Terminal → `python3 --version` | Usually pre-installed. If not: [python.org/downloads](https://www.python.org/downloads/) |
| **Windows** | Open CMD → `python --version` | [python.org/downloads](https://www.python.org/downloads/) — check "Add to PATH" during install |

### macOS: Accessibility Permission

GoGreen simulates mouse/keyboard input, which requires Accessibility permission on macOS:

1. Open **System Settings**
2. Go to **Privacy & Security** → **Accessibility**
3. Click the **+** button and add your **Terminal** app (e.g., Terminal.app, iTerm, VS Code)
4. Enable the toggle

GoGreen shows a helpful guide on first launch.

---

## 🖼️ Screenshots

*Screenshots coming soon — the app features a premium dark-theme interface with:*
- *Green pulsing status dot when active*
- *Live countdown timer*
- *Duration, interval, and schedule controls*
- *Real-time activity log*

---

## ❓ Frequently Asked Questions

<details>
<summary><strong>Is GoGreen safe to use?</strong></summary>
<br>
Yes. GoGreen only simulates a 1-pixel mouse movement and a Shift key press. It doesn't access Teams APIs, doesn't modify system files, and doesn't transmit any data. It's the digital equivalent of jiggling your mouse while reading a document.
</details>

<details>
<summary><strong>Will my IT department detect GoGreen?</strong></summary>
<br>
GoGreen doesn't install any software, doesn't create services, and doesn't modify the registry. It's just a Python script that runs in user space. The input it generates is identical to real keyboard and mouse activity. Most IT monitoring tools cannot distinguish GoGreen's activity from genuine user input.
</details>

<details>
<summary><strong>Does GoGreen work with the new Microsoft Teams?</strong></summary>
<br>
Yes. GoGreen works with both the classic and new (Teams 2.0) versions of Microsoft Teams on both macOS and Windows. Since it operates at the OS input level, it works regardless of which Teams version you use.
</details>

<details>
<summary><strong>Can I use GoGreen on my company/corporate laptop?</strong></summary>
<br>
Yes — GoGreen was specifically designed for corporate environments. It requires no installation, no admin password, no pip packages, and no USB devices. Just copy the files and run <code>python3 main.py</code>.
</details>

<details>
<summary><strong>Does GoGreen drain battery?</strong></summary>
<br>
Minimal impact. GoGreen simulates one tiny mouse wiggle + one key press every 60 seconds by default. CPU usage is essentially zero. However, the sleep prevention feature does keep your display on, which uses battery. Consider plugging in for extended use.
</details>

<details>
<summary><strong>Does GoGreen work when the laptop lid is closed?</strong></summary>
<br>
No. Closing the laptop lid puts the hardware into sleep mode, which no software can override. Keep the lid open for GoGreen to work. You can reduce screen brightness to save energy.
</details>

<details>
<summary><strong>How is this different from a USB mouse jiggler?</strong></summary>
<br>
USB mouse jigglers are physical devices that many corporate IT departments block or detect. GoGreen is pure software — no USB device, no driver installation, nothing to plug in. It also offers features no hardware jiggler can: scheduling, duration control, GUI, and activity logs.
</details>

<details>
<summary><strong>Does GoGreen work with Slack, Zoom, or other apps?</strong></summary>
<br>
Yes! While designed for Microsoft Teams, GoGreen's mouse wiggle and key press simulation prevents <em>any</em> application from detecting you as idle. This includes Slack, Zoom, Webex, Skype, and your operating system's screen saver.
</details>

<details>
<summary><strong>Why is there no pip install / requirements.txt?</strong></summary>
<br>
By design. Many corporate laptops restrict <code>pip install</code> and require admin approval for software installation. GoGreen uses only Python's standard library and OS-native tools, so it works everywhere Python is available — no additional packages needed.
</details>

<details>
<summary><strong>Can I run GoGreen in the background?</strong></summary>
<br>
The GoGreen GUI window needs to stay open (you can minimize it). A future update will add system tray / menu bar support for a more seamless background experience.
</details>

---

## 🔧 Comparison with Other Tools

### GoGreen vs. Mouse Jiggler (Hardware)
Hardware mouse jigglers plug into your USB port and simulate mouse movement. However, many corporate IT departments have endpoint detection that **blocks unknown USB devices** or flags them. GoGreen requires no hardware — it's pure software.

### GoGreen vs. Caffeine / Amphetamine (macOS)
Caffeine and Amphetamine prevent your Mac from sleeping, but **they don't simulate user activity**. Teams will still mark you as "Away" because there's no keyboard or mouse input. GoGreen does both: prevents sleep AND simulates activity.

### GoGreen vs. PowerToys Awake (Windows)
Microsoft's PowerToys Awake keeps your PC awake, but like Caffeine, it **doesn't simulate input**. Teams will still show you as inactive. GoGreen simulates actual mouse and keyboard activity that Teams recognizes.

### GoGreen vs. PyAutoGUI Scripts
Many online scripts use `pyautogui` for mouse/keyboard simulation. The problem? `pyautogui` requires **pip install**, which is blocked on many corporate laptops. GoGreen uses `osascript` (macOS) and `ctypes` (Windows) — both built into the OS. **Zero pip packages needed.**

### GoGreen vs. AutoHotKey (Windows)
AutoHotKey is powerful but requires **installation** and is **Windows-only**. Many corporate laptops block `.ahk` scripts or the AutoHotKey runtime. GoGreen is cross-platform and needs no installation.

---

## 📁 Project Structure

```
gogreen/
├── main.py          ← 🚀 Run this file to start GoGreen
├── app.py           ← 🎨 GUI (premium dark theme, all controls)
├── engine.py        ← ⚙️ Simulation engine (mouse, keyboard, sleep)
├── scheduler.py     ← 📅 Auto start/stop scheduling
├── settings.py      ← 💾 Settings persistence (JSON)
├── LICENSE          ← 📄 MIT License
├── README.md        ← 📖 This file
└── .gitignore       ← 🙈 Git ignore rules
```

---

## 🤝 Contributing

GoGreen is open source and contributions are welcome! Here's how:

1. **Fork** the repository
2. **Create** your feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Ideas for Contributions
- 🐧 **Linux support** — `xdotool` based simulation
- 🖼️ **System tray icon** — minimize to menu bar / system tray
- 🌍 **Localization** — translate the GUI to other languages
- 📊 **Statistics** — track daily/weekly green time
- 🔔 **Notifications** — alert when duration is ending

---

## ⭐ Star This Repo!

If GoGreen helped you stay green (and maybe saved your reputation), please give it a **⭐ star**!

Every star helps other people discover this tool. Let's build a movement for stress-free remote work. 💚

[![Star History](https://img.shields.io/github/stars/SuperShary/GoGreen?style=social)](https://github.com/SuperShary/GoGreen)

---

## 📄 License

This project is licensed under the **MIT License** — you're free to use, modify, and distribute it. See [LICENSE](LICENSE) for details.

---

## 🔑 Keywords

`keep teams status green` · `teams always available` · `prevent teams away status` · `microsoft teams green status` · `teams anti idle` · `teams mouse jiggler` · `teams status hack` · `keep teams active` · `teams away fix` · `corporate laptop teams status` · `no install teams green` · `teams status available python` · `prevent teams idle` · `teams status tool` · `remote work tools` · `work from home teams` · `teams always online` · `python mouse jiggler` · `cross platform teams tool` · `teams status keeper`

---

<p align="center">
  <strong>Made with 💚 for every remote worker who deserves a coffee break without judgment.</strong>
</p>

<p align="center">
  <sub>⚠️ Disclaimer: Use GoGreen responsibly and in accordance with your organization's IT and workplace policies. The developers are not responsible for any consequences arising from the use of this tool.</sub>
</p>
