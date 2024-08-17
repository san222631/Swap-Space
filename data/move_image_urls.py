import mysql.connector
import json
from mysql.connector import Error

def move_img_url():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='newuser',
            password='user_password',
            database='swap_space'
        )
        cursor = conn.cursor()
        print("成功連線mysql")

        with cursor:
            cursor.execute("SELECT Product_id, Image_url FROM furnitures")
            rows = cursor.fetchall()

            #parse JSON and insert into "images" table
            #each row is a tuple from rows
            for row in rows:
                product_id, image_urls = row #assign elements in a tuple directly to variable
                urls = json.loads(image_urls)
                for url in urls:
                    complete_url = "https://www.live-light.com" +url
                    cursor.execute(
                        "INSERT INTO images (product_id, url) VALUES (%s, %s)",
                        (product_id, complete_url)
                    )


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
    move_img_url()