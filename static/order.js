let currentPage = 0;
document.addEventListener('DOMContentLoaded', async() => {
    //連上TAPPAY
    const APP_IP = '151825';
    const APP_KEY = 'app_Idf5nklHD5lm9I0kpTtnzc3DLDv9EEFnmQUpj205kr5LAvufIEAdeE0iOzKS';
    const SERVER_TYPE = 'sandbox';

    TPDirect.setupSDK(APP_IP, APP_KEY, SERVER_TYPE);
    TPDirect.card.setup({
        fields: {
            number: {
                element: '#card-number',
                placeholder: '**** **** **** ****'
            },
            expirationDate: {
                element: '#card-expiration-date',
                placeholder: 'MM / YY'
            },
            ccv: {
                element: '#card-ccv',
                placeholder: 'ccv'
            }
        },
        styles: {
            'input': {
                'color': 'gray'
            },
            ':focus': {
                'color': 'black'
            },
            '.valid': {
                'color': 'green'
            },
            '.invalid': {
                'color': 'red'
            },
            '@media screen and (max-width: 400px)': {
                'input': {
                    'color': 'orange'
                }
            }
        },
        isMaskCreditCardNumber: true,
        maskCreditCardNumberRange: {
            beginIndex: 6,
            endIndex: 11
        }
    });

    // Enable or disable the submit button based on the card form's state
    TPDirect.card.onUpdate(function (update) {
        const submitButton = document.getElementById('O-button');

        if (update.canGetPrime) {
            // Enable the submit button
            submitButton.removeAttribute('disabled');
        } else {
            // Disable the submit button
            submitButton.setAttribute('disabled', true);
        }

        // Optionally, handle card type
        if (update.cardType === 'visa') {
            // Handle card type visa.
        }

        // Handle the status of each field
        const fields = ['number', 'expiry', 'ccv'];
        fields.forEach(field => {
            const fieldStatus = update.status[field];
            const fieldElement = document.getElementById(`card-${field}`);
            if (fieldStatus === 2) {
                setFieldToError(fieldElement);
            } else if (fieldStatus === 0) {
                setFieldToSuccess(fieldElement);
            } else {
                setFieldToNormal(fieldElement);
            }
        });
    });

    function setFieldToNormal(field) {
        const fieldElement = document.getElementById(field);
        if (fieldElement) {
            fieldElement.style.borderColor = "";
        }
    }
    
    function setFieldToSuccess(field) {
        const fieldElement = document.getElementById(field);
        if (fieldElement) {
            fieldElement.style.borderColor = "green";
        }
    }
    
    function setFieldToError(field) {
        const fieldElement = document.getElementById(field);
        if (fieldElement) {
            fieldElement.style.borderColor = "red";
        }
    }

    //會員輸入的訂購資訊
    const bookingInfo = await fetchBookingDetails();
    console.log(bookingInfo)
    //測試是否有錯!!!!!!!!!!!!!!!!!!!
    if (!bookingInfo) {
        console.error('Booking details are missing');
        // Handle the case where bookingInfo is missing
    } else {
        console.log('收到response了:', bookingInfo);
    }


    // Handle form submission
    document.getElementById('order-form').addEventListener('submit', onSubmit);
    
    // Define the onSubmit function
    function onSubmit(event) {
        event.preventDefault(); // Prevent the form from submitting normally

        // Calculate total price within the onSubmit function
        const totalPrice = bookingInfo.reduce((sum, item) => sum + (item.product.price * item.product.quantity), 0);

        // Get the start date value
        const startDate = document.getElementById('start-date').value;

        // Check if the start date is filled
        if (!startDate) {
            alert('Please select a start date.');
            return; // Stop the form submission
        }

        // Get the TapPay Fields status
        const tappayStatus = TPDirect.card.getTappayFieldsStatus();

        if (tappayStatus.canGetPrime) {
            // Get prime
            TPDirect.card.getPrime((result) => {
                if (result.status !== 0) {
                    console.log('Failed to get prime: ' + result.msg);
                    return;
                }

                console.log('Get prime success, prime: ' + result.card.prime);

                // Send prime to your server
                const token = localStorage.getItem('received_Token');
                fetch('/api/orders', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        prime: result.card.prime,
                        order: bookingInfo,
                        contact: {
                            name: document.getElementById('O-name').value,
                            email: document.getElementById('O-email').value,
                            phone: document.getElementById('O-phone').value
                        },
                        subscription: {
                            total_price: totalPrice,
                            subscription_period: document.getElementById('subscription-period').value,
                            start_date: startDate,
                            end_date: document.getElementById('end-date').value,
                        }
                    })
                }).then(response => {
                    return response.json();
                }).then(data => {
                    if (data.data.payment.status == 0) {
                        alert('付款成功');
                        window.location.href = `/member`;
                    } else {
                        alert('付款失敗: ' + data.data.payment.message);
                        window.location.href = `/member`;
                    }
                }).catch(error => {
                    console.error('Error:', error);
                    alert('付款失敗');
                });
            });
        } else {
            alert('Please complete the card information correctly.');
        }
    }
    
    //其他資料
    const userInfo = await fetchUserInfo();    

    if (userInfo) {
        //加入會換名字的問候語
        console.log(userInfo)
        const greeting = document.getElementById('greeting');
        greeting.textContent = `您好，${userInfo.name}，購物車內容如下:`;
        fetchBookingDetails();
    } else {
        window.location.href = '/';
        //const greeting = document.getElementById('greeting');
        //greeting.textContent = `您好，guest，購物車內容如下:`;
        //fetchBookingDetails();
    }  

    //按回首頁
    const goIndex = document.getElementById('go-index');
    goIndex.addEventListener('click', function(){
        window.location.href = '/';
    });

    //會員中心看訂單
    document.getElementById('member').addEventListener('click', function(){
        window.location.href = '/member';
    })

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

    //開始跟結束日期
    const subscriptionPeriod = document.getElementById("subscription-period");
    const startDate = document.getElementById("start-date");
    const endDate = document.getElementById("end-date");

    function updateEndDate() {
        const periodMonths = parseInt(subscriptionPeriod.value);
        const startDateValue = new Date(startDate.value);

        if (!isNaN(startDateValue) && !isNaN(periodMonths)) {
            const endDateValue = new Date(startDateValue);
            endDateValue.setMonth(endDateValue.getMonth() + periodMonths);
            
            // Format the date as YYYY-MM-DD
            const year = endDateValue.getFullYear();
            const month = String(endDateValue.getMonth() + 1).padStart(2, '0'); // Month is zero-based
            const day = String(endDateValue.getDate()).padStart(2, '0');
            endDate.value = `${year}-${month}-${day}`;
        }
    }

    startDate.addEventListener("change", updateEndDate);
    subscriptionPeriod.addEventListener("change", updateEndDate);
})


