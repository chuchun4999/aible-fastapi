from fastapi import FastAPI,Form
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import pymysql  
import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import FastAPI, HTTPException

app = FastAPI()

pymysql.install_as_MySQLdb()  # pymysql을 MySQLdb로 설정

MYSQL_URL = os.getenv("MYSQL_URL")  # Railway 환경변수에서 MySQL URL 가져오기
engine = create_engine(MYSQL_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 시 특정 도메인으로 제한할 것
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PreSubmit(Base):
    __tablename__ = "pre_submit"  # Railway에 생성된 테이블 이름과 동일해야 함

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()

# 입력 데이터 모델 정의
class InputData(BaseModel):
    email: str


# 데이터베이스 세션 종속성 정의
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Hello, Railway!"}

@app.post("/pre")
def add_data(input_data: InputData, db: Session = Depends(get_db)):
    print(f"📩 새로운 이메일 저장 시도: {input_data.email}")
    existing_entry = db.query(PreSubmit).filter(PreSubmit.email == input_data.email).first()
    if existing_entry:
        print("⚠️ 이미 존재하는 이메일입니다!")
        raise HTTPException(status_code=400, detail="Email already exists in database")
    new_entry = PreSubmit(email=input_data.email)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    print(f"✅ 이메일 저장 성공: {input_data.email}")
    return {"message": "Data added successfully!", "email": new_entry.email}


# GET 요청 테스트용 API
@app.get("/test")
def read_root():
    return {"message": "Hello, FastAPI + React!"}


# POST 요청 API (React에서 호출할 API)
@app.post("/process/")
def process_data(data: InputData):
    response = {"processed_text": data.text.upper()}
    return response

@app.get("/routes")
def get_routes():
    return { "routes": "이거 왜 안댐"}

@app.post("/submit")
async def submit_form(
    user_id: str = Form(...),  # 필수 필드
    gender: str = Form(...),  # 필수 필드
    age: int = Form(...),     # 필수 필드
    smoking: str = Form(...), # 필수 필드
    smoking_avg: int = Form(None),  # 선택 필드
    exercise: str = Form(...),      # 필수 필드
    exercise_freq: int = Form(None), # 선택 필드
    disability: str = Form(...),    # 필수 필드
    comments: str = Form(None),     # 선택 필드
    세부장애: object = Form(None)
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
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Railway에서 자동 할당된 포트 사용
    uvicorn.run(app, host="0.0.0.0", port=port)