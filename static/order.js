document.addEventListener('DOMContentLoaded', async() => {
    const userInfo = await fetchUserInfo();

    if (userInfo) {
        //加入會換名字的問候語
        console.log(userInfo)
        const greeting = document.getElementById('greeting');
        greeting.textContent = `您好，${userInfo.name}，購物車內容如下:`;
        fetchBookingDetails();
    } else {
        //window.location.href = '/';
        const greeting = document.getElementById('greeting');
        greeting.textContent = `您好，guest，購物車內容如下:`;
        fetchBookingDetails();
    }

    //按回首頁
    const goIndex = document.getElementById('go-index');
    goIndex.addEventListener('click', function(){
        window.location.href = '/';
    });


    //點擊products，想看所有商品
    //尚未加使用者驗證
    document.getElementById('products').addEventListener('click', function(){
        window.location.href = '/shop';
    });

    //點擊Cart，想看購物車
    //尚未加使用者驗證
    document.getElementById('start-booking').addEventListener('click', function(){
        window.location.href = '/shop/cart';
    });

    //點擊Member，看會員彈出視窗
    //處理登入
    const modal = document.getElementById('modal');
    const loginRegister = document.getElementById('login-register');
    const closeButton = document.getElementById('close-button');
    const loginButton = document.getElementById('login-button');
    const errorMessage = document.getElementById('error-message');
    const logout = document.getElementById('logout');
    const authForm = document.getElementById('auth-form');

    
    loginRegister.addEventListener('click', () => {
        modal.style.display = 'block';
    });
    
    closeButton.addEventListener('click', () => {
        modal.style.display = 'none';
        errorMessage.textContent = '';
    });
    
    window.addEventListener('mousedown', (event) => {
        if (event.target == modal) {
        modal.style.display = 'none';
        errorMessage.textContent = '';
        }
    });
    
    authForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
    
        fetch('/api/user/auth', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: email, password: password })
        })
        .then(response => {
        return response.json()
        .then(data => {
            if (!response.ok) {
                const error = new Error('HTTP error');
                error.data = data;
                throw error;
            }
            return data;
        });
        })
        .then(data => {
        if (data.token){
            localStorage.setItem('received_Token', data.token);
            console.log(data);
            modal.style.display = 'none';
            errorMessage.textContent = '';
            renderLogout()
        } else {
            throw new Error('無效的token response');
        }
        })
        .catch(error => {
        if (error.data) {
            errorMessage.textContent = error.data.message;
            console.error(error.data); // Log the entire detail object
        } else {
            errorMessage.textContent = error.message;
            console.error('Error是:', error.message || error); 
        }
        });
    });

    //註冊    
    const registerButton = document.getElementById('register');
    const R_modal = document.getElementById('R-modal'); 
    const R_closeButton = document.getElementById('R-close-button');
    const R_errorMessage = document.getElementById('R-error-message');
    const back_to_login = document.getElementById('back-to-login');
    const R_form = document.getElementById('R-form');

    registerButton.addEventListener('click', function(){
        errorMessage.textContent = '';
        modal.style.display = 'none';
        R_modal.style.display = 'block';
    });

    R_closeButton.addEventListener('click', function(){
        R_modal.style.display = 'none';
        R_errorMessage.textContent = '';
    });

    back_to_login.addEventListener('click', function(){
        R_errorMessage.textContent = '';
        R_modal.style.display = 'none';
        modal.style.display = 'block';
    });

    window.addEventListener('mousedown', (event) => {
        if (event.target == R_modal) {
            R_modal.style.display = 'none';
            R_errorMessage.textContent = '';
        }
    });   

    R_form.addEventListener('submit', function(event){
        event.preventDefault(); //避免預設的submission
        const R_name = document.getElementById('R-name').value;
        const R_email = document.getElementById('R-email').value;
        const R_password = document.getElementById('R-password').value;

        fetch('/api/user', {
            method: 'POST',
            headers: {
                'Content-type': 'application/json'
            },
            body: JSON.stringify({name: R_name, email: R_email, password: R_password})
        })
        .then(response => {  
            console.log(response)
            return response.json()
            .then(data => {
                if (!response.ok) {
                    const error = new Error('HTTP error');
                    error.data = data;
                    throw error;
                }
                return data;
            });
        })
        .then(data => {
            if (data.ok){
                console.log(data);
                R_errorMessage.textContent = '註冊成功';
            } else {
                throw new Error('無效的註冊data response');
            }            
        })
        .catch(error => {
            if (error.data) {
                R_errorMessage.textContent = error.data.message;
                console.error(error.data); // Log the entire detail object
            } else {
                errorMessage.textContent = error.message;
                console.error('Error是:', error.message || error);
            }
        });
    })

})

let currentPage = 0;
let fetching = false;

//去資料庫拿特定user的購物車的資料
async function fetchBookingDetails() {
    const token = localStorage.getItem('received_Token');
    try {
        const response = await fetch(`/api/shop/cart`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });
        console.log(response)
        if (!response.ok) {
            throw new Error(`/api/booking的response有錯誤: ${response.statusText}`);
        }

        const data = await response.json();
        //加入各種booking細節或是出現"目前沒有預定行程"
        console.log(data)
        if (data) {
            addBooking(data);            
        } else {
            //沒有預定行程在資料庫，因此隱藏預定行程，顯示無行程
            const bookingFound1 = document.getElementById('booking-found-1');
            const bookingFound2 = document.getElementById('booking-found-2');
            const noBooking = document.getElementById('no-booking');
            bookingFound1.classList.remove('visible');
            bookingFound2.classList.remove('visible');
            noBooking.classList.add('visible');
            document.getElementById('no-booking').textContent = '目前沒有任何待預定的行程';
        }
        
    } catch (error) {
        console.error('收到response前有錯誤:', error);
    }
}