let fetching = false;
//去資料庫拿特定user的購物車的資料
async function fetchBookingDetails() {
    const token = localStorage.getItem('received_Token');
    let sessionId = sessionStorage.getItem('session_id');

    // Setup headers for the fetch request
    const headers = {
        'Content-Type': 'application/json',
    };

    // Add the Authorization header if the user is logged in
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Add the X-Session-ID header if a session_id exists in sessionStorage
    if (sessionId) {
        headers['X-Session-ID'] = sessionId;
    }

    try {
        const response = await fetch(`/api/shop/cart`, {
            method: 'GET',
            headers: headers
        });
        console.log(response)
        if (!response.ok) {
            throw new Error(`/api/shop/cart的response有錯誤: ${response.statusText}`);
        }

        const data = await response.json();
        //加入各種booking細節或是出現"目前沒有預定行程"
        console.log(data)
        if (data && data.length > 0) {
            addBooking(data);
            console.log('/api/shop/cart收到的response:', data);
            return data
        } else {
            //沒有預定行程在資料庫，因此隱藏預定行程，顯示無行程
            const bookingFound1 = document.getElementById('booking-found-1');
            const bookingFound2 = document.getElementById('booking-found-2');
            const noBooking = document.getElementById('no-booking');
            bookingFound1.classList.remove('visible');
            bookingFound2.classList.remove('visible');
            noBooking.classList.add('visible');
            document.getElementById('no-booking').textContent = '目前沒有任何商品';
            return null;
        }
        
    } catch (error) {
        console.error('收到response前有錯誤:', error);
        return null;
    }
}

