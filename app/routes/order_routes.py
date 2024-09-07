from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

from fastapi.responses import FileResponse, JSONResponse
from app.config import DB_CONFIG, SECRET_KEY, ALGORITHM
from app.utils import fetch_order_by_number
from jwt import PyJWTError
from jose import jwt
import mysql.connector
from mysql.connector import Error
import uuid
import json 
import httpx
from dateutil.relativedelta import relativedelta


router = APIRouter()

@router.post("/api/orders")
async def create_order(request: Request):
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
    
    #看前端送來的request正不正確
    booking_user_id = payload.get("id")
    body = await request.json()
    prime = body.get("prime")
    order_info = body.get("order")
    contact_info = body.get("contact")
    subscription_info = body.get("subscription")
    total_price = subscription_info.get("total_price")
    period = int(subscription_info.get("subscription_period"))
    start_date = subscription_info.get("start_date")
    end_date = subscription_info.get("end_date")
    #print('這是body:', body)
    #print('這是order_info:', order_info)
    #print('這是contact_info:', contact_info)
    #print('這是subscription:', subscription_info)
    if not prime:
        return JSONResponse(
            status_code=400,
            content= {
                "error": True,
                "message": "prime有誤，訂單建立失敗"
            }
        )
    if not order_info:
        return JSONResponse(
            status_code=400,
            content= {
                "error": True,
                "message": "輸入的訂單資訊不正確，訂單建立失敗"
            }
        )
    if not contact_info:
        return JSONResponse(
            status_code=400,
            content= {
                "error": True,
                "message": "輸入的聯絡人資訊不正確，訂單建立失敗"
            }
        )
    if not subscription_info:
        return JSONResponse(
            status_code=400,
            content= {
                "error": True,
                "message": "輸入的訂閱時間不正確，訂單建立失敗"
            }
        )
    
    order_number = str(uuid.uuid4())
    #print(order_number)
    
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        query_orders = """
            INSERT INTO orders (order_number, member_id, total_price, subscription_period, start_date, end_date, order_info, contact, order_status, prime)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
        order_status = "UNPAID"
        cursor.execute(query_orders, 
                        (
                        order_number,
                        booking_user_id,
                        total_price,
                        period,
                        start_date,
                        end_date,
                        json.dumps(order_info), #把dictionary變成JSON string 才能存進mysql
                        json.dumps(contact_info), #把dictionary變成JSON string 才能存進mysql
                        order_status,
                        prime
                        )                       
                        )
        query_delete_booking = """
            DELETE FROM shopping_cart 
            WHERE user_id = %s
            """
        cursor.execute(query_delete_booking, (booking_user_id,))
        conn.commit()

        #Call "Tappay Bind Card" API
        #TAPPAY_API_URL = "https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime"
        TAPPAY_API_URL = "https://sandbox.tappaysdk.com/tpc/card/bind"
        PARTNER_KEY = "partner_jmg7WOPdhPJ3GcEZ89MYDcIsx0OCR0drYRwgnQNpmr727zbqrximL3S1"
        MERCHANT_ID = "san222631_GP_POS_1"
        payment_payload = {
            "prime": prime,
            "partner_key": PARTNER_KEY,
            "merchant_id": MERCHANT_ID,
            "currency": "TWD",
            "amount": total_price,
            "details": "TapPay Test",
            "cardholder": {
                "phone_number": contact_info["phone"],
                "name": contact_info["name"],
                "email": contact_info["email"]
            }
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": PARTNER_KEY
        }

        #call Tappay PayByPrime API
        async with httpx.AsyncClient() as client:
            payment_response = await client.post(TAPPAY_API_URL, json=payment_payload, headers=headers)
        payment_result = payment_response.json()
        print('這是PayByPrime API的response:', payment_result)


        #從這裡開始檢查!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if payment_result["status"] == 0:
            # Payment succeeded
            #print(payment_result)
            order_status = "PAID"
            payment_status = payment_result["status"]
            C_token = payment_result["card_secret"]["card_token"]
            C_key = payment_result["card_secret"]["card_key"]
            #print(period)

            # Calculate last_payment_date (current time) and next_payment_date (based on the period)
            last_payment_date = datetime.now()
            months_paid = 1 # assuming the first payment has just been made
            if months_paid < period:
                next_payment_date = last_payment_date + relativedelta(months=1)
            else:
                next_payment_date = None # All payments are completed

            cursor.execute("""
                UPDATE orders
                SET payment_status = %s, payment_record = %s, order_status = %s, card_token = %s, card_key = %s, last_payment_date = %s, next_payment_date = %s
                WHERE order_number = %s
                """, (payment_status, json.dumps(payment_result), order_status, C_token, C_key, last_payment_date, next_payment_date, order_number))
            conn.commit()
            return JSONResponse(
                status_code=200,
                content={
                    "data": {
                        "number": order_number,
                        "payment": {
                            "status": payment_result["status"],
                            "message": "付款成功"
                        }
                    }
                }
            )
        else:
            # Payment failed
            order_status = "UNPAID"
            payment_status = payment_result["status"]
            cursor.execute("""
                UPDATE orders
                SET payment_status = %s, payment_record = %s, order_status = %s
                WHERE order_number = %s
                """, (payment_status, json.dumps(payment_result), order_status, order_number)
                )
            conn.commit()
            return JSONResponse(
                status_code=200,
                content={
                    "data": {
                        "number": order_number,
                        "payment": {
                            "status": payment_result["status"],
                            "message": f"訂單建立成功，但付款失敗: {payment_result['msg']}"
                        }
                    }
                }
            )

    except Error as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": f"伺服器內部錯誤: {str(e)}"
            }
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/api/orders")
async def check_order(request: Request):
    #檢查是否有token，此get非彼@app.get
    token = request.headers.get('Authorization')
    user_id = None
    #print(token)

    if token and token != "Bearer null":
        extracted_token = token[len("Bearer "):]
        #print("extracted token:", extracted_token)
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
    
    #token正確的話，開始取資料
    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        if user_id:
            cursor.execute("""
                SELECT 
                    order_number, 
                    order_date, 
                    total_price, 
                    subscription_period,
                    start_date, end_date, 
                    order_status 
                FROM
                    orders 
                WHERE 
                    member_id = %s
                ORDER BY
                    order_date DESC
            """, (user_id,))
        #確認有沒有一樣的email已經在booking資料庫
        
        all_orders = cursor.fetchall()
        #print(all_orders)

        if (all_orders):
            # Prepare a list to hold the order details
            orders = []

            for item in all_orders:
                adjusted_response = {
                    "order_number": item['order_number'],
                    "order_date": item['order_date'].date().isoformat(),
                    "total_price": float(item['total_price']),
                    "subscription_period": item['subscription_period'],
                    "start_date": item['start_date'].isoformat(),
                    "end_date": item['end_date'].isoformat(),
                    "order_status": item['order_status']
                }
                orders.append(adjusted_response)                

            return JSONResponse(status_code=200, content=orders)
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
                "message": "資料庫連線失敗，輸入不正確或其他原因" + str(err)
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

@router.get("/api/member/{orderNumber}")
def get_order_by_number(orderNumber: str):
    order_details = fetch_order_by_number(orderNumber)
    if not order_details:
         return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "message": "Order not found"
            }
        )
    # Format response
    response = {
        "data": {
            "order_number": order_details['order_number'],
            "order_date": order_details['order_date'].date().isoformat(),
            "total_price": float(order_details['total_price']),
            "subscription_period": order_details['subscription_period'],
            "start_date": order_details['start_date'].isoformat(),
            "end_date": order_details['end_date'].isoformat(),
            "order_info": order_details['order_info'],
            "contact": order_details['contact'],
            "order_status": order_details['order_status'],
            "next_payment_date": order_details['next_payment_date'].isoformat() if order_details['next_payment_date'] else None,
            "last_payment_date": order_details['last_payment_date'].isoformat() if order_details['last_payment_date'] else None
        }
    }
    return response
