"""Conversation state manager with LLM-powered responses."""
import json
from typing import Optional, Dict, Any
from app.services.sarvam import sarvam_service
from app.config import settings


class ConversationManager:
    """
    Manages conversation state and generates context-aware responses
    using Sarvam-105b LLM for an automotive dealership voice bot.
    """
    
    SYSTEM_PROMPT = """You are a helpful and polite automotive dealership service assistant for an Indian car dealership (Maruti/Tata/Mahindra/Hyundai). 

Your job is to help customers with:
1. Booking service appointments
2. Checking recall notifications for their vehicle
3. Providing service estimates
4. Handling complaints and escalating when needed
5. Confirming or rescheduling existing appointments

RULES:
- Speak in Hindi or Hinglish (Hindi-English mix) naturally, as Indian customers do
- Be warm, professional, and patient
- Keep responses SHORT (2-3 sentences max) — this is a voice call
- If the customer wants to book service, ask for: vehicle model, preferred date, and type of service (regular/complaint/recall)
- If they mention a recall, acknowledge it and offer to fix it during the service visit
- If they are angry or the issue is complex, offer to connect to a human supervisor
- Always end with a clear next step or question
- If you don't understand, politely ask them to repeat

CONVERSATION STYLE:
- Use natural Indian conversational style
- Mix Hindi and English freely (Hinglish)
- Use respectful tone ("ji", "aap")
- Keep it friendly but professional

Current date: 20 July 2026
Dealership: AutoCare Motors, Bangalore
"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_or_create_session(self, call_sid: str) -> Dict[str, Any]:
        """Get existing session or create new one."""
        if call_sid not in self.sessions:
            self.sessions[call_sid] = {
                "call_sid": call_sid,
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT}
                ],
                "state": {
                    "intent": None,
                    "vehicle_model": None,
                    "service_type": None,
                    "preferred_date": None,
                    "customer_name": None,
                    "phone": None,
                    "escalation_needed": False,
                    "appointment_confirmed": False,
                    "turn_count": 0
                },
                "history": []
            }
        return self.sessions[call_sid]
    
    def _detect_intent(self, user_text: str, session_state: Dict) -> str:
        """Simple keyword-based intent detection."""
        text_lower = user_text.lower()
        
        intents = {
            "book_service": ["service", "booking", "slot", "appointment", "repair", "theek", "service karwani", "service chahiye"],
            "check_recall": ["recall", "airbag", "fault", "problem", "issue", "defect"],
            "get_estimate": ["price", "cost", "kitna", "paisa", "charge", "estimate", "rate"],
            "reschedule": ["change", "reschedule", "shift", "dusra", "badal", "time change"],
            "cancel": ["cancel", "band", "nahi", "stop"],
            "complaint": ["complaint", "gussa", "problem", "kharaab", "bekar", "issue"],
            "general_query": ["hello", "hi", "namaste", "kaise", "information", "detail"]
        }
        
        for intent, keywords in intents.items():
            if any(kw in text_lower for kw in keywords):
                return intent
        
        return "general_query"
    
    async def process_user_input(
        self, 
        call_sid: str, 
        user_text: str,
        user_audio_b64: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process user speech input and generate bot response."""
        session = self.get_or_create_session(call_sid)
        state = session["state"]
        state["turn_count"] += 1
        
        session["messages"].append({"role": "user", "content": user_text})
        session["history"].append({"role": "user", "text": user_text})
        
        intent = self._detect_intent(user_text, state)
        state["intent"] = intent
        
        self._extract_entities(user_text, state)
        
        context = self._build_context(state)
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT + "\n\n" + context},
            *session["messages"][-6:]
        ]
        
        try:
            bot_response = await sarvam_service.chat_completion(
                messages=messages,
                model="sarvam-105b",
                temperature=0.7,
                max_tokens=2048
            )
        except Exception as e:
            bot_response = "माफ़ कीजिए, कृपया फिर से कहें। Sorry, please say that again."
        
        session["messages"].append({"role": "assistant", "content": bot_response})
        session["history"].append({"role": "assistant", "text": bot_response})
        
        should_hangup = self._should_hangup(state, bot_response)
        state["escalation_needed"] = self._check_escalation(user_text, bot_response, state)
        
        return {
            "response_text": bot_response,
            "should_hangup": should_hangup,
            "escalation_needed": state["escalation_needed"],
            "state": state,
            "intent": intent
        }
    
    def _extract_entities(self, user_text: str, state: Dict):
        """Extract key entities from user text."""
        text_lower = user_text.lower()
        
        models = ["swift", "dzire", "baleno", "wagonr", "i20", "creta", "venue", 
                  "nexon", "punch", "harrier", "safari", "thar", "bolero", "scorpio",
                  "ertiga", "brezza", "fronx", "grand vitara", "ciaz", "xl6"]
        for model in models:
            if model in text_lower:
                state["vehicle_model"] = model.title()
        
        if any(w in text_lower for w in ["regular", "routine", "normal", "general"]):
            state["service_type"] = "regular"
        elif any(w in text_lower for w in ["repair", "theek", "problem", "issue", "fault"]):
            state["service_type"] = "repair"
        elif any(w in text_lower for w in ["recall", "airbag"]):
            state["service_type"] = "recall"
        
        if any(w in text_lower for w in ["kal", "tomorrow", "next"]):
            state["preferred_date"] = "tomorrow"
        elif any(w in text_lower for w in ["aaj", "today"]):
            state["preferred_date"] = "today"
        elif any(w in text_lower for w in ["parso", "day after"]):
            state["preferred_date"] = "day_after"
    
    def _build_context(self, state: Dict) -> str:
        """Build dynamic context string for LLM based on current state."""
        context_parts = []
        
        if state["vehicle_model"]:
            context_parts.append(f"Customer vehicle: {state['vehicle_model']}")
        if state["service_type"]:
            context_parts.append(f"Service type: {state['service_type']}")
        if state["preferred_date"]:
            context_parts.append(f"Preferred date: {state['preferred_date']}")
        if state["turn_count"] > 5:
            context_parts.append("This is a long conversation. Consider wrapping up or escalating.")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _should_hangup(self, state: Dict, response: str) -> bool:
        """Determine if the call should end."""
        if state["appointment_confirmed"]:
            return True
        if state["turn_count"] > 8:
            return True
        if any(w in response.lower() for w in ["bye", "alvida", "dhanyawad", "thank you", "goodbye"]):
            return True
        return False
    
    def _check_escalation(self, user_text: str, bot_response: str, state: Dict) -> bool:
        """Check if human supervisor is needed."""
        angry_words = ["gussa", "bekar", "fraud", "cheat", "manager", "supervisor", 
                       "complaint", "police", "court", "consumer", "pathetic"]
        if any(w in user_text.lower() for w in angry_words):
            return True
        if state["turn_count"] > 6 and not state["appointment_confirmed"]:
            return True
        return False
    
    async def summarize_session(self, call_sid: str) -> str:
        """Generate a concise English summary of the call for the dashboard."""
        session = self.sessions.get(call_sid)
        if not session or not session["history"]:
            return "No conversation recorded."

        transcript = "\n".join(
            f"{m['role'].upper()}: {m['text']}" for m in session["history"]
        )
        summary_prompt = [
            {
                "role": "system",
                "content": (
                    "You are a call-logging assistant for an auto dealership. "
                    "Summarize the following customer service call in 2-3 short "
                    "English sentences. Capture the customer's request, the vehicle, "
                    "any appointment date/time agreed, and the outcome. Be factual "
                    "and concise. Output only the summary, no preamble."
                ),
            },
            {"role": "user", "content": transcript},
        ]
        try:
            return await sarvam_service.chat_completion(
                messages=summary_prompt,
                model="sarvam-105b",
                temperature=0.3,
                max_tokens=2048,
            )
        except Exception:
            # Fallback: build a summary from extracted state without the LLM.
            state = session["state"]
            parts = []
            if state.get("vehicle_model"):
                parts.append(f"Vehicle: {state['vehicle_model']}")
            if state.get("service_type"):
                parts.append(f"Service: {state['service_type']}")
            if state.get("preferred_date"):
                parts.append(f"Date: {state['preferred_date']}")
            detail = ", ".join(parts) if parts else "no details captured"
            return f"Call handled ({state.get('intent', 'general')}). {detail}."

    def end_session(self, call_sid: str):
        """Clean up session data."""
        if call_sid in self.sessions:
            del self.sessions[call_sid]


# Singleton instance
conversation_manager = ConversationManager()
