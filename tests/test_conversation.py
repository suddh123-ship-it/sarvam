"""Local test script — simulate conversation without Twilio."""
import asyncio
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.conversation import conversation_manager


async def simulate_conversation():
    """Simulate a full dealership service booking conversation."""
    call_sid = "demo-call-001"
    
    print("=" * 60)
    print("🚗 SARVAM AUTO DEALERSHIP BOT — LOCAL TEST")
    print("=" * 60)
    print("Simulating a voice call conversation...\n")
    
    test_inputs = [
        {"text": "Namaste, meri car ki service karwani hai", "note": "Customer initiates"},
        {"text": "Maruti Swift hai meri, 2022 model", "note": "Provides vehicle details"},
        {"text": "Kal subah 10 baje ka slot chahiye", "note": "Requests specific time"},
        {"text": "Regular service hai, oil change bhi karwana hai", "note": "Specifies service type"},
        {"text": "Haan, airbag recall ke baare mein message aaya tha", "note": "Mentions recall"},
        {"text": "Theek hai, kal 10 baje aaunga. Dhanyawad!", "note": "Confirms appointment"}
    ]
    
    for i, turn in enumerate(test_inputs, 1):
        print(f"\n{'─' * 50}")
        print(f"📝 Turn {i} — {turn['note']}")
        print(f"{'─' * 50}")
        print(f"👤 Customer: \"{turn['text']}\"")
        
        result = await conversation_manager.process_user_input(call_sid, turn['text'])
        
        print(f"🤖 Bot: \"{result['response_text']}\"")
        print(f"📊 Intent: {result['intent']} | Escalation: {result['escalation_needed']} | Hangup: {result['should_hangup']}")
        
        state = result['state']
        entities = []
        if state['vehicle_model']: entities.append(f"Vehicle: {state['vehicle_model']}")
        if state['service_type']: entities.append(f"Service: {state['service_type']}")
        if state['preferred_date']: entities.append(f"Date: {state['preferred_date']}")
        if entities:
            print(f"📋 Extracted: {', '.join(entities)}")
        
        if result['should_hangup']:
            print(f"\n{'=' * 60}")
            print("👋 CALL ENDED — Appointment confirmed!")
            print(f"{'=' * 60}")
            break
    
    print(f"\n{'=' * 60}")
    print("📊 FULL CONVERSATION HISTORY")
    print(f"{'=' * 60}")
    session = conversation_manager.get_or_create_session(call_sid)
    for msg in session['history']:
        role = "👤" if msg['role'] == 'user' else "🤖"
        print(f"{role} {msg['role'].upper()}: {msg['text']}")
    
    conversation_manager.end_session(call_sid)
    print(f"\n✅ Test complete!")


async def test_hinglish_code_mixing():
    """Test Hinglish code-mixing capability."""
    call_sid = "demo-call-hinglish"
    
    print(f"\n{'=' * 60}")
    print("🎯 HINGLISH CODE-MIXING TEST")
    print(f"{'=' * 60}")
    
    hinglish_inputs = [
        "Mujhe morning slot chahiye, not evening",
        "Kal 11 baje ka time fix karo, I have a meeting at 2",
        "Swift ka engine thoda problematic hai, noise aa rahi hai",
    ]
    
    for text in hinglish_inputs:
        print(f"\n👤 Customer: \"{text}\"")
        result = await conversation_manager.process_user_input(call_sid, text)
        print(f"🤖 Bot: \"{result['response_text']}\"")
    
    conversation_manager.end_session(call_sid)


async def test_escalation():
    """Test angry customer escalation."""
    call_sid = "demo-call-escalation"
    
    print(f"\n{'=' * 60}")
    print("🚨 ESCALATION TEST — Angry Customer")
    print(f"{'=' * 60}")
    
    angry_inputs = [
        "Ye third time same problem aa rahi hai!",
        "Aap log kuch nahi karte, bas paise lete ho!",
        "Mujhe abhi aapke manager se baat karni hai!"
    ]
    
    for text in angry_inputs:
        print(f"\n👤 Customer: \"{text}\"")
        result = await conversation_manager.process_user_input(call_sid, text)
        print(f"🤖 Bot: \"{result['response_text']}\"")
        print(f"🚨 Escalation triggered: {result['escalation_needed']}")
        
        if result['escalation_needed']:
            print("✅ Escalation flow working correctly!")
            break
    
    conversation_manager.end_session(call_sid)


if __name__ == "__main__":
    asyncio.run(simulate_conversation())
    asyncio.run(test_hinglish_code_mixing())
    asyncio.run(test_escalation())
