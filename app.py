from fastapi import *
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from typing import Optional
import mysql.connector
from mysql.connector import Error

from passlib.context import CryptContext
from pydantic import BaseModel
import jwt
from jwt import PyJWTError
from datetime import datetime, timedelta, timezone

import traceback
import uuid

from decimal import Decimal
from datetime import datetime


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Static Pages
@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./static/index.html", media_type="text/html")
@app.get("/shop", include_in_schema=False)
async def shop(request: Request):
	return FileResponse("./static/shop.html", media_type="text/html")
@app.get("/product/{productId}", include_in_schema=False)
async def product(request: Request, productId: str):
	return FileResponse("./static/product.html", media_type="text/html")
@app.get("/shop/cart", include_in_schema=False)
async def shopping(request: Request):
	return FileResponse("./static/order.html", media_type="text/html")
@app.get("/shop/wishlist", include_in_schema=False)
async def wishlist(request: Request):
	return FileResponse("./static/wishlist.html", media_type="text/html")

DB_CONFIG = {
	'host': 'localhost',
	'user': 'newuser',
	'password': 'user_password',
	'database': 'swap_space',
	'charset': 'utf8'
}

#取得商品目錄資料
def fetch_data(page: int, keyword: Optional[str]):
	conn = None
	cursor = None
	try:
		conn = mysql.connector.connect(**DB_CONFIG)
		cursor = conn.cursor(dictionary=True)
		cursor.execute("SET SESSION group_concat_max_len = 1000000;")
		
		query = """
		SELECT furnitures.*, GROUP_CONCAT(images.url SEPARATOR ' ') AS image_urls
        FROM furnitures
        LEFT JOIN images ON images.product_id = furnitures.Product_id
		"""

		params = []
		if keyword:
			query += " WHERE furnitures.Name LIKE %s"
			like_keyword = f'%{keyword}%'
			params.extend([like_keyword])

		query += " GROUP BY furnitures.id LIMIT %s, 20"
		params.append(page * 20)

		cursor.execute(query, params)
		results = cursor.fetchall()
		return results
	except Exception as e:
		print(f"Internal Server Error: {e}")
		raise HTTPException(
			status_code=500,
			detail={
				"error": True,
				"message":"伺服器內部錯誤"
				})  
	finally:
		if cursor is not None:  
			cursor.close()
		if conn is not None:
			conn.close()


@app.get("/api/products/")
def get_products(page: int = 0, keyword: Optional[str] = Query(None)):
    data = fetch_data(page, keyword)
    if not data:
        raise HTTPException(status_code=404, detail="No Data, No products found.")
    
    # Determine if there's a next page
    next_page = page + 1 if len(data) == 20 else None
    
    # Format response
    response = {
        "nextPage": next_page,
        "data": [{
            "product_id": item['Product_id'],
            "name": item['Name'],
            "category": item['Category'],
            "description": item['Description'],
            "price": item['Price'],
            "link": item['Page_link'],
            "dimension": item['Dimension'],
            "images": item['image_urls'].split(' ')
        } for item in data]
    }
    return response


#___________________________________________________________________________________________
#for /api/shops/{productId} 根據商品編號取得特定商品資料
def fetch_data_by_id(productId: str):
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SET SESSION group_concat_max_len = 1000000;")

        query = """
        SELECT furnitures.*, GROUP_CONCAT(images.url SEPARATOR ' ') AS image_urls
        FROM furnitures
        LEFT JOIN images ON images.product_id = furnitures.Product_id
        WHERE furnitures.Product_id = %s
        GROUP BY furnitures.Product_id;
        """
        print("This is ID query", productId) #找錯誤
        cursor.execute(query, (productId,))
        result = cursor.fetchone()
        print("找到的結果", result)
        return result
    except Error as e:
        print(f"Error fetching data: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()    



@app.get("/api/product/{productId}")
def get_product_by_id(productId: str):
    product_details = fetch_data_by_id(productId)
    if not product_details:
         return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "message": "商品編號不正確"
            }
        )
    # Format response
    response = {
        "data": {
            "product_id": product_details['Product_id'],
            "name": product_details['Name'],
            "category": product_details['Category'],
            "description": product_details['Description'],
            "price": product_details['Price'],
            "link": product_details['Page_link'],
            "dimension": product_details['Dimension'],
            "images": product_details['image_urls'].split(' ')
        }
    }
    return response



#加密密碼
#使用者註冊時輸入的資訊
class registerInfo(BaseModel):
    name: str
    email: str
    password: str

# Initialize the bcrypt context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hashing a password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Verifying a password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


#使用者註冊
@app.post("/api/user")
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
            

#檢查使用者信箱+密碼，確認有的話給一個JWT，要符合Pydantic model
class Token(BaseModel):
    token: str
#使用者要登入時給的資料
class UserInfo(BaseModel):
    email: str
    password: str
#JWT Secret & Algorithm
SECRET_KEY = "whatsup"
ALGORITHM = "HS256"
#檢查使用者信箱+密碼，確認有的話給一個JWT
@app.put("/api/user/auth", response_model=Token)
#"user_info"是一個request body parameter，名字我可自訂
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
    
    

