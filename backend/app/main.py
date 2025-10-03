import io, zipfile
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from .db import engine, SessionLocal, Base
from .models import User
from .schemas import UserCreate, UserLogin, TokenResponse
from .auth import hash_password, verify_password, create_token, get_current_user_id
from .music import build_prompt, generate_music_bytes

app = FastAPI(title="TaG Ai API (MVP)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/auth/register", response_model=TokenResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == user.username)):
        raise HTTPException(status_code=400, detail="Username already exists")
    u = User(username=user.username, password_hash=hash_password(user.password), email=user.email)
    db.add(u); db.commit(); db.refresh(u)
    token = create_token(u.id)
    return TokenResponse(access_token=token)

@app.post("/auth/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    u = db.scalar(select(User).where(User.username == credentials.username))
    if not u or not verify_password(credentials.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(u.id)
    return TokenResponse(access_token=token)

@app.post("/covers/create")
async def create_cover(
    genre: str = Form(...),
    mood: str = Form(...),
    voice_type: str = Form(...),
    key_shift: int = Form(0),
    instruments: str = Form(""),
    audio: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id)
):
    inst_list = [s.strip() for s in instruments.split(",") if s.strip()]
    prompt = build_prompt(genre, inst_list, voice_type, mood, key_shift)
    audio_1 = generate_music_bytes(prompt)
    audio_2 = generate_music_bytes(prompt + " alternate arrangement, different groove")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("cover_option_1.mp3", audio_1)
        z.writestr("cover_option_2.mp3", audio_2)
        z.writestr("instrumental_option_1.mp3", b"")
        z.writestr("instrumental_option_2.mp3", b"")
        z.writestr("stems/README.txt", "Stems to be added in advanced build.")
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="tag_ai_covers.zip"'})