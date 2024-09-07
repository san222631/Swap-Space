from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import category_routes, static_pages, product_routes, user_routes, cart_routes, wishlist_routes, order_routes, profile_routes

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(static_pages.router)
app.include_router(product_routes.router)
app.include_router(user_routes.router)
app.include_router(cart_routes.router)
app.include_router(wishlist_routes.router)
app.include_router(order_routes.router)
app.include_router(profile_routes.router)
app.include_router(category_routes.router)  # Include category routes
