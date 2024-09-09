from fastapi import *
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.database import fetch_data, fetch_data_by_id, fetch_related_products
from app.config import DB_CONFIG, SECRET_KEY, ALGORITHM

import mysql.connector
from mysql.connector import Error
import random
from fastapi.responses import JSONResponse
from datetime import datetime
import jwt
from app.utils import get_redis_client

router = APIRouter()


@router.get("/api/products/")
def get_products(request: Request, page: int = 0, keyword: Optional[str] = Query(None)):
    redis_client = get_redis_client()  # Get the Redis client
    print(f"redis有嗎?", redis_client)
    # Check if the user is logged in
    token = request.headers.get('Authorization')
    user_id = None
    print(token)
    print(user_id)
    print(keyword)

    if token:
        extracted_token = token[len("Bearer "):]
        print(extracted_token)
        try:
            payload = jwt.decode(extracted_token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("id")
        except jwt.PyJWTError:
            user_id = None

    if user_id and keyword:
        print(f"有user_id也有keyword，存進redis:", {user_id})
        # Track the search keyword with timestamp if the user is logged in
        timestamp = datetime.now().timestamp()
        redis_client.zadd(f"user:{user_id}:searches", {keyword: timestamp})
        print(timestamp)
        print(redis_client)

    #不管有沒有登入都要顯示商品    
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
			

@router.get("/api/product/{productId}")
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

# 推薦相關商品
@router.get("/api/products/related")
def get_related_products(category: str, exclude_id: str, request: Request):
    redis_client = get_redis_client()  # Get the Redis client

    # Check if the user is logged in by extracting the token from the headers
    token = request.headers.get('Authorization')
    user_id = None

    if token:
        extracted_token = token[len("Bearer "):]
        try:
            payload = jwt.decode(extracted_token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("id")
        except jwt.PyJWTError:
            user_id = None

    related_products = []
    print(related_products)
    print(token)
    if user_id:
        # Check for keyword history in Redis
        keyword_history = redis_client.zrevrange(f"user:{user_id}:searches", 0, -1)

        if keyword_history:
            # Log the keyword history
            print(f"Keyword history for user {user_id}: {keyword_history}")      

            # Search the keyword in "Name" in the database
            conn = None
            cursor = None
            try:
                conn = mysql.connector.connect(**DB_CONFIG)
                cursor = conn.cursor(dictionary=True)

                for keyword in keyword_history:
                    query = """
                    SELECT Product_id, Name, Price, 
                    (SELECT url FROM images WHERE images.product_id = furnitures.Product_id LIMIT 1) AS image_url
                    FROM furnitures
                    WHERE Name LIKE %s AND Product_id != %s
                    LIMIT 4;
                    """
                    cursor.execute(query, (f"%{keyword.decode('utf-8')}%", exclude_id))
                    related_products.extend(cursor.fetchall())

                    # If we have enough related products, stop searching
                    if len(related_products) >= 4:
                        break
            except mysql.connector.Error as e:
                print(f"Error fetching related products based on keyword history: {e}")
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

        # If not enough related products found, fill with original logic
        if len(related_products) < 4:
            remaining_products = 4 - len(related_products)
            original_related = fetch_related_products(category, exclude_id, limit=remaining_products)
            related_products.extend(original_related)

    else:
        # User is not logged in, use original logic
        related_products = fetch_related_products(category, exclude_id)

    if not related_products:
         return JSONResponse(
            status_code=404,
            content={
                "error": True,
                "message": "找不到相關產品"
            }
        )

    return {
        "data": related_products[:4]  # Ensure only 4 products are returned
    }
