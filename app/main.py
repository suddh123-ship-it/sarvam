"""
Sarvam Automotive Dealership Voice Bot
======================================
FastAPI application handling Twilio voice webhooks and Sarvam AI integration.
"""
import sys

# Ensure emoji/Hindi log lines don't crash on Windows' cp1252 console.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi import FastAPI, Request, Form, Response, HTTPException
from fastapi.responses import PlainTextResponse, HTMLResponse
import base64
import os
import tempfile
from typing import Optional

from app.config import settings
from app.services.sarvam import sarvam_service
from app.services.twilio import twilio_service
from app.services.conversation import conversation_manager
from app.services.crm import crm_store
from app.dashboard import DASHBOARD_HTML


app = FastAPI(
    title="Sarvam Auto Dealership Bot",
    description="Voice AI bot for automotive service booking using Sarvam AI + Twilio",
    version="1.0.0"
)


async def _finalize_call(call_sid: str, escalated: bool):
    """Summarize a finished call and update the CRM before the session is cleared."""
    session = conversation_manager.sessions.get(call_sid)
    if not session:
        return
    state = session["state"]
    phone = state.get("phone") or "unknown"

    try:
        summary = await conversation_manager.summarize_session(call_sid)
    except Exception as e:
        print(f"⚠️ Summary generation failed: {e}")
        summary = "Summary unavailable."

    crm_store.record_call(
        call_sid=call_sid,
        phone=phone,
        summary=summary,
        intent=state.get("intent") or "general_query",
        state=state,
        escalated=escalated,
    )
    print(f"🗂️  CRM updated for {call_sid} (escalated={escalated})")


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Sarvam Auto Dealership Bot",
        "version": "1.0.0"
    }


@app.post("/voice/inbound")
async def handle_inbound_call(request: Request):
    """Handle incoming Twilio calls."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")
    from_number = form_data.get("From", "unknown")
    
    print(f"📞 Inbound call from {from_number}, CallSid: {call_sid}")

    # Remember the caller so we can match them to a CRM record when the call ends.
    session = conversation_manager.get_or_create_session(call_sid)
    session["state"]["phone"] = from_number

    welcome_msg = settings.welcome_message
    webhook_url = f"{request.base_url}voice/gather"
    
    twiml = twilio_service.generate_welcome_twiml(welcome_msg, webhook_url)
    
    return Response(content=twiml, media_type="application/xml")


@app.post("/voice/gather")
async def handle_gather(
    request: Request,
    CallSid: str = Form(""),
    SpeechResult: Optional[str] = Form(None),
    RecordingUrl: Optional[str] = Form(None),
    CallStatus: Optional[str] = Form(None)
):
    """Core voice loop handler."""
    print(f"\n🎯 Gather handler — CallSid: {CallSid}, SpeechResult: {SpeechResult}")
    
    user_text = ""
    
    if SpeechResult:
        user_text = SpeechResult
        print(f"📝 Twilio STT: {user_text}")
    
    if RecordingUrl:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                audio_response = await client.get(RecordingUrl)
                audio_bytes = audio_response.content
            
            sarvam_transcript = await sarvam_service.speech_to_text(
                audio_bytes=audio_bytes,
                language_code="unknown",
                model="saaras:v3",
                mode="transcribe"
            )
            if sarvam_transcript:
                user_text = sarvam_transcript
                print(f"📝 Sarvam STT (saaras:v3): {user_text}")
        except Exception as e:
            print(f"⚠️ Sarvam STT failed, using Twilio fallback: {e}")
    
    if not user_text:
        user_text = "hello"
    
    result = await conversation_manager.process_user_input(CallSid, user_text)
    
    bot_response = result["response_text"]
    should_hangup = result["should_hangup"]
    escalation = result["escalation_needed"]
    
    print(f"🤖 Bot response: {bot_response}")
    print(f"📊 State: intent={result['intent']}, escalation={escalation}, hangup={should_hangup}")
    
    audio_url = None
    try:
        audio_bytes = await sarvam_service.text_to_speech(
            text=bot_response,
            language_code="hi-IN",
            speaker="anushka",
            model="bulbul:v2",
            pace=1.1,
            pitch=0.1,
            loudness=1.2,
            enable_preprocessing=True
        )
        
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"{CallSid}_{result['state']['turn_count']}.wav")
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        
        audio_url = f"{request.base_url}audio/{CallSid}_{result['state']['turn_count']}.wav"
        print(f"🔊 TTS generated: {audio_url}")
        
    except Exception as e:
        print(f"⚠️ Sarvam TTS failed, using Twilio native TTS fallback: {e}")
        audio_url = None
    
    webhook_url = f"{request.base_url}voice/gather"
    
    if should_hangup:
        twiml = twilio_service.generate_hangup_twiml(bot_response)
        await _finalize_call(CallSid, escalated=False)
        conversation_manager.end_session(CallSid)
        print(f"👋 Call ended — CallSid: {CallSid}")
    elif escalation:
        escalation_msg = bot_response + " मैं आपको जल्द ही हमारे सुपरवाइज़र से कनेक्ट करवा दूँगा। I will connect you to our supervisor shortly."
        twiml = twilio_service.generate_hangup_twiml(escalation_msg)
        await _finalize_call(CallSid, escalated=True)
        conversation_manager.end_session(CallSid)
        print(f"🚨 Escalation triggered — CallSid: {CallSid}")
    else:
        twiml = twilio_service.generate_response_twiml(bot_response, webhook_url, audio_url)
    
    return Response(content=twiml, media_type="application/xml")


@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve generated TTS audio files to Twilio."""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    with open(file_path, "rb") as f:
        audio_data = f.read()
    
    return Response(content=audio_data, media_type="audio/wav")


@app.post("/voice/status")
async def handle_status_callback(
    CallSid: str = Form(""),
    CallStatus: str = Form(""),
    CallDuration: Optional[str] = Form(None)
):
    """Handle Twilio call status callbacks for logging."""
    print(f"📊 Call status — CallSid: {CallSid}, Status: {CallStatus}, Duration: {CallDuration}s")

    if CallStatus in ["completed", "failed", "busy", "no-answer", "canceled"]:
        # If the session is still open, the hangup branch never ran (e.g. caller
        # hung up mid-conversation) — capture whatever we have before clearing.
        if CallStatus == "completed" and CallSid in conversation_manager.sessions:
            await _finalize_call(CallSid, escalated=False)
        conversation_manager.end_session(CallSid)

    return {"status": "logged"}


@app.post("/voice/outbound")
async def trigger_outbound_call(to_number: str, request: Request):
    """Trigger an outbound call (for demo purposes)."""
    webhook_url = f"{request.base_url}voice/inbound"
    
    try:
        call_sid = twilio_service.make_outbound_call(to_number, webhook_url)
        return {"status": "initiated", "call_sid": call_sid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{call_sid}")
async def get_session(call_sid: str):
    """Get conversation session details (debugging)."""
    session = conversation_manager.sessions.get(call_sid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ── Dashboard ────────────────────────────────────────────────────────────────
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the call-summary dashboard UI."""
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/api/dashboard")
async def dashboard_data():
    """JSON feed powering the dashboard (polled by the UI)."""
    return {
        "stats": crm_store.stats(),
        "customers": crm_store.list_customers(),
        "calls": crm_store.list_call_records(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )
