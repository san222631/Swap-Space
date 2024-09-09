from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from ..database import fetch_data, fetch_data_by_id, fetch_related_products
from app.config import DB_CONFIG

import mysql.connector
from mysql.connector import Error
import random
from fastapi.responses import JSONResponse


router = APIRouter()


@router.get("/api/products/")
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


@router.get("/api/products/related")
def get_related_products(category: str, exclude_id: str):
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
        "data": related_products
    }
