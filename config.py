SERVICE_NAME = "speech_recognition"
USERNAME = "current_user"
APIS = {
    "OpenAI": {
        "username": "openai_api_key",
        "test_url": "https://api.openai.com/v1/models",
        "audio_url": "https://api.openai.com/v1/audio/transcriptions",
        "chat_url": "https://api.openai.com/v1/chat/completions"
    },
    "Google": {
        "username": "google_api_key",
        "model_name": "gemini-1.5-flash",
        "test_prompt": "Generate one test question"
    }
}