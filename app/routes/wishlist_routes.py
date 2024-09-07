from fastapi import *
from fastapi import APIRouter, Request
from pydantic import BaseModel
import uuid
import mysql.connector
from app.config import DB_CONFIG, SECRET_KEY, ALGORITHM
from app.utils import serialize_item
from fastapi.responses import FileResponse, JSONResponse
from jose import jwt
from jwt import PyJWTError

router = APIRouter()

class WishInfo(BaseModel):
    product_id: str

@router.post("/api/wishlist/add")
async def add_to_wishlist(request: Request, wishlist: WishInfo):
    product_id = wishlist.product_id
    #print(product_id)
    #檢查是否有token或session
    token = request.headers.get('Authorization')
    conn = None
    cursor = None
    response = None
    #沒登入的人
    if not token or not token.startswith("Bearer "):
        #檢查是否有session_id
        session_id = request.headers.get("X-Session-ID")
        #print(session_id)
        #如果沒有session_id
        if not session_id:
            session_id = str(uuid.uuid4())  # Generate a new session_id
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("INSERT INTO wishlist (session_id, product_id) VALUES (%s, %s)", (session_id, product_id))
            conn.commit()
            conn.close()
            cursor.close()
            response = JSONResponse(
                status_code=200,
                content={"ok": True, "session_id": session_id, "message": "Product added to wishlist"}
            )
            return response
        #如果有session_id
        else:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            #檢查是否重複加
            cursor.execute("SELECT * FROM wishlist WHERE product_id = %s AND session_id = %s", (product_id, session_id))
            double_entry = cursor.fetchone()
            #print(double_entry)
            if double_entry:
                response = JSONResponse(
                status_code=200,
                content={"error": True, "message": "Product is already in wishlist"}
                )
                return response
            cursor.execute("INSERT INTO wishlist (session_id, product_id) VALUES (%s, %s)", (session_id, product_id))
            conn.commit()
            conn.close()
            cursor.close()
            response = JSONResponse(
                status_code=200,
                content={"ok": True, "message": "Product added to wishlist"}
            )
            return response

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
        wish_user_id = payload.get("id")

        #看看是否已經有同樣商品存在wishlist
        cursor.execute("SELECT * FROM wishlist WHERE user_id = %s AND product_id LIKE %s", (wish_user_id, product_id))
        already_there = cursor.fetchone()
        if already_there:
            return JSONResponse(
                status_code=200,
                content={"error": True, "message": "Product is already in wishlist"}
                )
        else:
            cursor.execute("INSERT INTO wishlist (user_id, product_id) VALUES (%s, %s)", (wish_user_id, product_id))
        conn.commit()
        return JSONResponse(
            status_code= 200,
            content = {
                "ok": True,
                "message": "Product added to wishlist"
            }
        )
    except mysql.connector.Error as err:
        return JSONResponse(
            status_code=400,
            content = {
                "error": True,
                "message": "建立失敗，輸入不正確或其他原因"
            }
        )
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

@router.get("/api/wishlist")
async def get_wishlist(request: Request):
    # Extract token and session_id from headers
    token = request.headers.get('Authorization')
    session_id = request.headers.get('X-Session-ID')
    user_id = None

    # If token is present, decode the JWT to get the user_id
    if token and token != "Bearer null":
        extracted_token = token[len("Bearer "):]
        #print("extracted token:", extracted_token)
        try:
            payload = jwt.decode(extracted_token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("id")
        except jwt.PyJWTError:
            raise HTTPException(status_code=403, detail="Invalid token")

    elif not session_id:
        return JSONResponse(
            status_code=200,
            content={
                "error": True, 
                "message": "沒有session_id也沒有最愛清單"
            }
        )
    

    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        if user_id:
            cursor.execute("SELECT product_id FROM wishlist WHERE user_id = %s", (user_id,))
        else:
            cursor.execute("SELECT product_id FROM wishlist WHERE user_id = %s", (user_id,))

        wishlist_items = cursor.fetchall()

        # Convert any Decimal fields to float
        wishlist_items = [serialize_item(item) for item in wishlist_items]
        #print(wishlist_items)

        if (wishlist_items):
            products_with_images = []

            for item in wishlist_items:
                booked_item_id = item['product_id']
                product_query = """
                SELECT f.Name, f.Price, f.Page_link, f.Description, f.Dimension, i.url
                FROM furnitures f
                JOIN images i ON f.Product_id = i.product_id
                WHERE f.Product_id = %s
                ORDER BY i.image_id ASC
                LIMIT 1;
                """
                cursor.execute(product_query, (booked_item_id,))
                product_details = cursor.fetchone()
                #print(product_details)

                if product_details:
                    adjusted_response = {
                        "product": {
                        "id": booked_item_id,
                        "name": product_details['Name'],
                        "price": float(product_details['Price']),
                        "page_link": product_details['Page_link'],
                        "description": product_details['Description'],
                        "dimension": product_details['Dimension'],
                        "image": product_details['url'],
                        }
                    }
                    products_with_images.append(adjusted_response)

            return JSONResponse(status_code=200, content=products_with_images)
        #如果沒有商品在購物車
        return JSONResponse(
            status_code=200,
            content=[]
        )

    except mysql.connector.Error as err:
        return JSONResponse(
            status_code=500,
            content={
                "error": True, 
                "message": "Database query failed" + str(err)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={
                "error": True,
                "message": "伺服器內部錯誤" + str(e)
                }
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.delete("/api/wishlist")
async def delete_wishlist(request: Request):
    #檢查是否有token
    token = request.headers.get('Authorization')
    if not token or not token.startswith("Bearer "):
        return JSONResponse(
            status_code = 403,
            content = {
                "error": True,
                "message": "未登入系統，拒絕存取"
            }
        )    
        
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
    
    # 確保接收到的請求 body 是 JSON 格式
    request_data = await request.json()
    product_id = request_data.get("product_id")

    if not product_id:
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "message": "缺少 product_id"
            }
        )
    
    #開始刪除
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        booking_user_id = payload.get("id")

        delete_query = "DELETE FROM wishlist WHERE user_id = %s AND product_id = %s"
        cursor.execute(delete_query, (booking_user_id, product_id))
        conn.commit()
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "message": "商品刪除成功"
            }
        )
    except mysql.connector.Error as err:
        return JSONResponse(
            status_code=400,
            content = {
                "error": True,
                "message": "刪除失敗，輸入不正確或其他原因"
            }
        )
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