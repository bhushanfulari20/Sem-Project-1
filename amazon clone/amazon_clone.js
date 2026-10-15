/**
 * SafeCart Amazon Clone Integration
 * Connects the Amazon-style e-commerce frontend to the SafeCart database,
 * catalog of 500 products, inventory, orders, and Worker + Auditor AI chatbot.
 */

// -----------------------------------------------------------------------------
// Configuration & API Base URL
// -----------------------------------------------------------------------------
const getApiBaseUrl = () => {
    // If running on the FastAPI backend server (e.g. port 8000 or same host)
    if (window.location.port === "8000" || window.location.pathname.startsWith("/amazon")) {
        return window.location.origin + "/api";
    }
    // Fallback if opened via file:// or another static server (e.g. Live Server on 5500)
    return "http://127.0.0.1:8000/api";
};

const API_BASE = getApiBaseUrl();

// -----------------------------------------------------------------------------
// App State
// -----------------------------------------------------------------------------
const state = {
    allProducts: [],
    filteredProducts: [],
    categories: [],
    currentPage: 1,
    pageSize: 24,
    searchQuery: "",
    selectedCategory: "all",
    selectedSort: "featured",
    inStockOnly: false,
    maxPriceFilter: null,
    currentView: "shelves",
    
    // Shopping Cart
    cart: JSON.parse(localStorage.getItem("safecart_amazon_cart") || "[]"),
    
    // Logged in customer (default: Amazon Customer U005 from SafeCart users.csv)
    user: JSON.parse(localStorage.getItem("safecart_amazon_user") || JSON.stringify({
        user_id: "U005",
        name: "Amazon Customer",
        email: "customer@amazon.in",
        address: "202 Marine Drive, Mumbai, India"
    })),

    // Active Chat Context
    chatContext: {
        productId: null,
        productName: null,
        orderId: null
    },

    // Chat History
    chatMessages: [
        {
            sender: "bot",
            text: "Hello! I am your SafeCart AI Assistant. Every product price, stock level, delivery date, and policy response is strictly verified by our Auditor AI against the database. How can I help you today?",
            audit: {
                status: "APPROVED",
                audit_decision: "APPROVED",
                intent: "WELCOME",
                verified: true
            }
        }
    ]
};

// -----------------------------------------------------------------------------
// Category Visuals & Icons Mapping
// -----------------------------------------------------------------------------
const CATEGORY_VISUALS = {
    "Electronics": { img: "box4_image.jpg", icon: "fa-laptop", color: "#3a7bd5" },
    "Accessories": { img: "box10_image.jpg", icon: "fa-headphones", color: "#6a11cb" },
    "Clothing": { img: "box1_image.jpg", icon: "fa-shirt", color: "#ff6a00" },
    "Fashion": { img: "box8_image.jpg", icon: "fa-vest", color: "#f857a6" },
    "Footwear": { img: "box8_image.jpg", icon: "fa-shoe-prints", color: "#e52d27" },
    "Personal Care": { img: "box2_image.jpg", icon: "fa-heart-pulse", color: "#00b09b" },
    "Home & Kitchen": { img: "box3_image.jpg", icon: "fa-kitchen-set", color: "#f7971e" },
    "Home": { img: "box12_image.jpg", icon: "fa-house", color: "#43cea2" },
    "Furniture": { img: "box3_image.jpg", icon: "fa-couch", color: "#8e2de2" },
    "Fitness": { img: "box9_image.jpg", icon: "fa-dumbbell", color: "#11998e" },
    "Sports": { img: "box10_image.jpg", icon: "fa-futbol", color: "#fc4a1a" },
    "Mobiles": { img: "box4_image.jpg", icon: "fa-mobile-screen", color: "#2193b0" },
    "Computers": { img: "box4_image.jpg", icon: "fa-display", color: "#4776e6" },
    "Storage": { img: "box4_image.jpg", icon: "fa-hard-drive", color: "#596164" },
    "Networking": { img: "box4_image.jpg", icon: "fa-wifi", color: "#00c6ff" },
    "Stationery": { img: "box11_image.jpg", icon: "fa-pen-ruler", color: "#f2709c" },
    "Bags": { img: "box1_image.jpg", icon: "fa-briefcase", color: "#795548" },
    "Home Appliances": { img: "box3_image.jpg", icon: "fa-blender", color: "#3f51b5" }
};

// -----------------------------------------------------------------------------
// DOM Elements
// -----------------------------------------------------------------------------
const dom = {
    searchCategorySelect: document.getElementById("search-category-select"),
    searchInput: document.getElementById("search-input"),
    searchBtn: document.getElementById("search-btn"),
    navCartBtn: document.getElementById("nav-cart-btn"),
    navCartBadge: document.getElementById("nav-cart-badge"),
    navOrdersBtn: document.getElementById("nav-orders-btn"),
    navSigninBtn: document.getElementById("nav-signin-btn"),
    navUserGreeting: document.getElementById("nav-user-greeting"),
    navAddressText: document.getElementById("nav-address-text"),
    deliverAddressBtn: document.getElementById("deliver-address-btn"),
    panelAllBtn: document.getElementById("panel-all-btn"),
    
    // Catalog Views
    categoryShelvesContainer: document.getElementById("category-shelves-container"),
    gridViewWrapper: document.getElementById("grid-view-wrapper"),
    viewModeShelvesBtn: document.getElementById("view-mode-shelves-btn"),
    viewModeGridBtn: document.getElementById("view-mode-grid-btn"),
    productsGrid: document.getElementById("products-grid"),
    paginationContainer: document.getElementById("pagination-container"),
    resultsCount: document.getElementById("results-count"),
    catalogSortSelect: document.getElementById("catalog-sort-select"),
    filterPillsContainer: document.getElementById("filter-pills-container"),
    
    // Modals
    productModal: document.getElementById("product-detail-modal"),
    productModalBody: document.getElementById("product-modal-body"),
    cartDrawer: document.getElementById("cart-drawer"),
    cartDrawerOverlay: document.getElementById("cart-drawer-overlay"),
    cartItemsBody: document.getElementById("cart-items-body"),
    cartSubtotalText: document.getElementById("cart-subtotal-text"),
    cartHeaderCount: document.getElementById("cart-header-count"),
    checkoutModal: document.getElementById("checkout-modal"),
    checkoutModalBody: document.getElementById("checkout-modal-body"),
    ordersModal: document.getElementById("orders-modal"),
    ordersModalBody: document.getElementById("orders-modal-body"),
    authModal: document.getElementById("auth-modal"),
    dbSyncModal: document.getElementById("db-sync-modal"),
    
    // Chatbot
    chatWidget: document.getElementById("safecart-chat-widget"),
    chatToggleBtn: document.getElementById("chat-toggle-btn"),
    chatWindow: document.getElementById("chat-window"),
    chatCloseBtn: document.getElementById("chat-close-btn"),
    chatMessagesContainer: document.getElementById("chat-messages"),
    chatInput: document.getElementById("chat-input"),
    chatSendBtn: document.getElementById("chat-send-btn"),
    chatContextPill: document.getElementById("chat-context-pill"),
    chatContextText: document.getElementById("chat-context-text"),
    chatContextClear: document.getElementById("chat-context-clear")
};

// -----------------------------------------------------------------------------
// Toast Notice Helper
// -----------------------------------------------------------------------------
function showToast(message, type = "success") {
    let toast = document.querySelector(".toast-notice");
    if (!toast) {
        toast = document.createElement("div");
        toast.className = "toast-notice";
        document.body.appendChild(toast);
    }
    toast.className = `toast-notice show ${type}`;
    const icon = type === "success" ? "fa-circle-check" : "fa-circle-exclamation";
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    setTimeout(() => {
        toast.classList.remove("show");
    }, 3200);
}

// -----------------------------------------------------------------------------
// Initial Data Fetching from SafeCart Database
// -----------------------------------------------------------------------------
async function initApp() {
    updateUserDisplay();
    updateCartBadge();
    setupEventListeners();

    try {
        // 1. Fetch categories
        await fetchCategories();
        // 2. Fetch all 500 products from SafeCart backend
        await fetchProducts();
    } catch (err) {
        console.error("Initialization error:", err);
        showToast("Backend connection initialized with offline fallback.", "error");
    }
}

async function fetchCategories() {
    try {
        const res = await fetch(`${API_BASE}/categories`);
        if (res.ok) {
            const data = await res.json();
            state.categories = data.categories || [];
            populateCategoriesUI();
        }
    } catch (e) {
        console.warn("Could not fetch categories from API, will deduce from products:", e);
    }
}

async function fetchProducts() {
    try {
        if (dom.productsGrid) {
            dom.productsGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #565959;">
                    <i class="fa-solid fa-spinner fa-spin fa-2x"></i>
                    <p style="margin-top: 10px; font-weight: 600;">Loading 500 verified products from SafeCart database...</p>
                </div>
            `;
        }

        const res = await fetch(`${API_BASE}/products?limit=500`);
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const data = await res.json();
        
        state.allProducts = data.products || [];
        console.log(`Loaded ${state.allProducts.length} products from SafeCart database.`);

        // Deduce categories if not loaded
        if (!state.categories.length) {
            const catSet = new Set(state.allProducts.map(p => p.category).filter(Boolean));
            state.categories = Array.from(catSet).sort();
            populateCategoriesUI();
        }

        renderCategoryShelves();
        if (state.currentView === "shelves") {
            switchCatalogView("shelves");
        } else {
            applyFilters();
        }
    } catch (err) {
        console.error("Failed to load products from SafeCart API:", err);
        if (dom.productsGrid) {
            dom.productsGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #b12704; background: #fff; border-radius: 8px;">
                    <i class="fa-solid fa-triangle-exclamation fa-2x"></i>
                    <p style="margin-top: 10px; font-weight: 700;">Could not connect to SafeCart API at ${API_BASE}.</p>
                    <p style="font-size: 0.85rem; color: #565959; margin-top: 4px;">Make sure the FastAPI backend is running on http://127.0.0.1:8000.</p>
                    <button onclick="fetchProducts()" style="margin-top: 15px; padding: 8px 18px; border-radius: 20px; background: #ffd814; border: 1px solid #fcd200; cursor: pointer; font-weight: 600;">Retry</button>
                </div>
            `;
        }
    }
}

// -----------------------------------------------------------------------------
// Category Normalization & Matching Helper
// -----------------------------------------------------------------------------
function normalizeCategory(cat) {
    if (!cat) return "";
    return String(cat).trim().toLowerCase().replace(/&amp;/g, "&");
}

function categoryMatches(prodCat, targetCat) {
    const p = normalizeCategory(prodCat);
    const t = normalizeCategory(targetCat);
    if (!p || !t) return false;
    if (t === "all") return true;
    if (p === t) return true;
    if ((p === "bag" && t === "bags") || (p === "bags" && t === "bag")) return true;
    return false;
}

// -----------------------------------------------------------------------------
// UI Population: Categories Dropdown & Filter Pills
// -----------------------------------------------------------------------------
function populateCategoriesUI() {
    // Top search select dropdown
    if (dom.searchCategorySelect) {
        dom.searchCategorySelect.innerHTML = `<option value="all">All Categories</option>`;
        state.categories.forEach(cat => {
            const opt = document.createElement("option");
            opt.value = cat;
            opt.textContent = cat;
            dom.searchCategorySelect.appendChild(opt);
        });
    }

    // Filter pills toolbar
    if (dom.filterPillsContainer) {
        let html = `
            <button class="filter-btn ${state.selectedCategory === 'all' ? 'active' : ''}" data-category="all">All (${state.allProducts.length || 500})</button>
            <button class="filter-btn ${state.inStockOnly ? 'active' : ''}" data-filter="in_stock"><i class="fa-solid fa-check"></i> In Stock Only</button>
        `;
        state.categories.forEach(cat => {
            if (cat.toLowerCase() === "bag" && state.categories.includes("Bags")) return;
            const isActive = categoryMatches(cat, state.selectedCategory);
            html += `<button class="filter-btn ${isActive ? 'active' : ''}" data-category="${cat}">${cat}</button>`;
        });
        dom.filterPillsContainer.innerHTML = html;

        // Attach listeners to pills
        dom.filterPillsContainer.querySelectorAll(".filter-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                if (btn.dataset.filter === "in_stock") {
                    state.inStockOnly = !state.inStockOnly;
                    btn.classList.toggle("active", state.inStockOnly);
                    state.currentPage = 1;
                    applyFilters();
                } else if (btn.dataset.category) {
                    selectCategory(btn.dataset.category);
                }
            });
        });
    }
}

