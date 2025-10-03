from pydantic import BaseModel
from typing import List

class UserCreate(BaseModel):
    username: str
    password: str
    email: str | None = None

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CreateCoverRequest(BaseModel):
    genre: str
    instruments: List[str] = []
    voice_type: str  # 'male' | 'female' | 'duet'
    mood: str
    key_shift: int = 0  # -12..+12 semitones