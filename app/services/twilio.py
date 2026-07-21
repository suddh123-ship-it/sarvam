"""Twilio telephony integration service."""
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Say
from app.config import settings


class TwilioService:
    """Handles Twilio call management and TwiML generation."""
    
    def __init__(self):
        self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        self.phone_number = settings.twilio_phone_number
    
    def generate_welcome_twiml(self, welcome_message: str, webhook_url: str) -> str:
        """Generate TwiML for the initial welcome + gather user speech."""
        response = VoiceResponse()
        response.say(welcome_message, language="hi-IN", voice="Polly.Aditi")
        
        gather = Gather(
            input="speech",
            action=webhook_url,
            method="POST",
            language="hi-IN",
            speech_timeout="auto",
            speech_model="phone_call",
            enhanced=True,
            timeout=5
        )
        gather.say("कृपया दोहराएं। Please repeat.", language="hi-IN", voice="Polly.Aditi")
        response.append(gather)
        response.redirect(webhook_url)
        
        return str(response)
    
    def generate_response_twiml(self, bot_response: str, webhook_url: str, audio_url=None) -> str:
        """Generate TwiML to play bot response and gather next user input."""
        response = VoiceResponse()
        
        if audio_url:
            response.play(audio_url)
        else:
            response.say(bot_response, language="hi-IN", voice="Polly.Aditi")
        
        gather = Gather(
            input="speech",
            action=webhook_url,
            method="POST",
            language="hi-IN",
            speech_timeout="auto",
            speech_model="phone_call",
            enhanced=True,
            timeout=5
        )
        response.append(gather)
        response.redirect(webhook_url)
        
        return str(response)
    
    def generate_hangup_twiml(self, farewell_message: str) -> str:
        """Generate TwiML to end the call gracefully."""
        response = VoiceResponse()
        response.say(farewell_message, language="hi-IN", voice="Polly.Aditi")
        response.hangup()
        return str(response)
    
    def make_outbound_call(self, to_number: str, webhook_url: str) -> str:
        """Initiate an outbound call."""
        call = self.client.calls.create(
            to=to_number,
            from_=self.phone_number,
            url=webhook_url,
            method="POST"
        )
        return call.sid


# Singleton instance
twilio_service = TwilioService()