// -----------------------------------------------------------------------------
// Primary Category Selection Controller (Strict Category Isolation)
// -----------------------------------------------------------------------------
window.selectCategory = function(catName, shouldScroll = true) {
    if (!catName) catName = "all";
    state.selectedCategory = catName;
    state.currentPage = 1;

    // 1. Synchronize the top search category select
    if (dom.searchCategorySelect) {
        const foundOpt = Array.from(dom.searchCategorySelect.options).find(
            opt => categoryMatches(opt.value, catName)
        );
        if (foundOpt) {
            dom.searchCategorySelect.value = foundOpt.value;
        } else if (catName.toLowerCase() === "all") {
            dom.searchCategorySelect.value = "all";
        }
    }

    // 2. Synchronize active state of filter pills
    if (dom.filterPillsContainer) {
        dom.filterPillsContainer.querySelectorAll(".filter-btn").forEach(btn => {
            const bCat = btn.dataset.category;
            if (bCat) {
                btn.classList.toggle("active", categoryMatches(bCat, catName));
            }
        });
    }

    // 3. Render only the chosen category
    if (catName.toLowerCase() === "all") {
        switchCatalogView("shelves");
    } else {
        switchCatalogView("grid");
        applyFilters();
    }
    renderCategoryShelves();

    // 4. Smooth scroll to catalog section
    if (shouldScroll) {
        const catElem = document.getElementById("catalog-section");
        if (catElem) {
            catElem.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }
};

// -----------------------------------------------------------------------------
// Filtering, Sorting & Pagination Logic
// -----------------------------------------------------------------------------
function applyFilters() {
    let result = [...state.allProducts];

    // Category filter: strict isolation to selected category
    if (state.selectedCategory && state.selectedCategory.toLowerCase() !== "all") {
        result = result.filter(p => categoryMatches(p.category, state.selectedCategory));
    }

    // Search query filter (search across product_name, description, category, and product_id)
    if (state.searchQuery && state.searchQuery.trim()) {
        const q = state.searchQuery.trim().toLowerCase();
        result = result.filter(p =>
            String(p.product_name || "").toLowerCase().includes(q) ||
            String(p.description || "").toLowerCase().includes(q) ||
            String(p.category || "").toLowerCase().includes(q) ||
            String(p.product_id || "").toLowerCase().includes(q)
        );
    }

    // In Stock filter
    if (state.inStockOnly) {
        result = result.filter(p => p.in_stock && Number(p.quantity) > 0);
    }

    // Max Price filter (e.g. Under ₹899 box)
    if (state.maxPriceFilter !== null) {
        result = result.filter(p => Number(p.price) <= state.maxPriceFilter);
    }

    // Sort
    switch (state.selectedSort) {
        case "price_asc":
            result.sort((a, b) => Number(a.price) - Number(b.price));
            break;
        case "price_desc":
            result.sort((a, b) => Number(b.price) - Number(a.price));
            break;
        case "stock_desc":
            result.sort((a, b) => Number(b.quantity) - Number(a.quantity));
            break;
        case "name_asc":
            result.sort((a, b) => String(a.product_name).localeCompare(String(b.product_name)));
            break;
        default:
            // "featured" preserves natural DB ordering
            break;
    }

    state.filteredProducts = result;
    renderProducts();
    renderPagination();
    renderResultsMeta();
}

function renderResultsMeta() {
    if (!dom.resultsCount) return;
    const total = state.filteredProducts.length;
    const start = total === 0 ? 0 : (state.currentPage - 1) * state.pageSize + 1;
    const end = Math.min(state.currentPage * state.pageSize, total);

    let filterTag = "";
    if (state.selectedCategory !== "all") {
        filterTag += ` in <span style="color: #c45500; font-weight: 700;">${state.selectedCategory}</span>`;
    }
    if (state.searchQuery) {
        filterTag += ` for "<strong>${state.searchQuery}</strong>"`;
    }
    if (state.maxPriceFilter) {
        filterTag += ` (Under ₹${state.maxPriceFilter})`;
    }
    if (state.inStockOnly) {
        filterTag += ` (In Stock Only)`;
    }

    const isFiltered = (state.selectedCategory !== "all" || state.searchQuery || state.inStockOnly || state.maxPriceFilter !== null);
    const clearBtn = isFiltered
        ? `<button onclick="resetAllFilters()" style="margin-left: 12px; padding: 4px 12px; border-radius: 14px; background: #f0f2f2; border: 1px solid #d5d9d9; font-size: 0.8rem; cursor: pointer; font-weight: 600; color: #0f1111;">
            <i class="fa-solid fa-xmark"></i> Show All Categories
           </button>`
        : "";

    dom.resultsCount.innerHTML = `
        <span style="font-size: 0.9rem; color: #333;">Showing <strong>${start}–${end}</strong> of <strong>${total}</strong> verified products${filterTag}</span>
        ${clearBtn}
    `;
}

window.resetAllFilters = function() {
    state.selectedCategory = "all";
    state.searchQuery = "";
    state.inStockOnly = false;
    state.maxPriceFilter = null;
    state.currentPage = 1;
    if (dom.searchInput) dom.searchInput.value = "";
    if (dom.searchCategorySelect) dom.searchCategorySelect.value = "all";
    if (dom.filterPillsContainer) {
        dom.filterPillsContainer.querySelectorAll(".filter-btn").forEach(b => {
            b.classList.toggle("active", b.dataset.category === "all");
        });
    }
    switchCatalogView("shelves");
    renderCategoryShelves();
    applyFilters();
};

// -----------------------------------------------------------------------------
// Product Image Resolvers & Semantic Photo Library (Requirement 1 & Visuals)
// -----------------------------------------------------------------------------
const PRODUCT_IMAGE_RULES = [
    { keywords: ["bluetooth speaker", "speaker", "soundbar", "audio system", "boombox"], url: "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=500&auto=format&fit=crop&q=80", type: "speaker" },
    { keywords: ["wireless headphones", "noise cancelling headphones", "over-ear headphones", "headphones", "headset"], url: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=80", type: "headphones" },
    { keywords: ["bluetooth earbuds", "earbuds", "earphone", "airpods", "tws"], url: "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500&auto=format&fit=crop&q=80", type: "earbuds" },
    { keywords: ["smart watch", "smartwatch", "fitness band", "smart band"], url: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=80", type: "smartwatch" },
    { keywords: ["chronograph", "mesh watch", "analog watch", "watch"], url: "https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=500&auto=format&fit=crop&q=80", type: "watch" },
    { keywords: ["vertical mouse", "gaming mouse", "wireless mouse", "mouse pad", "mousepad", "mouse"], url: "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500&auto=format&fit=crop&q=80", type: "mouse" },
    { keywords: ["mechanical keyboard", "wireless keyboard", "keyboard", "keycap"], url: "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500&auto=format&fit=crop&q=80", type: "keyboard" },
    { keywords: ["webcam", "camera", "hd webcam"], url: "https://images.unsplash.com/photo-1588508065123-287b28e013da?w=500&auto=format&fit=crop&q=80", type: "webcam" },
    { keywords: ["power bank", "portable charger", "battery pack"], url: "https://images.unsplash.com/photo-1609592424079-0524bc1665a5?w=500&auto=format&fit=crop&q=80", type: "charger" },
    { keywords: ["usb-c charger", "fast charger", "charging pad", "usb hub", "charger", "adapter", "docking station"], url: "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=500&auto=format&fit=crop&q=80", type: "charger" },
    { keywords: ["laptop stand"], url: "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500&auto=format&fit=crop&q=80", type: "laptop" },
    { keywords: ["flagship 5g smartphone", "smartphone", "android phone", "phone", "mobile"], url: "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&auto=format&fit=crop&q=80", type: "phone" },
    { keywords: ["tablet", "ipad", "drawing tablet"], url: "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=500&auto=format&fit=crop&q=80", type: "tablet" },
    { keywords: ["gaming monitor", "4k uhd monitor", "monitor", "display"], url: "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500&auto=format&fit=crop&q=80", type: "monitor" },
    { keywords: ["laptop", "ultrabook", "macbook", "notebook"], url: "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&auto=format&fit=crop&q=80", type: "laptop" },
    { keywords: ["external ssd", "portable hard drive", "hard drive", "ssd", "nvme"], url: "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=500&auto=format&fit=crop&q=80", type: "storage" },
    { keywords: ["usb flash drive", "flash drive", "microsd", "memory card", "pen drive"], url: "https://images.unsplash.com/photo-1628191010210-a59de33e5941?w=500&auto=format&fit=crop&q=80", type: "storage" },
    { keywords: ["wi-fi router", "mesh wi-fi", "router", "extender", "ethernet switch", "access point", "networking"], url: "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=500&auto=format&fit=crop&q=80", type: "networking" },
    { keywords: ["smart led bulb", "strip light", "desk lamp", "lamp", "bulb", "light"], url: "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=500&auto=format&fit=crop&q=80", type: "lamp" },
    { keywords: ["smart plug", "universal remote", "smart home", "sensor", "gateway"], url: "https://images.unsplash.com/photo-1558002038-1055907df827?w=500&auto=format&fit=crop&q=80", type: "smarthome" },
    { keywords: ["bedsheet", "pillow", "blanket", "comforter", "quilt", "curtain"], url: "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=500&auto=format&fit=crop&q=80", type: "home" },
    { keywords: ["water bottle", "thermos flask", "flask", "tumbler", "bottle"], url: "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=500&auto=format&fit=crop&q=80", type: "bottle" },
    { keywords: ["coffee mug", "glass mug", "mug", "cup"], url: "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500&auto=format&fit=crop&q=80", type: "mug" },
    { keywords: ["air fryer", "electric kettle", "rice cooker", "cooker", "pan", "pot", "cookware"], url: "https://images.unsplash.com/photo-1584992236310-6edddc08acff?w=500&auto=format&fit=crop&q=80", type: "kitchen" },
    { keywords: ["mixer grinder", "blender", "grinder", "food processor"], url: "https://images.unsplash.com/photo-1570222094114-d054a817e56b?w=500&auto=format&fit=crop&q=80", type: "kitchen" },
    { keywords: ["laptop backpack", "waterproof travel backpack", "anti-theft hard shell backpack", "backpack", "bagpack"], url: "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&auto=format&fit=crop&q=80", type: "backpack" },
    { keywords: ["gym duffle bag", "messenger bag", "crossbody sling", "travel bag", "duffle", "bag"], url: "https://images.unsplash.com/photo-1546938576-6e6a64f317cc?w=500&auto=format&fit=crop&q=80", type: "backpack" },
    { keywords: ["leather bifold wallet", "card holder", "wallet", "purse"], url: "https://images.unsplash.com/photo-1627123424574-724758594e93?w=500&auto=format&fit=crop&q=80", type: "wallet" },
    { keywords: ["aviator sunglasses", "sunglasses", "shades", "glasses"], url: "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500&auto=format&fit=crop&q=80", type: "sunglasses" },
    { keywords: ["cotton tee", "t-shirt", "tee", "shirt", "casual shirt"], url: "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500&auto=format&fit=crop&q=80", type: "clothing" },
    { keywords: ["denim jeans", "jeans", "pants", "cargo pants", "trousers"], url: "https://images.unsplash.com/photo-1542272604-780c96856592?w=500&auto=format&fit=crop&q=80", type: "clothing" },
    { keywords: ["fleece jacket", "hoodie", "sweatshirt", "jacket"], url: "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=500&auto=format&fit=crop&q=80", type: "clothing" },
    { keywords: ["running shoes", "sports shoes", "walking shoes", "sneakers", "hiking shoes"], url: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&auto=format&fit=crop&q=80", type: "shoes" },
    { keywords: ["oxford shoes", "loafers", "formal shoes", "shoes"], url: "https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?w=500&auto=format&fit=crop&q=80", type: "shoes" },
    { keywords: ["sandals", "slippers", "flip flops"], url: "https://images.unsplash.com/photo-1603487742131-4160ec999306?w=500&auto=format&fit=crop&q=80", type: "shoes" },
    { keywords: ["executive chair", "office chair", "ergonomic recliner", "chair", "sofa", "stool"], url: "https://images.unsplash.com/photo-1580481077114-1e0586e58f00?w=500&auto=format&fit=crop&q=80", type: "chair" },
    { keywords: ["standing desk", "study table", "desk", "table"], url: "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=500&auto=format&fit=crop&q=80", type: "desk" },
    { keywords: ["bookshelf", "shoe rack", "wardrobe", "cabinet", "shelf"], url: "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=500&auto=format&fit=crop&q=80", type: "furniture" },
    { keywords: ["tpe exercise mat", "yoga mat", "mat"], url: "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=500&auto=format&fit=crop&q=80", type: "yogamat" },
    { keywords: ["dumbbells", "kettlebell", "weights", "push-up board", "exerciser"], url: "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=500&auto=format&fit=crop&q=80", type: "dumbbells" },
    { keywords: ["resistance bands", "speed rope", "skipping rope", "fitness"], url: "https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=500&auto=format&fit=crop&q=80", type: "fitness" },
    { keywords: ["cricket bat", "cricket ball", "cricket", "batting gloves"], url: "https://images.unsplash.com/photo-1531415074868-036b10f08a46?w=500&auto=format&fit=crop&q=80", type: "sports" },
    { keywords: ["football", "basketball", "volleyball", "ball"], url: "https://images.unsplash.com/photo-1552667466-07770ae110d0?w=500&auto=format&fit=crop&q=80", type: "sports" },
    { keywords: ["badminton racket", "shuttlecock", "badminton"], url: "https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?w=500&auto=format&fit=crop&q=80", type: "sports" },
    { keywords: ["face serum", "face wash", "serum", "cleaner", "lotion", "cream", "aloe vera"], url: "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop&q=80", type: "personalcare" },
    { keywords: ["shampoo", "conditioner", "hair oil", "castor hair"], url: "https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d?w=500&auto=format&fit=crop&q=80", type: "personalcare" },
    { keywords: ["hair straightener", "hair dryer", "electric trimmer", "trimmer", "straightener"], url: "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=500&auto=format&fit=crop&q=80", type: "personalcare" },
    { keywords: ["electric toothbrush", "toothbrush"], url: "https://images.unsplash.com/photo-1559591937-e1032b4bfa29?w=500&auto=format&fit=crop&q=80", type: "personalcare" },
    { keywords: ["spiral journal", "notebook", "diary", "journal"], url: "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500&auto=format&fit=crop&q=80", type: "stationery" },
    { keywords: ["ball pen", "gel pen", "pen set", "pencil", "pen"], url: "https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?w=500&auto=format&fit=crop&q=80", type: "stationery" },
    { keywords: ["calculator"], url: "https://images.unsplash.com/photo-1594980596870-8aa52a78d8cd?w=500&auto=format&fit=crop&q=80", type: "calculator" },
    { keywords: ["table fan", "standing fan", "purifier", "humidifier", "dehumidifier", "air cooler", "fan"], url: "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?w=500&auto=format&fit=crop&q=80", type: "appliance" }
];

const CATEGORY_FALLBACK_IMAGES = {
    "Electronics": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=80",
    "Accessories": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500&auto=format&fit=crop&q=80",
    "Mobiles": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&auto=format&fit=crop&q=80",
    "Computers": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&auto=format&fit=crop&q=80",
    "Storage": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=500&auto=format&fit=crop&q=80",
    "Networking": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=500&auto=format&fit=crop&q=80",
    "Home": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=500&auto=format&fit=crop&q=80",
    "Bags": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&auto=format&fit=crop&q=80",
    "Fashion": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=500&auto=format&fit=crop&q=80",
    "Clothing": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500&auto=format&fit=crop&q=80",
    "Footwear": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&auto=format&fit=crop&q=80",
    "Personal Care": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop&q=80",
    "Home & Kitchen": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=500&auto=format&fit=crop&q=80",
    "Furniture": "https://images.unsplash.com/photo-1580481077114-1e0586e58f00?w=500&auto=format&fit=crop&q=80",
    "Fitness": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=500&auto=format&fit=crop&q=80",
    "Sports": "https://images.unsplash.com/photo-1531415074868-036b10f08a46?w=500&auto=format&fit=crop&q=80",
    "Stationery": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500&auto=format&fit=crop&q=80",
    "Home Appliances": "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?w=500&auto=format&fit=crop&q=80"
};

function getProductImage(prod, isLarge = false) {
    if (!prod) return generateProductSvg({ category: "General", product_name: "SafeCart Product" }, isLarge);
    
    // Resolve local image path (/product_images/Pxxx.jpg)
    let u = (prod.image_url && typeof prod.image_url === "string" && prod.image_url.trim()) 
        ? prod.image_url.trim() 
        : (prod.image && typeof prod.image === "string" && prod.image.trim()) ? prod.image.trim() : "";

    const pid = prod.product_id || prod.productId;

    if (!u && pid && state.allProducts && state.allProducts.length) {
        const found = state.allProducts.find(p => String(p.product_id).toUpperCase() === String(pid).toUpperCase());
        if (found && found.image_url && typeof found.image_url === "string" && found.image_url.trim()) {
            u = found.image_url.trim();
        }
    }

    if (u) {
        // If opened directly from file system (file://)
        if (window.location.protocol === "file:" && u.startsWith("/")) {
            return u.replace(/^\//, "");
        }
        // If opened on another dev port (e.g. VS Code Live Server 5500), load from relative or backend
        if (window.location.port && window.location.port !== "8000" && u.startsWith("/")) {
            // Relative path resolves cleanly from amazon clone folder
            return u.replace(/^\//, "");
        }
        return u;
    }

    if (pid && /^P\d{3}$/i.test(pid)) {
        const cleanPid = String(pid).toUpperCase();
        if (window.location.protocol === "file:" || (window.location.port && window.location.port !== "8000")) {
            return `product_images/${cleanPid}.jpg`;
        }
        return `/product_images/${cleanPid}.jpg`;
    }

    // Default to clean deterministic SVG
    return generateProductSvg(prod, isLarge);
}

function handleProductImgError(imgElem, pid, isLarge = false) {
    if (!imgElem) return;
    imgElem.onerror = null;

    // First attempt: try FastAPI backend static mount if on alternate port or file protocol
    if (pid && !imgElem.src.includes(":8000/product_images/")) {
        imgElem.src = `http://127.0.0.1:8000/product_images/${pid}.jpg`;
        imgElem.onerror = () => {
            imgElem.onerror = null;
            const prod = (state.allProducts && state.allProducts.find(p => p.product_id === pid)) || {
                product_id: pid,
                category: "General",
                product_name: "SafeCart Verified Item"
            };
            imgElem.src = generateProductSvg(prod, isLarge);
        };
        return;
    }

    const prod = (state.allProducts && state.allProducts.find(p => p.product_id === pid)) || {
        product_id: pid,
        category: "General",
        product_name: "SafeCart Verified Item"
    };
    imgElem.src = generateProductSvg(prod, isLarge);
}
window.handleProductImgError = handleProductImgError;

function getProductTypeForSvg(prod) {
    const pName = String(prod.product_name || "").toLowerCase();
    for (const rule of PRODUCT_IMAGE_RULES) {
        if (rule.keywords.some(kw => pName.includes(kw))) {
            return rule.type;
        }
    }
    return "box";
}

function generateProductSvg(prod, isLarge = false) {
    const cat = String(prod.category || "General");
    const name = String(prod.product_name || "SafeCart Item");
    const type = getProductTypeForSvg(prod);
    const visual = CATEGORY_VISUALS[cat] || { color: "#232f3e", icon: "fa-box" };
    const baseColor = visual.color || "#ff9900";

    const width = isLarge ? 500 : 350;
    const height = isLarge ? 500 : 350;
    const cx = width / 2;
    const cy = height / 2 - 15;

    // Build vector illustration based on product type
    let itemIllustration = "";
    switch (type) {
        case "speaker":
            itemIllustration = `
                <!-- Bluetooth Speaker illustration -->
                <rect x="${cx - 55}" y="${cy - 70}" width="110" height="140" rx="28" fill="#2d3748" stroke="#1a202c" stroke-width="4"/>
                <circle cx="${cx}" cy="${cy - 20}" r="34" fill="#1a202c" stroke="${baseColor}" stroke-width="3"/>
                <circle cx="${cx}" cy="${cy - 20}" r="18" fill="#4a5568"/>
                <circle cx="${cx}" cy="${cy + 35}" r="22" fill="#1a202c"/>
                <circle cx="${cx - 24}" cy="${cy - 52}" r="4" fill="#cbd5e0"/>
                <circle cx="${cx}" cy="${cy - 52}" r="5" fill="#38a169"/>
                <circle cx="${cx + 24}" cy="${cy - 52}" r="4" fill="#cbd5e0"/>
                <!-- Sound waves -->
                <path d="M${cx + 65} ${cy - 40} Q${cx + 80} ${cy - 20} ${cx + 65} ${cy}" fill="none" stroke="${baseColor}" stroke-width="4" stroke-linecap="round"/>
                <path d="M${cx + 78} ${cy - 50} Q${cx + 98} ${cy - 20} ${cx + 78} ${cy + 10}" fill="none" stroke="${baseColor}" stroke-width="3" stroke-linecap="round" opacity="0.6"/>
            `;
            break;
        case "headphones":
            itemIllustration = `
                <!-- Headphones illustration -->
                <path d="M${cx - 65} ${cy} C${cx - 65} ${cy - 75}, ${cx + 65} ${cy - 75}, ${cx + 65} ${cy}" fill="none" stroke="#2d3748" stroke-width="12" stroke-linecap="round"/>
                <rect x="${cx - 78}" y="${cy - 15}" width="28" height="56" rx="14" fill="${baseColor}" stroke="#1a202c" stroke-width="3"/>
                <rect x="${cx + 50}" y="${cy - 15}" width="28" height="56" rx="14" fill="${baseColor}" stroke="#1a202c" stroke-width="3"/>
                <circle cx="${cx - 64}" cy="${cy + 13}" r="7" fill="#ffffff" opacity="0.4"/>
                <circle cx="${cx + 64}" cy="${cy + 13}" r="7" fill="#ffffff" opacity="0.4"/>
            `;
            break;
        case "smartwatch":
        case "watch":
            itemIllustration = `
                <!-- Smart Watch illustration -->
                <rect x="${cx - 22}" y="${cy - 85}" width="44" height="170" rx="8" fill="#4a5568"/>
                <rect x="${cx - 45}" y="${cy - 45}" width="90" height="90" rx="22" fill="#1a202c" stroke="${baseColor}" stroke-width="4"/>
                <rect x="${cx - 36}" y="${cy - 36}" width="72" height="72" rx="14" fill="#0f172a"/>
                <circle cx="${cx}" cy="${cy}" r="26" fill="none" stroke="${baseColor}" stroke-width="3" stroke-dasharray="120" stroke-dashoffset="30"/>
                <text x="${cx}" y="${cy + 5}" fill="#ffffff" font-family="sans-serif" font-size="16" font-weight="bold" text-anchor="middle">10:45</text>
                <circle cx="${cx + 46}" cy="${cy}" r="5" fill="#718096"/>
            `;
            break;
        case "laptop":
            itemIllustration = `
                <!-- Laptop illustration -->
                <rect x="${cx - 75}" y="${cy - 55}" width="150" height="95" rx="8" fill="#1e293b" stroke="#334155" stroke-width="3"/>
                <rect x="${cx - 67}" y="${cy - 47}" width="134" height="79" rx="4" fill="#0f172a"/>
                <polygon points="${cx - 95},${cy + 45} ${cx + 95},${cy + 45} ${cx + 85},${cy + 55} ${cx - 85},${cy + 55}" fill="#94a3b8"/>
                <rect x="${cx - 25}" y="${cy + 45}" width="50" height="4" fill="#cbd5e1" rx="2"/>
            `;
            break;
        case "phone":
            itemIllustration = `
                <!-- Phone illustration -->
                <rect x="${cx - 40}" y="${cy - 75}" width="80" height="150" rx="18" fill="#0f172a" stroke="#334155" stroke-width="4"/>
                <rect x="${cx - 34}" y="${cy - 68}" width="68" height="136" rx="12" fill="#1e293b"/>
                <circle cx="${cx}" cy="${cy - 60}" r="3" fill="#64748b"/>
                <rect x="${cx - 15}" y="${cy + 58}" width="30" height="3" rx="1.5" fill="#64748b"/>
            `;
            break;
        case "mouse":
            itemIllustration = `
                <!-- Mouse illustration -->
                <path d="M${cx} ${cy - 65} C${cx - 40} ${cy - 65}, ${cx - 45} ${cy + 20}, ${cx - 35} ${cy + 60} C${cx - 20} ${cy + 75}, ${cx + 20} ${cy + 75}, ${cx + 35} ${cy + 60} C${cx + 45} ${cy + 20}, ${cx + 40} ${cy - 65}, ${cx} ${cy - 65} Z" fill="#334155" stroke="#1e293b" stroke-width="3"/>
                <line x1="${cx}" y1="${cy - 65}" x2="${cx}" y2="${cy - 10}" stroke="#64748b" stroke-width="2"/>
                <rect x="${cx - 5}" y="${cy - 45}" width="10" height="22" rx="5" fill="${baseColor}"/>
            `;
            break;
        case "backpack":
            itemIllustration = `
                <!-- Backpack illustration -->
                <path d="M${cx} ${cy - 65} C${cx - 50} ${cy - 65}, ${cx - 55} ${cy + 30}, ${cx - 50} ${cy + 65} C${cx - 30} ${cy + 72}, ${cx + 30} ${cy + 72}, ${cx + 50} ${cy + 65} C${cx + 55} ${cy + 30}, ${cx + 50} ${cy - 65}, ${cx} ${cy - 65} Z" fill="#334155" stroke="#0f172a" stroke-width="3"/>
                <rect x="${cx - 35}" y="${cy - 5}" width="70" height="55" rx="8" fill="#475569" stroke="#1e293b" stroke-width="2"/>
                <line x1="${cx - 25}" y1="${cy - 5}" x2="${cx + 25}" y2="${cy - 5}" stroke="#cbd5e1" stroke-width="3"/>
                <path d="M${cx - 25} ${cy - 65} Q${cx} ${cy - 85} ${cx + 25} ${cy - 65}" fill="none" stroke="#64748b" stroke-width="6" stroke-linecap="round"/>
            `;
            break;
        case "shoes":
            itemIllustration = `
                <!-- Running shoe illustration -->
                <path d="M${cx - 75} ${cy + 20} Q${cx - 60} ${cy - 30} ${cx - 15} ${cy - 35} Q${cx + 20} ${cy - 15} ${cx + 55} ${cy + 5} Q${cx + 80} ${cy + 15} ${cx + 70} ${cy + 35} L${cx - 75} ${cy + 35} Z" fill="${baseColor}" stroke="#1e293b" stroke-width="3"/>
                <rect x="${cx - 78}" y="${cy + 35}" width="154" height="16" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
                <line x1="${cx - 25}" y1="${cy - 20}" x2="${cx - 5}" y2="${cy - 5}" stroke="#ffffff" stroke-width="3"/>
                <line x1="${cx - 18}" y1="${cy - 25}" x2="${cx + 2}" y2="${cy - 10}" stroke="#ffffff" stroke-width="3"/>
            `;
            break;
        default:
            itemIllustration = `
                <!-- Clean retail package box illustration -->
                <polygon points="${cx},${cy - 55} ${cx + 60},${cy - 25} ${cx},${cy + 5} ${cx - 60},${cy - 25}" fill="${baseColor}" opacity="0.9"/>
                <polygon points="${cx - 60},${cy - 25} ${cx},${cy + 5} ${cx},${cy + 65} ${cx - 60},${cy + 35}" fill="#2d3748"/>
                <polygon points="${cx},${cy + 5} ${cx + 60},${cy - 25} ${cx + 60},${cy + 35} ${cx},${cy + 65}" fill="#4a5568"/>
                <circle cx="${cx}" cy="${cy + 5}" r="8" fill="#ffd814"/>
            `;
            break;
    }

    const safeName = name.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    const safeCat = cat.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
        <defs>
            <linearGradient id="bg_grad_${type}" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#ffffff"/>
                <stop offset="100%" stop-color="#f1f5f9"/>
            </linearGradient>
            <filter id="soft_shadow" x="-10%" y="-10%" width="120%" height="120%">
                <feDropShadow dx="0" dy="6" stdDeviation="8" flood-opacity="0.12"/>
            </filter>
        </defs>
        <rect width="${width}" height="${height}" rx="12" fill="url(#bg_grad_${type})" stroke="#e2e8f0" stroke-width="1.5"/>
        
        <!-- Category Badge at Top Left (Never PID/Order ID) -->
        <rect x="16" y="16" width="110" height="24" rx="12" fill="${baseColor}"/>
        <text x="71" y="32" fill="#ffffff" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="11" font-weight="700" text-anchor="middle" letter-spacing="0.4">${safeCat.toUpperCase()}</text>
        
        <!-- SafeCart Verified Pill at Top Right -->
        <rect x="${width - 126}" y="16" width="110" height="24" rx="12" fill="#e6f4ea" stroke="#ceead6"/>
        <text x="${width - 71}" y="32" fill="#137333" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="10" font-weight="700" text-anchor="middle">✓ VERIFIED</text>
        
        <!-- Center Product Illustration (Depicting the actual object) -->
        <g filter="url(#soft_shadow)">
            ${itemIllustration}
        </g>
        
        <!-- Product Label at Bottom -->
        <text x="${cx}" y="${height - 24}" fill="#334155" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="${isLarge ? 15 : 13}" font-weight="700" text-anchor="middle">${safeName.length > 28 ? safeName.substring(0, 26) + '...' : safeName}</text>
    </svg>`;

    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

// -----------------------------------------------------------------------------
// Product Card Component (Reusable for Shelves & Grid)
// -----------------------------------------------------------------------------
function createProductCardHtml(prod) {
    const pid = prod.product_id;
    const inStock = prod.in_stock && Number(prod.quantity) > 0;
    const formattedPrice = Number(prod.price).toLocaleString("en-IN");
    const imgSrc = getProductImage(prod, false);
    
    // Deterministic pseudo-rating based on PID for realistic Amazon look
    const numId = parseInt(pid.replace(/\D/g, "") || "1", 10);
    const rating = (4.0 + (numId % 10) * 0.1).toFixed(1);
    const ratingCount = 45 + (numId * 13) % 450;

    return `
        <div class="product-card" data-pid="${pid}">
            <div class="product-card-top" onclick="openProductDetail('${pid}')">
                <div class="card-img-wrapper">
                    <img src="${imgSrc}" alt="${prod.product_name}" loading="lazy" onerror="handleProductImgError(this, '${pid}', false)">
                    <span class="card-category-badge">${prod.category}</span>
                </div>
                <h3 class="card-title" title="${prod.product_name}">${prod.product_name}</h3>
                <div class="card-rating">
                    <span><i class="fa-solid fa-star"></i> ${rating}</span>
                    <span class="rating-count">(${ratingCount})</span>
                </div>
                <div class="card-price-row">
                    <span class="card-price-currency">₹</span>
                    <span class="card-price">${formattedPrice}</span>
                </div>
                <div class="card-stock-status">
                    ${inStock 
                        ? `<span class="stock-in"><i class="fa-solid fa-check"></i> In Stock (${prod.quantity} available)</span>` 
                        : `<span class="stock-out"><i class="fa-solid fa-xmark"></i> Currently Out of Stock</span>`}
                </div>
            </div>

            <div class="card-actions">
                <button class="btn-add-cart" onclick="addToCart('${pid}', 1)" ${!inStock ? "disabled" : ""}>
                    <i class="fa-solid fa-cart-plus"></i> ${inStock ? "Add to Cart" : "Out of Stock"}
                </button>
                <button class="btn-quick-view" onclick="openProductDetail('${pid}')">
                    Quick Look
                </button>
            </div>
        </div>
    `;
}

// -----------------------------------------------------------------------------
// Category-Wise Shelves View (Requirement 1)
// -----------------------------------------------------------------------------
function renderCategoryShelves() {
    const container = dom.categoryShelvesContainer;
    if (!container) return;

    if (state.allProducts.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #565959;">
                <i class="fa-solid fa-spinner fa-spin fa-2x"></i>
                <p style="margin-top: 10px;">Loading category shelves from SafeCart database...</p>
            </div>
        `;
        return;
    }

    // Isolate categories: if a category is selected, render ONLY this category's shelf!
    let categoriesToRender = state.categories;
    if (state.selectedCategory && state.selectedCategory.toLowerCase() !== "all") {
        categoriesToRender = state.categories.filter(c => categoryMatches(c, state.selectedCategory));
    }

    if (categoriesToRender.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 50px 20px; background: white; border-radius: 8px; margin: 20px 0;">
                <p style="font-size: 1.1rem; color: #565959;">No shelves available for category "<strong>${state.selectedCategory}</strong>".</p>
                <button onclick="resetAllFilters()" style="margin-top: 12px; padding: 8px 20px; border-radius: 20px; background: #ffd814; border: 1px solid #fcd200; font-weight: 600; cursor: pointer;">
                    View All Categories
                </button>
            </div>
        `;
        return;
    }

    let shelvesHtml = "";
    categoriesToRender.forEach((cat, idx) => {
        const catProducts = state.allProducts.filter(p => categoryMatches(p.category, cat));
        if (catProducts.length === 0) return;

        const visual = CATEGORY_VISUALS[cat] || { icon: "fa-tag", color: "#3a7bd5" };
        const shelfId = `shelf-row-${idx}`;

        let cardsHtml = "";
        catProducts.forEach(prod => {
            cardsHtml += createProductCardHtml(prod);
        });

        shelvesHtml += `
            <section class="category-shelf-section" data-category="${cat}">
                <div class="shelf-header">
                    <div class="shelf-title-left">
                        <i class="fa-solid ${visual.icon} shelf-icon" style="color: ${visual.color};"></i>
                        <h3>${cat}</h3>
                        <span class="shelf-count-badge">${catProducts.length} verified products</span>
                    </div>
                    <button class="shelf-see-all-btn" onclick="selectCategory('${cat}')">
                        View only ${cat} grid <i class="fa-solid fa-chevron-right"></i>
                    </button>
                </div>
                <div class="shelf-carousel-wrapper">
                    <button class="shelf-scroll-btn prev" onclick="scrollShelf('${shelfId}', -360)" title="Scroll left">
                        <i class="fa-solid fa-chevron-left"></i>
                    </button>
                    <div class="shelf-cards-row" id="${shelfId}">
                        ${cardsHtml}
                    </div>
                    <button class="shelf-scroll-btn next" onclick="scrollShelf('${shelfId}', 360)" title="Scroll right">
                        <i class="fa-solid fa-chevron-right"></i>
                    </button>
                </div>
            </section>
        `;
    });

    container.innerHTML = shelvesHtml;
}

window.scrollShelf = function(shelfId, offset) {
    const shelf = document.getElementById(shelfId);
    if (shelf) {
        shelf.scrollBy({ left: offset, behavior: "smooth" });
    }
};

window.filterByShelfCategory = function(cat) {
    selectCategory(cat);
};

window.switchCatalogView = function(mode) {
    state.currentView = mode;
    const shelvesBtn = document.getElementById("view-mode-shelves-btn");
    const gridBtn = document.getElementById("view-mode-grid-btn");
    const shelvesContainer = document.getElementById("category-shelves-container");
    const gridWrapper = document.getElementById("grid-view-wrapper");

    if (mode === "shelves") {
        if (shelvesBtn) shelvesBtn.classList.add("active");
        if (gridBtn) gridBtn.classList.remove("active");
        if (shelvesContainer) shelvesContainer.style.display = "flex";
        if (gridWrapper) gridWrapper.style.display = "none";
        renderCategoryShelves();
    } else {
        if (shelvesBtn) shelvesBtn.classList.remove("active");
        if (gridBtn) gridBtn.classList.add("active");
        if (shelvesContainer) shelvesContainer.style.display = "none";
        if (gridWrapper) gridWrapper.style.display = "block";
        renderProducts();
        renderPagination();
        renderResultsMeta();
    }
};

// -----------------------------------------------------------------------------
// Products Grid View (Filtered & Paginated)
// -----------------------------------------------------------------------------
function renderProducts() {
    if (!dom.productsGrid) return;

    const start = (state.currentPage - 1) * state.pageSize;
    const pageItems = state.filteredProducts.slice(start, start + state.pageSize);

    if (pageItems.length === 0) {
        dom.productsGrid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; background: white; border-radius: 8px;">
                <i class="fa-solid fa-magnifying-glass fa-2x" style="color: #888c8c; margin-bottom: 12px;"></i>
                <h3 style="color: #0f1111; margin-bottom: 6px;">No products found in SafeCart database</h3>
                <p style="color: #565959; font-size: 0.9rem;">Try checking your spelling or clearing search filters to see all 500 products.</p>
                <button onclick="resetAllFilters()" style="margin-top: 15px; padding: 8px 20px; border-radius: 20px; background: #ffd814; border: 1px solid #fcd200; cursor: pointer; font-weight: 600;">View Category Shelves</button>
            </div>
        `;
        return;
    }

    let cardsHtml = "";
    pageItems.forEach(prod => {
        cardsHtml += createProductCardHtml(prod);
    });

    dom.productsGrid.innerHTML = cardsHtml;
}

// -----------------------------------------------------------------------------
// Database Synchronization Console (Requirement 8)
// -----------------------------------------------------------------------------
window.openDbSyncModal = function() {
    const modal = document.getElementById("db-sync-modal");
    if (!modal) return;
    modal.classList.add("active");

    const prodMetric = document.getElementById("metric-products-count");
    const catMetric = document.getElementById("metric-categories-count");
    const stockMetric = document.getElementById("metric-stock-count");

    if (prodMetric) prodMetric.textContent = state.allProducts.length;
    if (catMetric) catMetric.textContent = state.categories.length;
    if (stockMetric) {
        const inStockTotal = state.allProducts.filter(p => p.in_stock && Number(p.quantity) > 0).length;
        stockMetric.textContent = `${inStockTotal} in stock`;
    }
};

window.switchSyncTab = function(tab) {
    const stockBtn = document.getElementById("tab-stock-btn");
    const addBtn = document.getElementById("tab-add-btn");
    const stockPanel = document.getElementById("sync-panel-stock");
    const addPanel = document.getElementById("sync-panel-add");

    if (tab === "stock") {
        if (stockBtn) stockBtn.classList.add("active");
        if (addBtn) addBtn.classList.remove("active");
        if (stockPanel) stockPanel.style.display = "block";
        if (addPanel) addPanel.style.display = "none";
    } else {
        if (stockBtn) stockBtn.classList.remove("active");
        if (addBtn) addBtn.classList.add("active");
        if (stockPanel) stockPanel.style.display = "none";
        if (addPanel) addPanel.style.display = "block";
    }
};

window.handleStockUpdateSubmit = async function(e) {
    e.preventDefault();
    const pid = document.getElementById("sync-stock-pid").value.trim().toUpperCase();
    const qty = parseInt(document.getElementById("sync-stock-qty").value, 10);
    const resultMsg = document.getElementById("sync-result-msg");

    try {
        const res = await fetch(`${API_BASE}/products/${pid}/stock`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ quantity: qty })
        });
        const data = await res.json();
        if (res.ok) {
            showToast(`Stock updated for ${pid} to ${qty} in SafeCart database!`, "success");
            if (resultMsg) {
                resultMsg.style.display = "block";
                resultMsg.style.color = "#067d62";
                resultMsg.textContent = `✓ Success: ${data.message}`;
            }
            await fetchProducts();
        } else {
            throw new Error(data.message || "Failed to update stock");
        }
    } catch (err) {
        showToast(err.message, "error");
        if (resultMsg) {
            resultMsg.style.display = "block";
            resultMsg.style.color = "#b12704";
            resultMsg.textContent = `✗ Error: ${err.message}`;
        }
    }
};

window.handleAddProductSubmit = async function(e) {
    e.preventDefault();
    const name = document.getElementById("sync-new-name").value.trim();
    const category = document.getElementById("sync-new-cat").value.trim();
    const price = parseFloat(document.getElementById("sync-new-price").value);
    const stock = parseInt(document.getElementById("sync-new-stock").value, 10);
    const desc = document.getElementById("sync-new-desc").value.trim();
    const resultMsg = document.getElementById("sync-result-msg");

    try {
        const res = await fetch(`${API_BASE}/products`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                product_name: name,
                category: category,
                price: price,
                initial_stock: stock,
                description: desc
            })
        });
        const data = await res.json();
        if (res.ok) {
            showToast(`Product ${data.product.product_id} saved to SafeCart database!`, "success");
            if (resultMsg) {
                resultMsg.style.display = "block";
                resultMsg.style.color = "#067d62";
                resultMsg.textContent = `✓ Success: Added product ${data.product.product_id} to database!`;
            }
            await fetchCategories();
            await fetchProducts();
        } else {
            throw new Error(data.message || "Failed to add product");
        }
    } catch (err) {
        showToast(err.message, "error");
        if (resultMsg) {
            resultMsg.style.display = "block";
            resultMsg.style.color = "#b12704";
            resultMsg.textContent = `✗ Error: ${err.message}`;
        }
    }
};

