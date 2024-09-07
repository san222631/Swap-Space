import asyncio
from datetime import datetime, timedelta
import httpx
import mysql.connector
from app.config import DB_CONFIG, SECRET_KEY, ALGORITHM
import json


#使用cron job處理每月扣款
async def process_recurring_payment(order_number, card_token, card_key, amount, contact_info):
    TAPPAY_API_URL = "https://sandbox.tappaysdk.com/tpc/payment/pay-by-token"
    PARTNER_KEY = "partner_jmg7WOPdhPJ3GcEZ89MYDcIsx0OCR0drYRwgnQNpmr727zbqrximL3S1"
    MERCHANT_ID = "san222631_CTBC_Union_Pay"

    payment_payload = {
        "card_key": card_key,
        "card_token": card_token,
        "partner_key": PARTNER_KEY,
        "merchant_id": MERCHANT_ID,
        "currency": "TWD",
        "amount": amount,
        "details": "Recurring Payment",
        "order_number": order_number,
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

    async with httpx.AsyncClient() as client:
        payment_response = await client.post(TAPPAY_API_URL, json=payment_payload, headers=headers)
    
    payment_result = payment_response.json()
    return payment_result



#每天喚醒，檢查處理每月扣款
async def job():
    # Fetch due orders from the database
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT order_number, card_token, card_key, total_price, contact 
        FROM orders 
        WHERE end_date > NOW() AND payment_status = 'PAID' AND next_payment_date <= NOW()
    """)

    orders = cursor.fetchall()

    for order in orders:
        order_number = order['order_number']
        card_token = order['card_token']
        card_key = order['card_key']
        total_price = order['total_price']
        contact_info = json.loads(order['contact'])

        # Process the recurring payment
        payment_result = await process_recurring_payment(order_number, card_token, card_key, total_price, contact_info)

        if payment_result["status"] == 0:
            # Payment succeeded, update next_payment_date
            cursor.execute("""
                UPDATE orders
                SET next_payment_date = DATE_ADD(next_payment_date, INTERVAL 1 MONTH)
                WHERE order_number = %s
            """, (order_number,))
            conn.commit()
        else:
            # Handle failed payment
            print(f"Payment failed for order {order_number}: {payment_result['msg']}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(job())
