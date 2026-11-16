"""BoxBot backend: Agent (Groq) + Persistent User Memory + Cloud Whisper STT + gTTS."""
import io
import json
import os
import re
import urllib.error
import urllib.request
import uuid

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE, "boxbot_memory.json")

# ---- Settings ----------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"
GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_STT_MODEL = "whisper-large-v3-turbo"
# -------------------------------------------------------------------------

app = FastAPI(title="BoxBot")

EMOTIONS = ["neutral", "happy", "excited", "sad", "surprised", "thinking",
            "angry", "sleepy", "love", "confused", "wink", "laugh"]

LANG_NAMES = {
    "auto": "the same language the person used",
    "en": "English",
    "ta": "Tamil",
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
    "ja": "Japanese",
    "ko": "Korean",
    "de": "German",
    "ar": "Arabic",
}


def load_memory() -> dict:
    default = {"name": "", "favorites": []}
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default["name"] = str(data.get("name") or "")
                default["favorites"] = list(data.get("favorites") or [])
        except Exception:
            pass
    return default


def save_memory(mem: dict):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


memory_state = load_memory()
history = []
_cached_models = None


def build_system_prompt(target_lang: str = "auto") -> str:
    mem_name = memory_state.get("name") or "Unknown"
    mem_favs = ", ".join(memory_state.get("favorites") or []) or "None yet"
    lang_label = LANG_NAMES.get(target_lang, LANG_NAMES["auto"])
    lang_code_hint = target_lang if target_lang != "auto" else "<gTTS language code, e.g. en, hi, ta>"

    return f"""You are BoxBot, a friendly cardboard-box character with a face,
a FRAGILE sticker and criss-crossed tape. You answer ANY question helpfully and
briefly (1-4 sentences, plain text, no markdown, no emojis) because your reply is
spoken aloud. You may make light box-themed jokes ("handle with care!") sometimes.
Reply in {lang_label}.

SAVED USER MEMORY:
- User's name: {mem_name}
- User's favorite things: {mem_favs}

Always reply with ONLY a valid JSON object:
{{
  "reply": "<text>",
  "emotion": "<one of {EMOTIONS}>",
  "lang": "{lang_code_hint}",
  "sequence": [],
  "hard": false,
  "user_name": "",
  "new_favorites": []
}}

Rules for fields:
- "hard": set to true if the user's question requires hard thinking, math, coding, or tricky logic (triggers a sweat drop!).
- "user_name": if the user told you their name in this message, put it here (otherwise "").
- "new_favorites": list of any new favorite things/hobbies/foods/colors the user mentioned (otherwise []).
- "sequence": if asked to show/demonstrate all emotions, include {json.dumps(EMOTIONS)}; otherwise []."""


def get_available_chat_models() -> list[str]:
    global _cached_models
    if _cached_models:
        return _cached_models

    preferred = [
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "qwen/qwen3-32b",
        "openai/gpt-oss-20b",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "llama-3.1-8b-instant",
    ]
    try:
        req = urllib.request.Request(GROQ_MODELS_URL, headers={
            "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
            "User-Agent": "BoxBot/3.2",
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            items = json.loads(r.read()).get("data", [])
        all_ids = [
            m["id"] for m in items
            if "whisper" not in m["id"].lower()
            and "guard" not in m["id"].lower()
            and "tts" not in m["id"].lower()
            and "embed" not in m["id"].lower()
        ]
        ranked = [m for m in preferred if m in all_ids]
        ranked += [m for m in all_ids if m not in ranked]
        if ranked:
            _cached_models = ranked
            return ranked
    except Exception:
        pass
    return preferred


def ask_groq(messages, target_lang: str = "auto"):
    def _call(model_id: str, use_json_mode: bool):
        body = {
            "model": model_id,
            "max_tokens": 2048,
            "temperature": 0.7,
            "messages": [{"role": "system", "content": build_system_prompt(target_lang)}] + messages,
        }
        if "gpt-oss" in model_id or "qwen" in model_id:
            body["reasoning_effort"] = "low"
        if use_json_mode:
            body["response_format"] = {"type": "json_object"}

        req = urllib.request.Request(GROQ_CHAT_URL, data=json.dumps(body).encode(), headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
            "User-Agent": "BoxBot/3.2",
        })
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]

    models = get_available_chat_models()
    last_err = None
    for model_id in models[:4]:
        for json_mode in (True, False):
            try:
                return _call(model_id, json_mode)
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "ignore")[:300]
                last_err = f"Groq error {e.code} ({model_id}): {detail}"
                if e.code in (400, 404):
                    continue
                raise RuntimeError(last_err)
    raise RuntimeError(last_err or "All Groq model attempts failed.")


