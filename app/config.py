import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "5"))

MAX_RETRY_ATTEMPTS = 3
CONFIDENCE_THRESHOLD = 6  # Production threshold


from langchain_core.callbacks import BaseCallbackHandler
from app.utils.logger import log

class FallbackNotifyHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        # We only log once per object instance to avoid log spam on automatic retries
        if not getattr(self, "_notified", False):
            log("System", "WARNING", "Parent model rate-limited; shifting to less powerful model llama-3.1-8b-instant")
            self._notified = True

def get_llm(temperature: float = 0.2):
    primary_llm = ChatGroq(
        model=LLM_MODEL,
        api_key=GROQ_API_KEY,
        temperature=temperature,
        max_tokens=1024,
    )
    
    fallback_llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=GROQ_API_KEY,
        temperature=temperature,
        max_tokens=1024,
        callbacks=[FallbackNotifyHandler()]
    )
    
    return primary_llm.with_fallbacks([fallback_llm])
