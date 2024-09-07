from fastapi import APIRouter, Request, HTTPException, Response
from pydantic import BaseModel
import uuid
import mysql.connector
from app.config import DB_CONFIG, SECRET_KEY, ALGORITHM
from fastapi.responses import FileResponse, JSONResponse
from jose import jwt
from jwt import PyJWTError


router = APIRouter()

class BookingInfo(BaseModel):
    productId: str
    quantity: int
    price: float

@router.post("/api/shop/cart")
async def save_booking_in_mysql(request: Request, booking_info: BookingInfo, response: Response):
    #檢查是否有token
    token = request.headers.get('Authorization')
    session_id = request.headers.get("X-Session-ID")
    conn = None
    cursor = None
    #沒登入的人
    if not token or not token.startswith("Bearer "):        
        if not session_id:
            session_id = str(uuid.uuid4())  # Generate a new session_id

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            booking_product_id = booking_info.productId
            booking_quantity = booking_info.quantity 
            booking_price = booking_info.price            
 
            cursor.execute("SELECT * FROM shopping_cart WHERE session_id = %s AND product_id LIKE %s", (session_id, booking_product_id))
            to_update = cursor.fetchone()
            if to_update:
                update_query = """
                UPDATE shopping_cart
                SET quantity = %s, updated_at = NOW()
                WHERE session_id = %s AND product_id LIKE %s
                """
                cursor.execute(update_query, (
                    booking_quantity,
                    session_id,
                    booking_product_id,
                ))
            else:
                query = """
                INSERT INTO shopping_cart (session_id, product_id, quantity, price, added_at, updated_at)
                VALUES
                (%s, %s, %s, %s, NOW(), NOW())
                """
                cursor.execute(query, (
                    session_id,
                    booking_product_id,
                    booking_quantity,
                    booking_price,
                ))
            conn.commit()
            return JSONResponse(content={"ok": True, "session_id": session_id})
        except mysql.connector.Error as err:
            return JSONResponse(
                status_code=400,
                content={
                    "error": True,
                    "message": "Failed to save booking. Please check your input."
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "message": "Internal server error"
                }
            )
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

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
        booking_product_id = booking_info.productId
        booking_quantity = booking_info.quantity 
        booking_price = booking_info.price

        #看看是否已經member_id存在booking table
        cursor.execute("SELECT * FROM shopping_cart WHERE user_id = %s AND product_id = %s", (booking_user_id, booking_product_id))
        to_update = cursor.fetchone()

        if to_update:            
            new_quantity = to_update["quantity"] + booking_quantity
            new_total_price = to_update["price"] * new_quantity
            #print(new_total_price)
            update_query = """
            UPDATE shopping_cart
            SET quantity = %s, total_price = %s
            WHERE user_id = %s AND product_id = %s
            """
            cursor.execute(update_query, (
                new_quantity,
                new_total_price,
                booking_user_id,
                booking_product_id
                )
            )
        else:
            total_price = booking_quantity * booking_price
            query = """
            INSERT INTO shopping_cart (user_id, product_id, quantity, price, total_price)
            VALUES
            (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                booking_user_id,
                booking_product_id,
                booking_quantity,
                booking_price,
                total_price
                )
            )
        conn.commit()
        return JSONResponse(
            status_code= 200,
            content = {
                "ok": True
            }
        )
    except mysql.connector.Error as err:
        return JSONResponse(
            status_code=400,
            content = {
                "error": True,
                "message": "建立失敗，輸入不正確或其他原因",
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

#SHOPPING CART APIs
#使用者想進入"預定行程"的頁面，透過這個api檢查是否有token以及booking資料庫內有沒有之前的預定行程
@router.get("/api/shop/cart")
async def check_order(request: Request):
    #檢查是否有token，此get非彼@app.get
    token = request.headers.get('Authorization')
    session_id = request.headers.get("X-Session-ID")
    user_id = None
    #print(token)

    if token and token != "Bearer null":
        extracted_token = token[len("Bearer "):]
        print("extracted token:", extracted_token)
        try:
            payload = jwt.decode(extracted_token, SECRET_KEY, algorithms=[ALGORITHM])
            #print(payload)
            user_id = payload.get("id")
        except PyJWTError:
            return JSONResponse(
                status_code = 403,
                content = {
                    "error": True,
                    "message": "未登入系統，拒絕存取，token不合常理"
                }
            )
    elif not session_id:
        return JSONResponse(
            status_code=200,
            content={
                "error": True, 
                "message": "沒有session_id也沒有購物車內容"
            }
        )
    
    #token正確的話，開始取資料
    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        if user_id:
            cursor.execute("SELECT product_id, quantity, price FROM shopping_cart WHERE user_id = %s", (user_id,))
        #確認有沒有一樣的email已經在booking資料庫
        else:
            cursor.execute("SELECT product_id, quantity, price FROM shopping_cart WHERE session_id = %s", (session_id,))
        
        cart_items = cursor.fetchall()
        #print(cart_items)

        if (cart_items):
            # Prepare a list to hold the product details
            products_with_images = []

            for item in cart_items:
                booked_item_id = item['product_id']
                quantity = item['quantity']
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
                            "quantity": quantity
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
            status_code=400,
            content = {
                "error": True,
                "message": "建立失敗，輸入不正確或其他原因" + str(err)
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

@router.put("/api/shop/cart")
async def update_cart(request: Request, update_info: BookingInfo, response: Response):
    #檢查是否有token
    token = request.headers.get('Authorization')
    session_id = request.headers.get("X-Session-ID")
    conn = None
    cursor = None
    #沒登入的人
    if not token or not token.startswith("Bearer "):        
        if not session_id:
            session_id = str(uuid.uuid4())  # Generate a new session_id

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            booking_product_id = update_info.productId
            booking_quantity = update_info.quantity 
            booking_price = update_info.price            
 
            cursor.execute("SELECT * FROM shopping_cart WHERE session_id = %s AND product_id LIKE %s", (session_id, booking_product_id))
            to_update = cursor.fetchone()
            if to_update:
                update_query = """
                UPDATE shopping_cart
                SET quantity = %s, updated_at = NOW()
                WHERE session_id = %s AND product_id LIKE %s
                """
                cursor.execute(update_query, (
                    booking_quantity,
                    session_id,
                    booking_product_id,
                ))
            else:
                query = """
                INSERT INTO shopping_cart (session_id, product_id, quantity, price, added_at, updated_at)
                VALUES
                (%s, %s, %s, %s, NOW(), NOW())
                """
                cursor.execute(query, (
                    session_id,
                    booking_product_id,
                    booking_quantity,
                    booking_price,
                ))
            conn.commit()
            return JSONResponse(content={"ok": True, "session_id": session_id})
        except mysql.connector.Error as err:
            return JSONResponse(
                status_code=400,
                content={
                    "error": True,
                    "message": "Failed to save booking. Please check your input."
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "message": "Internal server error"
                }
            )
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

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
        booking_product_id = update_info.productId
        booking_quantity = update_info.quantity 

        #看看是否已經member_id存在booking table
        cursor.execute("SELECT * FROM shopping_cart WHERE user_id = %s AND product_id = %s", (booking_user_id, booking_product_id))
        to_update = cursor.fetchone()

        if to_update:            
            new_total_price = to_update["price"] * booking_quantity
            #print(new_total_price)
            update_query = """
            UPDATE shopping_cart
            SET quantity = %s, total_price = %s
            WHERE user_id = %s AND product_id = %s
            """
            cursor.execute(update_query, (
                booking_quantity,
                new_total_price,
                booking_user_id,
                booking_product_id
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
                "message": "Cart updated!"
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

@router.delete("/api/shop/cart")
async def delete_booking(request: Request):
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

        delete_query = "DELETE FROM shopping_cart WHERE user_id = %s AND product_id = %s"
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
