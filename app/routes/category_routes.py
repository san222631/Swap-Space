from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.utils import fetch_CAT_data

router = APIRouter()

@router.get("/api/category")
def get_CAT_products(page: int = 0, keyword: str = Query(None)):
    data = fetch_CAT_data(page, keyword)
    if not data:
        return {
            "nextPage": None,
            "data": []
        }

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
