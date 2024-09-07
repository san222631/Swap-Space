from pydantic import BaseModel

class registerInfo(BaseModel):
    name: str
    email: str
    password: str

class Token(BaseModel):
    token: str

class UserInfo(BaseModel):
    email: str
    password: str

#確認使用者的JWT有沒有正確
#{"data": {"id": 1,"name": "彭彭彭","email": "ply@ply.com"}}
#要回傳給使用者的資料規定格式
class verified_user(BaseModel):
    id: int
    name: str
    email: str

#把使用者input的quantity以及product_id, userId加入資料庫
class BookingInfo(BaseModel):
    productId: str
    quantity: int
    price: float

#更新 購物車數量
class UpdateInfo(BaseModel):
    productId: str
    quantity: int

#把使用者喜歡的加入wishlist資料庫
class WishInfo(BaseModel):
    product_id: str

#更新 密碼
class updatePassword(BaseModel):
    oldPassword: str
    newPassword: str

#更新 姓名跟信箱
class updateProfile(BaseModel):
    name: str
    email: str

#刪除整個帳戶
class deleteProfile(BaseModel):
    password: str