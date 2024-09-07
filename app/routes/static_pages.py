from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/", include_in_schema=False)
async def index(request: Request):
    return FileResponse("./static/index.html", media_type="text/html")
@router.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./static/index.html", media_type="text/html")
@router.get("/shop", include_in_schema=False)
async def shop(request: Request):
	return FileResponse("./static/shop.html", media_type="text/html")
@router.get("/product/{productId}", include_in_schema=False)
async def product(request: Request, productId: str):
	return FileResponse("./static/product.html", media_type="text/html")
@router.get("/shop/cart", include_in_schema=False)
async def shopping(request: Request):
	return FileResponse("./static/order.html", media_type="text/html")
@router.get("/wishlist", include_in_schema=False)
async def wishlist(request: Request):
	return FileResponse("./static/wishlist.html", media_type="text/html")
@router.get("/member", include_in_schema=False)
async def member(request: Request):
	return FileResponse("./static/member.html", media_type="text/html")
@router.get("/member/{orderNumber}", include_in_schema=False)
async def member(request: Request):
	return FileResponse("./static/order_details.html", media_type="text/html")
@router.get("/account", include_in_schema=False)
async def member(request: Request):
	return FileResponse("./static/account.html", media_type="text/html")
@router.get("/account/change-password", include_in_schema=False)
async def member(request: Request):
	return FileResponse("./static/change_pass.html", media_type="text/html")
@router.get("/account/edit-profile", include_in_schema=False)
async def member(request: Request):
	return FileResponse("./static/edit_profile.html", media_type="text/html")
@router.get("/account/delete-profile", include_in_schema=False)
async def member(request: Request):
	return FileResponse("./static/delete_profile.html", media_type="text/html")