// -----------------------------------------------------------------------------
// Pagination Rendering
// -----------------------------------------------------------------------------
function renderPagination() {
    if (!dom.paginationContainer) return;
    const totalPages = Math.ceil(state.filteredProducts.length / state.pageSize);

    if (totalPages <= 1) {
        dom.paginationContainer.innerHTML = "";
        return;
    }

    let html = `
        <button class="page-btn" onclick="changePage(${state.currentPage - 1})" ${state.currentPage === 1 ? "disabled" : ""}>
            <i class="fa-solid fa-chevron-left"></i> Previous
        </button>
    `;

    // Window of pages
    const cur = state.currentPage;
    const maxButtons = 7;
    let startPage = Math.max(1, cur - 3);
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);
    if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
    }

    if (startPage > 1) {
        html += `<button class="page-btn" onclick="changePage(1)">1</button>`;
        if (startPage > 2) html += `<span style="padding: 0 4px; color: #565959;">...</span>`;
    }

    for (let p = startPage; p <= endPage; p++) {
        html += `
            <button class="page-btn ${p === cur ? "active" : ""}" onclick="changePage(${p})">
                ${p}
            </button>
        `;
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += `<span style="padding: 0 4px; color: #565959;">...</span>`;
        html += `<button class="page-btn" onclick="changePage(${totalPages})">${totalPages}</button>`;
    }

    html += `
        <button class="page-btn" onclick="changePage(${state.currentPage + 1})" ${state.currentPage === totalPages ? "disabled" : ""}>
            Next <i class="fa-solid fa-chevron-right"></i>
        </button>
    `;

    dom.paginationContainer.innerHTML = html;
}

