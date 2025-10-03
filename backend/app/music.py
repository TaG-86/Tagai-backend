import os, requests

HF_API_KEY = os.getenv("HF_API_KEY", "")
HF_MUSICGEN_MODEL = os.getenv("HF_MUSICGEN_MODEL", "facebook/musicgen-small")

INFER_URL = f"https://api-inference.huggingface.co/models/{HF_MUSICGEN_MODEL}"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"} if HF_API_KEY else {}

def build_prompt(genre: str, instruments: list[str], voice_type: str, mood: str, key_shift: int) -> str:
    instr = ", ".join(instruments) if instruments else "instruments"
    voice = {"male":"male vocal", "female":"female vocal", "duet":"male and female duet"}.get(voice_type, "vocal")
    shift_txt = f" key shift {key_shift:+d} semitones" if key_shift else ""
    return f"A {genre} cover with {instr}, {voice}, {mood} mood,{shift_txt} high quality."

def generate_music_bytes(prompt: str) -> bytes:
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 256}}
    r = requests.post(INFER_URL, headers=HEADERS, json=payload, timeout=120)
    r.raise_for_status()
    return r.content