from datetime import datetime
from decimal import Decimal
import mysql.connector
from app.config import DB_CONFIG, SECRET_KEY, ALGORITHM
from fastapi import *


def serialize_item(item):
    """Convert all Decimal and datetime fields in a dictionary to JSON-serializable formats."""
    for key, value in item.items():
        if isinstance(value, Decimal):
            item[key] = float(value)
        elif isinstance(value, datetime):
            item[key] = value.isoformat()
    return item

#取特定的訂單資料
#for /api/member/{orderNumber} 根據訂單編號
def fetch_order_by_number(orderNumber: str):
    print(orderNumber)
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT 
            order_number, 
            order_date, 
            total_price, 
            subscription_period, 
            start_date, 
            end_date, 
            order_info, 
            contact, 
            order_status, 
            next_payment_date, 
            last_payment_date
        FROM
            orders
        WHERE
            order_number = %s
        """
        #print("This is ID query", productId) #找錯誤
        cursor.execute(query, (orderNumber,))
        result = cursor.fetchone()
        #print("找到的結果", result)
        return result
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None
    except  Exception as e:
        print(f"Error fetching data: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()   


#根據目錄，取得商品資料
def fetch_CAT_data(page: int, keyword: str):
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
        WHERE Category LIKE %s
        GROUP BY furnitures.Product_id
        LIMIT %s, 20
		"""

		params = []
		like_keyword = f'%{keyword}%'
		params.extend([like_keyword])
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