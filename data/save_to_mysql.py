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
            INSERT INTO furnitures (Product_id, Name, Price, Image_url, Page_link, Description, Dimension)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
        columns = ['id', 'name', 'price', 'image_srcs', 'href', 'description', 'dimension']
        for item in data:
            values = tuple(
                json.dumps(item.get('image_srcs')) if key == 'image_srcs' else item.get(key) 
                for key in columns
            )
            cursor.execute(query, values)

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