window.changePage = function(page) {
    const totalPages = Math.ceil(state.filteredProducts.length / state.pageSize);
    if (page < 1 || page > totalPages) return;
    state.currentPage = page;
    applyFilters();
    // Smooth scroll to catalog section
    const catElem = document.getElementById("catalog-section");
    if (catElem) {
        catElem.scrollIntoView({ behavior: "smooth", block: "start" });
    }
};

// -----------------------------------------------------------------------------
// Product Detail Modal
// -----------------------------------------------------------------------------
window.openProductDetail = async function(productId) {
    if (!dom.productModal || !dom.productModalBody) return;

    // Show loading state
    dom.productModal.classList.add("active");
    dom.productModalBody.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 60px;">
            <i class="fa-solid fa-spinner fa-spin fa-2x"></i>
            <p style="margin-top: 10px;">Verifying live price & inventory from SafeCart database...</p>
        </div>
    `;

    try {
        const res = await fetch(`${API_BASE}/products/${productId}`);
        if (!res.ok) throw new Error("Product not found");
        const data = await res.json();
        const prod = data.product;
        const inStock = prod.in_stock && Number(prod.quantity) > 0;
        const qty = Number(prod.quantity || 0);
        const largeImgSrc = getProductImage(prod, true);

        dom.productModalBody.innerHTML = `
            <div class="detail-img-box">
                <img src="${largeImgSrc}" alt="${prod.product_name}" onerror="handleProductImgError(this, '${prod.product_id}', true)">
                <div class="detail-badges-row">
                    <span class="detail-badge"><i class="fa-solid fa-shield-halved"></i> SafeCart Shield Verified</span>
                    <span class="detail-badge"><i class="fa-solid fa-rotate-left"></i> 7-Day Return Policy</span>
                    <span class="detail-badge"><i class="fa-solid fa-truck-fast"></i> Guaranteed Delivery</span>
                </div>
            </div>

            <div class="detail-info-box">
                <h2>${prod.product_name}</h2>
                <div class="detail-category-meta">
                    Brand / Category: <strong style="color: #007185;">${prod.category}</strong> | 
                    Product ID: <strong>${prod.product_id}</strong>
                </div>

                <div class="card-rating" style="margin-bottom: 12px;">
                    <i class="fa-solid fa-star"></i>
                    <i class="fa-solid fa-star"></i>
                    <i class="fa-solid fa-star"></i>
                    <i class="fa-solid fa-star"></i>
                    <i class="fa-solid fa-star-half-stroke"></i>
                    <span style="color: #0f1111; font-weight: 600; margin-left: 6px;">4.5 out of 5</span>
                </div>

                <div class="detail-price-box">
                    <span style="font-size: 0.85rem; color: #565959;">SafeCart Verified Price:</span><br>
                    <span class="price-tag">₹${Number(prod.price).toLocaleString("en-IN")}</span>
                    <span style="font-size: 0.8rem; color: #565959; margin-left: 6px;">Inclusive of all taxes</span>
                </div>

                <div style="margin-bottom: 14px;">
                    ${inStock 
                        ? `<p style="color: #067d62; font-weight: 700; font-size: 1.05rem;"><i class="fa-solid fa-circle-check"></i> In Stock (${qty} units available in inventory)</p>` 
                        : `<p style="color: #b12704; font-weight: 700; font-size: 1.05rem;"><i class="fa-solid fa-circle-xmark"></i> Currently unavailable in database</p>`}
                </div>

                <p class="detail-desc">
                    <strong>About this item:</strong><br>
                    ${prod.description || "High quality e-commerce item certified by SafeCart AI verification policies."}
                </p>

                <div class="detail-buy-box">
                    ${inStock ? `
                        <div class="qty-select-row">
                            <label for="detail-qty-select">Quantity:</label>
                            <select id="detail-qty-select">
                                ${Array.from({ length: Math.min(qty, 10) }, (_, i) => `<option value="${i+1}">${i+1}</option>`).join("")}
                            </select>
                        </div>
                        <div class="detail-action-buttons">
                            <button class="btn-add-cart" onclick="addCurrentModalToCart('${prod.product_id}')">
                                <i class="fa-solid fa-cart-plus"></i> Add to Cart
                            </button>
                            <button class="btn-buy-now" onclick="buyNowSingleProduct('${prod.product_id}')">
                                Buy Now
                            </button>
                            <button class="btn-ask-ai-item" onclick="askAiAboutProduct('${prod.product_id}', '${prod.product_name.replace(/'/g, "\\'")}')">
                                <i class="fa-solid fa-robot"></i> Ask SafeCart AI about this item
                            </button>
                        </div>
                    ` : `
                        <p style="color: #b12704; font-size: 0.9rem; margin-bottom: 12px;">This product is currently out of stock according to the SafeCart database.</p>
                        <button class="btn-ask-ai-item" onclick="askAiAboutProduct('${prod.product_id}', '${prod.product_name.replace(/'/g, "\\'")}')">
                            <i class="fa-solid fa-robot"></i> Ask SafeCart AI about restocking
                        </button>
                    `}
                </div>
            </div>
        `;
    } catch (e) {
        dom.productModalBody.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #b12704;">
                <p>Could not load details for product ID: ${productId}.</p>
                <button onclick="closeModal('product-detail-modal')" style="margin-top: 10px; padding: 6px 14px;">Close</button>
            </div>
        `;
    }
};