//在HTML加入各種資料
function addBooking(data_booking) {
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
        const imageElement = document.createElement('img');
        imageElement.src = product.image;
        imageElement.alt = product.name;
        imageElement.className = 'product-image';
        productContainer.appendChild(imageElement);

        // 加入名稱
        const nameElement = document.createElement('h3');
        nameElement.textContent = product.name;
        productContainer.appendChild(nameElement);
        nameElement.addEventListener('click', function(){
            window.location.href = `/product/${product.id}`;
        });

        // 加入描述
        const descriptionElement = document.createElement('p');
        descriptionElement.textContent = product.description;
        descriptionElement.className = 'product-description';
        productContainer.appendChild(descriptionElement);

        // 加入價格
        const priceElement = document.createElement('p');
        priceElement.textContent = `Price: ${product.price} €/month`;
        priceElement.className = 'product-price';
        priceElement.dataset.product_price = product.price;
        productContainer.appendChild(priceElement);

        // 加入數量
        const quantityElement = document.createElement('input');
        quantityElement.type = 'number';
        quantityElement.id = `order-amount-${product.id}`;
        quantityElement.name = 'amount';
        //quantityElement.textContent = `Amount: ${product.quantity}`;
        quantityElement.value = product.quantity;
        quantityElement.min = 1;
        quantityElement.className = 'product-quantity';
        productContainer.appendChild(quantityElement);

        //送出新的數量
        //const updateButton = document.createElement('div');
        //updateButton.id = `update-button-${product.id}`;
        //updateButton.className = 'update-button';
        //productContainer.appendChild(updateButton);

        // 刪除按鈕
        const deleteButton = document.createElement('div');
        deleteButton.id = 'delete-booking';
        deleteButton.className = 'delete-booking';
        deleteButton.dataset.product_id = product.id;
        productContainer.appendChild(deleteButton);

        // 將商品容器加入到購物車項目容器中
        cartItemsContainer.appendChild(productContainer);

        //加入刪除按鈕
        deleteButton.addEventListener('click', function(){
            deleteBooking(product.id);
        });

        //更新數量
        quantityElement.addEventListener('input', function () {
            const newQuantity = parseInt(quantityElement.value, 10);
            
            if (newQuantity < 1) {
                alert("Quantity cannot be less than 1");
                quantityElement.value = product.quantity; // Reset to previous value if input is invalid
                return;
            }
        
            // Call a function to update the quantity in the backend
            updateCartQuantity(product.id, newQuantity);
        });
    }); 

    // 計算並顯示總價
    const totalPriceElement = document.getElementById('total-price');
    const totalPrice = data_booking.reduce((sum, item) => sum + (item.product.price * item.product.quantity), 0);
    console.log(totalPrice)
    totalPriceElement.textContent = `Recurring price/month: ${totalPrice} €`;
}

//刪除booking資料庫
async function deleteBooking(productId) {
    const token = localStorage.getItem('received_Token');

    try {
        const response = await fetch(`/api/shop/cart`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body:JSON.stringify({ product_id: productId})
        });
        if (!response.ok) {
            throw new Error(`/api/shop/cart的response有錯誤: ${response.statusText}`);
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

//更新購物車數量
async function updateCartQuantity(productId, newQuantity) {
    const token = localStorage.getItem('received_Token');

    try {
        const response = await fetch(`/api/shop/cart`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                productId: productId,
                quantity: newQuantity,
            })
        });

        if (!response.ok) {
            throw new Error(`/api/shop/cart的response有錯誤: ${response.statusText}`);
        }

        const data = await response.json();
        if (data.ok) {
            console.log('Quantity updated successfully');
            await fetchBookingDetails();
            // Optionally, refresh the cart or update the UI to reflect changes
        } else {
            throw new Error('Failed to update quantity');
        }
    } catch (error) {
        console.error('Error updating quantity:', error);
        alert('Error updating quantity');
    }
}