//在HTML加入各種資料
function addBooking(data_booking) {
    if (fetching) return;
    fetching = true;

    //有預定行程在資料庫，因此顯示預定行程
    const bookingFound1 = document.getElementById('booking-found-1');
    const bookingFound2 = document.getElementById('booking-found-2');
    const noBooking = document.getElementById('no-booking');
    bookingFound1.classList.add('visible');
    bookingFound2.classList.add('visible');
    noBooking.classList.remove('visible');

    // 取得放置商品的容器 (假設你有一個 id 為 cart-items 的 div 來放置商品)
    const cartItemsContainer = document.getElementById('cart-items');
    cartItemsContainer.innerHTML = '';  // 清空容器內容

    // 迭代每個購物車中的商品，並將其加入到HTML
    data_booking.forEach(item => {
        const product = item.product;

        // 創建商品的容器
        const productContainer = document.createElement('div');
        productContainer.className = 'product-container';

        // 加入圖片
        //const imageElement = document.createElement('img');
        //imageElement.src = product.image;
        //imageElement.alt = product.name;
        //imageElement.className = 'product-image';
        //productContainer.appendChild(imageElement);

        // 加入名稱
        const nameElement = document.createElement('h3');
        nameElement.textContent = product.name;
        productContainer.appendChild(nameElement);

        // 加入描述
        const descriptionElement = document.createElement('p');
        descriptionElement.textContent = product.description;
        descriptionElement.className = 'product-description';
        productContainer.appendChild(descriptionElement);

        // 加入價格
        const priceElement = document.createElement('p');
        priceElement.textContent = `Price: ${product.price} EURO`;
        priceElement.className = 'product-price';
        productContainer.appendChild(priceElement);

        // 加入數量
        const quantityElement = document.createElement('p');
        quantityElement.textContent = `Amount: ${product.quantity}`;
        quantityElement.className = 'product-quantity';
        productContainer.appendChild(quantityElement);

        // 刪除按鈕
        const deleteButton = document.createElement('div');
        deleteButton.id = 'delete-booking';
        deleteButton.className = 'delet-booking';
        productContainer.appendChild(deleteButton);

        // 將商品容器加入到購物車項目容器中
        cartItemsContainer.appendChild(productContainer);
    });

    //加入刪除按鈕
    const delete_button = document.getElementById('delete-booking');
    delete_button.addEventListener('click', async function(){
        deleteBooking();
    }); 
    

    // 計算並顯示總價
    const totalPriceElement = document.getElementById('total-price');
    const totalPrice = data_booking.reduce((sum, item) => sum + (item.product.price * item.product.quantity), 0);
    console.log(totalPrice)
    totalPriceElement.textContent = `Total: ${totalPrice} EURO`;
}

//刪除booking資料庫
async function deleteBooking() {
    const token = localStorage.getItem('received_Token');

    try {
        const response = await fetch(`/api/shop/cart`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) {
            throw new Error(`/api/booking的response有錯誤: ${response.statusText}`);
        }

        const data = await response.json();
        if (data.ok) {
            //刪除成功的話，refresh page載入資料
            await fetchBookingDetails();
        } else {
            throw new Error('刪除行程失敗');
        }
    } catch (error) {
        console.error('刪除行程時發生錯誤:', error);
        alert('刪除行程時發生錯誤');
    }
}

//每次重新整理頁面，都檢查一次使用者的TOKEN
function fetchUserInfo() {
    const token = localStorage.getItem('received_Token');

    //這個return很重要，因為有這個才有完整的promise chain，其他功能可以使用驗證以後的promise
    return fetch('/api/user/auth', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            //token ? ... : ... 這個確認token變數是不是truthy，非null,undefined, empty string
            //如果truthy，冒號前面的會執行; falsy的話，後面的empty string會執行
            'Authorization': token ? `Bearer ${token}` : ''
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('網路response was not ok')
        }
        return response.json();
    }
    )
    .then(data => {
        console.log(data);
        //如果使用者token正確，要把收到的data傳給以後的promise chain
        if (data !== null && data.data){
            renderLogout();
            return data.data;
        } else {
            //如果使用者token不正確，要把null傳給以後的promise chain
            renderLogin();
            return null;
        }
    })
    .catch(error => {
        //如果使用者token不正確，要把null傳給以後的promise chain
        console.error('Error fetching user info:', error);
        renderLogin();
        return null;
    });
}




//render 登出系統
function renderLogout(){
    document.getElementById('login-register').style.display = 'none';
    document.getElementById('logout').style.display = 'block';
    document.getElementById('login-register').classList.remove('visible');
    document.getElementById('logout').classList.add('visible');
}
//render 登入/註冊
function renderLogin(){
    document.getElementById('logout').style.display = 'none';
    document.getElementById('login-register').style.display = 'block';
    document.getElementById('logout').classList.remove('visible');
    document.getElementById('login-register').classList.add('visible');
}

//登出功能
document.getElementById('logout').addEventListener('click', function(){
    localStorage.removeItem('received_Token');
    //登出後重整頁面
    location.reload();
})