window.addCurrentModalToCart = function(productId) {
    const qtySelect = document.getElementById("detail-qty-select");
    const qty = qtySelect ? parseInt(qtySelect.value, 10) : 1;
    addToCart(productId, qty);
    closeModal("product-detail-modal");
};

window.buyNowSingleProduct = function(productId) {
    const qtySelect = document.getElementById("detail-qty-select");
    const qty = qtySelect ? parseInt(qtySelect.value, 10) : 1;
    addToCart(productId, qty);
    closeModal("product-detail-modal");
    openCheckout();
};

window.askAiAboutProduct = function(productId, productName) {
    closeModal("product-detail-modal");
    openChatWindow();
    setChatContext("product", productId, productName);
    sendCustomerChatMessage(`Tell me about this product and confirm its price and availability`, productId);
};

// -----------------------------------------------------------------------------
// Cart Management (Synchronized with Database)
// -----------------------------------------------------------------------------
window.addToCart = function(productId, quantity = 1) {
    const prod = state.allProducts.find(p => p.product_id === productId);
    if (!prod) {
        showToast("Product not found.", "error");
        return;
    }

    if (!prod.in_stock || Number(prod.quantity) <= 0) {
        showToast(`Cannot add to cart: ${prod.product_name} is out of stock in database.`, "error");
        return;
    }

    const availableStock = Number(prod.quantity);
    const existingIndex = state.cart.findIndex(item => item.product_id === productId);

    if (existingIndex >= 0) {
        const newQty = state.cart[existingIndex].quantity + quantity;
        if (newQty > availableStock) {
            showToast(`Cannot add more: only ${availableStock} units available in stock.`, "error");
            return;
        }
        state.cart[existingIndex].quantity = newQty;
    } else {
        if (quantity > availableStock) {
            showToast(`Cannot add: only ${availableStock} units available in stock.`, "error");
            return;
        }
        state.cart.push({
            product_id: productId,
            product_name: prod.product_name,
            price: Number(prod.price),
            category: prod.category,
            quantity: quantity,
            available_stock: availableStock
        });
    }

    saveCart();
    updateCartBadge();
    showToast(`Added "${prod.product_name}" to your cart!`, "success");
};

function saveCart() {
    localStorage.setItem("safecart_amazon_cart", JSON.stringify(state.cart));
}

function updateCartBadge() {
    const totalItems = state.cart.reduce((sum, item) => sum + item.quantity, 0);
    if (dom.navCartBadge) {
        dom.navCartBadge.textContent = totalItems;
    }
    if (dom.cartHeaderCount) {
        dom.cartHeaderCount.textContent = `(${totalItems} items)`;
    }
}

window.openCartDrawer = function() {
    renderCartDrawer();
    if (dom.cartDrawer && dom.cartDrawerOverlay) {
        dom.cartDrawer.classList.add("active");
        dom.cartDrawerOverlay.classList.add("active");
    }
};

window.closeCartDrawer = function() {
    if (dom.cartDrawer && dom.cartDrawerOverlay) {
        dom.cartDrawer.classList.remove("active");
        dom.cartDrawerOverlay.classList.remove("active");
    }
};

function renderCartDrawer() {
    if (!dom.cartItemsBody) return;

    if (state.cart.length === 0) {
        dom.cartItemsBody.innerHTML = `
            <div class="cart-empty-message">
                <i class="fa-solid fa-cart-shopping"></i>
                <h4 style="font-size: 1.1rem; color: #0f1111; margin-bottom: 6px;">Your SafeCart is empty</h4>
                <p style="font-size: 0.85rem;">Browse our 500 verified products and add items to your cart.</p>
            </div>
        `;
        if (dom.cartSubtotalText) dom.cartSubtotalText.textContent = "₹0";
        return;
    }

    let subtotal = 0;
    let html = "";

    state.cart.forEach(item => {
        const itemSub = item.price * item.quantity;
        subtotal += itemSub;
        const itemImg = getProductImage(item, false);

        html += `
            <div class="cart-item-row" data-pid="${item.product_id}">
                <div class="cart-item-thumb">
                    <img src="${itemImg}" alt="${item.product_name}" onerror="handleProductImgError(this, '${item.product_id}', false)">
                </div>
                <div class="cart-item-info">
                    <h4>${item.product_name}</h4>
                    <span class="item-id">Category: ${item.category} • SafeCart Verified</span>
                    <div class="item-price">₹${item.price.toLocaleString("en-IN")}</div>
                    <button class="cart-item-remove" onclick="removeCartItem('${item.product_id}')">
                        <i class="fa-solid fa-trash-can"></i> Delete
                    </button>
                </div>
                <div class="cart-stepper">
                    <button onclick="changeCartItemQty('${item.product_id}', -1)">-</button>
                    <span>${item.quantity}</span>
                    <button onclick="changeCartItemQty('${item.product_id}', 1)">+</button>
                </div>
            </div>
        `;
    });

    dom.cartItemsBody.innerHTML = html;
    if (dom.cartSubtotalText) {
        dom.cartSubtotalText.textContent = `₹${subtotal.toLocaleString("en-IN")}`;
    }
}

window.changeCartItemQty = function(productId, delta) {
    const item = state.cart.find(i => i.product_id === productId);
    if (!item) return;

    const newQty = item.quantity + delta;
    if (newQty <= 0) {
        removeCartItem(productId);
        return;
    }

    // Verify against product live stock
    const prod = state.allProducts.find(p => p.product_id === productId);
    const stock = prod ? Number(prod.quantity) : item.available_stock;
    if (newQty > stock) {
        showToast(`Cannot increase: maximum ${stock} units available in database.`, "error");
        return;
    }

    item.quantity = newQty;
    saveCart();
    updateCartBadge();
    renderCartDrawer();
};

window.removeCartItem = function(productId) {
    state.cart = state.cart.filter(i => i.product_id !== productId);
    saveCart();
    updateCartBadge();
    renderCartDrawer();
    showToast("Item removed from cart.", "success");
};

window.clearCart = function() {
    state.cart = [];
    saveCart();
    updateCartBadge();
    renderCartDrawer();
    showToast("Cart cleared.", "success");
};

// -----------------------------------------------------------------------------
// Checkout & Safe Order Placement
// -----------------------------------------------------------------------------
window.openCheckout = function() {
    if (state.cart.length === 0) {
        showToast("Your cart is empty. Add products before checkout.", "error");
        return;
    }
    closeCartDrawer();
    renderCheckoutModal();
    if (dom.checkoutModal) {
        dom.checkoutModal.classList.add("active");
    }
};