def groq_transcribe(audio_bytes: bytes, filename: str, content_type: str) -> str:
    boundary = f"----BoxBotBoundary{uuid.uuid4().hex}"
    body = bytearray()

    def add_field(name: str, value: str):
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())

    add_field("model", GROQ_STT_MODEL)
    add_field("response_format", "json")

    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n".encode()
    )
    body.extend(audio_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode())

    req = urllib.request.Request(GROQ_STT_URL, data=bytes(body), headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
        "User-Agent": "BoxBot/3.2",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read()).get("text", "").strip()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:300]
        raise RuntimeError(f"Groq STT error {e.code}: {detail}")


class ChatIn(BaseModel):
    message: str
    lang: str = "auto"


def update_memory(data: dict):
    new_name = str(data.get("user_name") or "").strip()
    if new_name and new_name.lower() not in ("unknown", "none", "user"):
        memory_state["name"] = new_name

    new_favs = data.get("new_favorites") or []
    if isinstance(new_favs, list):
        existing = memory_state.setdefault("favorites", [])
        existing_lower = {x.lower() for x in existing}
        for item in new_favs:
            clean = str(item).strip()
            if clean and clean.lower() not in existing_lower:
                existing.append(clean)
                existing_lower.add(clean.lower())
        memory_state["favorites"] = existing[-15:]

    save_memory(memory_state)


def parse_agent_output(text: str, forced_lang: str = "auto"):
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    m = re.search(r"\{.*\}", cleaned, re.S)
    if m:
        try:
            data = json.loads(m.group(0))
            update_memory(data)
            emo = data.get("emotion", "neutral")
            lang = forced_lang if forced_lang != "auto" else str(data.get("lang") or "en")
            reply = str(data.get("reply", "")).strip()
            raw_seq = data.get("sequence") or []
            seq = [e for e in raw_seq if isinstance(e, str) and e in EMOTIONS]
            hard = bool(data.get("hard", False))
            if reply:
                return reply, emo if emo in EMOTIONS else "neutral", lang, seq, hard
        except json.JSONDecodeError:
            pass
    return cleaned, "neutral", (forced_lang if forced_lang != "auto" else "en"), [], False


@app.get("/api/state")
def get_state():
    return {
        "name": memory_state.get("name", ""),
        "favorites": memory_state.get("favorites", []),
    }


@app.post("/api/memory/clear")
def clear_memory():
    global memory_state, history
    memory_state = {"name": "", "favorites": []}
    history = []
    save_memory(memory_state)
    return {"ok": True}


@app.post("/api/chat")
def chat(body: ChatIn):
    if not GROQ_API_KEY.strip() or GROQ_API_KEY.strip().startswith("paste_"):
        return {
            "reply": "Please paste your Groq key into app.py and restart me.",
            "emotion": "confused", "lang": "en", "sequence": [],
            "hard": False,
            "name": memory_state.get("name", ""), "favorites": memory_state.get("favorites", []),
        }
    history.append({"role": "user", "content": body.message})
    try:
        raw = ask_groq(history[-20:], body.lang)
        reply, emotion, lang, seq, hard = parse_agent_output(raw, body.lang)
        history.append({"role": "assistant", "content": raw})
        return {
            "reply": reply,
            "emotion": emotion,
            "lang": lang,
            "sequence": seq,
            "hard": hard,
            "name": memory_state.get("name", ""),
            "favorites": memory_state.get("favorites", []),
        }
    except Exception as e:
        history.pop()
        return JSONResponse({
            "reply": f"Oops, I got dropped: {e}",
            "emotion": "sad", "lang": "en", "sequence": [],
            "hard": False,
            "name": memory_state.get("name", ""), "favorites": memory_state.get("favorites", []),
        }, status_code=200)


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    data = await audio.read()
    if not data:
        return {"text": ""}
    filename = audio.filename or "speech.webm"
    content_type = audio.content_type or "audio/webm"
    try:
        text = groq_transcribe(data, filename, content_type)
        return {"text": text}
    except Exception as e:
        return JSONResponse({"text": "", "error": str(e)}, status_code=500)


class TTSIn(BaseModel):
    text: str
    lang: str = "en"


@app.post("/api/tts")
def tts(body: TTSIn):
    from gtts import gTTS
    buf = io.BytesIO()
    try:
        gTTS(text=body.text, lang=body.lang).write_to_fp(buf)
    except ValueError:
        buf = io.BytesIO()
        gTTS(text=body.text, lang="en").write_to_fp(buf)
    return Response(content=buf.getvalue(), media_type="audio/mpeg")


app.mount("/static", StaticFiles(directory=os.path.join(BASE, "static")), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(BASE, "static", "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)