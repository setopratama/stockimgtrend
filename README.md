# stockimgtrend 🍌📊

Sistem AI Multi-Agent & **Terminal User Interface (TUI) Dashboard Real-Time** untuk riset tren visual stock image (khususnya Adobe Stock) memanfaatkan **Google Trends Live Scan**, **Tavily Search API (Cloud Proxy)**, dan **OpenRouter AI**.

Aplikasi ini menghadirkan antarmuka visual modular layar penuh berbasis keyboard (*keyboard-driven*) dengan animasi telemetri data langsung, audit kualitas otomatis oleh **AI Senior Art Director**, serta generator **1 Master Prompt & Tema Kuat** yang dioptimalkan khusus untuk engine **Nanobanana**.

---

## ⚡ Cara Menjalankan Super Cepat

Cukup jalankan script launcher:

```bash
./start.sh
```

### Navigasi Shortcut Keyboard di Dashboard:
- **`[a]`**: **Auto Discovery** (Live scan Google Trends -> AI Konseptor & Art Director filter -> Cek supply gap Adobe Stock -> Racik Master Prompt).
- **`[k]`**: **Ketik Keyword** (Dialog input minimalis untuk menganalisis topik visual spesifik).
- **`[g]`**: **Gen Nanobanana** (Meracik Master Prompt, Negative Prompt, dan 50 Tags dari riset aktif).
- **`[h]`**: **Riwayat (DB)** (Viewer tabel database SQLite dengan navigasi keyboard).
- **`[c]`**: **Clear Log** (Membersihkan panel aktivitas sistem).
- **`[q]`**: **Keluar** (Menutup dashboard dengan rapi).

---

## 🛠️ Parameter Tambahan (Opsional)

Script `start.sh` juga mendukung parameter langsung dari terminal:

```bash
# Riset keyword tertentu langsung
./start.sh -k "bionic athlete outdoors"

# Langsung jalankan Autonomous Discovery
./start.sh --auto

# Cek tabel riwayat SQLite secara instan di terminal
./start.sh -H
```

---

## 🔒 Keamanan IP (Zero Local Scraping)

Seluruh riset pasar dan pelacakan hasil Adobe Stock dilakukan **100% melalui Tavily Search API di cloud**. Komputer Anda tidak melakukan scraping langsung ke `stock.adobe.com`, sehingga IP Anda sepenuhnya aman dari risiko rate limit, CAPTCHA, atau IP ban.

Dokumentasi lengkap arsitektur multi-agent dapat dibaca di [AGENTS.md](AGENTS.md).
