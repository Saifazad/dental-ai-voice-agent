# 🦷 Dental AI Voice Agent (`dental-ai-voice-agent`)

Yeh project Dental Clinics ke liye ek **Autonomous AI Voice Receptionist & Clinic Operations Platform** hai.

Is project me:
1. **React 19 Frontend Dashboard (Vite):** Modern, glassmorphic real-time portal (React 19 + Vite + TypeScript + Tailwind) jahan live appointments, emergency alerts, aur metrics dikhte hain.
2. **AI Voice Agent (Vapi.ai):** Patient se natural Hinglish/English me real-time call par baat karta hai.
3. **Modular FastAPI Backend:** Slots calculation, emergency triage detection, clinic pricing, aur appointments booking engine.
4. **Multi-Storage Sync:** Real-time SQLite database cache with 2-way sync to Dental CRM (PostgreSQL) and Google Sheets.

---

## 📁 Architecture & Folder Structure

```text
dental-ai-voice-agent/
├── frontend/                     # Pure React 19 SPA (Vite + Tailwind)
│   ├── src/App.tsx               # Real-time Operations Dashboard
│   ├── src/main.tsx              # React DOM entry point
│   └── src/index.css             # Glassmorphism styling & animations
├── backend/                      # Python FastAPI Modular Backend
│   ├── app/
│   │   ├── main.py               # Clean controller entry point (~55 lines)
│   │   ├── core/                 # App settings & environment config
│   │   ├── db/                   # SQLite connection & schema initialization
│   │   ├── schemas/              # Pydantic validation models
│   │   ├── routers/              # clinics, appointments, crm, simulation, webhooks
│   │   ├── services/             # Pure business rules (slots, triage, booking)
│   │   └── integrations/         # CRM client & Google Sheets service
│   ├── data/dental_saas.db       # Primary SQLite Database
│   └── requirements.txt
├── vapi_config/                  # Vapi AI Voice configuration
│   ├── system_prompt.txt         # Voice Persona & Hinglish conversation guidelines
│   ├── tools_schema.json         # Function calling schema for Vapi tools
│   └── assistant_settings.json   # Telephony voice model settings
└── README.md
```

---

## 🚀 Quickstart (Kaise Run aur Test Karein)

### Step 1: Backend Start Karein (Terminal 1)

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend `http://localhost:8000` par start ho jayega.

---

### Step 2: React Frontend Start Karein (Terminal 2)

Ek nayi terminal window kholein:

```bash
cd frontend
npm run dev
```

Browser me open karein:
👉 **`http://localhost:3000`**

Aapke samne **Dental AI Voice Agent ka Operations Dashboard** khul jayega!

---

### Step 3: Vapi Webhook Connect Karein (Free Cloud URL)

Kyunki Vapi cloud par hai, local server ko public URL assign karein:

```bash
npx localtunnel --port 8000
# Ya ngrok:
# ngrok http 8000
```

Aapka Vapi Webhook URL hoga:
`https://<your-subdomain>.loca.lt/api/vapi/webhook`

---

### Step 4: Vapi.ai me Assistant Setup Karein

1. [Vapi.ai](https://vapi.ai) par login karein.
2. **Create Assistant** par click karein.
3. **Model:** `GPT-4o-mini` select karein.
4. **System Prompt:** `vapi_config/system_prompt.txt` ka text paste karein.
5. **First Message:** 
   `Namaste! Apex Dental Care me aapka swagat hai. Main assistant Aanya bol rahi hu. Main aapki kya madad kar sakti hu?`
6. **Server URL:** Step 3 wala URL daalein (`https://.../api/vapi/webhook`).
7. **Tools:** `vapi_config/tools_schema.json` ke functions add karein (`check_availability`, `book_appointment`, `get_service_pricing`, `check_emergency`).

---

### Step 5: Test Karein (Zero Cost)

1. **Dashboard par test button:** `http://localhost:3000` par **"+ Simulate Live AI Booking"** button dabayein — bina phone call ke turant nayee booking create hogi!
2. **Real Voice Call:** Vapi dashboard me **"Talk to Assistant"** dabakar mic se bolein:
   - *"Namaste, mujhe kal scaling / daant safai karwani hai."*
3. AI appointment book karega, aur **Next.js dashboard par bina refresh kiye live sync ho jayega!**
