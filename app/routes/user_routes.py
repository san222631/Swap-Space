from fastapi import *
from fastapi import APIRouter, HTTPException, Request
from ..auth import hash_password, verify_password
from app.models import registerInfo, Token, UserInfo
from app.config import DB_CONFIG, SECRET_KEY, ALGORITHM

import mysql.connector
from fastapi.responses import FileResponse, JSONResponse
import traceback
from datetime import datetime, timedelta, timezone
from jose import jwt
from jwt import PyJWTError


router = APIRouter()

@router.post("/api/user")
async def signup(register_Info: registerInfo):
    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        register_name = register_Info.name
        register_email = register_Info.email
        register_password = hash_password(register_Info.password)        

        #確認有沒有一樣的email已經在資料庫
        cursor.execute("SELECT * FROM member WHERE email = %s", (register_email,))
        existingUser = cursor.fetchone()

        if (existingUser):
            return JSONResponse(
                status_code=400,
                content={
                    "error": True,
                    "message": "email已經註冊過"
                }
            )           

        register_query = """
        INSERT INTO member (name, email, hashed_password)
        VALUES
        (%s, %s, %s)
        """
        cursor.execute(
            register_query,
            (register_name, register_email, register_password)
        )
        conn.commit()
        return {"ok": True}
    except mysql.connector.Error as err:
        print("MySQL Error:", err)
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "MySQL出了問題"
            }
        )
    except Exception as e:
        print("General Error:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "伺服器內部錯誤"
            }
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.put("/api/user/auth", response_model=Token)
async def login(user_info: UserInfo, response: Response):
    conn = None
    cursor = None
    #進資料庫檢查有沒有這個帳號密碼
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        received_email = user_info.email
        received_password = user_info.password
        cursor.execute(
            "SELECT id, name, email, hashed_password FROM member WHERE email = %s",
            (received_email,)
        )
        fetched_user = cursor.fetchone()
        #verify_password = pwd_context.verify(received_password, fetched_user["hashed_password"])

        #要return None嗎?
        if not fetched_user:
            return JSONResponse(
                status_code=400, 
                content={"error": True, "message": "找不到這位使用者"}
            )          
        if not verify_password(received_password, fetched_user["hashed_password"]):
            return JSONResponse(
                status_code=400, 
                content={"error": True, "message": "密碼錯誤"}
            )       
        
        #在token加入有效的時間，然後加密
        original_data = {
            "id": fetched_user["id"],
            "name": fetched_user["name"],
            "email": fetched_user["email"]}
        data_to_encode = original_data.copy()
        expire_time = datetime.now(timezone.utc) + timedelta(days=7)
        data_to_encode.update({"exp": expire_time})
        encoded_jwt = jwt.encode(data_to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return {"token": encoded_jwt} 
        
    except mysql.connector.Error as err:
        return JSONResponse(
            status_code=500, 
            content={"error": True, "message": "內部伺服器錯誤"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"error": True, "message": "內部伺服器錯誤"}
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/api/user/auth")
async def authenticate(request: Request):
    #從前端送過來的headers get"Authorization"然後decode
    auth_header = request.headers.get("Authorization")
    #print(auth_header)
    if auth_header is None or not auth_header.startswith("Bearer "):
        return None

    extracted_token = auth_header[len("Bearer "):]
    try:
        payload = jwt.decode(extracted_token, SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError:
        return None
    
    #資料庫內驗證使用者
    conn =None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        user_email = payload.get("email")
        #print(user_email)
        cursor.execute(
            "SELECT id, name, email FROM member WHERE email = %s",
            (user_email,)
        )
        verified_user = cursor.fetchone()
        #print(verified_user)
        if not verified_user:
            return None
        return {"data": verified_user}    

    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={
                "error": True,  
                "message": "伺服器內部錯誤"
                }
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()    