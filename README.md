# Telegram Star Gifts Monitor ⭐🎁

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Telegram](https://img.shields.io/badge/Telegram-MTProto%20%2F%20Bot%20API-2CA5E0)
![Monitoring](https://img.shields.io/badge/Monitoring-Real--Time-orange)
![Type](https://img.shields.io/badge/Type-Digital%20Collectibles-purple)
![Infra](https://img.shields.io/badge/Infra-Alert%20System-grey)

Real-time **Telegram Star Gifts** monitoring bot that tracks:

* New gift releases
* Limited gift availability changes
* Sold-out events
* Upgrade availability

…and sends automated alerts to Telegram channels.

---

## ✨ Features

* 🆕 Detects newly released Star Gifts
* 📉 Tracks availability decrease
* 🔥 Detects sold-out gifts
* ⬆️ Monitors upgrade availability
* 🧠 Persistent state storage (JSON)
* 🖼️ Sends sticker + formatted alert
* ✏️ Edits alerts when data updates
* 🔁 Multi-bot anti-rate-limit rotation
* ⚡ Real-time monitoring loop

---

## 🧠 How it works

1. Connects to Telegram via **MTProto (user session)**
2. Fetches Star Gifts via raw API
3. Compares with stored state
4. Detects changes:

   * New gifts
   * Availability changes
   * Sold-out
   * Upgrades
5. Sends Telegram alerts
6. Saves updated state locally

---

## 📦 Project structure

```text
telegram-star-gifts-monitor/
│
├─ detector.py            # Main monitoring loop
├─ parse_data.py          # Raw Telegram data parser
├─ star_gifts_data.py     # Data models + persistence
├─ constants.py           # Paths / directories
├─ config.py              # Runtime config loader
├─ utils.py               # Logging & helpers
│
├─ data/
│   └─ star_gifts.json    # Stored gifts state
│
├─ logs/
│   └─ main.log           # Runtime logs
│
├─ .env.example
├─ .gitignore
├─ requirements.txt
└─ README.md
```

---

## 🚀 Quick start

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

---

### 2) Get Telegram API credentials

Go to:

https://my.telegram.org

Create an app → get:

* API_ID
* API_HASH

---

### 3) Configure environment

Copy:

```
.env.example → .env
```

Fill:

```env
API_ID=1234567
API_HASH=your_hash

SESSION_NAME=account

BOT_TOKENS=123:ABC...

NOTIFY_CHAT_ID=@YourChannel
NOTIFY_UPGRADES_CHAT_ID=@UpgradesChannel

CHECK_INTERVAL=1
CHECK_UPGRADES_PER_CYCLE=2
```

---

### 4) Run

```bash
python detector.py
```

First run will ask for Telegram login code.

---

## 📢 Alert types

### 🆕 New gift

* Sticker preview
* Gift ID
* Price
* Supply
* Availability %

---

### 📉 Availability update

Message auto-edited when supply decreases.

---

### 🔥 Sold out

Tracks full depletion time.

---

### ⬆️ Upgrade available

Sent to separate channel (optional).

---

## 💾 State storage

All detected gifts are stored locally:

```
data/star_gifts.json
```

Prevents duplicate alerts and enables update tracking.

---

## 🔐 Security

Secrets stored in:

```
.env
```

Never commit:

* API_HASH
* BOT_TOKENS
* Session files

---

## 🛠️ Requirements

```txt
pyrofork
tgcrypto
pydantic
httpx
pytz
```

---

## 📡 Use cases

* Digital collectibles monitoring
* Telegram marketplace tracking
* Alpha signal infrastructure
* Release sniping alerts
* Supply exhaustion tracking

---

## ⚠️ Disclaimer

For monitoring and research purposes only.
Not affiliated with Telegram.

---

## 🧩 Architecture highlights

* Async monitoring loop
* Raw MTProto parsing
* Stateful comparison engine
* Queue-based update processing
* Multi-bot alert rotation
* Persistent JSON storage
* Structured logging

---

**Part of blockchain & digital asset monitoring tooling ecosystem.**
