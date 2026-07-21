"""Application configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Sarvam AI
    sarvam_api_key: str = Field(..., alias="SARVAM_API_KEY")
    sarvam_base_url: str = "https://api.sarvam.ai"
    
    # Twilio
    twilio_account_sid: str = Field(..., alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(..., alias="TWILIO_AUTH_TOKEN")
    twilio_phone_number: str = Field(..., alias="TWILIO_PHONE_NUMBER")
    
    # App
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Call
    default_language: str = Field(default="hi-IN", alias="DEFAULT_LANGUAGE")
    welcome_message: str = Field(
        default="नमस्ते, मैं आपकी कार सर्विस बुकिंग में मदद कर सकता हूँ। कृपया बताएं आप क्या चाहते हैं?",
        alias="WELCOME_MESSAGE"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
