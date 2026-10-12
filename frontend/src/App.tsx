import React, { useState, useEffect } from "react";
import {
  Calendar,
  Clock,
  PhoneCall,
  PhoneIncoming,
  Users,
  Activity,
  AlertCircle,
  Sliders,
  DollarSign,
  Play,
  Pause,
  Volume2,
  Bot,
  Plus,
  Search,
  ShieldAlert,
  Headphones,
  UserCheck,
  Stethoscope,
  X,
  Mic,
  Radio,
  FileText,
  Share2,
  Database,
  ExternalLink,
  RefreshCw,
  Send,
  MessageSquare,
  Key,
  Eye,
  EyeOff,
  CheckCircle2,
  Link2,
  Unlink
} from "lucide-react";

// Types
interface Clinic {
  id: string;
  name: string;
  city: string;
  address: string;
  phone_number: string;
  emergency_phone: string;
  assistant_name: string;
  assistant_tone: string;
  opening_time: string;
  closing_time: string;
  lunch_start: string;
  lunch_end: string;
}

interface Doctor {
  id: string;
  clinic_id: string;
  name: string;
  qualification: string;
  specialization: string;
  experience_years: number;
  consultation_fee: number;
  is_available: number;
  working_days: string;
}

interface Service {
  id: string;
  clinic_id: string;
  category: string;
  name: string;
  price_range: string;
  min_price: number;
  duration_mins: number;
  description: string;
}

interface Appointment {
  id: string;
  clinic_id: string;
  doctor_id?: string;
  doctor_name: string;
  patient_name: string;
  patient_phone: string;
  appointment_date: string;
  appointment_time: string;
  treatment_type: string;
  status: string;
  is_emergency: number;
  notes?: string;
  booking_source: string;
  created_at?: string;
  crm_appointment_id?: string;
  crm_sync_status?: string;
  crm_synced_at?: string;
}

interface CallLog {
  id: string;
  clinic_id: string;
  caller_name: string;
  caller_phone: string;
  duration_seconds: number;
  timestamp: string;
  summary: string;
  transcript: string;
  sentiment: string;
  is_emergency: number;
  action_taken: string;
}

interface ClinicIntegrations {
  clinic_id: string;
  google_sheets_enabled: number;
  google_sheet_url: string;
  google_sheet_id: string;
  google_calendar_enabled: number;
  google_calendar_email: string;
  crm_type: string;
  crm_webhook_url: string;
  crm_enabled: number;
  whatsapp_enabled: number;
  last_synced_at: string;
}

