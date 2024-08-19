let observer;
let currentPage = 0;
let keyword = '';
document.addEventListener('DOMContentLoaded', function(){
    const urlParams = new URLSearchParams(window.location.search);
    keyword = sessionStorage.getItem('searchKeyword') || '';
    fetchUserInfo()
    if (keyword) {
        document.getElementById('search-input').value = decodeURIComponent(keyword);
        fetchProducts(currentPage, keyword)
            .then(() => {
                sessionStorage.removeItem('searchKeyword');
            })
            .catch(error => {
                console.error('Error during fetchProducts call:', error);                
            });
    } else {
        fetchProducts(currentPage);
    }    

    //偵測滾動
    observer = new IntersectionObserver(handleIntersection, {
        root: null,
        rootMargin: '0px',
        threshold: 0
    });

    const sentinel = document.createElement('div');
    sentinel.id = 'sentinel';
    document.body.appendChild(sentinel);
    observer.observe(sentinel);


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

    //搜尋關鍵字
    document.getElementById('search-button').addEventListener('click', function () {
        const keyword = document.getElementById('search-input').value;
        if (keyword) {
            searchProducts(keyword);
            fetchUserInfo()
        } else {
            alert("Please enter a keyword to search");
        }
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

function fetchProducts(page, keyword = '') {
    if (fetching) return Promise.resolve();
    fetching = true;
    console.log(`Fetching products for page ${page} with keyword '${keyword}'`); //EXTRA
    return fetch(`/api/products/?page=${page}&keyword=${encodeURIComponent(keyword)}`)
        .then(response => {
            if (!response.ok) {
                if (response.status == 404) {
                    throw new Error('No related furniture found');
                } else {
                    throw new Error('Network response was not ok');
                }                
            }
            return response.json();
        })
        .then(data => {
            const gridContent = document.getElementById('inside-product-grid');
            if (page === 0) {
                gridContent.innerHTML = '';
            }

            data.data.forEach(attraction => {
                const card = createProductCard(attraction);
                gridContent.appendChild(card);
            });

            // Ensure the sentinel is re-created and appended if necessary
            let sentinel = document.getElementById('sentinel');
            if (!sentinel) {
                sentinel = document.createElement('div');
                sentinel.id = 'sentinel';
            }
            gridContent.appendChild(sentinel);

            observer.observe(sentinel);

            currentPage = data.nextPage;
            fetching = false;
        })
        .catch(error => {
            console.error('Error loading the products:', error);
            const gridContent = document.getElementById('inside-product-grid');
            gridContent.innerHTML = '<p>No related furnitures.</p>';
            sessionStorage.removeItem('searchKeyword');
            fetching = false;
            throw error;
        });
}


//產生每個商品的<div><class>，包括圖片、名稱、捷運站、分類，
function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'card';
    //增加了每個商品的id以及偵測有沒有被click
    card.id = product.product_id;
    card.addEventListener('click', function(){
            window.location.href = `/product/${product.product_id}`;
    });

    const image = document.createElement('img');
    image.src = product.images[0];
    image.alt = product.name;
    image.className = 'product-image';

    const name = document.createElement('div');
    name.textContent = product.name;
    name.className = 'product-name';

    const price = document.createElement('div');
    price.textContent = `${product.price} €/month`;
    price.className = 'product-price';

    const mrt = document.createElement('div');
    mrt.textContent = product.mrt;
    mrt.className = 'attraction-mrt';

    card.appendChild(image);
    card.appendChild(name);
    card.appendChild(price);
    card.appendChild(mrt);

    return card;
}

//偵測滾動
function handleIntersection(entries, observer) {
    entries.forEach(entry => {
        if (entry.isIntersecting && currentPage !== null) {
            const keyword = document.getElementById('search-input').value;
            fetchProducts(currentPage, keyword);
        }
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

//用關鍵字找景點
function searchProducts(keyword) {
    currentPage = 0;
    fetchProducts(currentPage, keyword);
}