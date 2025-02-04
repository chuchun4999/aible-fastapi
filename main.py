from fastapi import FastAPI,Form
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import pymysql  
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
# 입력 데이터 모델 정의
class InputData(BaseModel):
    text: str

# GET 요청 테스트용 API
@app.get("/test")
def read_root():
    return {"message": "Hello, FastAPI + React!"}

# POST 요청 API (React에서 호출할 API)
@app.post("/process/")
def process_data(data: InputData):
    response = {"processed_text": data.text.upper()}
    return response

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
