from fastapi import *
from fastapi import APIRouter, Request
from pydantic import BaseModel
from jose import jwt
from jwt import PyJWTError
from fastapi.responses import FileResponse, JSONResponse
from app.config import DB_CONFIG, SECRET_KEY, ALGORITHM
from app.auth import hash_password, verify_password
from app.models import deleteProfile, updatePassword, updateProfile
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta, timezone


router = APIRouter()

@router.put("/api/user/change-password")
async def update_password(request: Request, update_password: updatePassword, response: Response):
    #檢查是否有token
    token = request.headers.get('Authorization')
    conn = None
    cursor = None

    # 有登入的使用者
    extracted_token = token[len("Bearer "):]
    try:
        payload = jwt.decode(extracted_token, SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError:
        return JSONResponse(
            status_code = 403,
            content = {
                "error": True,
                "message": "未登入系統，拒絕存取"
            }
        )

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        booking_user_id = payload.get("id")
        old_pass = update_password.oldPassword
        new_pass = hash_password(update_password.newPassword)
        cursor.execute(
            "SELECT id, name, email, hashed_password FROM member WHERE id = %s",
            (booking_user_id,)
        )
        fetched_user = cursor.fetchone()
        if not fetched_user:
            return JSONResponse(
                status_code=400, 
                content={"error": True, "message": "token有誤"}
            )          
        if not verify_password(old_pass, fetched_user["hashed_password"]):
            return JSONResponse(
                status_code=400, 
                content={"error": True, "message": "密碼錯誤"}
            )

        if fetched_user:            
            update_query = """
            UPDATE member
            SET hashed_password = %s
            WHERE id = %s;
            """
            cursor.execute(update_query, (
                new_pass,
                booking_user_id
                )
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"error": True, "message": "No data found in database"}
            )
        conn.commit()
        return JSONResponse(
            status_code= 200,
            content = {
                "ok": True,
                "message": "Password updated!"
            }
        )
    except mysql.connector.Error as err:
        return JSONResponse(
            status_code=400,
            content = {
                "error": True,
                "message": "更新失敗，輸入不正確或其他原因",
                "details": str(err)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "伺服器內部錯誤",
                "details": str(e)
            }
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.put("/api/user/edit-profile")
async def update_profile(request: Request, update_profile: updateProfile, response: Response):
    #檢查是否有token
    token = request.headers.get('Authorization')
    if not token:
        return JSONResponse(
            status_code=403,
            content={
                "error": True,
                "message": "No token provided, access denied"
            }
        )

    # 有登入的使用者
    extracted_token = token[len("Bearer "):]
    try:
        payload = jwt.decode(extracted_token, SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError:
        return JSONResponse(
            status_code = 403,
            content = {
                "error": True,
                "message": "未登入系統，拒絕存取"
            }
        )

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        booking_user_id = payload.get("id")
        name = update_profile.name
        email = update_profile.email
        cursor.execute(
            "SELECT id, name, email, hashed_password FROM member WHERE id = %s",
            (booking_user_id,)
        )
        fetched_user = cursor.fetchone()
        if not fetched_user:
            return JSONResponse(
                status_code=400, 
                content={"error": True, "message": "token有誤"}
            )          
        if fetched_user:            
            update_query = """
            UPDATE member
            SET name = %s, email = %s
            WHERE id = %s;
            """
            cursor.execute(update_query, (
                name,
                email,
                booking_user_id
                )
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"error": True, "message": "No data found in database"}
            )
        conn.commit()

        # Generate a new JWT token with the updated user details
        updated_data = {
            "id": booking_user_id,
            "name": name,
            "email": email
        }
        expire_time = datetime.now(timezone.utc) + timedelta(days=7)
        updated_data.update({"exp": expire_time})
        new_token = jwt.encode(updated_data, SECRET_KEY, algorithm=ALGORITHM)

        return JSONResponse(
            status_code= 200,
            content = {
                "ok": True,
                "message": "Profile updated!",
                "token": new_token
            }
        )
    except mysql.connector.Error as err:
        return JSONResponse(
            status_code=400,
            content = {
                "error": True,
                "message": "更新失敗，輸入不正確或其他原因",
                "details": str(err)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "伺服器內部錯誤",
                "details": str(e)
            }
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.delete("/api/user/delete-profile")
async def delete_profile(request: Request, delete_profile: deleteProfile, response: Response):
    #檢查是否有token
    token = request.headers.get('Authorization')
    if not token:
        raise HTTPException(status_code=403, detail="No token provided, access denied")

    # 有登入的使用者
    extracted_token = token[len("Bearer "):]
    try:
        payload = jwt.decode(extracted_token, SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError:
        return JSONResponse(
            status_code = 403,
            content = {
                "error": True,
                "message": "未登入系統，拒絕存取"
            }
        )

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        booking_user_id = payload.get("id")
        old_pass = delete_profile.password
        cursor.execute(
            "SELECT id, name, email, hashed_password FROM member WHERE id = %s",
            (booking_user_id,)
        )
        fetched_user = cursor.fetchone()
        if not fetched_user:
            return JSONResponse(
                status_code=400, 
                content={"error": True, "message": "token有誤"}
            )          
        if not verify_password(old_pass, fetched_user["hashed_password"]):
            return JSONResponse(
                status_code=400, 
                content={"error": True, "message": "密碼錯誤"}
            )

        if fetched_user:            
            update_query = """
            DELETE FROM member
            WHERE id = %s;
            """
            cursor.execute(update_query, (
                booking_user_id,
                )
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"error": True, "message": "No data found in database"}
            )
        conn.commit()
        return JSONResponse(
            status_code= 200,
            content = {
                "ok": True,
                "message": "Profile deleted successfully"
            }
        )
    except mysql.connector.Error as err:
        return JSONResponse(
            status_code=400,
            content = {
                "error": True,
                "message": "更新失敗，輸入不正確或其他原因",
                "details": str(err)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "伺服器內部錯誤",
                "details": str(e)
            }
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()