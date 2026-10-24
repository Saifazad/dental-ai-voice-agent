from typing import Optional
from fastapi import APIRouter, Request, Query
from app.services.dental_service import dental_service

router = APIRouter(prefix="/api/vapi", tags=["Vapi AI Telephony Webhook"])

@router.post("/webhook")
async def vapi_webhook(request: Request, clinic_id: Optional[str] = Query(None)):
    """
    Production-ready Multi-Tenant Webhook for Vapi.ai / Retell / Twilio.
    Identifies the tenant from URL query param `?clinic_id=...` or assistant metadata.
    """
    body = await request.json()
    message = body.get("message", {})
    message_type = message.get("type")

    if not clinic_id:
        raw_cid = message.get("call", {}).get("assistant", {}).get("metadata", {}).get("clinic_id")
        clinic_id = dental_service.resolve_clinic_id(raw_cid)

    print(f"\n📞 [Vapi Webhook] Tenant: {clinic_id} | Message: {message_type}")

    # Direct API Tool Call Support (when Vapi apiRequest tool sends raw JSON body directly)
    if not message and ("patient_name" in body or "appointment_date" in body):
        patient_name = body.get("patient_name", "Patient")
        patient_phone = body.get("patient_phone", "Not Provided")
        app_date = body.get("appointment_date", "tomorrow")
        app_time = body.get("appointment_time", "11:15 AM")
        treatment = body.get("treatment_type", "General Consultation")
        notes = body.get("notes", "")

        booking_result = dental_service.book_appointment(
            clinic_id=clinic_id,
            patient_name=patient_name,
            patient_phone=patient_phone,
            appointment_date=app_date,
            appointment_time=app_time,
            treatment_type=treatment,
            notes=notes
        )
        return {
            "success": True,
            "message": f"Appointment confirmed for {patient_name} on {app_date} at {app_time}.",
            "appointment": booking_result
        }

    if message_type in ("tool-calls", "function-call"):
        tool_calls = message.get("toolCalls") or []
        if not tool_calls and "functionCall" in message:
            fc = message["functionCall"]
            tool_calls = [{"id": fc.get("id", "call_1"), "function": fc}]
        results = []

        for tc in tool_calls:
            call_id = tc.get("id")
            func = tc.get("function", {})
            func_name = func.get("name")
            args = func.get("arguments", {})

            print(f"🔧 Tool: {func_name} with args: {args}")

            if func_name == "check_availability":
                date_val = args.get("date", "tomorrow")
                pref = args.get("time_preference", "any")
                slots = dental_service.get_available_slots(clinic_id, date_val, pref)
                slots_str = ", ".join(slots)
                reply = f"{date_val} ke liye open slots hain: {slots_str}."
                results.append({"toolCallId": call_id, "result": reply})

            elif func_name == "book_appointment":
                patient_name = args.get("patient_name", "Patient")
                patient_phone = args.get("patient_phone", "Not Provided")
                app_date = args.get("appointment_date", "tomorrow")
                app_time = args.get("appointment_time", "11:15 AM")
                treatment = args.get("treatment_type", "General Consultation")
                notes = args.get("notes", "")

                booking_result = dental_service.book_appointment(
                    clinic_id=clinic_id,
                    patient_name=patient_name,
                    patient_phone=patient_phone,
                    appointment_date=app_date,
                    appointment_time=app_time,
                    treatment_type=treatment,
                    notes=notes,
                    booking_source="AI Voice Agent"
                )

                if booking_result.get("conflict"):
                    reply = booking_result["message"]
                else:
                    crm_ref = booking_result.get("crm_appointment_id")
                    doc = booking_result.get("doctor_name", "Dr. Alok Aggarwal")
                    if crm_ref:
                        reply = f"Appointment successfully confirmed and registered in Dental CRM for {patient_name} on {app_date} at {app_time} for {treatment} with {doc}. CRM Reference ID is {crm_ref}. Confirmation SMS sent."
                    else:
                        reply = f"Appointment successfully booked for {patient_name} on {app_date} at {app_time} for {treatment} with {doc}. Confirmation SMS sent."
                results.append({"toolCallId": call_id, "result": reply})

            elif func_name == "get_service_pricing":
                treatment = args.get("treatment", "")
                reply = dental_service.get_service_pricing_reply(clinic_id, treatment)
                results.append({"toolCallId": call_id, "result": reply})

            elif func_name == "check_emergency":
                symptoms = args.get("symptoms", "")
                triage = dental_service.evaluate_emergency(symptoms)
                results.append({"toolCallId": call_id, "result": triage["message"]})

            else:
                results.append({"toolCallId": call_id, "result": f"Tool {func_name} handled."})

        return {"results": results}

    elif message_type == "end-of-call-report":
        call_data = message.get("call", {})
        customer = call_data.get("customer", {})
        caller_phone = customer.get("number") or message.get("customer", {}).get("number") or "Incoming Patient"
        caller_name = customer.get("name") or "Patient"
        duration = int(call_data.get("durationSeconds") or message.get("durationSeconds") or 45)
        summary = message.get("summary") or "Patient phone call handled by AI Voice Receptionist."
        transcript = message.get("transcript") or ""
        recording_url = message.get("recordingUrl") or call_data.get("recordingUrl") or ""

        # Auto evaluate emergency flag
        is_emerg = 1 if dental_service.evaluate_emergency(f"{summary} {transcript}")["is_emergency"] else 0

        dental_service.log_call(
            clinic_id=clinic_id,
            caller_name=caller_name,
            caller_phone=caller_phone,
            duration=duration,
            summary=summary,
            transcript=transcript,
            is_emergency=is_emerg,
            action_taken="Auto-logged from Vapi Live Phone Call",
            recording_url=recording_url
        )
        print(f"✅ [Vapi Report] Logged call from {caller_phone} ({duration}s) | Emergency: {is_emerg}")
        return {"status": "success", "message": "Call report logged to dashboard"}

    return {"status": "received"}
