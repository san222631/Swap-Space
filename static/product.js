//全域變數，給"開始預訂行程"用的
let productData = null;
let observer;
let currentPage = 0;
document.addEventListener('DOMContentLoaded', async() => {
    fetchUserInfo()

    //拿url後面的id並開始使用資料
    const pathname = window.location.pathname;
    const specialId = pathname.split('/').pop();
    console.log('特別的號碼:', specialId)
   
    try {
        //等fetch call拿到promise以後才做下一步動作
        const response = await fetch(`/api/product/${specialId}`);
        //如果response有問題
        if (!response.ok) {
            throw new Error(`/api/product/id送過來的response有錯誤: ${response.statusText}`);
        }

        //把收到的response變成json格式
        const data = await response.json();
        //檢查json
        console.log(data);
        //存起來給"開始預訂行程"用
        productData = data;

        addDetails(data);

        //給相關推薦
        fetchRelevantProducts(data.data.category, specialId);
  
    } catch (error) {
        console.error('收到response前有錯誤:', error);
        document.getElementById('check').textContent = '加載細節失敗';
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

//加入各種資料
function addDetails(details) {
    if (fetching) return;
    fetching = true;

    const imageList = document.getElementById('image-list');   

    details.data.images.forEach(image => {
        const picture = document.createElement('img');
        picture.src = image
        picture.className = 'picture';
        picture.alt = details.data.name;
        imageList.appendChild(picture);
    });

    //一開始先幫每張圖片加入圈圈，然後把第一張的class變成active
    const circleList = document.getElementById('allCircles');
    details.data.images.forEach((_, index) => {
        const circle = document.createElement('div');
        circle.className = 'circle';
        //circle的class本來是.circle，現在變.circle.active
        if (index === 0) circle.classList.add('active');
        circleList.appendChild(circle);
    })

    //圖片slide show的關鍵
    setupCarousel();

    //加入不同的內容
    const name = document.getElementById('name');
    name.textContent = details.data.name;

    const description = document.getElementById('description');
    description.textContent = details.data.description;

    const price = document.getElementById('cost');
    price.textContent = `${details.data.price} €/month`;

    const dimension = document.getElementById('dimension');
    dimension.textContent = `Size: ${details.data.dimension}`;

    const prduct_code = document.getElementById('product_id');
    prduct_code.textContent = `Product Code: ${details.data.product_id}`
    
}

//圖片slide show旋轉木馬的關鍵
function setupCarousel() {
    //選擇所有的圖片+確認總共有幾張
    const imageList = document.getElementById('image-list');
    const allImages = imageList.querySelectorAll('img');
    const numberImages = allImages.length;
    //選擇所有的circle elements
    const allCircles = document.querySelectorAll('.circle');
    //從第1張圖片開始, index=0
    let currentIndex = 0;


    //操縱css裡面.image-list的transform
    //在X軸上translate移動
    //移動圖片的同時，也讓圈圈的class轉換，用圖片的index確認是哪一個圈圈要變active
    function showImage(index) {
        imageList.style.transform = `translateX( -${index *100}%)`;
        allCircles.forEach((eachCircle, i) => {
            eachCircle.classList.toggle('active', i === index);
        })
    };

    document.getElementById('scroll-left').addEventListener(
        'click', function() {
            currentIndex = (currentIndex - 1 + numberImages) % numberImages;
            showImage(currentIndex);
        }
    );

    document.getElementById('scroll-right').addEventListener(
        'click', function() {
        currentIndex = (currentIndex + 1) % numberImages;
        showImage(currentIndex);
        }
    );

    showImage(currentIndex);
};

//加入購物車
document.getElementById('reserve').addEventListener('click', async function(event){
    event.preventDefault();
    const check_status = await fetchUserInfo();
    let token = null;
    let sessionId = sessionStorage.getItem('session_id');

    //已登入的會員
    if (check_status) {
        token = localStorage.getItem('received_Token');
    } 

    if (!productData){
        throw new Error('Not an existing product');
    }

    const requestBody = {
        "productId": productData.data.product_id,
        "quantity": document.getElementById('order-amount').value,
        "price": productData.data.price
    };

    const headers = {
        'Content-Type': 'application/json'
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    if (sessionId) {
        headers['X-Session-ID'] = sessionId;  // Custom header for session_id
    }

    try {
        const response = await fetch('/api/shop/cart', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(requestBody),
        });
    
        if (!response.ok) {
            throw new Error(`/api/shop/cart的response有錯誤: ${response.statusText}`);
        };

        const data = await response.json();
        if (data.ok) {
            //window.location.href = '/booking';
            alert('Product added to your shopping cart!');
            if (data.session_id) {
                sessionStorage.setItem('session_id', data.session_id)
            }
            console.log("新增到購物車了!", data)
        } else {
            throw new Error('新增商品失敗');
        }
    } catch (error) {
        console.error('Error:', error);
    }
});

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

//加入最愛清單
function addToWishlist() {    
    // Extract the product_id from the URL
    const url = window.location.href;
    const productId = url.split('/').pop();

    // Debugging: log the extracted productId
    console.log("Extracted product ID:", productId);

    // Retrieve the session_id from sessionStorage
    const sessionId = sessionStorage.getItem('session_id');
    const token = localStorage.getItem('received_Token');

    // Set up headers
    const headers = {
        'Content-Type': 'application/json',
    };

    if (token) {
        headers['Authorization'] = token ? `Bearer ${token}` : '';
    } else if (sessionId) {
        headers['X-Session-ID'] = sessionId;
    }

    fetch('/api/wishlist/add', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ product_id: productId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === "Product added to wishlist") {
            alert('Product added to your wishlist!');
        } else if (data.message === "Product is already in wishlist") {
            alert('Product is already in your wishlist!');
        }

        // If a new session_id is returned, save it to sessionStorage
        if (data.session_id) {
            sessionStorage.setItem('session_id', data.session_id);
        }
    })
    .catch(error => {
        console.error('Error adding product to wishlist:', error);
    });
}

//推薦相關商品
async function fetchRelevantProducts(category, currentProductId) {
    try {
        const response = await fetch(`/api/products/related?category=${encodeURIComponent(category)}&exclude_id=${currentProductId}`);
        if (!response.ok) {
            throw new Error(`Error fetching related products: ${response.statusText}`);
        }

        const relatedProductsData = await response.json();
        console.log(relatedProductsData)
        displayRelevantProducts(relatedProductsData.data);
    } catch (error) {
        console.error('Error fetching related products:', error);
    }
}

function displayRelevantProducts(products) {
    const relevantContainer = document.getElementById('relevant-container');
    
    if (products.length === 0) {
        relevantContainer.textContent = 'No related products found.';
        return;
    }

    products.forEach(product => {
        const productDiv = document.createElement('div');
        productDiv.className = 'relevant-product';
        productDiv.innerHTML = '';
        // 加入圖片
        const reImageElement = document.createElement('img');
        reImageElement.src = product.image_url;
        reImageElement.alt = product.Name;
        reImageElement.className = 're-product-image';
        reImageElement.addEventListener('click', function(){
            window.location.href = `/product/${product.Product_id}`;
        });
        productDiv.appendChild(reImageElement);

        // 加入名稱
        const reNameElement = document.createElement('div');
        reNameElement.textContent = product.Name;
        reNameElement.className = 're-product-name';
        productDiv.appendChild(reNameElement);
        reNameElement.addEventListener('click', function(){
            window.location.href = `/product/${product.Product_id}`;
        });

        // 加入價格
        const rePriceElement = document.createElement('div');
        rePriceElement.textContent = `${product.Price} €/month`;
        rePriceElement.className = 're-product-price';
        rePriceElement.dataset.product_price = product.Price;
        productDiv.appendChild(rePriceElement);

        relevantContainer.appendChild(productDiv);
    });
}