function renderCheckoutModal() {
    if (!dom.checkoutModalBody) return;
    const subtotal = state.cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

    let itemsTable = "";
    state.cart.forEach(item => {
        const itemImg = getProductImage(item, false);
        itemsTable += `
            <div style="display: flex; gap: 12px; align-items: center; padding: 10px 0; border-bottom: 1px solid #f0f0f0;">
                <img src="${itemImg}" alt="${item.product_name}" style="width: 48px; height: 48px; object-fit: contain; border-radius: 4px; border: 1px solid #eee; background: white;" onerror="handleProductImgError(this, '${item.product_id}', false)">
                <div style="flex: 1;">
                    <div style="font-weight: 600; font-size: 0.88rem; color: #0f1111;">${item.product_name}</div>
                    <div style="font-size: 0.78rem; color: #565959;">Category: ${item.category} • Qty: <strong>${item.quantity}</strong> × ₹${item.price.toLocaleString("en-IN")}</div>
                </div>
                <div style="font-weight: 700; color: #0f1111; font-size: 0.95rem;">
                    ₹${(item.price * item.quantity).toLocaleString("en-IN")}
                </div>
            </div>
        `;
    });

    dom.checkoutModalBody.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h2 style="margin: 0; font-size: 1.35rem; display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-lock" style="color: #067d62;"></i> SafeCart Secure Checkout
            </h2>
            <span class="db-status-pill"><i class="fa-solid fa-shield-halved" style="color: #067d62;"></i> 100% Purchase Protection</span>
        </div>

        <div class="checkout-guarantee-alert" style="display: flex; gap: 12px; align-items: center; background: #f0fdf4; border: 1px solid #bbf7d0; padding: 10px 14px; border-radius: 6px; margin-bottom: 14px;">
            <i class="fa-solid fa-shield-halved" style="font-size: 1.3rem; color: #16a34a;"></i>
            <div>
                <strong style="color: #15803d; font-size: 0.9rem;">SafeCart Verified Checkout</strong>
                <p style="margin: 2px 0 0; font-size: 0.82rem; color: #374151; line-height: 1.35;">
                    SafeCart Safe Shopping Guarantee. Real-time live inventory verified directly against database.
                </p>
            </div>
        </div>
        
        <div class="checkout-step">
            <h3><i class="fa-solid fa-location-dot" style="color: #ff9900;"></i> 1. Delivery & Customer Details</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 10px;">
                <div class="checkout-input-group">
                    <label>Recipient Full Name</label>
                    <input type="text" id="checkout-name-input" value="${state.user.name}" placeholder="Full Name" required>
                </div>
                <div class="checkout-input-group">
                    <label>Mobile Number</label>
                    <input type="tel" id="checkout-phone-input" value="+91 98765 43210" placeholder="+91 98765 43210">
                </div>
            </div>
            <div class="checkout-input-group">
                <label>Shipping Address (India)</label>
                <textarea id="checkout-address-input" rows="2" placeholder="Street, Building, Area" required>${state.user.address}</textarea>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px;">
                <div class="checkout-input-group">
                    <label>City & State</label>
                    <input type="text" id="checkout-city-input" value="Mumbai, Maharashtra" placeholder="City, State">
                </div>
                <div class="checkout-input-group">
                    <label>PIN Code</label>
                    <input type="text" id="checkout-pincode-input" value="400020" placeholder="400020">
                </div>
            </div>
        </div>

        <div class="checkout-step">
            <h3><i class="fa-solid fa-credit-card" style="color: #ff9900;"></i> 2. Payment Method</h3>
            <div class="checkout-payment-options">
                <label class="payment-option-card selected">
                    <input type="radio" name="paymethod" value="Instant Online Pay" checked>
                    <div style="flex: 1;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong>Instant Online Pay (Card / NetBanking)</strong>
                            <span style="font-size: 0.72rem; background: #e6f4ea; color: #137333; padding: 2px 7px; border-radius: 4px; font-weight: 700;">Recommended</span>
                        </div>
                        <span style="font-size: 0.78rem; color: #565959;">Instant electronic order clearance with zero friction.</span>
                    </div>
                </label>
                <label class="payment-option-card">
                    <input type="radio" name="paymethod" value="Cash on Delivery">
                    <div style="flex: 1;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong>Cash on Delivery (Pay on Delivery)</strong>
                            <span style="font-size: 0.72rem; background: #f0f2f2; color: #0f1111; padding: 2px 7px; border-radius: 4px; font-weight: 600;">Available</span>
                        </div>
                        <span style="font-size: 0.78rem; color: #565959;">Pay via Cash/UPI upon doorstep arrival.</span>
                    </div>
                </label>
                <label class="payment-option-card">
                    <input type="radio" name="paymethod" value="UPI / NetBanking">
                    <div style="flex: 1;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong>UPI / NetBanking</strong>
                            <span style="font-size: 0.72rem; background: #e0f2fe; color: #0369a1; padding: 2px 7px; border-radius: 4px; font-weight: 600;">Fast UPI</span>
                        </div>
                        <span style="font-size: 0.78rem; color: #565959;">Instant payment via Google Pay, PhonePe, Paytm, or BHIM.</span>
                    </div>
                </label>
            </div>
        </div>

        <div class="checkout-step">
            <h3><i class="fa-solid fa-receipt" style="color: #ff9900;"></i> 3. Order Items & Price Summary</h3>
            <div style="max-height: 220px; overflow-y: auto; margin-bottom: 12px;">
                ${itemsTable}
            </div>
            <table class="checkout-summary-table">
                <tr>
                    <td>Items Total (${state.cart.reduce((s, i) => s + i.quantity, 0)} items):</td>
                    <td style="text-align: right; font-weight: 600;">₹${subtotal.toLocaleString("en-IN")}</td>
                </tr>
                <tr>
                    <td>SafeCart Prime Delivery:</td>
                    <td style="text-align: right; color: #067d62; font-weight: bold;">FREE</td>
                </tr>
                <tr class="total-row">
                    <td>Total Amount:</td>
                    <td style="text-align: right; color: #b12704; font-size: 1.15rem;">₹${subtotal.toLocaleString("en-IN")}</td>
                </tr>
            </table>
            <p style="font-size: 0.78rem; color: #565959; margin-top: 8px;">
                <i class="fa-solid fa-shield-check" style="color: #067d62;"></i> Protected by SafeCart AI Auditor. Inventory safely decremented in database.
            </p>
        </div>

        <div style="display: flex; gap: 12px; margin-top: 20px;">
            <button class="btn-proceed-checkout" id="btn-place-order" onclick="submitCheckoutOrder()" style="flex: 1;">
                Place Order (₹${subtotal.toLocaleString("en-IN")})
            </button>
            <button onclick="closeModal('checkout-modal')" style="padding: 10px 18px; border: 1px solid #d5d9d9; border-radius: 20px; background: white; cursor: pointer;">
                Cancel
            </button>
        </div>
    `;
}

window.submitCheckoutOrder = async function() {
    const btn = document.getElementById("btn-place-order");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Placing Order & Updating SafeCart DB...`;
    }

    const nameInput = document.getElementById("checkout-name-input");
    const phoneInput = document.getElementById("checkout-phone-input");
    const addrInput = document.getElementById("checkout-address-input");
    const cityInput = document.getElementById("checkout-city-input");
    const pinInput = document.getElementById("checkout-pincode-input");
    const payRadio = document.querySelector('input[name="paymethod"]:checked');

    const customerName = nameInput ? nameInput.value.trim() : state.user.name;
    const customerPhone = phoneInput ? phoneInput.value.trim() : "+91 98765 43210";
    const streetAddr = addrInput ? addrInput.value.trim() : state.user.address;
    const cityState = cityInput ? cityInput.value.trim() : "";
    const pincode = pinInput ? pinInput.value.trim() : "";
    const fullAddress = [streetAddr, cityState, pincode ? `PIN: ${pincode}` : ""].filter(Boolean).join(", ");
    const paymentMethod = payRadio ? payRadio.value : "Instant Online Pay";

    // Update user display
    state.user.name = customerName;
    state.user.address = streetAddr;
    localStorage.setItem("safecart_amazon_user", JSON.stringify(state.user));
    updateUserDisplay();

    try {
        const payload = {
            items: state.cart.map(item => ({
                product_id: item.product_id,
                quantity: item.quantity
            })),
            customer_name: customerName,
            customer_email: state.user.email,
            customer_phone: customerPhone,
            shipping_address: fullAddress,
            payment_method: paymentMethod,
            is_demo: true
        };

        const res = await fetch(`${API_BASE}/checkout`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.message || "Failed to process order.");
        }

        // Successfully placed order in database
        const createdOrders = data.orders || [];
        const orderIds = createdOrders.map(o => o.order_id).join(", ");
        const firstOrder = createdOrders[0] || {};
        const orderedItems = [...state.cart];

        // Refresh live products immediately to reflect decremented inventory in database
        await fetchProducts();

        // Clear shopping cart
        state.cart = [];
        saveCart();
        updateCartBadge();

        // Build item receipt rows
        let receiptItemsHtml = "";
        orderedItems.forEach(item => {
            const itemImg = getProductImage(item, false);
            receiptItemsHtml += `
                <div style="display: flex; gap: 10px; align-items: center; padding: 6px 0; border-bottom: 1px solid #eee;">
                    <img src="${itemImg}" alt="${item.product_name}" style="width: 40px; height: 40px; object-fit: contain; border-radius: 4px; background: white; border: 1px solid #ddd;" onerror="handleProductImgError(this, '${item.product_id}', false)">
                    <div style="flex: 1; text-align: left;">
                        <div style="font-size: 0.82rem; font-weight: 600; color: #0f1111;">${item.product_name}</div>
                        <div style="font-size: 0.74rem; color: #565959;">Qty: ${item.quantity} • ₹${item.price.toLocaleString("en-IN")}</div>
                    </div>
                    <div style="font-size: 0.85rem; font-weight: 700;">
                        ₹${(item.price * item.quantity).toLocaleString("en-IN")}
                    </div>
                </div>
            `;
        });

        // Show Enhanced Order Confirmation Screen
        dom.checkoutModalBody.innerHTML = `
            <div style="text-align: center; padding: 20px 10px;">
                <div style="width: 64px; height: 64px; background: #e6f4ea; color: #137333; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2rem; margin: 0 auto 12px;">
                    <i class="fa-solid fa-check"></i>
                </div>
                <h2 style="justify-content: center; color: #067d62; font-size: 1.4rem; margin-bottom: 4px;">Order Placed Successfully!</h2>
                <div style="display: inline-block; background: #e6f4ea; color: #137333; font-size: 0.8rem; font-weight: 700; padding: 4px 12px; border-radius: 12px; margin-bottom: 12px; border: 1px solid #ceead6;">
                    <i class="fa-solid fa-circle-check"></i> Payment Confirmed • Verified
                </div>
                <p style="font-size: 0.95rem; color: #0f1111; margin: 4px 0 14px;">
                    Thank you, <strong>${customerName}</strong>. SafeCart database has permanently recorded your order.
                </p>

                <!-- Order Receipt Card -->
                <div style="background: #f8f9fa; border: 1px solid #e7e7e7; border-radius: 8px; padding: 16px; max-width: 500px; margin: 0 auto 18px; text-align: left; font-size: 0.85rem;">
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #e0e0e0; padding-bottom: 8px; margin-bottom: 10px;">
                        <div>
                            <span style="color: #565959; font-size: 0.78rem;">Generated Order ID(s):</span><br>
                            <span style="color: #b12704; font-weight: bold; font-size: 1.05rem;">${orderIds}</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="color: #565959; font-size: 0.78rem;">Delivery Guaranteed By:</span><br>
                            <span style="color: #067d62; font-weight: bold; font-size: 0.95rem;">${firstOrder.delivery_date || "Within 4 business days"}</span>
                        </div>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <strong>Delivering to:</strong> ${fullAddress}
                    </div>
                    <div style="margin-bottom: 10px;">
                        <strong>Payment:</strong> ${paymentMethod}
                    </div>
                    <div style="margin-bottom: 10px;">
                        <strong>Database Update:</strong> <span style="color: #067d62; font-weight: 600;">✓ Inventory safely decremented in inventory.csv</span>
                    </div>
                    <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #e0e0e0;">
                        <strong style="display: block; margin-bottom: 6px;">Ordered Items:</strong>
                        ${receiptItemsHtml}
                    </div>
                </div>

                <!-- Action Buttons: Track Order, AI Chatbot, Orders list -->
                <div style="display: flex; gap: 10px; justify-content: center; margin-top: 20px; flex-wrap: wrap;">
                    <button onclick="closeModal('checkout-modal'); openOrderTracking('${firstOrder.order_id}');" style="background: #ffd814; border: 1px solid #fcd200; border-radius: 20px; padding: 11px 22px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 8px;">
                        <i class="fa-solid fa-map-location-dot"></i> Track Order (Visual Timeline)
                    </button>
                    <button onclick="closeModal('checkout-modal'); trackOrderWithAi('${firstOrder.order_id}');" style="background: #232f3e; color: white; border: none; border-radius: 20px; padding: 11px 22px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px;">
                        <i class="fa-solid fa-robot" style="color: #febd69;"></i> Track with SafeCart AI
                    </button>
                    <button onclick="closeModal('checkout-modal'); openOrdersModal();" style="background: #f0f2f2; border: 1px solid #d5d9d9; border-radius: 20px; padding: 11px 18px; cursor: pointer; font-weight: 600;">
                        <i class="fa-solid fa-box"></i> View All Orders
                    </button>
                    <button onclick="closeModal('checkout-modal');" style="background: white; border: 1px solid #d5d9d9; border-radius: 20px; padding: 11px 18px; cursor: pointer;">
                        Continue Shopping
                    </button>
                </div>
            </div>
        `;
        showToast(`Order ${orderIds} confirmed & saved in SafeCart database!`, "success");

    } catch (err) {
        console.error("Checkout failure:", err);
        showToast(err.message || "Checkout failed.", "error");
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `Place Order`;
        }
    }
};

