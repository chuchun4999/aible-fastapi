import os
import uuid
import uvicorn
import json
import pymysql
# import cv2
import base64
import numpy as np
# import Calibrator

from fastapi import FastAPI, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# SQLAlchemy 비동기 관련 import
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.ext.declarative import declarative_base

# fastapi-users 관련 import
from fastapi_users import FastAPIUsers, UUIDIDMixin, BaseUserManager, schemas
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase, SQLAlchemyBaseUserTable, SQLAlchemyBaseUserTableUUID
from fastapi_users.authentication import AuthenticationBackend, BearerTransport
from fastapi_users.authentication.strategy import JWTStrategy
from typing import AsyncGenerator
from fastapi_users import UUIDIDMixin

# ------------------ Database 설정 ------------------

# 단일 async 엔진 및 세션 생성 (동기 세션 생성기는 제거)
MYSQL_URL = os.getenv("MYSQL_URL")
if MYSQL_URL.startswith("mysql://"):
    MYSQL_URL = MYSQL_URL.replace("mysql://", "mysql+asyncmy://", 1)
engine = create_async_engine(MYSQL_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

# 단일 Base (모든 모델이 이 Base를 사용)
Base = declarative_base()

# ------------------ 일반 모델 (예: PreSubmit) ------------------
class PreSubmit(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    gender = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)

# 비동기 DB 세션 종속성 (일반 데이터용)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# ------------------ FastAPI 앱 설정 ------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chuchun4999.github.io"],  # 배포 시 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ PreSubmit 관련 엔드포인트 ------------------
class InputData(BaseModel):
    email: str
    gender: str
    age: int

@app.get("/")
async def read_root():
    return {"message": "Hello, Railway!"}

@app.post("/pre")
async def add_data(input_data: InputData, db: AsyncSession = Depends(get_db)):
    print(f"📩 새로운 이메일 저장 시도: {input_data.email}")
    stmt = select(PreSubmit).where(PreSubmit.email == input_data.email)
    result = await db.execute(stmt)
    existing_entry = result.scalars().first()
    if existing_entry:
        print("⚠️ 이미 존재하는 이메일입니다!")
        raise HTTPException(status_code=400, detail="Email already exists in database")
    new_entry = PreSubmit(email=input_data.email, gender=input_data.gender, age=input_data.age)
    db.add(new_entry)
    await db.commit()
    await db.refresh(new_entry)
    print(f"✅ 이메일 저장 성공: {input_data.email}")
    return {"message": "Data added successfully!", "email": new_entry.email}

@app.get("/test")
async def test_root():
    return {"message": "Hello, FastAPI + React!"}

# ------------------ 이미지 처리 엔드포인트 ------------------
class ImageData(BaseModel):
    image: str

# @app.post("/process_frame")
# async def process_frame(image_data: ImageData):
#     try:
#         # Base64 데이터에서 헤더 제거 후 디코딩
#         b64data = image_data.image.split(",")[1]
#         image_bytes = base64.b64decode(b64data)
#         image_np = np.frombuffer(image_bytes, dtype=np.uint8)
#         frame = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
#         calibrator = Calibrator(calibration_frames=1, rom_duration=3)
#         frame, joint_angles = calibrator.process_frame(frame)
#         return joint_angles
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# ------------------ 폼 제출 엔드포인트 ------------------
@app.post("/submit")
async def submit_form(
    user_id: str = Form(...),
    gender: str = Form(...),
    age: int = Form(...),
    smoking: str = Form(...),
    smoking_avg: int = Form(None),
    exercise: str = Form(...),
    exercise_freq: int = Form(None),
    disability: str = Form(...),
    comments: str = Form(None),
    세부장애: str = Form(None)
):
    return {
        "user_id": user_id,
        "gender": gender,
        "age": age,
        "smoking": smoking,
        "smoking_avg": smoking_avg,
        "exercise": exercise,
        "exercise_freq": exercise_freq,
        "disability": disability,
        "comments": comments,
    }

# ------------------ 테라피스트 매칭 엔드포인트 ------------------
class Teraphy(BaseModel):
    therapist_gender: str
    therapist_style: str
    exercise_intensity: str
    num_of_week: int

@app.post("/teraphy")
async def find_matching_therapist(input: Teraphy):
    with open('therapists.json', 'r', encoding='utf-8') as f:
        therapists = json.load(f)
    matching_therapists = [
        therapist for therapist in therapists
        if therapist["therapist_gender"] == input.therapist_gender
        and therapist["therapist_style"] == input.therapist_style
        and therapist["exercise_intensity"] == input.exercise_intensity
        and therapist["num_of_week"] == input.num_of_week
    ]
    return matching_therapists

# ------------------ fastapi-users 관련 설정 (비동기) ------------------
# 인증용 User 모델 (테이블명 충돌 방지를 위해 별도 이름 사용)
# fastapi‑users 관련 import
from fastapi_users import FastAPIUsers, UUIDIDMixin, BaseUserManager, schemas
from fastapi_users_db_sqlalchemy import (
    SQLAlchemyUserDatabase,
    SQLAlchemyBaseUserTableUUID,
)
from fastapi_users.authentication import AuthenticationBackend, BearerTransport
from fastapi_users.authentication.strategy import JWTStrategy
import uuid
# 인증용 User 모델 (테이블명 충돌 방지를 위해 별도 이름 사용)
class AuthUser(UUIDIDMixin, SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "auth_user"
    # SQLAlchemyBaseUserTableUUID가 이미 기본 컬럼들을 정의합니다.

# fastapi‑users 비동기 DB 세션 종속성 (AuthUser용)
async def get_user_db_users() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_user_db_users_wrapper(
    session: AsyncSession = Depends(get_user_db_users)
):
    yield SQLAlchemyUserDatabase(session, AuthUser)

# JWT 인증 설정 for fastapi‑users
SECRET = "SECRET_KEY"
bearer_transport_users = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy_users() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend_users = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport_users,
    get_strategy=get_jwt_strategy_users,
)

# 사용자 관리 클래스 for fastapi‑users
class UserManager(BaseUserManager[AuthUser, uuid.UUID]):
    user_db_model = AuthUser

    async def on_after_register(self, user: AuthUser, request=None):
        print(f"New auth user registered: {user.id}")
    def parse_id(self, user_id: str) -> uuid.UUID:
        return uuid.UUID(user_id)

# fastapi‑users 의존성 함수: 구체적인 UserManager를 반환하도록 수정
async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[AuthUser, uuid.UUID] = Depends(get_user_db_users_wrapper)
):
    yield UserManager(user_db)  # BaseUserManager 대신, 우리가 구현한 구체적인 UserManager를 반환

# fastapi‑users 스키마 설정
from fastapi_users import schemas

class UserRead(schemas.BaseUser[uuid.UUID]):
    pass

class UserCreate(schemas.BaseUserCreate):
    pass

class UserUpdate(schemas.BaseUserUpdate):
    pass

# FastAPIUsers 인스턴스 생성 (의존성 함수 사용)
fastapi_users_instance = FastAPIUsers[AuthUser, uuid.UUID](
    get_user_manager,
    [auth_backend_users]
)

app.include_router(
    fastapi_users_instance.get_auth_router(auth_backend_users),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users_instance.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users_instance.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


# ------------------ 데이터베이스 초기화 ------------------
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("startup")
async def on_startup_event():
    await init_db()


# ------------------ 애플리케이션 실행 ------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
