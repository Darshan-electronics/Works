import os
from pathlib import Path
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parent.parent
ENV_FILE=ROOT/'.env'
load_dotenv(ENV_FILE, override=False)
DATA=ROOT/'data'; DATA.mkdir(exist_ok=True)
ACCESS_TOKEN=os.getenv('JARVIS_ACCESS_TOKEN','')

def get_access_token():
    load_dotenv(ENV_FILE, override=False)
    return os.getenv('JARVIS_ACCESS_TOKEN','')
AI_PROVIDER=os.getenv('AI_PROVIDER','ollama').lower()
OPENAI_API_KEY=os.getenv('OPENAI_API_KEY','')
OPENAI_MODEL=os.getenv('OPENAI_MODEL','gpt-5.6')
OPENAI_IMAGE_MODEL=os.getenv('OPENAI_IMAGE_MODEL','gpt-image-1')
OPENAI_TTS_MODEL=os.getenv('OPENAI_TTS_MODEL','gpt-4o-mini-tts')
OPENAI_TRANSCRIBE_MODEL=os.getenv('OPENAI_TRANSCRIBE_MODEL','gpt-4o-mini-transcribe')
OLLAMA_BASE_URL=os.getenv('OLLAMA_BASE_URL','http://127.0.0.1:11434').rstrip('/')
OLLAMA_MODEL=os.getenv('OLLAMA_MODEL','qwen3.5:9b')
GITHUB_OWNER=os.getenv('GITHUB_OWNER','Darshan-electronics')
GITHUB_TOKEN=os.getenv('GITHUB_TOKEN','')
WORKSPACE=Path(os.getenv('JARVIS_WORKSPACE',str(ROOT/'workspace'))).expanduser().resolve(); WORKSPACE.mkdir(parents=True,exist_ok=True)
DB_PATH=Path(os.getenv('JARVIS_DB',str(DATA/'jarvis.db'))).expanduser().resolve()
CONFIRM_MEDIUM=os.getenv('REQUIRE_CONFIRMATION_MEDIUM','true').lower()=='true'
CONFIRM_HIGH=os.getenv('REQUIRE_CONFIRMATION_HIGH','true').lower()=='true'
CONFIRM_CRITICAL=os.getenv('REQUIRE_CONFIRMATION_CRITICAL','true').lower()=='true'
WEB_RESEARCH_ENABLED=os.getenv('WEB_RESEARCH_ENABLED','true').lower()=='true'
SEARXNG_URL=os.getenv('SEARXNG_URL','http://127.0.0.1:8081').rstrip('/')

def get_web_research_enabled():
    load_dotenv(ENV_FILE, override=False)
    return os.getenv('WEB_RESEARCH_ENABLED','true').strip().lower() in {'1','true','yes','on'}

def get_searxng_url():
    load_dotenv(ENV_FILE, override=False)
    return os.getenv('SEARXNG_URL','http://127.0.0.1:8081').rstrip('/')

def get_searxng_urls():
    primary = get_searxng_url()
    configured = os.getenv('SEARXNG_FALLBACK_URLS','http://127.0.0.1:8888')
    urls = [primary] + [x.strip().rstrip('/') for x in configured.split(',') if x.strip()]
    return list(dict.fromkeys(urls))
