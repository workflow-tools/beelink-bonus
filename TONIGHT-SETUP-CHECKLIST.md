# Beelink Setup Checklist — Tonight's Session

> **Goal:** Get Tailscale working so every future session is from your Mac.
> **Time budget:** 30-45 minutes
> **Date:** March 11, 2026

---

## Phase 1: Tailscale (15 minutes) — DO THIS FIRST

### On the Beelink (Windows):

1. **Download Tailscale:** https://tailscale.com/download/windows
2. **Install and sign in** with your Google account (or GitHub — pick one and stick with it)
3. **Note the Tailscale IP** shown in the system tray icon (e.g., `100.x.y.z`)
4. **Open PowerShell as Admin and run:**
   ```powershell
   # Verify Tailscale is running
   tailscale status
   ```

### On your MacBook:

1. **Install Tailscale:**
   - App Store: search "Tailscale" (easiest)
   - Or: `brew install --cask tailscale`
2. **Sign in with the SAME account** you used on the Beelink
3. **Test connectivity:**
   ```bash
   # Ping the Beelink
   ping 100.x.y.z    # use the IP you noted above

   # Test Ollama is reachable
   curl http://100.x.y.z:11434/api/tags
   ```

### Enable SSH on the Beelink (Windows):

```powershell
# Run in PowerShell as Admin on the Beelink:
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
```

Then from your Mac:
```bash
ssh your-windows-username@100.x.y.z
```

**If SSH works, you're done with Phase 1. Everything else can be done from your Mac.**

---

## Phase 2: Verify Ollama + Benchmark (10 minutes)

You said Ollama is already installed. Let's verify GPU detection and pull the models you need.

### From the Beelink (or SSH):

```powershell
# Check what models you already have
ollama list

# Check if GPU is detected (look for "AMD" in output)
ollama run llama3.1:8b "Say hello"

# Watch GPU usage while Ollama runs:
# Open Task Manager → Performance → GPU
# If GPU usage is 0% during inference, ROCm isn't working
```

### If GPU IS detected, pull the generation models:

```powershell
# The 70B model — your competitive moat (this is a ~40GB download, let it run overnight if needed)
ollama pull llama3.1:70b-instruct-q4_K_M

# Fast model for high-volume generation
ollama pull mistral:7b-instruct-q4_K_M
```

### Quick benchmark (save this output!):

```powershell
# Time a 70B generation (if already downloaded)
ollama run llama3.1:70b-instruct-q4_K_M "Generate a realistic German Mittelstand company name in the Maschinenbau sector located in Oberpfalz, Bavaria. Return ONLY the company name, nothing else."

# Note the tok/s shown at the end of generation
# Expected on your hardware: 8-15 tok/s for 70B q4
# If you get <3 tok/s, GPU isn't being used
```

---

## Phase 3: Python Environment (10 minutes)

```powershell
# Check if Python is installed
python --version

# If not, install via winget:
winget install Python.Python.3.11

# Create the factory directory
mkdir C:\VilseckKI\factory
cd C:\VilseckKI\factory

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install the data generation stack
pip install sdv evidently faker pyyaml requests pandas
```

**That's it for tonight.** Once Tailscale + SSH works, you never need to sit at the Beelink again.

---

## Phase 4: Tomorrow (from your Mac, 15 min)

SSH into the Beelink and run a tiny test:

```bash
ssh your-windows-username@100.x.y.z

cd C:\VilseckKI\factory
.\venv\Scripts\Activate.ps1

python -c "
from sdv.single_table import GaussianCopulaSynthesizer
from sdv.metadata import SingleTableMetadata
import pandas as pd

# Minimal test: generate 10 fake companies
data = pd.DataFrame({
    'firma': ['Test GmbH'] * 5,
    'umsatz': [100000, 500000, 1200000, 50000, 8000000],
    'mitarbeiter': [3, 25, 80, 1, 450],
    'branche': ['IT', 'Maschinenbau', 'Logistik', 'Handwerk', 'Automotive']
})

metadata = SingleTableMetadata()
metadata.detect_from_dataframe(data)

synth = GaussianCopulaSynthesizer(metadata)
synth.fit(data)
samples = synth.sample(10)
print(samples.to_string())
print('SDV is working!')
"
```

If that prints 10 synthetic rows, your pipeline foundation is ready.

---

## Seed Data: What's Freely Available

Good news — you don't need to go find anything manually. All the aggregate statistics you need for realistic distributions are published by German federal agencies:

### Ready-to-use distribution parameters:

**Employee size (from Destatis Unternehmensregister 2024):**
- <10 employees: 84%
- 10-49: 12%
- 50-249: 3.5%
- 250+: 0.5%

**Rechtsform (from Destatis):**
- Einzelunternehmen/e.K.: ~58%
- GmbH: ~25%
- UG (haftungsbeschränkt): ~9.5%
- GmbH & Co. KG: ~5%
- OHG/KG: ~2%
- AG: ~0.5%

**Geographic (Bavaria share):**
- ~18% of all German companies are in Bavaria (~695,000 companies)

**Industry breakdown (approximate, from KfW Panel):**
- Services: ~60%
- Trade/Handel: ~15%
- Crafts/Handwerk: ~15%
- Manufacturing/Verarbeitendes Gewerbe: ~8%
- Construction/Bau: ~10%

### Where to download structured data:

| Data | Source | URL |
|------|--------|-----|
| Size + revenue + legal form | GENESIS-Online (free, CSV export) | https://www-genesis.destatis.de/datenbank/online |
| SME panel (industry, revenue, size) | KfW Mittelstandspanel 2024 Tabellenband | https://www.kfw.de/About-KfW/Service/Download-Center/Research-(EN)/KfW-Mittelstandspanel/ |
| Regional breakdown | IfM Bonn statistics | https://www.ifm-bonn.org/en/statistics/overview |
| Bavaria-specific | Bayern GENESIS | https://statistikdaten.bayern.de/genesis/online/ |

These are aggregate statistics (distributions, percentages, totals) — exactly what you need to parameterize CTGAN/GaussianCopula. You're not copying any company's data; you're using published national statistics to make your synthetic data demographically realistic.

---

## vilseckki.de — Hold For Now

You're right to wait. No development dependency on the domain. When you're ready, INWX.de (German registrar, no US dependency) has .de domains for ~EUR 5/year. Takes 5 minutes.

---

## What Success Looks Like After Tonight

- [ ] Tailscale installed on both machines, Beelink reachable from Mac
- [ ] SSH working from Mac to Beelink
- [ ] Ollama verified (GPU detection confirmed or noted as issue)
- [ ] 70B model pull started (can run overnight)
- [ ] Python venv created with SDV + Evidently installed
- [ ] You can close the Beelink's monitor lid and never open it again