// -----------------------------------------------------------------------------
// Real-Time Visual Order Tracking Modal (Requirement 6)
// -----------------------------------------------------------------------------
window.openOrderTracking = async function(orderId) {
    const modal = document.getElementById("order-tracking-modal");
    const body = document.getElementById("tracking-modal-body");
    if (!modal || !body) return;

    modal.classList.add("active");
    body.innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <i class="fa-solid fa-spinner fa-spin fa-2x"></i>
            <p style="margin-top: 12px; color: #565959;">Fetching live tracking details for order ${orderId} from SafeCart database...</p>
        </div>
    `;

    try {
        const res = await fetch(`${API_BASE}/orders/${orderId}`);
        if (!res.ok) throw new Error("Order not found");
        const data = await res.json();
        const order = data.order;
        const prod = state.allProducts.find(p => p.product_id === order.product_id) || {
            product_id: order.product_id,
            product_name: order.product_name,
            category: order.category || "General",
            price: order.price
        };
        const prodImg = getProductImage(prod, false);

        // Stages: 1. Order Placed, 2. Packed, 3. In Transit, 4. Out for Delivery, 5. Delivered
        const isDelivered = String(order.status || "").toLowerCase() === "delivered";
        const progressWidth = isDelivered ? 100 : 58;

        body.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e7e7e7; padding-bottom: 14px; margin-bottom: 16px;">
                <div>
                    <span class="tracking-header-badge"><i class="fa-solid fa-circle-check"></i> SafeCart Express Tracking</span>
                    <h2 style="font-size: 1.3rem; margin: 4px 0; color: #0f1111;">Tracking Order: ${order.order_id}</h2>
                    <span style="font-size: 0.82rem; color: #565959;">Placed on: ${order.order_date || "Recent"} • Single Source of Truth Verified</span>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 0.78rem; color: #565959; display: block;">Estimated Delivery</span>
                    <strong style="color: #067d62; font-size: 1.05rem;">${order.delivery_date || "Within 4 business days"}</strong>
                </div>
            </div>

            <!-- Product Card Preview with Real Image -->
            <div style="display: flex; gap: 14px; align-items: center; background: #fdfdfd; border: 1px solid #e7e7e7; border-radius: 8px; padding: 12px; margin-bottom: 20px;">
                <img src="${prodImg}" alt="${order.product_name}" style="width: 65px; height: 65px; object-fit: contain; border-radius: 6px; border: 1px solid #eee; background: white;" onerror="handleProductImgError(this, '${order.product_id}', false)">
                <div style="flex: 1;">
                    <h4 style="font-size: 0.95rem; margin-bottom: 3px; color: #0f1111;">${order.product_name}</h4>
                    <span style="font-size: 0.78rem; color: #565959;">Category: <strong>${prod.category || "General"}</strong> • Verified Price: <strong>₹${Number(order.price || 0).toLocaleString("en-IN")}</strong></span>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 0.78rem; background: #e8f0fe; color: #1a73e8; padding: 3px 8px; border-radius: 4px; font-weight: 600;">SafeCart Prime</span>
                </div>
            </div>

            <!-- 5-Stage Visual Stepper Timeline -->
            <div class="tracking-stepper-container">
                <div class="tracking-progress-bar-bg">
                    <div class="tracking-progress-bar-fill" style="width: ${progressWidth}%;"></div>
                </div>
                <div class="tracking-steps">
                    <div class="tracking-step-item completed">
                        <div class="tracking-step-node"><i class="fa-solid fa-receipt"></i></div>
                        <span class="tracking-step-label">Order Placed</span>
                    </div>
                    <div class="tracking-step-item completed">
                        <div class="tracking-step-node"><i class="fa-solid fa-boxes-packing"></i></div>
                        <span class="tracking-step-label">Dispatched</span>
                    </div>
                    <div class="tracking-step-item active">
                        <div class="tracking-step-node"><i class="fa-solid fa-truck-fast"></i></div>
                        <span class="tracking-step-label">In Transit</span>
                    </div>
                    <div class="tracking-step-item">
                        <div class="tracking-step-node"><i class="fa-solid fa-house-chimney"></i></div>
                        <span class="tracking-step-label">Out for Delivery</span>
                    </div>
                    <div class="tracking-step-item ${isDelivered ? 'completed' : ''}">
                        <div class="tracking-step-node"><i class="fa-solid fa-circle-check"></i></div>
                        <span class="tracking-step-label">Delivered</span>
                    </div>
                </div>
            </div>

            <!-- Logistics Details Grid -->
            <div class="tracking-card-details">
                <div style="font-size: 0.88rem; font-weight: 700; color: #0f1111; margin-bottom: 6px;">
                    <i class="fa-solid fa-location-crosshairs" style="color: #ff9900;"></i> Live Transit Logistics
                </div>
                <p style="font-size: 0.82rem; color: #333; line-height: 1.4; margin-bottom: 10px;">
                    Package is currently moving through the SafeCart National Logistics Hub. On schedule for arrival by <strong>${order.delivery_date || "scheduled date"}</strong>.
                </p>
                <div class="tracking-logistics-grid">
                    <div>
                        <span style="color: #565959; display: block;">Carrier:</span>
                        <strong>SafeCart Express Prime</strong>
                    </div>
                    <div>
                        <span style="color: #565959; display: block;">Tracking Number:</span>
                        <strong>SFCT-${order.order_id}-IN</strong>
                    </div>
                    <div>
                        <span style="color: #565959; display: block;">Shipping Address:</span>
                        <strong title="${state.user.address}">${state.user.address.length > 32 ? state.user.address.substring(0, 30) + '...' : state.user.address}</strong>
                    </div>
                    <div>
                        <span style="color: #565959; display: block;">Return Eligibility:</span>
                        <strong style="color: #067d62;">7-Day Refund Protected</strong>
                    </div>
                </div>
            </div>

            <!-- Interactive Actions with Chatbot -->
            <div style="display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap;">
                <button onclick="closeModal('order-tracking-modal'); trackOrderWithAi('${order.order_id}');" style="flex: 1; min-width: 200px; background: #232f3e; color: white; border: none; border-radius: 20px; padding: 10px 16px; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <i class="fa-solid fa-robot" style="color: #febd69;"></i> Ask SafeCart AI Where Is My Order
                </button>
                <button onclick="closeModal('order-tracking-modal'); checkRefundWithAi('${order.order_id}');" style="background: #ffd814; border: 1px solid #fcd200; border-radius: 20px; padding: 10px 18px; font-weight: 600; cursor: pointer;">
                    <i class="fa-solid fa-rotate-left"></i> Check Refund Policy
                </button>
                <button onclick="closeModal('order-tracking-modal');" style="background: white; border: 1px solid #d5d9d9; border-radius: 20px; padding: 10px 16px; cursor: pointer;">
                    Close
                </button>
            </div>
        `;
    } catch (e) {
        body.innerHTML = `
            <div style="text-align: center; padding: 30px; color: #b12704;">
                <p>Could not load tracking details for order: ${orderId}</p>
                <button onclick="closeModal('order-tracking-modal')" style="margin-top: 10px; padding: 6px 14px;">Close</button>
            </div>
        `;
    }
};

window.openDemoInfoModal = function() {
    // Demo modal removed
};

window.trackOrderWithAi = function(orderId) {
    openChatWindow();
    setChatContext("order", null, null, orderId);
    sendCustomerChatMessage(`When will my order arrive?`, null, orderId);
};

// -----------------------------------------------------------------------------
// Returns & Orders Modal (SafeCart Database Integration)
// -----------------------------------------------------------------------------
window.openOrdersModal = async function() {
    if (!dom.ordersModal || !dom.ordersModalBody) return;
    dom.ordersModal.classList.add("active");

    dom.ordersModalBody.innerHTML = `
        <h2><i class="fa-solid fa-box-open" style="color: #ff9900;"></i> Your Orders (SafeCart Database)</h2>
        <div class="orders-search-bar">
            <input type="text" id="order-lookup-input" placeholder="Search by Order ID (e.g. O001, O002)...">
            <button onclick="lookupSpecificOrder()" style="padding: 8px 16px; border-radius: 4px; background: #ffd814; border: 1px solid #fcd200; cursor: pointer; font-weight: 600;">Search</button>
        </div>
        <div class="orders-list" id="orders-list-container">
            <div style="text-align: center; padding: 30px;"><i class="fa-solid fa-spinner fa-spin fa-2x"></i><p style="margin-top: 8px;">Loading orders from database (orders.csv)...</p></div>
        </div>
    `;

    try {
        const res = await fetch(`${API_BASE}/orders?limit=30`);
        if (!res.ok) throw new Error("Could not load orders");
        const data = await res.json();
        renderOrdersList(data.orders || []);
    } catch (e) {
        const listCont = document.getElementById("orders-list-container");
        if (listCont) {
            listCont.innerHTML = `<p style="color: #b12704; text-align: center;">Could not load orders from SafeCart backend.</p>`;
        }
    }
};

function renderOrdersList(orders) {
    const listCont = document.getElementById("orders-list-container");
    if (!listCont) return;

    if (!orders.length) {
        listCont.innerHTML = `<p style="text-align: center; color: #565959; padding: 20px;">No orders found.</p>`;
        return;
    }

    let html = "";
    // Display in reverse chronological order (newest first)
    const reversed = [...orders].reverse();

    reversed.forEach(order => {
        const isRefundable = String(order.refundable || "").toLowerCase() === "yes";
        const isRefunded = String(order.refunded || "").toLowerCase() === "yes";
        const prod = state.allProducts.find(p => p.product_id === order.product_id) || {
            product_id: order.product_id,
            product_name: order.product_name,
            category: order.category || "General",
            price: order.price
        };
        const orderImg = getProductImage(prod, false);

        html += `
            <div class="order-card">
                <div class="order-header-line">
                    <div>
                        <span class="order-id-tag">${order.order_id}</span>
                        <span style="margin-left: 8px; color: #565959;">Placed: ${order.order_date || "Recent"}</span>
                    </div>
                    <div>
                        <span style="font-size: 0.82rem; font-weight: 600; color: #067d62;">Delivery: ${order.delivery_date || "Scheduled"}</span>
                    </div>
                </div>

                <div style="display: flex; gap: 14px; align-items: center; margin: 10px 0;">
                    <img src="${orderImg}" alt="${order.product_name}" style="width: 58px; height: 58px; object-fit: contain; border-radius: 6px; border: 1px solid #e7e7e7; background: #fff;" onerror="handleProductImgError(this, '${order.product_id}', false)">
                    <div style="flex: 1;">
                        <h4 style="font-size: 0.95rem; color: #0f1111; margin-bottom: 3px;">${order.product_name || "SafeCart Catalog Item"}</h4>
                        <span style="font-size: 0.78rem; color: #565959;">Category: <strong>${prod.category || "General"}</strong> • Verified Price: <strong>₹${Number(order.price || 0).toLocaleString("en-IN")}</strong></span>
                    </div>
                    <div style="text-align: right;">
                        <span class="order-status-badge" style="display: inline-block; background: #e6f4ea; color: #137333; font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 4px;"><i class="fa-solid fa-circle-check"></i> Confirmed</span>
                    </div>
                </div>

                <div style="font-size: 0.8rem; display: flex; gap: 15px; color: #565959; margin-bottom: 10px;">
                    <span>Refund Policy: <strong>${isRefundable ? "Eligible (7 Days)" : "Non-refundable"}</strong></span>
                    <span>Status: <strong style="color: #067d62;">${isRefunded ? "Refunded" : "Active & In Transit"}</strong></span>
                </div>

                <div class="order-actions-row">
                    <button class="btn-order-action" style="background: #ffd814; border-color: #fcd200; font-weight: 600;" onclick="closeModal('orders-modal'); openOrderTracking('${order.order_id}')">
                        <i class="fa-solid fa-map-location-dot"></i> Track Order (Timeline)
                    </button>
                    <button class="btn-order-action" onclick="closeModal('orders-modal'); trackOrderWithAi('${order.order_id}')">
                        <i class="fa-solid fa-robot"></i> Track Delivery with AI
                    </button>
                    <button class="btn-order-action" onclick="closeModal('orders-modal'); checkRefundWithAi('${order.order_id}')">
                        <i class="fa-solid fa-rotate-left"></i> Check Refund with AI
                    </button>
                    <button class="btn-order-action" onclick="closeModal('orders-modal'); fileComplaintWithAi('${order.order_id}')">
                        <i class="fa-solid fa-comment-dots"></i> Issue / Help
                    </button>
                </div>
            </div>
        `;
    });

    listCont.innerHTML = html;
}

window.lookupSpecificOrder = async function() {
    const input = document.getElementById("order-lookup-input");
    const oid = input ? input.value.trim().toUpperCase() : "";
    if (!oid) {
        openOrdersModal();
        return;
    }

    const listCont = document.getElementById("orders-list-container");
    if (listCont) {
        listCont.innerHTML = `<div style="text-align: center; padding: 20px;"><i class="fa-solid fa-spinner fa-spin"></i> Searching order ${oid}...</div>`;
    }

    try {
        const res = await fetch(`${API_BASE}/orders/${oid}`);
        if (!res.ok) {
            listCont.innerHTML = `<p style="text-align: center; color: #b12704; padding: 20px;">Order <strong>${oid}</strong> not found in SafeCart database.</p>`;
            return;
        }
        const data = await res.json();
        renderOrdersList([data.order]);
    } catch (e) {
        listCont.innerHTML = `<p style="text-align: center; color: #b12704; padding: 20px;">Error searching order: ${e.message}</p>`;
    }
};

window.checkRefundWithAi = function(orderId) {
    openChatWindow();
    setChatContext("order", null, null, orderId);
    sendCustomerChatMessage(`Can I get a refund for order ${orderId}?`, null, orderId);
};

window.fileComplaintWithAi = function(orderId) {
    openChatWindow();
    setChatContext("order", null, null, orderId);
    sendCustomerChatMessage(`I have an issue with order ${orderId}`, null, orderId);
};

// -----------------------------------------------------------------------------
// User Authentication & Profile
// -----------------------------------------------------------------------------
window.openAuthModal = function() {
    if (!dom.authModal) return;
    dom.authModal.classList.add("active");
};

function updateUserDisplay() {
    if (dom.navUserGreeting) {
        dom.navUserGreeting.textContent = `Hello, ${state.user.name.split(" ")[0]}`;
    }
    if (dom.navAddressText) {
        dom.navAddressText.textContent = state.user.address.split(",").slice(-2).join(",").trim() || "India";
    }
}

window.switchUserAccount = function(userIndex) {
    const defaultAccounts = [
        { user_id: "U005", name: "Amazon Customer", email: "customer@amazon.in", address: "202 Marine Drive, Mumbai, India" },
        { user_id: "U001", name: "Bhushan Fulari", email: "bhushan@safecart.com", address: "123 MG Road, Mumbai, India" },
        { user_id: "U002", name: "Harshada Dhangar", email: "harshada@safecart.com", address: "456 Park Street, Pune, India" }
    ];
    state.user = defaultAccounts[userIndex] || defaultAccounts[0];
    localStorage.setItem("safecart_amazon_user", JSON.stringify(state.user));
    updateUserDisplay();
    closeModal("auth-modal");
    showToast(`Switched account to ${state.user.name}`, "success");
};

