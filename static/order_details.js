document.addEventListener('DOMContentLoaded', async() => {    
    //其他資料
    const userInfo = await fetchUserInfo();
    const orderNumber = window.location.pathname.split('/').pop();    

    if (userInfo) {
        //加入會換名字跟訂單編號的感謝語
        console.log(userInfo)
        const greeting = document.getElementById('greeting');
        greeting.textContent = `${userInfo.name} , order number: ${orderNumber}`;
        fetchOrderDetails(orderNumber);
    } else {
        window.location.href = '/';
    }  

    //按回首頁
    const goIndex = document.getElementById('go-index');
    goIndex.addEventListener('click', function(){
        window.location.href = '/';
    });

    //會員中心看訂單或帳號更改
    document.getElementById('account').addEventListener('click', function(){
        window.location.href = '/account';  // Redirect to the Account page
    });
    document.getElementById('order-list').addEventListener('click', function(){
        window.location.href = '/member';  // Redirect to the Order List page
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

    //搜尋關鍵字
    document.getElementById('search-button').addEventListener('click', function () {
        const keyword = document.getElementById('search-input').value;
        if (keyword) {
            sessionStorage.setItem('searchKeyword', keyword);
            window.location.href = `/shop`;
        } else {
            alert("Please enter a keyword to search");
        }
    });

    //進入最愛清單
    document.getElementById('go-to-wishlist').addEventListener('click', function() {
        window.location.href = '/wishlist';
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
                // Remove the session_id from session storage
                sessionStorage.removeItem('session_id');
                localStorage.setItem('received_Token', data.token);
                console.log(data);
                modal.style.display = 'none';
                errorMessage.textContent = '';
                renderLogout()
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
                // Remove the session_id from session storage
                sessionStorage.removeItem('session_id');
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


let fetching = false;
//去資料庫拿特定user的購物車的資料
async function fetchOrderDetails(order_number) {
    const token = localStorage.getItem('received_Token');

    // Setup headers for the fetch request
    const headers = {
        'Content-Type': 'application/json',
    };

    // Add the Authorization header if the user is logged in
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`/api/member/${order_number}`, {
            method: 'GET',
            headers: headers
        });
        console.log(response)
        if (!response.ok) {
            throw new Error(`/api/member/orderNumeber的response有錯誤: ${response.statusText}`);
        }

        const data = await response.json();
        //加入各種booking細節或是出現"目前沒有預定行程"
        console.log(data)
        if (data && data.data) {
            addOrders(data);
            console.log('/api/member/orderNumber收到的response:', data);
            return data
        } else {
            //沒有預定行程在資料庫，因此隱藏預定行程，顯示無行程
            const bookingFound1 = document.getElementById('booking-found-1');
            const bookingFound2 = document.getElementById('booking-found-2');
            const noBooking = document.getElementById('no-booking');
            bookingFound1.classList.remove('visible');
            bookingFound2.classList.remove('visible');
            noBooking.classList.add('visible');
            document.getElementById('no-booking').textContent = '沒有這個訂單';
            return null;
        }
        
    } catch (error) {
        console.error('收到response前有錯誤:', error);
        return null;
    }
}

//在HTML加入各種資料
function addOrders(data_booking) {
    //有預定行程在資料庫，因此顯示預定行程
    const bookingFound1 = document.getElementById('booking-found-1');
    const bookingFound2 = document.getElementById('booking-found-2');
    const noBooking = document.getElementById('no-booking');
    bookingFound1.classList.add('visible');
    bookingFound2.classList.add('visible');
    noBooking.classList.remove('visible');

    // 取得放置商品的容器 (假設你有一個 id 為 cart-items 的 div 來放置商品)
    const tableBody = document.querySelector('#orders-table tbody');
    tableBody.innerHTML = '';  // 清空容器內容

    // Create a new table row
    const row = document.createElement('tr');
    // Order Date
    const orderDateCell = document.createElement('td');
    orderDateCell.textContent = data_booking.data.order_date;
    row.appendChild(orderDateCell);
    // Subscription Period
    const subPeriodCell = document.createElement('td');
    subPeriodCell.textContent = `${data_booking.data.subscription_period} months`;
    row.appendChild(subPeriodCell);
    // Start Date
    const startDateCell = document.createElement('td');
    startDateCell.textContent = data_booking.data.start_date;
    row.appendChild(startDateCell);

    // End Date
    const endDateCell = document.createElement('td');
    endDateCell.textContent = data_booking.data.end_date;
    row.appendChild(endDateCell);

    // Total Price
    const priceCell = document.createElement('td');
    priceCell.textContent = `${data_booking.data.total_price} €/month`;
    row.appendChild(priceCell);

    // Order Status
    const statusCell = document.createElement('td');
    statusCell.textContent = data_booking.data.order_status;
    row.appendChild(statusCell);
    // Order Status
    const nextPaymentCell = document.createElement('td');
    nextPaymentCell.textContent = data_booking.data.next_payment_date;
    row.appendChild(nextPaymentCell);

    // Append the row to the table body
    tableBody.appendChild(row);

    // 取得放置商品的容器 (假設你有一個 id 為 cart-items 的 div 來放置商品)
    const cartItemsContainer = document.getElementById('cart-items');
    cartItemsContainer.innerHTML = '';  // 清空容器內容
    let products_in_order = JSON.parse(data_booking.data.order_info);
    // 迭代每個購物車中的商品，並將其加入到HTML
    products_in_order.forEach(item => {
        // 創建商品的容器
        const productContainer = document.createElement('div');
        productContainer.className = 'product-container';

        // 加入圖片
        const imageItem = document.createElement('img');
        imageItem.src = item.product.image;
        imageItem.alt = item.product.name;
        imageItem.className = 'product-image';
        productContainer.appendChild(imageItem);

        // 創建文字的容器
        const textContainer = document.createElement('div');
        textContainer.className = 'text-container';
        // 加入名稱
        const nameElement = document.createElement('div');
        nameElement.textContent = item.product.name;
        nameElement.className = 'product-name';
        textContainer.appendChild(nameElement);
        nameElement.addEventListener('click', function(){
            window.location.href = `/product/${item.product.id}`;
        });
        // 加入商品id
        const idElement = document.createElement('div');
        idElement.textContent = `Product id: ${item.product.id}`;
        idElement.className = 'product-id';
        textContainer.appendChild(idElement);
        // 加入價格
        const priceElement = document.createElement('div');
        priceElement.textContent = `${item.product.price} €/month`;
        priceElement.className = 'product-price';
        priceElement.dataset.product_price = item.product.price;
        textContainer.appendChild(priceElement);

        // 加入數量
        const quantityItem = document.createElement('div');
        quantityItem.textContent = `${item.product.quantity} piece`;
        quantityItem.className = 'product-quantity';
        quantityItem.id = `order-amount-${item.product.id}`;
        textContainer.appendChild(quantityItem);

        productContainer.appendChild(textContainer);

        //每個家具總價
        const subPrice = document.createElement('div');
        subTotal = item.product.price*item.product.quantity;
        subPrice.textContent = `${subTotal.toFixed(2)} €`;
        subPrice.className = 'sub-price';
        productContainer.appendChild(subPrice);

        // 將商品容器加入到購物車項目容器中
        cartItemsContainer.appendChild(productContainer);

        const seperatorElement = document.createElement('div');
        seperatorElement.className = 'product-seperator';
        cartItemsContainer.appendChild(seperatorElement);

    })
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