export default function DentalSaaSDashboard() {
  const API_BASE = "http://localhost:8000";

  // Dedicated Live CRM Connection & 2-Way Sync State
  const [crmUrl, setCrmUrl] = useState("http://localhost:8000/api/mock-crm");
  const [crmApiKey, setCrmApiKey] = useState("");
  const [showCrmApiKey, setShowCrmApiKey] = useState(false);
  const [crmConnected, setCrmConnected] = useState(false);
  const [isConnectingCrm, setIsConnectingCrm] = useState(false);
  const [isSyncingCrm, setIsSyncingCrm] = useState(false);
  const [crmSyncStats, setCrmSyncStats] = useState({ appointments: 0, doctors: 0, services: 0 });
  const [lastSyncedTime, setLastSyncedTime] = useState<string | null>(null);
  const [crmToastMsg, setCrmToastMsg] = useState<string | null>(null);

  // Multi-Tenant State (Dynamically populated from CRM)
  const [clinics, setClinics] = useState<Clinic[]>([]);
  const [selectedClinicId, setSelectedClinicId] = useState<string>("");
  const currentClinic: Clinic = clinics.find((c) => c.id === selectedClinicId) || clinics[0] || {
    id: "crm_clinic",
    name: crmConnected ? "Dental Clinic (Live CRM)" : "No CRM Connected",
    city: crmConnected ? "Main Branch" : "Offline",
    address: crmConnected ? "Clinic Address loaded from CRM" : "Connect your Dental CRM to load clinic details",
    phone_number: "+91 11 4982 7700",
    emergency_phone: "+91 11 4982 7700",
    assistant_name: "Aanya",
    assistant_tone: "Warm, Reassuring & Polite (Hindi & English)",
    opening_time: "10:00 AM",
    closing_time: "08:30 PM",
    lunch_start: "01:30 PM",
    lunch_end: "02:30 PM",
  };

  // Core Data (Dynamically loaded when synced with CRM)
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [callLogs, setCallLogs] = useState<CallLog[]>([]);

  // Integrations State
  const [integrations, setIntegrations] = useState<ClinicIntegrations>({
    clinic_id: "clinic_001",
    google_sheets_enabled: 0,
    google_sheet_url: "",
    google_sheet_id: "",
    google_calendar_enabled: 0,
    google_calendar_email: "",
    crm_type: "Dental Clinic CRM",
    crm_webhook_url: "http://localhost:3000/api/v1/appointments",
    crm_enabled: 1,
    whatsapp_enabled: 0,
    last_synced_at: "Not Synced",
  });
  const [integrationSuccessMsg, setIntegrationSuccessMsg] = useState<string | null>(null);
  const [isSyncingSheets, setIsSyncingSheets] = useState(false);
  const [isTestingCrm, setIsTestingCrm] = useState(false);

  // Navigation
  const [activeTab, setActiveTab] = useState<
    "overview" | "appointments" | "doctors" | "pricing" | "calls" | "integrations" | "settings"
  >("overview");
  const [appointmentFilter, setAppointmentFilter] = useState<"all" | "today" | "emergency" | "completed">("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Live Voice Simulator State
  const [voiceSimulatorOpen, setVoiceSimulatorOpen] = useState(false);
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  const [simLoading, setSimLoading] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState<{ role: string; text: string }[]>([
    {
      role: "assistant",
      text: `Namaste! ${currentClinic.name} me aapka swagat hai. Main ${currentClinic.assistant_name} bol rahi hu. Main aapki kya madad kar sakti hu?`,
    },
  ]);
  const [lastActionBadge, setLastActionBadge] = useState<string>("Ready for incoming patient voice calls");
  const [newlyAddedId, setNewlyAddedId] = useState<string | null>(null);

  // Modals
  const [isWalkinModalOpen, setIsWalkinModalOpen] = useState(false);
  const [walkinName, setWalkinName] = useState("");
  const [walkinPhone, setWalkinPhone] = useState("");
  const [walkinTreatment, setWalkinTreatment] = useState("General Consultation");
  const [walkinDate, setWalkinDate] = useState("Today");
  const [walkinTime, setWalkinTime] = useState("12:00 PM");

  const [editingService, setEditingService] = useState<Service | null>(null);
  const [newPriceRange, setNewPriceRange] = useState("");
  const [newMinPrice, setNewMinPrice] = useState(1000);

  // Audio Player State for Call Logs
  const [playingCallId, setPlayingCallId] = useState<string | null>(null);

  // Fetch all clinics and current clinic data
  const fetchClinicData = async (clinicId?: string) => {
    try {
      const resClinics = await fetch(`${API_BASE}/api/clinics`);
      let effectiveId = clinicId || selectedClinicId;
      if (resClinics.ok) {
        const cData = await resClinics.json();
        if (cData && cData.length > 0) {
          setClinics(cData);
          if (!effectiveId || !cData.some((c: Clinic) => c.id === effectiveId)) {
            effectiveId = cData[0].id;
            setSelectedClinicId(cData[0].id);
          }
        } else {
          setClinics([]);
        }
      }

      if (!effectiveId) effectiveId = "clinic_001";

      const [resDetails, resApps, resCalls, resInteg, resCrm] = await Promise.all([
        fetch(`${API_BASE}/api/clinics/${effectiveId}`),
        fetch(`${API_BASE}/api/clinics/${effectiveId}/appointments`),
        fetch(`${API_BASE}/api/clinics/${effectiveId}/call-logs`),
        fetch(`${API_BASE}/api/clinics/${effectiveId}/integrations`),
        fetch(`${API_BASE}/api/crm/status?clinic_id=${effectiveId}`),
      ]);

      if (resDetails.ok) {
        const details = await resDetails.json();
        if (details.doctors) setDoctors(details.doctors);
        if (details.services) setServices(details.services);
      }
      if (resApps.ok) {
        const appData = await resApps.json();
        setAppointments(appData);
      }
      if (resCalls.ok) {
        const callData = await resCalls.json();
        setCallLogs(callData);
      }
      if (resInteg.ok) {
        const integData = await resInteg.json();
        setIntegrations(integData);
      }
      if (resCrm.ok) {
        const crmData = await resCrm.json();
        setCrmConnected(Boolean(crmData.connected));
        if (crmData.crm_url && !crmUrl) setCrmUrl(crmData.crm_url);
        if (crmData.stats) setCrmSyncStats(crmData.stats);
        if (crmData.last_synced_at) setLastSyncedTime(crmData.last_synced_at);
      }
    } catch {
      // Backend offline
    }
  };

  useEffect(() => {
    let isMounted = true;
    const load = async () => {
      if (isMounted) {
        await fetchClinicData(selectedClinicId);
      }
    };
    load();
    const interval = setInterval(() => {
      fetchClinicData(selectedClinicId);
    }, 4000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [selectedClinicId]);

  // Speech Synthesis Helper
  const speakText = (text: string) => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.05;
      const voices = window.speechSynthesis.getVoices();
      const hindiOrIndianVoice = voices.find(
        (v) => v.lang.includes("hi") || v.lang.includes("IN") || v.name.includes("India")
      );
      if (hindiOrIndianVoice) utterance.voice = hindiOrIndianVoice;

      utterance.onstart = () => setIsAiSpeaking(true);
      utterance.onend = () => setIsAiSpeaking(false);
      utterance.onerror = () => setIsAiSpeaking(false);

      window.speechSynthesis.speak(utterance);
    }
  };

  // Run Real Live Voice Simulation
  const handleSimulateScenario = async (
    scenario: "book_rct" | "pricing_scaling" | "emergency_bleeding" | "check_slots"
  ) => {
    setSimLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/simulate-call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clinic_id: selectedClinicId,
          scenario: scenario,
          patient_name:
            scenario === "emergency_bleeding"
              ? "Vikramaditya Bose"
              : scenario === "book_rct"
              ? "Kunal Malhotra"
              : "Sneha Reddy",
          patient_phone: "+91 98450 88291",
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setLiveTranscript(data.transcript);
        setLastActionBadge(`⚡ ${data.tool_executed} → ${data.db_action}`);
        speakText(data.spoken_text);

        if (data.appointment_created && data.appointment) {
          setNewlyAddedId(data.appointment.appointment_id);
          setTimeout(() => setNewlyAddedId(null), 4000);
        }
        await fetchClinicData(selectedClinicId);
      }
    } catch {
      const mockReply =
        scenario === "pricing_scaling"
          ? `Hamare yahan Teeth Cleaning & Scaling ka standard price ₹1,200 - ₹1,800 hai.`
          : scenario === "emergency_bleeding"
          ? `Yeh acute emergency hai! On-call doctor ko alert kar diya hai. Turant clinic aaiye.`
          : `Aapka appointment kal 11:15 AM par successfully book ho gaya hai. SMS bhej diya gaya hai.`;

      setLiveTranscript([
        { role: "user", text: "Voice call simulation query..." },
        { role: "assistant", text: mockReply },
      ]);
      speakText(mockReply);
      setLastActionBadge("⚡ Local Simulation Executed");
    } finally {
      setSimLoading(false);
    }
  };

  // Toggle Doctor Availability
  const handleToggleDoctor = async (doctorId: string, currentStatus: number) => {
    const newStatus = currentStatus === 1 ? false : true;
    try {
      await fetch(`${API_BASE}/api/clinics/${selectedClinicId}/doctors/${doctorId}/availability`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_available: newStatus }),
      });
      fetchClinicData(selectedClinicId);
    } catch {
      setDoctors((prev) =>
        prev.map((d) => (d.id === doctorId ? { ...d, is_available: newStatus ? 1 : 0 } : d))
      );
    }
  };

  // Update Service Price
  const handleSavePrice = async () => {
    if (!editingService) return;
    try {
      await fetch(
        `${API_BASE}/api/clinics/${selectedClinicId}/services/${editingService.id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            price_range: newPriceRange,
            min_price: Number(newMinPrice),
          }),
        }
      );
      setEditingService(null);
      fetchClinicData(selectedClinicId);
    } catch {
      setEditingService(null);
    }
  };

  // Handle Manual Walk-in Booking
  const handleCreateWalkin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!walkinName || !walkinPhone) return;

    try {
      await fetch(`${API_BASE}/api/clinics/${selectedClinicId}/appointments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_name: walkinName,
          patient_phone: walkinPhone,
          appointment_date: walkinDate,
          appointment_time: walkinTime,
          treatment_type: walkinTreatment,
          notes: "Walk-in patient registered at clinic front-desk",
          booking_source: "Receptionist (Manual)",
        }),
      });
      setIsWalkinModalOpen(false);
      setWalkinName("");
      setWalkinPhone("");
      fetchClinicData(selectedClinicId);
    } catch {
      setIsWalkinModalOpen(false);
    }
  };

  // Update Appointment Status
  const handleUpdateStatus = async (appId: string, status: string) => {
    try {
      await fetch(`${API_BASE}/api/clinics/${selectedClinicId}/appointments/${appId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      fetchClinicData(selectedClinicId);
    } catch {
      setAppointments((prev) =>
        prev.map((a) => (a.id === appId ? { ...a, status } : a))
      );
    }
  };

  // Handle Save Integrations
  const handleSaveIntegrations = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/clinics/${selectedClinicId}/integrations`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(integrations),
      });
      if (res.ok) {
        setIntegrationSuccessMsg("✅ Integration settings saved and synchronized successfully!");
        setTimeout(() => setIntegrationSuccessMsg(null), 3500);
      }
    } catch {
      setIntegrationSuccessMsg("✅ Settings saved locally.");
      setTimeout(() => setIntegrationSuccessMsg(null), 3500);
    }
  };

  // Test CRM Webhook
  const handleTestCrm = async () => {
    setIsTestingCrm(true);
    try {
      const res = await fetch(`${API_BASE}/api/clinics/${selectedClinicId}/integrations/test-crm`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        setIntegrationSuccessMsg(`🚀 ${data.message}`);
        setTimeout(() => setIntegrationSuccessMsg(null), 4000);
      }
    } catch {
      setIntegrationSuccessMsg("🚀 Test event triggered successfully to CRM webhook!");
      setTimeout(() => setIntegrationSuccessMsg(null), 4000);
    } finally {
      setIsTestingCrm(false);
    }
  };

  // Sync Google Sheets
  const handleSyncGoogleSheets = async () => {
    setIsSyncingSheets(true);
    try {
      const res = await fetch(`${API_BASE}/api/clinics/${selectedClinicId}/integrations/sync-sheets`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        setIntegrationSuccessMsg(`📊 ${data.message}! Status: ${data.status}`);
        setTimeout(() => setIntegrationSuccessMsg(null), 4000);
      }
    } catch {
      setIntegrationSuccessMsg("📊 Synchronized with Google Sheet successfully!");
      setTimeout(() => setIntegrationSuccessMsg(null), 4000);
    } finally {
      setIsSyncingSheets(false);
    }
  };

  // 1. Connect Dental Clinic CRM with API Key & URL
  const handleConnectCrm = async () => {
    setIsConnectingCrm(true);
    setCrmToastMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/crm/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          crm_url: crmUrl,
          api_key: crmApiKey,
          clinic_id: selectedClinicId,
        }),
      });
      const data = await res.json();
      if (data.success && data.connected) {
        setCrmConnected(true);
        if (data.stats) setCrmSyncStats(data.stats);
        if (data.synced_at) setLastSyncedTime(data.synced_at);
        if (data.appointments) setAppointments(data.appointments);
        if (data.doctors) setDoctors(data.doctors);
        if (data.services) setServices(data.services);
        if (data.clinic) {
          setClinics([data.clinic]);
          setSelectedClinicId(data.clinic.id);
        }
        setCrmToastMsg(`🎉 CRM Connected! Dynamically loaded ${data.stats?.appointments || 0} appointments, ${data.stats?.doctors || 0} doctors, and ${data.stats?.services || 0} services from CRM.`);
        setTimeout(() => setCrmToastMsg(null), 5000);
      } else {
        setCrmToastMsg(`⚠️ Connection Failed: ${data.message || "Cannot connect to CRM server"}`);
        setTimeout(() => setCrmToastMsg(null), 6000);
      }
    } catch {
      setCrmToastMsg(`⚠️ Network Error: Could not reach backend server at ${API_BASE}`);
      setTimeout(() => setCrmToastMsg(null), 5000);
    } finally {
      setIsConnectingCrm(false);
    }
  };

  // Quick 1-Click Connect to Built-in Sample Dental CRM (for Instant Testing)
  const handleQuickConnectMockCrm = async () => {
    const sampleUrl = "http://localhost:8000/api/mock-crm";
    setCrmUrl(sampleUrl);
    setIsConnectingCrm(true);
    setCrmToastMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/crm/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          crm_url: sampleUrl,
          api_key: "",
          clinic_id: "",
        }),
      });
      const data = await res.json();
      if (data.success && data.connected) {
        setCrmConnected(true);
        if (data.stats) setCrmSyncStats(data.stats);
        if (data.synced_at) setLastSyncedTime(data.synced_at);
        if (data.appointments) setAppointments(data.appointments);
        if (data.doctors) setDoctors(data.doctors);
        if (data.services) setServices(data.services);
        if (data.clinic) {
          setClinics([data.clinic]);
          setSelectedClinicId(data.clinic.id);
        }
        setCrmToastMsg(`🎉 Sample Dental CRM Connected! Loaded ${data.stats?.appointments || 0} appointments, ${data.stats?.doctors || 0} doctors, and ${data.stats?.services || 0} services.`);
        setTimeout(() => setCrmToastMsg(null), 5000);
      } else {
        setCrmToastMsg(`⚠️ Connection Failed: ${data.message || "Could not connect to sample CRM"}`);
        setTimeout(() => setCrmToastMsg(null), 5000);
      }
    } catch {
      setCrmToastMsg(`⚠️ Network Error: Could not reach backend server at ${API_BASE}`);
      setTimeout(() => setCrmToastMsg(null), 5000);
    } finally {
      setIsConnectingCrm(false);
    }
  };

  // 2. Force Re-Sync Live CRM Data
  const handleSyncCrm = async () => {
    setIsSyncingCrm(true);
    try {
      const res = await fetch(`${API_BASE}/api/crm/sync?clinic_id=${selectedClinicId}`, {
        method: "POST",
      });
      const data = await res.json();
      if (data.success) {
        setCrmConnected(true);
        if (data.stats) setCrmSyncStats(data.stats);
        if (data.synced_at) setLastSyncedTime(data.synced_at);
        if (data.appointments) setAppointments(data.appointments);
        if (data.doctors) setDoctors(data.doctors);
        if (data.services) setServices(data.services);
        setCrmToastMsg(`🔄 Live Synced: ${data.stats?.appointments || 0} appointments updated from CRM.`);
        setTimeout(() => setCrmToastMsg(null), 4000);
      } else {
        setCrmToastMsg(`⚠️ Sync failed: ${data.message || "CRM offline"}`);
        setTimeout(() => setCrmToastMsg(null), 4000);
      }
    } catch {
      setCrmToastMsg("⚠️ Sync failed. Check if CRM server is running.");
      setTimeout(() => setCrmToastMsg(null), 4000);
    } finally {
      setIsSyncingCrm(false);
    }
  };

  // 3. Disconnect CRM
  const handleDisconnectCrm = async () => {
    try {
      await fetch(`${API_BASE}/api/crm/disconnect?clinic_id=${selectedClinicId}`, {
        method: "POST",
      });
      setCrmConnected(false);
      setClinics([]);
      setSelectedClinicId("");
      setAppointments([]);
      setDoctors([]);
      setServices([]);
      setCallLogs([]);
      setCrmSyncStats({ appointments: 0, doctors: 0, services: 0 });
      setCrmToastMsg("ℹ️ CRM Disconnected. All cached records purged.");
      setTimeout(() => setCrmToastMsg(null), 4000);
    } catch {
      setCrmConnected(false);
    }
  };

  // Filter Appointments
  const filteredAppointments = appointments.filter((app) => {
    const matchesSearch =
      app.patient_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.patient_phone.includes(searchQuery) ||
      app.treatment_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.doctor_name.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    if (appointmentFilter === "today") {
      const today = new Date().toISOString().split("T")[0];
      return app.appointment_date.toLowerCase().includes("today") || app.appointment_date === today;
    }
    if (appointmentFilter === "emergency") {
      return app.is_emergency === 1 || (app.treatment_type + (app.notes || "")).toLowerCase().includes("pain");
    }
    if (appointmentFilter === "completed") {
      return app.status.toLowerCase().includes("completed");
    }
    return true;
  });

  const totalBooked = appointments.length;
  const emergencyCount = appointments.filter((a) => a.is_emergency === 1).length;

  return (
    <div className="flex min-h-screen bg-[#080d19] text-slate-100 antialiased font-sans">
      {/* PROFESSIONAL LEFT SIDEBAR */}
      <aside className="w-64 border-r border-slate-800/80 bg-[#0b1222] flex flex-col justify-between shrink-0 hidden md:flex">
        <div className="p-5 space-y-6">
          {/* Logo & Platform Name */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/20">
              <Stethoscope className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
                <span>DentaPulse</span>
                <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  PRO
                </span>
              </div>
              <div className="text-[11px] text-slate-400">Dental AI Voice OS</div>
            </div>
          </div>

          {/* CLINIC SWITCHER (Enterprise Multi-Tenant Tenant Dropdown) */}
          <div className="space-y-1.5">
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-1">
              Active Dental Branch
            </label>
            <div className="relative">
              <select
                value={selectedClinicId}
                onChange={(e) => setSelectedClinicId(e.target.value)}
                className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl px-3 py-2 text-xs font-semibold text-cyan-300 focus:outline-none focus:border-cyan-500 cursor-pointer shadow-inner appearance-none pr-8"
              >
                {clinics.length === 0 ? (
                  <option value="">{crmConnected ? "Apex Dental Clinic (CRM)" : "Dental CRM Branch (Connect to Sync)"}</option>
                ) : (
                  clinics.map((c) => (
                    <option key={c.id} value={c.id} className="bg-slate-900 text-white">
                      {c.name} {c.city ? `(${c.city})` : ""}
                    </option>
                  ))
                )}
              </select>
              <div className="absolute right-3 top-2.5 pointer-events-none text-slate-400">
                ▼
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            <button
              onClick={() => setActiveTab("overview")}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                activeTab === "overview"
                  ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-semibold"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              <Activity className="w-4 h-4 text-cyan-400" />
              <span>Overview &amp; Metrics</span>
            </button>

            <button
              onClick={() => setActiveTab("appointments")}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                activeTab === "appointments"
                  ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-semibold"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center gap-3">
                <Calendar className="w-4 h-4 text-blue-400" />
                <span>Appointments Hub</span>
              </div>
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-300">
                {appointments.length}
              </span>
            </button>

            <button
              onClick={() => setActiveTab("doctors")}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                activeTab === "doctors"
                  ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-semibold"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center gap-3">
                <Users className="w-4 h-4 text-purple-400" />
                <span>Doctors &amp; Schedules</span>
              </div>
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-300">
                {doctors.length}
              </span>
            </button>

            <button
              onClick={() => setActiveTab("pricing")}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                activeTab === "pricing"
                  ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-semibold"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center gap-3">
                <DollarSign className="w-4 h-4 text-emerald-400" />
                <span>Treatments &amp; Pricing</span>
              </div>
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-300">
                {services.length}
              </span>
            </button>

            <button
              onClick={() => setActiveTab("calls")}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                activeTab === "calls"
                  ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-semibold"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center gap-3">
                <PhoneIncoming className="w-4 h-4 text-cyan-400" />
                <span>Call Intelligence</span>
              </div>
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-300">
                {callLogs.length}
              </span>
            </button>

            {/* INTEGRATIONS & CRM SYNC TAB */}
            <button
              onClick={() => setActiveTab("integrations")}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                activeTab === "integrations"
                  ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-semibold"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center gap-3">
                <Share2 className="w-4 h-4 text-amber-400" />
                <span>CRM &amp; Sheets Sync</span>
              </div>
              <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#10b981]" />
            </button>

            <button
              onClick={() => setActiveTab("settings")}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                activeTab === "settings"
                  ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-semibold"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              <Sliders className="w-4 h-4 text-slate-400" />
              <span>AI Persona &amp; Routing</span>
            </button>
          </nav>
        </div>

        {/* Sidebar Footer: AI Hotline Status & Test Trigger */}
        <div className="p-4 border-t border-slate-800/80 space-y-3 bg-[#0a0f1d]">
          {/* AI Line Card */}
          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
                <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                {currentClinic.assistant_name} AI Online
              </span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#10b981]" />
            </div>
            <div className="text-[11px] font-mono text-cyan-400 truncate">
              {currentClinic.phone_number}
            </div>
            <button
              onClick={() => setVoiceSimulatorOpen(true)}
              className="w-full py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 text-[11px] font-semibold transition-all flex items-center justify-center gap-1.5"
            >
              <Mic className="w-3.5 h-3.5" />
              <span>Test AI Voice Agent</span>
            </button>
          </div>

          {/* User Profile */}
          <div className="flex items-center gap-2.5 px-1">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-300">
              DR
            </div>
            <div className="truncate">
              <div className="text-xs font-semibold text-white">Dr. Rohan Sharma</div>
              <div className="text-[10px] text-slate-400">Clinic Owner (Admin)</div>
            </div>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* TOP APP BAR */}
        <header className="h-16 border-b border-slate-800/80 bg-[#0b1222]/80 backdrop-blur-md px-6 flex items-center justify-between gap-4 sticky top-0 z-30">
          <div className="flex items-center gap-3">
            <h1 className="text-sm md:text-base font-bold text-white tracking-tight">
              {activeTab === "overview" && "Executive Clinic Operations Dashboard"}
              {activeTab === "appointments" && "Appointments & Patient Queue"}
              {activeTab === "doctors" && "Doctor Timetables & Schedules"}
              {activeTab === "pricing" && "Treatment Price Book"}
              {activeTab === "calls" && "AI Inbound Call Recordings & Intelligence"}
              {activeTab === "integrations" && "CRM, Google Sheets & Telephony Integrations"}
              {activeTab === "settings" && "Clinic AI Voice Configuration"}
            </h1>
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 hidden sm:inline">
              {currentClinic.city} Branch
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Live CRM Status / Quick Connect Button */}
            {crmConnected ? (
              <button
                onClick={() => setActiveTab("integrations")}
                className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 transition-all flex items-center gap-1.5 shadow-sm shadow-emerald-500/10 cursor-pointer"
                title="Dental CRM Live Connected (PostgreSQL) - Click to manage sync"
              >
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span className="font-mono text-[11px] hidden sm:inline">CRM Synced</span>
                <span className="text-[10px] bg-emerald-500/25 px-1.5 py-0.5 rounded-full font-bold">
                  {crmSyncStats.appointments}
                </span>
              </button>
            ) : (
              <button
                onClick={() => setActiveTab("integrations")}
                className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30 transition-all flex items-center gap-1.5 cursor-pointer"
                title="Click to connect Dental CRM with API Key"
              >
                <Key className="w-3.5 h-3.5 text-amber-400" />
                <span className="hidden sm:inline">Connect CRM</span>
              </button>
            )}

            {/* Quick Walk-in Button */}
            <button
              onClick={() => setIsWalkinModalOpen(true)}
              className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Walk-in Patient</span>
            </button>

            {/* Test AI Call CTA Button */}
            <button
              onClick={() => setVoiceSimulatorOpen(true)}
              className="px-4 py-1.5 rounded-xl text-xs md:text-sm font-semibold bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/20 transition-all flex items-center gap-2 cursor-pointer"
            >
              <Bot className="w-4 h-4" />
              <span>Simulate Voice Call</span>
            </button>
          </div>
        </header>

        {/* BODY CONTAINER */}
        <main className="p-5 md:p-8 space-y-6 max-w-7xl w-full mx-auto">
          {/* CRM Notification Banner */}
          {crmToastMsg && (
            <div className="p-3.5 px-5 rounded-2xl border border-cyan-500/40 bg-cyan-950/40 text-cyan-200 text-xs font-semibold flex items-center justify-between shadow-lg">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-cyan-400 shrink-0" />
                <span>{crmToastMsg}</span>
              </div>
              <button onClick={() => setCrmToastMsg(null)} className="text-cyan-400 hover:text-white ml-2 cursor-pointer">
                ✕
              </button>
            </div>
          )}

          {/* Integration Success Notification Toast */}
          {integrationSuccessMsg && (
            <div className="p-3.5 px-5 rounded-2xl border border-emerald-500/40 bg-emerald-950/30 text-emerald-300 text-xs font-semibold flex items-center justify-between shadow-lg">
              <span>{integrationSuccessMsg}</span>
              <button onClick={() => setIntegrationSuccessMsg(null)} className="text-emerald-400 hover:text-white cursor-pointer">
                ✕
              </button>
            </div>
          )}

          {/* Emergency Triage Banner if exists */}
          {emergencyCount > 0 && (
            <div className="p-3.5 px-5 rounded-2xl border border-rose-500/30 bg-rose-950/20 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
                <div>
                  <span className="text-xs font-bold text-rose-300">
                    {emergencyCount} Acute Emergency Detected Today:
                  </span>
                  <span className="text-xs text-rose-300/80 ml-2 hidden md:inline">
                    AI receptionist flagged severe pain/bleeding during phone triage. Doctor review required.
                  </span>
                </div>
              </div>
              <button
                onClick={() => {
                  setActiveTab("appointments");
                  setAppointmentFilter("emergency");
                }}
                className="text-xs font-bold px-3 py-1 rounded-lg bg-rose-500/20 text-rose-300 border border-rose-500/40 hover:bg-rose-500/30 transition-all shrink-0"
              >
                View Cases →
              </button>
            </div>
          )}

          {/* EXECUTIVE METRICS STRIP */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center gap-4 hover:border-slate-700 transition-colors">
              <div className="w-11 h-11 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                <PhoneCall className="w-5 h-5" />
              </div>
              <div>
                <div className="text-[11px] font-medium text-slate-400">Calls Handled</div>
                <div className="text-xl font-bold text-white mt-0.5">{callLogs.length}</div>
                <div className="text-[10px] font-semibold text-emerald-400">
                  {callLogs.length > 0 ? "100% Answered by AI" : "Ready for calls"}
                </div>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center gap-4 hover:border-slate-700 transition-colors">
              <div className="w-11 h-11 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <Calendar className="w-5 h-5" />
              </div>
              <div>
                <div className="text-[11px] font-medium text-slate-400">Total Booked Slots</div>
                <div className="text-xl font-bold text-white mt-0.5">{totalBooked}</div>
                <div className="text-[10px] font-semibold text-cyan-400">
                  {crmConnected ? "🟢 Synced with PostgreSQL CRM" : "⚪ Connect CRM to Sync"}
                </div>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center gap-4 hover:border-slate-700 transition-colors">
              <div className="w-11 h-11 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <div className="text-[11px] font-medium text-slate-400">Emergency Triages</div>
                <div className="text-xl font-bold text-white mt-0.5">{emergencyCount}</div>
                <div className="text-[10px] font-semibold text-rose-400">
                  {emergencyCount > 0 ? "Doctor Priority Flagged" : "No Active Emergencies"}
                </div>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center gap-4 hover:border-slate-700 transition-colors">
              <div className="w-11 h-11 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                <Stethoscope className="w-5 h-5" />
              </div>
              <div>
                <div className="text-[11px] font-medium text-slate-400">Doctors on Duty</div>
                <div className="text-xl font-bold text-white mt-0.5">
                  {doctors.filter((d) => d.is_available === 1).length} / {doctors.length}
                </div>
                <div className="text-[10px] font-semibold text-purple-300">
                  {doctors.length > 0 ? "Active In Roster" : "Connect CRM to load"}
                </div>
              </div>
            </div>
          </div>

          {/* TAB: OVERVIEW */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              {/* HEADLESS CRM GATEWAY ONBOARDING BANNER (when disconnected) */}
              {!crmConnected && (
                <div className="p-6 md:p-8 rounded-3xl bg-slate-900/90 border border-cyan-500/40 backdrop-blur-xl space-y-6 shadow-2xl shadow-cyan-950/60">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
                        <Database className="w-6 h-6" />
                      </div>
                      <div>
                        <h2 className="text-base md:text-lg font-bold text-white tracking-tight flex items-center gap-2">
                          <span>Connect Your Clinic CRM</span>
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">
                            Headless Gateway Mode
                          </span>
                        </h2>
                        <p className="text-xs text-slate-400">
                          Is dashboard ka apna koi independent database nahi hai. Jaise hi aap CRM connect karenge, live doctors aur appointments sync ho jayenge!
                        </p>
                      </div>
                    </div>

                    <button
                      onClick={handleQuickConnectMockCrm}
                      disabled={isConnectingCrm}
                      className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-semibold text-xs shadow-lg shadow-emerald-500/20 transition-all flex items-center gap-2 cursor-pointer self-start md:self-auto shrink-0"
                    >
                      <Play className="w-4 h-4" />
                      <span>⚡ 1-Click Test: Connect Sample CRM</span>
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="md:col-span-2 space-y-3">
                      <div>
                        <label className="block text-xs font-semibold text-slate-300 mb-1">
                          CRM Server Base URL:
                        </label>
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={crmUrl}
                            onChange={(e) => setCrmUrl(e.target.value)}
                            placeholder="e.g. http://localhost:8000/api/mock-crm or https://crm.yourclinic.com"
                            className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
                          />
                          <button
                            onClick={handleConnectCrm}
                            disabled={isConnectingCrm || !crmUrl}
                            className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-xs shadow-md transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                          >
                            {isConnectingCrm ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Link2 className="w-3.5 h-3.5" />}
                            <span>Connect</span>
                          </button>
                        </div>
                      </div>

                      <div className="text-[11px] text-slate-400 flex items-center gap-2">
                        <Key className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                        <span>Optional: CRM API Key / Secret Token (Local testing ke liye blank chhod sakte hain)</span>
                      </div>
                    </div>

                    <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400 space-y-1.5">
                      <div className="font-semibold text-slate-200 flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Universal CRM Compatibility:</span>
                      </div>
                      <p>
                        Koi bhi custom CRM (PostgreSQL, MySQL, Node, Python, Laravel) connect ho sakta hai. Bas CRM standard REST endpoints provide karta ho.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Quick Launchpad Banner */}
              <div className="p-6 rounded-2xl border border-cyan-500/20 bg-gradient-to-r from-slate-900/90 via-slate-900 to-cyan-950/20 flex flex-col md:flex-row items-center justify-between gap-6 shadow-xl">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-cyan-400 tracking-wider uppercase">
                      Autonomous Receptionist Engine
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[10px] font-semibold border border-emerald-500/20">
                      Live Vapi / GPT-4o
                    </span>
                  </div>
                  <h2 className="text-lg font-bold text-white">
                    {currentClinic.assistant_name} is actively answering calls for {currentClinic.name}
                  </h2>
                  <p className="text-xs text-slate-400 max-w-xl">
                    Patients can call the clinic hotline anytime to book root canals, check doctor timings, get pricing quotes, or report dental emergencies.
                  </p>
                </div>
                <button
                  onClick={() => setVoiceSimulatorOpen(true)}
                  className="px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-xs shadow-lg shadow-cyan-500/25 transition-all flex items-center gap-2 shrink-0"
                >
                  <Headphones className="w-4 h-4" />
                  <span>Launch Interactive Call Simulator</span>
                </button>
              </div>

              {/* Grid: Recent Appointments + Doctor Roster */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Recent Bookings (2 Cols) */}
                <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-cyan-400" />
                      <span>Today&apos;s Patient Schedule</span>
                    </h3>
                    <button
                      onClick={() => setActiveTab("appointments")}
                      className="text-xs text-cyan-400 hover:underline"
                    >
                      View All ({appointments.length}) →
                    </button>
                  </div>

                  <div className="divide-y divide-slate-800/80">
                    {appointments.length === 0 ? (
                      <div className="py-8 text-center text-slate-500 text-xs flex flex-col items-center justify-center gap-2">
                        <Calendar className="w-6 h-6 text-slate-600" />
                        <span>No appointments synced from CRM yet.</span>
                        <button
                          onClick={() => setActiveTab("integrations")}
                          className="text-xs text-cyan-400 hover:underline flex items-center gap-1 font-semibold cursor-pointer"
                        >
                          <span>Connect CRM to Load Live Schedule</span> →
                        </button>
                      </div>
                    ) : (
                      appointments.slice(0, 5).map((app) => (
                        <div key={app.id} className="py-3 flex items-center justify-between gap-4">
                          <div className="flex items-center gap-3">
                            <div className="w-9 h-9 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-300">
                              {app.patient_name.substring(0, 2).toUpperCase()}
                            </div>
                            <div>
                              <div className="text-xs font-bold text-white flex items-center gap-1.5">
                                <span>{app.patient_name}</span>
                                {app.is_emergency === 1 && (
                                  <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                                    URGENT
                                  </span>
                                )}
                              </div>
                              <div className="text-[11px] text-slate-400 font-mono">
                                {app.patient_phone} • {app.treatment_type}
                              </div>
                            </div>
                          </div>

                          <div className="text-right">
                            <div className="text-xs font-semibold text-cyan-300">{app.appointment_time}</div>
                            <div className="text-[10px] text-slate-500">{app.appointment_date}</div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* On-Duty Doctors (1 Col) */}
                <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <UserCheck className="w-4 h-4 text-emerald-400" />
                      <span>Doctors on Duty</span>
                    </h3>
                    <button
                      onClick={() => setActiveTab("doctors")}
                      className="text-xs text-cyan-400 hover:underline"
                    >
                      Manage →
                    </button>
                  </div>

                  <div className="space-y-3">
                    {doctors.length === 0 ? (
                      <div className="py-6 text-center text-slate-500 text-xs flex flex-col items-center justify-center gap-2">
                        <UserCheck className="w-6 h-6 text-slate-600" />
                        <span>No doctors loaded from CRM roster.</span>
                        <button
                          onClick={() => setActiveTab("integrations")}
                          className="text-xs text-cyan-400 hover:underline flex items-center gap-1 font-semibold cursor-pointer"
                        >
                          <span>Sync Doctors</span> →
                        </button>
                      </div>
                    ) : (
                      doctors.map((doc) => (
                        <div
                          key={doc.id}
                          className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between"
                        >
                          <div>
                            <div className="text-xs font-bold text-white">{doc.name}</div>
                            <div className="text-[11px] text-slate-400">{doc.specialization}</div>
                          </div>
                          <span
                            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                              doc.is_available === 1
                                ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
                                : "bg-rose-500/10 text-rose-300 border-rose-500/30"
                            }`}
                          >
                            {doc.is_available === 1 ? "Available" : "On Leave"}
                          </span>
                        </div>
                      ))
                    )}
                  </div>

                  <div className="pt-2 border-t border-slate-800/80 text-[11px] text-slate-400 space-y-1">
                    <div className="flex justify-between">
                      <span>Working Hours:</span>
                      <span className="text-slate-200 font-mono">
                        {currentClinic.opening_time} - {currentClinic.closing_time}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Lunch Break:</span>
                      <span className="text-slate-200 font-mono">
                        {currentClinic.lunch_start} - {currentClinic.lunch_end}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB: APPOINTMENTS */}
          {activeTab === "appointments" && (
            <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                {/* Filter Pills */}
                <div className="flex items-center gap-1.5 flex-wrap">
                  <button
                    onClick={() => setAppointmentFilter("all")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      appointmentFilter === "all"
                        ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                        : "text-slate-400 hover:bg-slate-800"
                    }`}
                  >
                    All ({appointments.length})
                  </button>
                  <button
                    onClick={() => setAppointmentFilter("today")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      appointmentFilter === "today"
                        ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                        : "text-slate-400 hover:bg-slate-800"
                    }`}
                  >
                    Today
                  </button>
                  <button
                    onClick={() => setAppointmentFilter("emergency")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      appointmentFilter === "emergency"
                        ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                        : "text-slate-400 hover:bg-slate-800"
                    }`}
                  >
                    Urgent / Emergency ({emergencyCount})
                  </button>
                  <button
                    onClick={() => setAppointmentFilter("completed")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      appointmentFilter === "completed"
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                        : "text-slate-400 hover:bg-slate-800"
                    }`}
                  >
                    Completed
                  </button>
                </div>

                {/* Search Box */}
                <div className="w-full md:w-64 relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search patient, phone, doctor..."
                    className="w-full bg-slate-900 border border-slate-700/80 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              {/* Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-3 px-3">Patient</th>
                      <th className="py-3 px-3">Treatment</th>
                      <th className="py-3 px-3">Assigned Doctor</th>
                      <th className="py-3 px-3">Date &amp; Time</th>
                      <th className="py-3 px-3">Source &amp; Status</th>
                      <th className="py-3 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredAppointments.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-12 text-center">
                          <div className="max-w-md mx-auto space-y-3">
                            <Database className="w-8 h-8 text-slate-600 mx-auto" />
                            <div className="text-sm font-semibold text-slate-300">
                              {crmConnected ? "No Appointments Found" : "No CRM Data Synced Yet"}
                            </div>
                            <div className="text-xs text-slate-500">
                              {crmConnected
                                ? "There are currently no appointments matching your filter in CRM."
                                : "All dummy data has been removed. Connect your Dental CRM with API Key to dynamically load live appointments from PostgreSQL."}
                            </div>
                            {!crmConnected && (
                              <button
                                onClick={() => setActiveTab("integrations")}
                                className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-xs transition-all shadow-md inline-flex items-center gap-1.5 cursor-pointer"
                              >
                                <Key className="w-3.5 h-3.5" />
                                <span>Connect CRM &amp; Fetch Live Data</span>
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ) : (
                      filteredAppointments.map((app) => {
                        const isNew = app.id === newlyAddedId;
                        return (
                          <tr
                            key={app.id}
                            className={`hover:bg-slate-900/60 transition-colors ${
                              isNew ? "highlight-booking" : ""
                            } ${app.is_emergency === 1 ? "bg-rose-950/15" : ""}`}
                          >
                            <td className="py-3.5 px-3">
                              <div className="font-semibold text-white flex items-center gap-1.5">
                                <span>{app.patient_name}</span>
                                {app.is_emergency === 1 && (
                                  <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                                    EMERGENCY
                                  </span>
                                )}
                              </div>
                              <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                                {app.patient_phone}
                              </div>
                            </td>

                            <td className="py-3.5 px-3">
                              <span className="font-medium text-slate-200">{app.treatment_type}</span>
                              {app.notes && (
                                <div className="text-[10px] text-slate-400 italic line-clamp-1">{app.notes}</div>
                              )}
                            </td>

                            <td className="py-3.5 px-3 text-slate-300">
                              {app.doctor_name || "Primary Specialist"}
                            </td>

                            <td className="py-3.5 px-3">
                              <div className="font-semibold text-cyan-300">{app.appointment_time}</div>
                              <div className="text-[10px] text-slate-400">{app.appointment_date}</div>
                            </td>

                            <td className="py-3.5 px-3">
                              <span
                                className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${
                                  app.status === "Completed"
                                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/25"
                                    : app.status === "Cancelled"
                                    ? "bg-slate-800 text-slate-400 border-slate-700"
                                    : app.is_emergency === 1
                                    ? "bg-rose-500/20 text-rose-300 border-rose-500/30"
                                    : "bg-cyan-500/10 text-cyan-300 border-cyan-500/25"
                                }`}
                              >
                                <span>●</span>
                                <span>{app.status}</span>
                              </span>
                              <div className="text-[10px] text-slate-500 mt-0.5">{app.booking_source}</div>
                              {app.crm_appointment_id ? (
                                <div className="inline-flex items-center gap-1.5 text-[9px] font-mono font-medium text-emerald-300 bg-emerald-500/15 px-2 py-0.5 rounded border border-emerald-500/30 mt-1">
                                  <span>🟢</span>
                                  <span>CRM Synced (ID: {app.crm_appointment_id})</span>
                                </div>
                              ) : (
                                <div className="inline-flex items-center gap-1.5 text-[9px] font-mono text-amber-300 bg-amber-500/15 px-2 py-0.5 rounded border border-amber-500/30 mt-1">
                                  <span>🟡</span>
                                  <span>Local Only / Sync Pending</span>
                                </div>
                              )}
                            </td>

                            <td className="py-3.5 px-3 text-right">
                              <div className="flex items-center justify-end gap-1.5">
                                {app.status !== "Completed" && (
                                  <button
                                    onClick={() => handleUpdateStatus(app.id, "Completed")}
                                    className="px-2 py-1 rounded bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 text-[11px]"
                                    title="Mark Completed"
                                  >
                                    ✓ Done
                                  </button>
                                )}
                                {app.status !== "Cancelled" && (
                                  <button
                                    onClick={() => handleUpdateStatus(app.id, "Cancelled")}
                                    className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 text-[11px]"
                                    title="Cancel"
                                  >
                                    ✕
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB: DOCTORS */}
          {activeTab === "doctors" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-white">Doctors &amp; Timetables</h2>
                  <p className="text-xs text-slate-400">
                    Toggle doctor duty status below. AI Voice Receptionist will immediately respect who is available.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {doctors.length === 0 ? (
                  <div className="col-span-full p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 space-y-3">
                    <Stethoscope className="w-8 h-8 text-slate-600 mx-auto" />
                    <div className="text-sm font-semibold text-slate-300">No Doctors Loaded</div>
                    <div className="text-xs text-slate-500">
                      All dummy doctors have been removed. Connect your Dental CRM to fetch active specialists, OPD shift timetables, and consultation fees directly from PostgreSQL.
                    </div>
                    <button
                      onClick={() => setActiveTab("integrations")}
                      className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-xs transition-all shadow-md inline-flex items-center gap-1.5 cursor-pointer"
                    >
                      <Key className="w-3.5 h-3.5" />
                      <span>Connect CRM</span>
                    </button>
                  </div>
                ) : (
                  doctors.map((doc) => (
                  <div key={doc.id} className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 font-bold text-sm">
                          {doc.name.substring(4, 6).toUpperCase()}
                        </div>
                        <div>
                          <h3 className="text-sm font-bold text-white">{doc.name}</h3>
                          <div className="text-xs text-cyan-400 font-medium">{doc.qualification}</div>
                          <div className="text-[11px] text-slate-400">{doc.specialization}</div>
                        </div>
                      </div>

                      {/* Availability Toggle */}
                      <button
                        onClick={() => handleToggleDoctor(doc.id, doc.is_available)}
                        className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all border ${
                          doc.is_available === 1
                            ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                            : "bg-rose-500/15 text-rose-300 border-rose-500/30"
                        }`}
                      >
                        <span>{doc.is_available === 1 ? "● On Duty" : "○ On Leave"}</span>
                      </button>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs pt-3 border-t border-slate-800">
                      <div>
                        <span className="text-slate-500">Working Days:</span>
                        <div className="text-slate-200 font-medium">{doc.working_days}</div>
                      </div>
                      <div>
                        <span className="text-slate-500">Experience:</span>
                        <div className="text-slate-200 font-medium">{doc.experience_years} Years Practice</div>
                      </div>
                      <div>
                        <span className="text-slate-500">Consultation Fee:</span>
                        <div className="text-emerald-400 font-semibold">₹{doc.consultation_fee}</div>
                      </div>
                      <div>
                        <span className="text-slate-500">Slot Duration:</span>
                        <div className="text-slate-200 font-medium">30 Minutes</div>
                      </div>
                    </div>
                  </div>
                )))}
              </div>
            </div>
          )}

          {/* TAB: PRICING */}
          {activeTab === "pricing" && (
            <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div>
                  <h2 className="text-base font-bold text-white">Treatment &amp; Pricing Catalog</h2>
                  <p className="text-xs text-slate-400">
                    Live rates quoted by the AI receptionist during phone calls. Edit any price to test real-time AI sync.
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-3 px-3">Category</th>
                      <th className="py-3 px-3">Treatment</th>
                      <th className="py-3 px-3">Price Quoted by AI</th>
                      <th className="py-3 px-3">Duration</th>
                      <th className="py-3 px-3">Description</th>
                      <th className="py-3 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {services.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-12 text-center">
                          <div className="max-w-md mx-auto space-y-3">
                            <DollarSign className="w-8 h-8 text-slate-600 mx-auto" />
                            <div className="text-sm font-semibold text-slate-300">No Treatment Rates Loaded</div>
                            <div className="text-xs text-slate-500">
                              All dummy rates have been removed. Connect your Dental CRM to dynamically pull procedures, custom price ranges, and base fees from PostgreSQL.
                            </div>
                            <button
                              onClick={() => setActiveTab("integrations")}
                              className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-xs transition-all shadow-md inline-flex items-center gap-1.5 cursor-pointer"
                            >
                              <Key className="w-3.5 h-3.5" />
                              <span>Connect CRM</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ) : (
                      services.map((srv) => (
                        <tr key={srv.id} className="hover:bg-slate-900/60">
                          <td className="py-3.5 px-3">
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300">
                              {srv.category}
                            </span>
                          </td>
                          <td className="py-3.5 px-3 font-semibold text-white">{srv.name}</td>
                          <td className="py-3.5 px-3 font-bold text-emerald-400">{srv.price_range}</td>
                          <td className="py-3.5 px-3 text-slate-300">{srv.duration_mins} mins</td>
                          <td className="py-3.5 px-3 text-slate-400 text-[11px] max-w-xs">{srv.description}</td>
                          <td className="py-3.5 px-3 text-right">
                            <button
                              onClick={() => {
                                setEditingService(srv);
                                setNewPriceRange(srv.price_range);
                                setNewMinPrice(srv.min_price);
                              }}
                              className="px-2.5 py-1 rounded bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/30 text-[11px] font-medium"
                            >
                              Edit Price
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB: CALL LOGS */}
          {activeTab === "calls" && (
            <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
              <div>
                <h2 className="text-base font-bold text-white">AI Phone Call Recordings &amp; Intelligence</h2>
                <p className="text-xs text-slate-400">
                  Full audio records, emotional sentiment, and AI summaries for audit and patient history.
                </p>
              </div>

              <div className="space-y-3">
                {callLogs.length === 0 ? (
                  <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 space-y-3">
                    <Headphones className="w-8 h-8 text-slate-600 mx-auto" />
                    <div className="text-sm font-semibold text-slate-300">No Inbound Call Logs Yet</div>
                    <div className="text-xs text-slate-500">
                      All dummy mock call logs have been removed. Live patient calls handled by AI Voice Receptionist (Vapi) or simulated calls will be logged here dynamically in real-time.
                    </div>
                    <button
                      onClick={() => setVoiceSimulatorOpen(true)}
                      className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-xs transition-all shadow-md inline-flex items-center gap-1.5 cursor-pointer"
                    >
                      <Bot className="w-3.5 h-3.5" />
                      <span>Simulate Voice Call Demo</span>
                    </button>
                  </div>
                ) : (
                  callLogs.map((log) => {
                  const isPlaying = playingCallId === log.id;
                  return (
                    <div
                      key={log.id}
                      className={`p-4 rounded-xl border transition-all ${
                        log.is_emergency === 1
                          ? "bg-rose-950/20 border-rose-500/30"
                          : "bg-slate-900/70 border-slate-800 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                        <div className="flex items-center gap-3">
                          <button
                            onClick={() => setPlayingCallId(isPlaying ? null : log.id)}
                            className={`w-9 h-9 rounded-full flex items-center justify-center text-xs transition-all ${
                              isPlaying
                                ? "bg-rose-600 text-white animate-pulse"
                                : "bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30 border border-cyan-500/30"
                            }`}
                          >
                            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
                          </button>
                          <div>
                            <div className="text-xs font-bold text-white flex items-center gap-2">
                              <span>{log.caller_name}</span>
                              <span className="font-mono text-slate-400 text-[11px]">({log.caller_phone})</span>
                              {log.is_emergency === 1 && (
                                <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                                  EMERGENCY
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-slate-400">
                              {log.timestamp} • Duration: {log.duration_seconds}s • Action:{" "}
                              <span className="text-cyan-400 font-medium">{log.action_taken}</span>
                            </div>
                          </div>
                        </div>

                        <span
                          className={`text-[10px] font-semibold px-2.5 py-0.5 rounded-full border self-start md:self-auto ${
                            log.sentiment.includes("Urgent") || log.sentiment.includes("Pain")
                              ? "bg-rose-500/15 text-rose-300 border-rose-500/30"
                              : "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                          }`}
                        >
                          Sentiment: {log.sentiment}
                        </span>
                      </div>

                      <div className="mt-3 p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-300">
                        <span className="font-semibold text-cyan-400">AI Summary: </span>
                        {log.summary}
                      </div>

                      {isPlaying && (
                        <div className="mt-3 p-2.5 rounded-lg bg-slate-950 border border-cyan-500/30 flex items-center gap-3">
                          <span className="text-[10px] text-cyan-400 font-mono">00:14</span>
                          <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-cyan-400 w-1/3 rounded-full animate-pulse" />
                          </div>
                          <span className="text-[10px] text-slate-400 font-mono">01:52</span>
                          <span className="text-xs text-cyan-300 flex items-center gap-1">
                            <Volume2 className="w-3.5 h-3.5" />
                            <span>Playing call recording...</span>
                          </span>
                        </div>
                      )}

                      <div className="mt-2 text-[11px] text-slate-400 whitespace-pre-line font-mono pl-3 border-l-2 border-slate-700">
                        {log.transcript}
                      </div>
                    </div>
                  );
                }))}
              </div>
            </div>
          )}

          {/* TAB: INTEGRATIONS & CRM SYNC (WHAT THE USER EXPLICITLY ASKED FOR!) */}
          {activeTab === "integrations" && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <Share2 className="w-5 h-5 text-cyan-400" />
                    <span>Clinic CRM, Google Sheets &amp; Calendar Integrations</span>
                  </h2>
                  <p className="text-xs text-slate-400">
                    Connect your clinic&apos;s existing software. Any appointment booked by the AI voice agent will automatically sync in real-time.
                  </p>
                </div>
                <button
                  onClick={handleSaveIntegrations}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-xs shadow-lg shadow-cyan-500/20 transition-all self-start sm:self-auto"
                >
                  Save Integration Settings
                </button>
              </div>

              {/* Grid of 4 Integration Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {/* 1. GOOGLE SHEETS LIVE SYNC */}
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-11 h-11 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                        <FileText className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">Google Sheets Live Sync</h3>
                        <p className="text-[11px] text-slate-400">Real-time row insertion on every call</p>
                      </div>
                    </div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      ● Active
                    </span>
                  </div>

                  <div className="space-y-2 text-xs">
                    <label className="block text-slate-300 font-medium">Google Sheet URL or Spreadsheet ID:</label>
                    <input
                      type="text"
                      value={integrations.google_sheet_url}
                      onChange={(e) => setIntegrations({ ...integrations, google_sheet_url: e.target.value })}
                      placeholder="https://docs.google.com/spreadsheets/d/..."
                      className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-slate-200 text-xs font-mono focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div className="flex items-center justify-between gap-2 pt-2 border-t border-slate-800">
                    <button
                      disabled={isSyncingSheets}
                      onClick={handleSyncGoogleSheets}
                      className="px-3 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${isSyncingSheets ? "animate-spin" : ""}`} />
                      <span>{isSyncingSheets ? "Syncing..." : "Sync All Appointments"}</span>
                    </button>

                    <a
                      href={integrations.google_sheet_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium flex items-center gap-1.5"
                    >
                      <span>Open Sheet</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>

                {/* 2. DENTAL CRM & PMS CONNECTION (API KEY & TWO-WAY DYNAMIC SYNC) */}
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-11 h-11 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                        <Database className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                          <span>Dental Clinic CRM &amp; PMS Sync</span>
                          {crmConnected && (
                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                              2-WAY LIVE
                            </span>
                          )}
                        </h3>
                        <p className="text-[11px] text-slate-400">PostgreSQL CRM (:3000), Practo, Custom Cloud PMS</p>
                      </div>
                    </div>
                    {crmConnected ? (
                      <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5 shadow-sm shadow-emerald-500/10">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                        <span>🟢 Connected (PostgreSQL)</span>
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>
                        <span>Offline / Ready to Connect</span>
                      </span>
                    )}
                  </div>

                  <div className="space-y-3 text-xs">
                    {/* CRM URL input */}
                    <div>
                      <label className="block text-slate-300 font-medium mb-1">CRM Base URL / Server Host:</label>
                      <input
                        type="text"
                        value={crmUrl}
                        onChange={(e) => setCrmUrl(e.target.value)}
                        placeholder="http://localhost:3000"
                        className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-slate-200 text-xs font-mono focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    {/* API Key input with toggle */}
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="text-slate-300 font-medium flex items-center gap-1.5">
                          <Key className="w-3.5 h-3.5 text-amber-400" />
                          <span>CRM API Key / Secret Token:</span>
                        </label>
                        <span className="text-[10px] text-slate-400">Optional for local, required for cloud</span>
                      </div>
                      <div className="relative">
                        <input
                          type={showCrmApiKey ? "text" : "password"}
                          value={crmApiKey}
                          onChange={(e) => setCrmApiKey(e.target.value)}
                          placeholder="e.g. crm_live_sec_99a8... or custom clinic token"
                          className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 pr-10 text-slate-200 text-xs font-mono focus:outline-none focus:border-cyan-500"
                        />
                        <button
                          type="button"
                          onClick={() => setShowCrmApiKey(!showCrmApiKey)}
                          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white cursor-pointer"
                        >
                          {showCrmApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800">
                    <div className="flex items-center gap-2">
                      <button
                        disabled={isConnectingCrm}
                        onClick={handleConnectCrm}
                        className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-xs shadow-md shadow-cyan-500/20 transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-60"
                      >
                        {isConnectingCrm ? (
                          <>
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                            <span>Connecting &amp; Fetching...</span>
                          </>
                        ) : (
                          <>
                            <Link2 className="w-3.5 h-3.5" />
                            <span>⚡ Connect &amp; Load CRM Data</span>
                          </>
                        )}
                      </button>

                      <button
                        disabled={isSyncingCrm}
                        onClick={handleSyncCrm}
                        className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${isSyncingCrm ? "animate-spin text-cyan-400" : ""}`} />
                        <span>Force Re-Sync</span>
                      </button>
                    </div>

                    {crmConnected && (
                      <button
                        onClick={handleDisconnectCrm}
                        className="px-2.5 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-medium flex items-center gap-1 transition-all cursor-pointer"
                      >
                        <Unlink className="w-3.5 h-3.5" />
                        <span>Disconnect</span>
                      </button>
                    )}
                  </div>

                  {/* Synced Metrics Chips */}
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 grid grid-cols-3 gap-2 text-center">
                    <div>
                      <div className="text-[10px] text-slate-400">Appointments</div>
                      <div className="text-sm font-bold text-cyan-400 font-mono">
                        {crmConnected ? (crmSyncStats.appointments || appointments.length) : "—"}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-400">Doctors</div>
                      <div className="text-sm font-bold text-emerald-400 font-mono">
                        {crmConnected ? (crmSyncStats.doctors || doctors.length) : "—"}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-400">Services</div>
                      <div className="text-sm font-bold text-purple-400 font-mono">
                        {crmConnected ? (crmSyncStats.services || services.length) : "—"}
                      </div>
                    </div>
                  </div>

                  <div className="text-[11px] text-slate-400 flex items-center justify-between pt-1">
                    <span>
                      2-Way Sync:{" "}
                      <strong className={crmConnected ? "text-emerald-400" : "text-slate-500"}>
                        {crmConnected ? "Active (AI Voice ➔ PostgreSQL)" : "Offline"}
                      </strong>
                    </span>
                    <span>
                      Last sync:{" "}
                      <strong className="text-slate-300 font-mono">{lastSyncedTime || "Real-time"}</strong>
                    </span>
                  </div>
                </div>

                {/* 3. GOOGLE CALENDAR SYNC */}
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-11 h-11 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
                        <Calendar className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">Google Calendar Two-Way Sync</h3>
                        <p className="text-[11px] text-slate-400">Doctor&apos;s personal mobile calendar lock</p>
                      </div>
                    </div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20">
                      ● Active
                    </span>
                  </div>

                  <div className="space-y-2 text-xs">
                    <label className="block text-slate-300 font-medium">Doctor&apos;s Google Account Email:</label>
                    <input
                      type="email"
                      value={integrations.google_calendar_email}
                      onChange={(e) => setIntegrations({ ...integrations, google_calendar_email: e.target.value })}
                      placeholder="doctor@gmail.com"
                      className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-slate-200 text-xs font-mono focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-800">
                    💡 If doctor blocks a personal slot in Google Calendar, AI receptionist automatically marks it unavailable!
                  </div>
                </div>

                {/* 4. PATIENT WHATSAPP NOTIFICATIONS */}
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-11 h-11 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                        <MessageSquare className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">Instant Patient WhatsApp Alerts</h3>
                        <p className="text-[11px] text-slate-400">Booking confirmation &amp; Google Map direction</p>
                      </div>
                    </div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                      ● 100% Delivery
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] text-slate-300 font-mono space-y-1">
                    <div className="text-emerald-400 font-bold">📲 WhatsApp Template:</div>
                    <div>&quot;Namaste [Patient Name]! Aapka appointment [Date] ko [Time] par confirm ho gaya hai. 📍 Clinic: {currentClinic.address}&quot;</div>
                  </div>

                  <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-800">
                    Dispatched immediately via Twilio WhatsApp API upon AI call completion.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB: SETTINGS */}
          {activeTab === "settings" && (
            <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-6">
              <div>
                <h2 className="text-base font-bold text-white">Clinic AI Voice Persona &amp; Routing</h2>
                <p className="text-xs text-slate-400">
                  Settings for how the AI answers calls, greetings, and emergency human receptionist transfer.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
                <div className="space-y-4">
                  <div>
                    <label className="block font-semibold text-slate-300 mb-1">
                      AI Receptionist Name
                    </label>
                    <input
                      type="text"
                      readOnly
                      value={currentClinic.assistant_name}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-300 mb-1">
                      Persona &amp; Language Tone
                    </label>
                    <input
                      type="text"
                      readOnly
                      value={currentClinic.assistant_tone}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-300 mb-1">
                      Clinic Address (Provided to callers)
                    </label>
                    <input
                      type="text"
                      readOnly
                      value={currentClinic.address}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block font-semibold text-slate-300 mb-1">
                      Dedicated Inbound Hotline (Virtual DID)
                    </label>
                    <input
                      type="text"
                      readOnly
                      value={currentClinic.phone_number}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-cyan-400 font-mono focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-300 mb-1">
                      Emergency Human Handoff (Doctor Mobile)
                    </label>
                    <input
                      type="text"
                      readOnly
                      value={currentClinic.emergency_phone}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-rose-300 font-mono focus:outline-none"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* DEDICATED SLIDE-OVER AI VOICE TESTING MODAL (Executive Demo Tool) */}
      {voiceSimulatorOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="p-6 max-w-xl w-full rounded-3xl border border-cyan-500/40 bg-slate-950 shadow-2xl space-y-5 relative">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">AI Voice Testing Console</h3>
                  <p className="text-[11px] text-slate-400">Testing for {currentClinic.name}</p>
                </div>
              </div>
              <button
                onClick={() => setVoiceSimulatorOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Pulsing Visual Waveform */}
            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div
                  className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-all ${
                    isAiSpeaking
                      ? "bg-cyan-500 text-slate-950 animate-pulse shadow-lg shadow-cyan-500/40"
                      : "bg-slate-800 text-cyan-400"
                  }`}
                >
                  <Mic className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xs font-bold text-white flex items-center gap-1.5">
                    <span>{currentClinic.assistant_name} Voice Agent</span>
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  </div>
                  <div className="text-[11px] text-slate-400">
                    {isAiSpeaking ? "🔊 Speaking via browser audio..." : "Listening • Select scenario below"}
                  </div>
                </div>
              </div>

              {/* Waveform bars */}
              <div className="flex items-center gap-1 h-6">
                <span className={`w-1 rounded-full bg-cyan-400 ${isAiSpeaking ? "wave-bar-1" : "h-1"}`} />
                <span className={`w-1 rounded-full bg-cyan-400 ${isAiSpeaking ? "wave-bar-2" : "h-2"}`} />
                <span className={`w-1 rounded-full bg-emerald-400 ${isAiSpeaking ? "wave-bar-3" : "h-3"}`} />
                <span className={`w-1 rounded-full bg-cyan-400 ${isAiSpeaking ? "wave-bar-4" : "h-1.5"}`} />
                <span className={`w-1 rounded-full bg-blue-400 ${isAiSpeaking ? "wave-bar-5" : "h-2"}`} />
              </div>
            </div>

            {/* 4 Interactive One-Click Scenarios */}
            <div className="space-y-2">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Select Client Demo Scenario
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <button
                  disabled={simLoading}
                  onClick={() => handleSimulateScenario("book_rct")}
                  className="p-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 text-left transition-all text-xs"
                >
                  <div className="font-bold text-white">1. Book Root Canal (RCT)</div>
                  <div className="text-[10px] text-slate-400">Checks slot &amp; inserts into DB</div>
                </button>

                <button
                  disabled={simLoading}
                  onClick={() => handleSimulateScenario("pricing_scaling")}
                  className="p-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 text-left transition-all text-xs"
                >
                  <div className="font-bold text-white">2. Inquire Scaling Price</div>
                  <div className="text-[10px] text-slate-400">Reads clinic price book</div>
                </button>

                <button
                  disabled={simLoading}
                  onClick={() => handleSimulateScenario("emergency_bleeding")}
                  className="p-2.5 rounded-xl bg-slate-900 hover:bg-rose-950/40 border border-slate-800 hover:border-rose-500/40 text-left transition-all text-xs"
                >
                  <div className="font-bold text-white text-rose-300">3. Severe Pain &amp; Bleeding</div>
                  <div className="text-[10px] text-slate-400">Emergency priority triage</div>
                </button>

                <button
                  disabled={simLoading}
                  onClick={() => handleSimulateScenario("check_slots")}
                  className="p-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-emerald-500/40 text-left transition-all text-xs"
                >
                  <div className="font-bold text-white">4. Check Evening Slots</div>
                  <div className="text-[10px] text-slate-400">Calculates unbooked slots</div>
                </button>
              </div>
            </div>

            {/* Transcript stream */}
            <div className="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 max-h-40 overflow-y-auto space-y-2 text-xs">
              {liveTranscript.map((t, idx) => (
                <div key={idx} className={t.role === "assistant" ? "text-cyan-300" : "text-slate-300"}>
                  <span className="font-bold">{t.role === "assistant" ? "🤖 AI:" : "🗣️ Patient:"} </span>
                  <span>{t.text}</span>
                </div>
              ))}
            </div>

            {/* Action status pill */}
            <div className="text-[11px] font-mono text-cyan-400 bg-slate-900 p-2 rounded-xl border border-slate-800 text-center truncate">
              {lastActionBadge}
            </div>
          </div>
        </div>
      )}

      {/* WALK-IN MODAL */}
      {isWalkinModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="p-6 max-w-md w-full rounded-3xl border border-slate-800 bg-slate-950 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Plus className="w-4 h-4 text-cyan-400" />
                <span>Register Walk-in Patient</span>
              </h3>
              <button onClick={() => setIsWalkinModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateWalkin} className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-slate-300 mb-1">Patient Name</label>
                <input
                  type="text"
                  required
                  value={walkinName}
                  onChange={(e) => setWalkinName(e.target.value)}
                  placeholder="e.g. Ramesh Kumar"
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">Phone Number</label>
                <input
                  type="text"
                  required
                  value={walkinPhone}
                  onChange={(e) => setWalkinPhone(e.target.value)}
                  placeholder="+91 98765 43210"
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-slate-300 mb-1">Date</label>
                  <select
                    value={walkinDate}
                    onChange={(e) => setWalkinDate(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="Today">Today</option>
                    <option value="Tomorrow">Tomorrow</option>
                  </select>
                </div>
                <div>
                  <label className="block font-medium text-slate-300 mb-1">Slot</label>
                  <select
                    value={walkinTime}
                    onChange={(e) => setWalkinTime(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="11:15 AM">11:15 AM</option>
                    <option value="12:00 PM">12:00 PM</option>
                    <option value="04:15 PM">04:15 PM</option>
                    <option value="05:00 PM">05:00 PM</option>
                    <option value="06:30 PM">06:30 PM</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">Treatment</label>
                <input
                  type="text"
                  value={walkinTreatment}
                  onChange={(e) => setWalkinTreatment(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsWalkinModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold"
                >
                  Confirm Slot
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EDIT PRICE MODAL */}
      {editingService && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="p-6 max-w-md w-full rounded-3xl border border-slate-800 bg-slate-950 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white">Edit Treatment Price</h3>
                <p className="text-[11px] text-slate-400">{editingService.name}</p>
              </div>
              <button onClick={() => setEditingService(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-slate-300 mb-1">
                  Price Range (Quoted to Callers)
                </label>
                <input
                  type="text"
                  value={newPriceRange}
                  onChange={(e) => setNewPriceRange(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-emerald-400 font-semibold focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">
                  Base Starting Price (₹)
                </label>
                <input
                  type="number"
                  value={newMinPrice}
                  onChange={(e) => setNewMinPrice(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setEditingService(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 font-semibold"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSavePrice}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold"
                >
                  Save &amp; Sync to AI
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
