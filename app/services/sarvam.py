"""Sarvam AI API integration service."""
import base64
import httpx
from app.config import settings


class SarvamService:
    """Handles all Sarvam AI API calls: STT, TTS, Chat Completion."""
    
    def __init__(self):
        self.api_key = settings.sarvam_api_key
        self.base_url = settings.sarvam_base_url
        self.headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def speech_to_text(
        self, 
        audio_bytes: bytes,
        language_code: str = "unknown",
        model: str = "saaras:v3",
        mode: str = "transcribe"
    ) -> str:
        """Convert speech audio to text using Sarvam Saaras STT."""
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        payload = {
            "model": model,
            "language_code": language_code,
            "audio_format": "wav",
            "mode": mode,
            "audio_data": audio_b64
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/speech-to-text",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data.get("transcript", "")
    
    async def text_to_speech(
        self,
        text: str,
        language_code: str = "hi-IN",
        speaker: str = "anushka",
        model: str = "bulbul:v2",
        pace: float = 1.0,
        pitch: float = 0.0,
        loudness: float = 1.0,
        enable_preprocessing: bool = True
    ) -> bytes:
        """Convert text to speech using Sarvam Bulbul TTS."""
        payload = {
            "inputs": [text],
            "target_language_code": language_code,
            "speaker": speaker,
            "model": model,
            "speech_sample_rate": 22050 if model == "bulbul:v2" else 24000,
            "pace": pace,
            "enable_preprocessing": enable_preprocessing,
            "output_audio_format": "wav"
        }
        
        if model == "bulbul:v2":
            payload["pitch"] = pitch
            payload["loudness"] = loudness
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/text-to-speech",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            audio_b64 = data.get("audios", [""])[0]
            return base64.b64decode(audio_b64)
    
    async def chat_completion(
        self,
        messages: list[dict],
        model: str = "sarvam-105b",
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> str:
        """Get chat completion from Sarvam LLM."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if not content:
                raise ValueError(
                    f"Sarvam chat completion returned empty content "
                    f"(finish_reason={data['choices'][0].get('finish_reason')}); "
                    f"increase max_tokens if the model was still reasoning"
                )
            return content


# Singleton instance
sarvam_service = SarvamService()
