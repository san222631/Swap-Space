import mysql.connector
import json
from mysql.connector import Error

def save_json_to_mysql():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='newuser',
            password='user_password',
            database='swap_space'
        )
        cursor = conn.cursor()
        print("成功連線mysql")

        with open('data/data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            print(data[2])
        
        query = """
            UPDATE furnitures 
            SET Category = %s
            WHERE Product_id = %s;
            """
        for item in data:
            product_id = item.get('id')
            categories = item.get('category', [])
            category_str = ",".join(categories) 
            cursor.execute(query, (category_str, product_id))

        conn.commit()
        print("成功儲存資料")
    
    except Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.") 

if __name__ == '__main__':
    save_json_to_mysql()