window.handleUserLoginSubmit = async function(e) {
    e.preventDefault();
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value.trim();

    try {
        const res = await fetch(`${API_BASE}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.message || "Invalid credentials");

        state.user = data.user;
        localStorage.setItem("safecart_amazon_user", JSON.stringify(state.user));
        updateUserDisplay();
        closeModal("auth-modal");
        showToast(`Welcome back, ${state.user.name}!`, "success");
    } catch (err) {
        showToast(err.message, "error");
    }
};

// -----------------------------------------------------------------------------
// SafeCart AI Chatbot Widget (Worker + Auditor Agents)
// -----------------------------------------------------------------------------
window.toggleChatWindow = function() {
    if (dom.chatWindow.classList.contains("active")) {
        closeChatWindow();
    } else {
        openChatWindow();
    }
};

window.openChatWindow = function() {
    if (dom.chatWindow) {
        dom.chatWindow.classList.add("active");
        renderChatMessages();
        setTimeout(() => {
            if (dom.chatInput) dom.chatInput.focus();
        }, 150);
    }
};

window.closeChatWindow = function() {
    if (dom.chatWindow) {
        dom.chatWindow.classList.remove("active");
    }
};

function setChatContext(type, productId = null, productName = null, orderId = null) {
    state.chatContext.productId = productId;
    state.chatContext.productName = productName;
    state.chatContext.orderId = orderId;
    updateChatContextPill();
}

function updateChatContextPill() {
    if (!dom.chatContextPill || !dom.chatContextText) return;
    const { productId, productName, orderId } = state.chatContext;

    if (productId) {
        dom.chatContextPill.style.display = "flex";
        dom.chatContextText.textContent = `Attached Product: ${productId} (${productName || "Product"})`;
    } else if (orderId) {
        dom.chatContextPill.style.display = "flex";
        dom.chatContextText.textContent = `Attached Order: ${orderId}`;
    } else {
        dom.chatContextPill.style.display = "none";
    }
}

window.clearChatContext = function() {
    setChatContext(null);
};

function renderChatMessages() {
    if (!dom.chatMessagesContainer) return;

    let html = "";
    state.chatMessages.forEach(msg => {
        if (msg.sender === "user") {
            html += `
                <div class="chat-msg user">
                    <div class="msg-bubble">${escapeHtml(msg.text)}</div>
                </div>
            `;
        } else {
            const audit = msg.audit || {};
            const isApproved = audit.audit_decision === "APPROVED" || audit.status === "APPROVED";
            const isCorrected = audit.audit_decision === "CORRECTED" || audit.status === "CORRECTED";
            const isError = audit.status === "ERROR";

            let auditBadge = "";
            if (isApproved) {
                auditBadge = `<span class="audit-status-badge approved"><i class="fa-solid fa-circle-check"></i> Auditor Approved</span>`;
            } else if (isCorrected) {
                auditBadge = `<span class="audit-status-badge corrected"><i class="fa-solid fa-triangle-exclamation"></i> Auditor Calibrated</span>`;
            } else if (isError) {
                auditBadge = `<span class="audit-status-badge error"><i class="fa-solid fa-circle-xmark"></i> SafeCart Blocked</span>`;
            }

            // Accordion with compliance checks
            let accordionHtml = "";
            if (audit && (audit.intent || audit.errors || audit.corrections)) {
                const intent = audit.intent || "GENERAL";
                const errorNotes = (audit.errors && audit.errors.length) ? audit.errors.join("; ") : "None (fully compliant)";
                const correctionNotes = (audit.corrections && audit.corrections.length) ? audit.corrections.join("; ") : "No calibration needed";

                accordionHtml = `
                    <div class="audit-accordion">
                        <div class="audit-accordion-header" onclick="this.parentElement.classList.toggle('open')">
                            <span>Compliance Inspection</span>
                            <i class="fa-solid fa-chevron-down"></i>
                        </div>
                        <div class="audit-accordion-content">
                            <div><strong>Intent:</strong> ${intent}</div>
                            <div><strong>Status:</strong> ${audit.status || "APPROVED"}</div>
                            <div><strong>Violations:</strong> ${errorNotes}</div>
                            <div><strong>Calibration:</strong> ${correctionNotes}</div>
                        </div>
                    </div>
                `;
            }

            // Quick actions if product ID or order ID mentioned in message
            let actionBtn = "";
            const mProd = msg.text.match(/\b(P\d{3,4})\b/i);
            const mOrd = msg.text.match(/\b(O\d{3,4})\b/i);
            const isMissingMsg = msg.text.toLowerCase().includes("was not found");

            if (mProd && !isMissingMsg) {
                const pid = mProd[1].toUpperCase();
                const prod = (state.allProducts && state.allProducts.find(p => p.product_id === pid)) || msg.product || null;
                if (prod) {
                    const prodImg = getProductImage(prod, false);
                    actionBtn = `
                        <div class="chat-product-minicard" style="display: flex; gap: 10px; align-items: center; background: #f7fafa; border: 1px solid #d5d9d9; border-radius: 8px; padding: 8px 10px; margin-top: 8px;">
                            <img src="${prodImg}" alt="${escapeHtml(prod.product_name)}" style="width: 48px; height: 48px; object-fit: contain; border-radius: 4px; background: #fff; border: 1px solid #e7e7e7;" onerror="handleProductImgError(this, '${pid}', false)">
                            <div style="flex: 1; min-width: 0;">
                                <div style="font-weight: 700; font-size: 0.82rem; color: #0f1111; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(prod.product_name)}</div>
                                <div style="font-size: 0.78rem; color: #565959;">₹${Number(prod.price).toLocaleString("en-IN")} • <span style="color: ${prod.in_stock ? '#067d62' : '#b12704'}; font-weight: 600;">${prod.in_stock ? 'In Stock' : 'Out of Stock'}</span></div>
                            </div>
                            <div style="display: flex; flex-direction: column; gap: 4px;">
                                <button onclick="openProductDetail('${pid}')" style="font-size: 0.72rem; padding: 3px 8px; border-radius: 12px; background: #f0f2f2; border: 1px solid #d5d9d9; cursor: pointer; font-weight: 600;">
                                    View
                                </button>
                                ${prod.in_stock ? `<button onclick="addToCart('${pid}'); showToast('Added to cart!');" style="font-size: 0.72rem; padding: 3px 8px; border-radius: 12px; background: #ffd814; border: 1px solid #fcd200; cursor: pointer; font-weight: 700;">+ Cart</button>` : ''}
                            </div>
                        </div>
                    `;
                } else {
                    actionBtn = `
                        <div style="margin-top: 6px;">
                            <button onclick="openProductDetail('${pid}')" style="font-size: 0.75rem; padding: 4px 10px; border-radius: 12px; background: #ffd814; border: 1px solid #fcd200; cursor: pointer; font-weight: 600;">
                                View ${pid} in Store
                            </button>
                        </div>
                    `;
                }
            } else if (mOrd && !isMissingMsg) {
                const oid = mOrd[1].toUpperCase();
                actionBtn = `
                    <div style="display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap;">
                        <button onclick="openOrderTracking('${oid}')" style="font-size: 0.75rem; padding: 4px 12px; border-radius: 14px; background: #ffd814; border: 1px solid #fcd200; cursor: pointer; font-weight: 600;">
                            <i class="fa-solid fa-map-location-dot"></i> Track ${oid} Timeline
                        </button>
                        <button onclick="openOrdersModal()" style="font-size: 0.75rem; padding: 4px 12px; border-radius: 14px; background: #f0f2f2; border: 1px solid #d5d9d9; cursor: pointer; font-weight: 600;">
                            <i class="fa-solid fa-clock-rotate-left"></i> Order History
                        </button>
                    </div>
                `;
            }

            html += `
                <div class="chat-msg bot">
                    <div class="msg-bubble">${escapeHtml(msg.text)}</div>
                    ${auditBadge}
                    ${actionBtn}
                    ${accordionHtml}
                </div>
            `;
        }
    });

    dom.chatMessagesContainer.innerHTML = html;
    dom.chatMessagesContainer.scrollTop = dom.chatMessagesContainer.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

window.sendCustomerChatMessage = async function(textOverride = null, prodOverride = null, ordOverride = null) {
    const query = textOverride || (dom.chatInput ? dom.chatInput.value.trim() : "");
    if (!query) return;

    if (!textOverride && dom.chatInput) {
        dom.chatInput.value = "";
    }

    // Add user message to history
    state.chatMessages.push({ sender: "user", text: query });
    renderChatMessages();

    // Show temporary bot typing indicator
    const typingMsg = {
        sender: "bot",
        text: "Checking SafeCart Worker AI and verifying with Auditor AI...",
        audit: null,
        isTyping: true
    };
    state.chatMessages.push(typingMsg);
    renderChatMessages();

    const productId = prodOverride || state.chatContext.productId || null;
    const orderId = ordOverride || state.chatContext.orderId || null;

    try {
        const payload = {
            query: query,
            product_id: productId,
            order_id: orderId,
            customer_name: state.user ? state.user.name : "Amazon Customer",
            customer_email: state.user ? state.user.email : "customer@amazon.in",
            user_id: state.user ? state.user.user_id : "U005"
        };

        const res = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        
        // Remove typing indicator
        state.chatMessages.pop();

        state.chatMessages.push({
            sender: "bot",
            text: data.response || "No response received.",
            audit: data.audit || data.worker_response || {},
            product: (data.worker_response && data.worker_response.product) || null,
            order: (data.worker_response && data.worker_response.order) || null
        });

        renderChatMessages();

    } catch (err) {
        console.error("Chat error:", err);
        state.chatMessages.pop();
        state.chatMessages.push({
            sender: "bot",
            text: "Could not connect to SafeCart AI agents. Please check that the backend server is running on http://127.0.0.1:8000.",
            audit: { status: "ERROR", audit_decision: "ERROR" }
        });
        renderChatMessages();
    }
};

window.sendSuggestedQuery = function(queryText) {
    sendCustomerChatMessage(queryText);
};

// -----------------------------------------------------------------------------
// Modal Helpers
// -----------------------------------------------------------------------------
window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove("active");
    }
};

// -----------------------------------------------------------------------------
// Event Listeners Setup
// -----------------------------------------------------------------------------
function setupEventListeners() {
    // Search Button & Enter Key
    if (dom.searchBtn) {
        dom.searchBtn.addEventListener("click", () => {
            handleSearchTrigger();
        });
    }
    if (dom.searchInput) {
        dom.searchInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") handleSearchTrigger();
        });
    }

    // Category Select Dropdown
    if (dom.searchCategorySelect) {
        dom.searchCategorySelect.addEventListener("change", (e) => {
            state.selectedCategory = e.target.value;
            state.currentPage = 1;
            applyFilters();
        });
    }

    // Sort Dropdown
    if (dom.catalogSortSelect) {
        dom.catalogSortSelect.addEventListener("change", (e) => {
            state.selectedSort = e.target.value;
            applyFilters();
        });
    }

    // Cart Button & Drawer
    if (dom.navCartBtn) {
        dom.navCartBtn.addEventListener("click", openCartDrawer);
    }
    if (dom.cartDrawerOverlay) {
        dom.cartDrawerOverlay.addEventListener("click", closeCartDrawer);
    }

    // Returns & Orders
    if (dom.navOrdersBtn) {
        dom.navOrdersBtn.addEventListener("click", openOrdersModal);
    }

    // Sign in / Account
    if (dom.navSigninBtn) {
        dom.navSigninBtn.addEventListener("click", openAuthModal);
    }

    // Deliver To Address
    if (dom.deliverAddressBtn) {
        dom.deliverAddressBtn.addEventListener("click", () => {
            const newAddr = prompt("Enter delivery address in India:", state.user.address);
            if (newAddr && newAddr.trim()) {
                state.user.address = newAddr.trim();
                localStorage.setItem("safecart_amazon_user", JSON.stringify(state.user));
                updateUserDisplay();
                showToast("Delivery address updated.", "success");
            }
        });
    }

    // Panel "All" Button
    if (dom.panelAllBtn) {
        dom.panelAllBtn.addEventListener("click", () => {
            resetAllFilters();
            const catElem = document.getElementById("catalog-section");
            if (catElem) catElem.scrollIntoView({ behavior: "smooth" });
        });
    }

    // Panel Category Links (.panel-ops p)
    document.querySelectorAll(".panel-ops p").forEach(item => {
        item.addEventListener("click", () => {
            const text = item.textContent.trim();
            if (text === "Customer Service") {
                openChatWindow();
            } else if (text === "Best Sellers" || text === "Today's Deals") {
                resetAllFilters();
                const catElem = document.getElementById("catalog-section");
                if (catElem) catElem.scrollIntoView({ behavior: "smooth" });
            } else {
                // Category match
                filterByCategoryName(text);
            }
        });
    });

    // Panel Deals Link
    const panelDeals = document.querySelector(".panel-deals");
    if (panelDeals) {
        panelDeals.addEventListener("click", () => {
            filterByCategoryName("Electronics");
        });
    }

    // Shop Section 12 Boxes
    document.querySelectorAll(".shop-section .box").forEach(box => {
        box.style.cursor = "pointer";
        box.addEventListener("click", (e) => {
            const h2 = box.querySelector("h2");
            const boxTitle = h2 ? h2.textContent.trim() : "";
            handleBoxClick(boxTitle);
        });
    });

    // Chatbot Toggle & Close
    if (dom.chatToggleBtn) {
        dom.chatToggleBtn.addEventListener("click", toggleChatWindow);
    }
    if (dom.chatCloseBtn) {
        dom.chatCloseBtn.addEventListener("click", closeChatWindow);
    }

    // Chat Send & Enter
    if (dom.chatSendBtn) {
        dom.chatSendBtn.addEventListener("click", () => sendCustomerChatMessage());
    }
    if (dom.chatInput) {
        dom.chatInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") sendCustomerChatMessage();
        });
    }

    // Chat Context Clear
    if (dom.chatContextClear) {
        dom.chatContextClear.addEventListener("click", clearChatContext);
    }

    // Modal Background Clicks
    document.querySelectorAll(".modal-overlay").forEach(overlay => {
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) {
                overlay.classList.remove("active");
            }
        });
    });
}

function handleSearchTrigger() {
    if (!dom.searchInput) return;
    state.searchQuery = dom.searchInput.value.trim();
    state.currentPage = 1;
    applyFilters();

    const catElem = document.getElementById("catalog-section");
    if (catElem) {
        catElem.scrollIntoView({ behavior: "smooth" });
    }
}

function filterByCategoryName(categoryName) {
    state.selectedCategory = categoryName;
    state.searchQuery = "";
    state.maxPriceFilter = null;
    state.currentPage = 1;
    if (dom.searchCategorySelect) dom.searchCategorySelect.value = categoryName;
    if (dom.searchInput) dom.searchInput.value = "";
    applyFilters();

    const catElem = document.getElementById("catalog-section");
    if (catElem) {
        catElem.scrollIntoView({ behavior: "smooth" });
    }
}

function handleBoxClick(boxTitle) {
    if (boxTitle.includes("Clothing")) {
        filterByCategoryName("Clothing");
    } else if (boxTitle.includes("Health & Personal Care") || boxTitle.includes("Beauty")) {
        filterByCategoryName("Personal Care");
    } else if (boxTitle.includes("Furniture")) {
        filterByCategoryName("Furniture");
    } else if (boxTitle.includes("Electronics")) {
        filterByCategoryName("Electronics");
    } else if (boxTitle.includes("Pet care")) {
        filterByCategoryName("Home & Kitchen");
    } else if (boxTitle.includes("Toys")) {
        filterByCategoryName("Accessories");
    } else if (boxTitle.includes("Fashion")) {
        filterByCategoryName("Fashion");
    } else if (boxTitle.includes("Fitness")) {
        filterByCategoryName("Fitness");
    } else if (boxTitle.includes("Sports")) {
        filterByCategoryName("Sports");
    } else if (boxTitle.includes("Under ₹899")) {
        state.maxPriceFilter = 899;
        state.selectedCategory = "all";
        state.currentPage = 1;
        applyFilters();
        const catElem = document.getElementById("catalog-section");
        if (catElem) catElem.scrollIntoView({ behavior: "smooth" });
    } else {
        filterByCategoryName("Home");
    }
}

// -----------------------------------------------------------------------------
// Boot on DOM Ready
// -----------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", initApp);