#確認使用者的JWT有沒有正確
#{"data": {"id": 1,"name": "彭彭彭","email": "ply@ply.com"}}
#要回傳給使用者的資料規定格式
class verified_user(BaseModel):
    id: int
    name: str
    email: str

@app.get("/api/user/auth")
async def authenticate(request: Request):
    #從前端送過來的headers get"Authorization"然後decode
    auth_header = request.headers.get("Authorization")
    print(auth_header)
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
        print(user_email)
        cursor.execute(
            "SELECT id, name, email FROM member WHERE email = %s",
            (user_email,)
        )
        verified_user = cursor.fetchone()
        print(verified_user)
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
            

#把使用者input的quantity以及product_id, userId加入資料庫
class BookingInfo(BaseModel):
    productId: str
    quantity: int
    price: float

@app.post("/api/shop/cart")
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
        cursor.execute("SELECT * FROM shopping_cart WHERE user_id = %s AND product_id LIKE %s", (booking_user_id, booking_product_id))
        to_update = cursor.fetchone()
        if to_update:
            update_query = """
            UPDATE shopping_cart
            SET quantity = %s
            WHERE member_id = %s AND product_id LIKE %s
            """
            cursor.execute(update_query, (
                booking_quantity,
                booking_user_id,
                booking_product_id,
                )
            )
        else:
            query = """
            INSERT INTO shopping_cart (user_id, product_id, quantity, price)
            VALUES
            (%s, %s, %s, %s)
            """
            cursor.execute(query, (
                booking_user_id,
                booking_product_id,
                booking_quantity,
                booking_price
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


#刪除使用者在booking資料庫裏面的行程
@app.delete("/api/shop/cart")
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
    
    #開始刪除
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        booking_user_id = payload.get("id")

        delete_query = "DELETE FROM shopping_cart WHERE user_id = %s"
        cursor.execute(delete_query, (booking_user_id,))
        conn.commit()
        return JSONResponse(
            status_code=200,
            content={
                "ok": True
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


#SHOPPING CART APIs
#使用者想進入"預定行程"的頁面，透過這個api檢查是否有token以及booking資料庫內有沒有之前的預定行程
@app.get("/api/shop/cart")
async def check_order(request: Request):
    #檢查是否有token，此get非彼@app.get
    token = request.headers.get('Authorization')
    session_id = request.headers.get("X-Session-ID")
    user_id = None
    print(token)

    if token and token != "Bearer null":
        extracted_token = token[len("Bearer "):]
        print("extracted token:", extracted_token)
        try:
            payload = jwt.decode(extracted_token, SECRET_KEY, algorithms=[ALGORITHM])
            print(payload)
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
        print(cart_items)

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
                print(product_details)

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
        print(e)
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


#把使用者喜歡的加入wishlist資料庫
class WishInfo(BaseModel):
    product_id: str

@app.post("/api/shop/wishlist/add")
async def add_to_wishlist(request: Request, wishlist: WishInfo):
    product_id = wishlist.product_id
    print(product_id)
    #檢查是否有token或session
    token = request.headers.get('Authorization')
    conn = None
    cursor = None
    response = None
    #沒登入的人
    if not token or not token.startswith("Bearer "):
        #檢查是否有session_id
        session_id = request.headers.get("X-Session-ID")
        print(session_id)
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
            print(double_entry)
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

#點最愛清單時，導向最愛清單頁面
@app.get("/api/wishlist")
async def get_wishlist(request: Request):
    # Extract token and session_id from headers
    token = request.headers.get('Authorization')
    session_id = request.headers.get('X-Session-ID')

    user_id = None

    # If token is present, decode the JWT to get the user_id
    if token and token != "Bearer null":
        extracted_token = token[len("Bearer "):]
        print("extracted token:", extracted_token)
        try:
            payload = jwt.decode(extracted_token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("id")
        except jwt.PyJWTError:
            raise HTTPException(status_code=403, detail="Invalid token")

    if not user_id and not session_id:
        raise HTTPException(status_code=400, detail="No user_id or session_id provided")

    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        if user_id:
            # Query to fetch wishlist items for a logged-in user
            query = """
            SELECT furnitures.* FROM furnitures
            JOIN wishlist ON furnitures.Product_id = wishlist.product_id
            WHERE wishlist.user_id = %s
            """
            cursor.execute(query, (user_id,))
        else:
            # Query to fetch wishlist items for a guest user with a session_id
            query = """
            SELECT furnitures.* FROM furnitures
            JOIN wishlist ON furnitures.Product_id = wishlist.product_id
            WHERE wishlist.session_id = %s
            """
            cursor.execute(query, (session_id,))

        wishlist_items = cursor.fetchall()

        # Convert any Decimal fields to float
        wishlist_items = [serialize_item(item) for item in wishlist_items]

        return JSONResponse(status_code=200, content=wishlist_items)

    except mysql.connector.Error as err:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "Database query failed"}
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def serialize_item(item):
    """Convert all Decimal and datetime fields in a dictionary to JSON-serializable formats."""
    for key, value in item.items():
        if isinstance(value, Decimal):
            item[key] = float(value)
        elif isinstance(value, datetime):
            item[key] = value.isoformat()  # Convert datetime to ISO 8601 string
    return item