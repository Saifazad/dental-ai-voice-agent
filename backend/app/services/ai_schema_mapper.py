import os
import re
import json
from typing import Dict, Any, Optional, List, Tuple

class AISchemaMapper:
    """
    AI & Semantic Schema Mapping Engine for Dental Clinic CRMs.
    Takes any arbitrary CRM JSON (Practo, HubSpot, Dentrix, Salesforce, Custom PostgreSQL)
    and automatically identifies, matches, and maps disparate field names to the Voice Agent standard schema.
    """

    STANDARD_FIELDS = {
        "patient_name": {
            "label": "Patient Full Name",
            "description": "Full name of the patient",
            "aliases": ["patient_name", "patient_fullname", "fullname", "name", "pat_name", "client_name", "customer_name", "patname", "first_name", "patient"],
            "sample_fallback": "Aarav Sharma"
        },
        "patient_phone": {
            "label": "Contact Phone / Mobile",
            "description": "Patient telephone or mobile number",
            "aliases": ["patient_phone", "phone", "mobile", "contact_no", "contact", "cell", "phone_number", "mob_no", "wirelessphone", "contact_number", "tele"],
            "sample_fallback": "+91 98765 43210"
        },
        "appointment_date": {
            "label": "Appointment Date",
            "description": "Scheduled date (YYYY-MM-DD or readable)",
            "aliases": ["appointment_date", "date", "visit_date", "scheduled_date", "booking_date", "sch_date", "day", "aptdate", "start_date"],
            "sample_fallback": "2026-10-25"
        },
        "appointment_time": {
            "label": "Appointment Time Slot",
            "description": "Time slot or hour of visit",
            "aliases": ["appointment_time", "time", "slot", "slot_time", "timing", "slot_timing", "apttime", "hour", "slot_hr", "starts_at"],
            "sample_fallback": "11:15 AM"
        },
        "treatment_type": {
            "label": "Dental Treatment / Procedure",
            "description": "Type of treatment (RCT, Cleaning, Braces, etc.)",
            "aliases": ["treatment_type", "treatment_name", "treatment", "procedure", "service", "service_name", "service_type", "procdescript", "reason", "procedure_name"],
            "sample_fallback": "Root Canal Treatment"
        },
        "doctor_name": {
            "label": "Doctor / Dentist Name",
            "description": "Dentist or specialist assigned",
            "aliases": ["doctor_name", "doctor", "dentist", "dentist_name", "provider", "physician", "doc_name", "staff_name"],
            "sample_fallback": "Dr. Alok Aggarwal"
        },
        "notes": {
            "label": "Clinical Notes / Remarks",
            "description": "Symptoms, chief complaint, or receptionist notes",
            "aliases": ["notes", "remarks", "chief_complaint", "comment", "description", "details", "reason_notes", "symptoms"],
            "sample_fallback": "Mild swelling on lower molar"
        },
        "status": {
            "label": "Booking Status",
            "description": "Current status (Confirmed, Pending, etc.)",
            "aliases": ["status", "state", "appointment_status", "booking_status"],
            "sample_fallback": "Confirmed"
        }
    }

    def __init__(self):
        # In-memory store of active schema mapping per clinic
        self.active_mappings: Dict[str, Dict[str, str]] = {}

    def extract_flat_keys_and_values(self, data: Any, prefix: str = "") -> List[Tuple[str, Any]]:
        """Flatten nested dicts (e.g. HubSpot { properties: { phone: ... } }) into flat key-value pairs."""
        items: List[Tuple[str, Any]] = []
        if isinstance(data, list) and len(data) > 0:
            return self.extract_flat_keys_and_values(data[0], prefix)
        elif isinstance(data, dict):
            for k, v in data.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    items.extend(self.extract_flat_keys_and_values(v, full_key))
                else:
                    items.append((full_key, v))
        return items

    def _calculate_field_similarity(self, standard_key: str, crm_key: str, sample_val: Any) -> float:
        """Calculate confidence score between 0.0 and 1.0 based on key semantics and value sniffing."""
        meta = self.STANDARD_FIELDS[standard_key]
        aliases = meta["aliases"]
        clean_crm_key = re.sub(r'[^a-zA-Z0-9_]', '', crm_key.lower().split(".")[-1])

        score = 0.0

        # Exact match with standard key or alias
        if clean_crm_key == standard_key or clean_crm_key in aliases:
            score = 0.95
        else:
            # Substring / token matching
            for alias in aliases:
                if alias in clean_crm_key or clean_crm_key in alias:
                    score = max(score, 0.78)
                    break

        # Value sniffing boost
        val_str = str(sample_val).strip() if sample_val is not None else ""
        if val_str:
            if standard_key == "patient_phone":
                # Check if value looks like a phone number
                if re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\d{10}', val_str):
                    score = max(score + 0.35, 0.92)
            elif standard_key == "appointment_time":
                # Check if value looks like time (e.g. 11:00 AM, 15:30)
                if re.search(r'\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b', val_str):
                    score = max(score + 0.35, 0.92)
            elif standard_key == "appointment_date":
                # Check if value looks like date (e.g. 2026-10-25, 25/10/2026)
                if re.search(r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', val_str):
                    score = max(score + 0.35, 0.92)
            elif standard_key == "doctor_name":
                if "dr." in val_str.lower() or "doctor" in val_str.lower():
                    score = max(score + 0.30, 0.90)

        return min(round(score, 2), 1.0)

    def analyze_schema(self, sample_payload: Any) -> Dict[str, Any]:
        """
        Takes arbitrary CRM JSON (single record, list of records, or nested structure)
        and returns auto-matched schema mapping with confidence metrics.
        """
        flat_items = self.extract_flat_keys_and_values(sample_payload)
        if not flat_items:
            return {
                "success": False,
                "error": "Could not parse JSON. Please provide a valid JSON object or list."
            }

        matched_mapping: Dict[str, Dict[str, Any]] = {}
        assigned_crm_keys = set()

        for std_key, meta in self.STANDARD_FIELDS.items():
            best_crm_key = None
            best_score = 0.0
            best_val = None

            for crm_key, val in flat_items:
                if crm_key in assigned_crm_keys:
                    continue
                score = self._calculate_field_similarity(std_key, crm_key, val)
                if score > best_score:
                    best_score = score
                    best_crm_key = crm_key
                    best_val = val

            if best_crm_key and best_score >= 0.50:
                matched_mapping[std_key] = {
                    "crm_field": best_crm_key,
                    "label": meta["label"],
                    "confidence": int(best_score * 100),
                    "sample_value": str(best_val) if best_val is not None else meta["sample_fallback"]
                }
                assigned_crm_keys.add(best_crm_key)
            else:
                matched_mapping[std_key] = {
                    "crm_field": std_key,  # fallback to standard
                    "label": meta["label"],
                    "confidence": 60,
                    "sample_value": meta["sample_fallback"]
                }

        all_crm_keys = [k for k, _ in flat_items]
        unmapped_fields = [k for k in all_crm_keys if k not in assigned_crm_keys]

        return {
            "success": True,
            "engine": "AI Semantic Schema Engine",
            "total_detected_fields": len(flat_items),
            "mapped_count": len([m for m in matched_mapping.values() if m["confidence"] > 60]),
            "mapping": matched_mapping,
            "unmapped_crm_fields": unmapped_fields
        }

    def set_active_mapping(self, clinic_id: str, mapping: Dict[str, str]):
        """Persist mapping dictionary { "patient_name": "pat_fullname", ... }"""
        self.active_mappings[clinic_id] = mapping

    def get_active_mapping(self, clinic_id: str) -> Dict[str, str]:
        """Retrieve active mapping for clinic, or default identity map."""
        if clinic_id in self.active_mappings:
            return self.active_mappings[clinic_id]
        # Default identity mapping
        return {k: k for k in self.STANDARD_FIELDS.keys()}

    def transform_outbound(self, clinic_id: str, standard_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforms Voice Agent standard data into CRM-specific payload
        using the active AI schema mapping.
        """
        mapping = self.get_active_mapping(clinic_id)
        crm_payload: Dict[str, Any] = {}

        for std_key, val in standard_data.items():
            crm_key = mapping.get(std_key, std_key)
            # Support dot-notation nested paths (e.g. "properties.phone")
            if "." in crm_key:
                parts = crm_key.split(".")
                curr = crm_payload
                for p in parts[:-1]:
                    if p not in curr:
                        curr[p] = {}
                    curr = curr[p]
                curr[parts[-1]] = val
            else:
                crm_payload[crm_key] = val

        return crm_payload

    def transform_inbound(self, clinic_id: str, raw_crm_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforms CRM-specific record into Voice Agent standard internal appointment.
        """
        mapping = self.get_active_mapping(clinic_id)
        # Reverse lookup: std_key -> crm_key
        flat_crm = dict(self.extract_flat_keys_and_values(raw_crm_item))

        normalized: Dict[str, Any] = {}
        for std_key in self.STANDARD_FIELDS.keys():
            crm_key = mapping.get(std_key, std_key)
            if crm_key in flat_crm:
                normalized[std_key] = flat_crm[crm_key]
            elif crm_key in raw_crm_item:
                normalized[std_key] = raw_crm_item[crm_key]
            else:
                normalized[std_key] = self.STANDARD_FIELDS[std_key]["sample_fallback"]

        # Preserve standard meta
        normalized["id"] = raw_crm_item.get("id") or raw_crm_item.get("appointment_id") or "crm_app"
        normalized["status"] = normalized.get("status") or "Confirmed"
        return normalized

ai_schema_mapper = AISchemaMapper()
