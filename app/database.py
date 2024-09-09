import mysql.connector
from fastapi import HTTPException
from typing import Optional
from app.config import DB_CONFIG
import mysql.connector
from mysql.connector import Error
import random


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
        #print("This is ID query", productId) #找錯誤
        cursor.execute(query, (productId,))
        result = cursor.fetchone()
        #print("找到的結果", result)
        return result
    except Error as e:
        print(f"Error fetching data: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()   
			
#推薦相關商品
def fetch_related_products(categories: str, current_product_id: str, limit: int = 4):
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Split the categories into a list
        category_list = categories.split(',')
        print(category_list)

        # Randomly select one category
        selected_category = random.choice(category_list).strip()
        print(f"Selected Category: {selected_category}")
        
        query = """
        SELECT Product_id, Name, Price, 
        (SELECT url FROM images WHERE images.product_id = furnitures.Product_id LIMIT 1) AS image_url
        FROM furnitures
        WHERE Category LIKE %s AND Product_id != %s
        ORDER BY RAND()
        LIMIT 4;
        """
        # Prepare parameters for the query
        params = (f"%{selected_category}%", current_product_id)
        print(f"會帶入的參數: {params}")

        cursor.execute(query, params)
        related_products = cursor.fetchall()
        return related_products
    except Error as e:
        print(f"Error fetching related products: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
