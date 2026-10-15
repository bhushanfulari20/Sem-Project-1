from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import os
import sys

# The documented launch command runs from Backend/, while these shared modules
# live at the repository root. Add that root for both launch styles.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Detect built React frontend dist directory
FRONTEND_DIST_DIR = (
    PROJECT_ROOT / "frontend" / "dist"
    if (PROJECT_ROOT / "frontend" / "dist").is_dir()
    else PROJECT_ROOT / "Frontend" / "dist"
)

from models.schemas import (
    ChatRequest,
    OrderCreateRequest,
    CheckoutRequest,
    LoginRequest,
    RegisterRequest,
    CartItemRequest,
    ProductCreateRequest,
    ProductUpdateRequest,
    StockUpdateRequest
)
from utils.helpers import to_json_safe
import Database.database as db

try:
    from .worker_agent import worker_agent
    from .auditor_agent import auditor_agent
except ImportError:  # pragma: no cover - allows running main.py directly
    from worker_agent import worker_agent
    from auditor_agent import auditor_agent


# --------------------------------------------------
# SafeCart FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="SafeCart API",
    description="Self-Calibrating AI Agent for E-Commerce Compliance",
    version="1.0.0"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

origins_env = os.getenv("ALLOWED_ORIGINS", "*").strip()
if origins_env == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    if origins_env:
        allowed_origins.extend([o.strip() for o in origins_env.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False if "*" in allowed_origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def fallback_amazon_assets(request, call_next):
    response = await call_next(request)
    if response.status_code == 404 and AMAZON_CLONE_DIR.is_dir():
        rel_path = request.url.path.lstrip("/")
        if rel_path:
            candidate = AMAZON_CLONE_DIR / rel_path
            if candidate.is_file():
                return FileResponse(candidate)
    return response


# --------------------------------------------------
# Home Route
# --------------------------------------------------

@app.get("/")
def root():
    index_file = FRONTEND_DIST_DIR / "index.html"
    if FRONTEND_DIST_DIR.is_dir() and index_file.is_file():
        return FileResponse(index_file)
    return {
        "message": "SafeCart API is running",
        "status": "OK"
    }


@app.get("/api")
def api_root():
    return {
        "message": "SafeCart API is running",
        "status": "OK"
    }


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "SafeCart API"
    }


def json_response(content: dict) -> JSONResponse:
    """Return API data after converting pandas/NumPy values to JSON values.

    CSV records can contain ``NaN`` or NumPy scalar values.  Starlette rejects
    non-finite floats while serializing a response, which otherwise turns a
    successfully handled request into an HTTP 500.
    """
    return JSONResponse(content=jsonable_encoder(to_json_safe(content)))


# --------------------------------------------------
# Chat Route
# --------------------------------------------------

@app.post("/api/chat")
@app.post("/chat", include_in_schema=False)  # Backwards compatibility for existing clients.
def chat(request: ChatRequest):

    # Check empty query
    if not request.query.strip():
        return json_response({
            "status": "ERROR",
            "response": "Customer query cannot be empty."
        })

    try:

        # ------------------------------------------
        # STEP 1: Worker AI
        # ------------------------------------------

        worker_result = worker_agent(
            query=request.query,
            order_id=request.order_id,
            product_id=request.product_id,
            customer_name=request.customer_name,
            user_id=request.user_id,
            customer_email=request.customer_email
        )


        # ------------------------------------------
        # STEP 2: Auditor AI
        # ------------------------------------------

        audit_result = auditor_agent(
            query=request.query,
            order_id=request.order_id,
            product_id=request.product_id,
            worker_result=worker_result,
            customer_name=request.customer_name,
            user_id=request.user_id,
            customer_email=request.customer_email
        )


        # ------------------------------------------
        # STEP 3: Return Safe Response
        # ------------------------------------------

        return json_response({
            "status": audit_result.get(
                "status",
                "ERROR"
            ),

            "response": audit_result.get(
                "response",
                "SafeCart could not generate a response."
            ),

            "worker_response": worker_result,

            "audit": audit_result
        })


    except Exception as e:

        return {
            "status": "ERROR",
            "response": "An internal SafeCart error occurred.",
            "error": str(e)
        }


# --------------------------------------------------
# SafeCart Catalog & E-Commerce APIs
# --------------------------------------------------

@app.get("/api/products")
def get_products(
    search: str = "",
    category: str = None,
    limit: int = 500,
    offset: int = 0,
    in_stock_only: bool = False
):
    """Retrieve catalog products with real-time stock and prices from SafeCart database."""
    items = db.search_products(
        query=search,
        category=category,
        limit=limit if limit > 0 else None,
        offset=offset
    )
    total = db.count_products(query=search, category=category)
    if in_stock_only:
        items = [p for p in items if p.get("in_stock")]
    return json_response({
        "status": "SUCCESS",
        "total": total,
        "count": len(items),
        "offset": offset,
        "limit": limit,
        "products": items
    })


@app.get("/api/products/{product_id}")
def get_single_product(product_id: str):
    """Get single product details with live stock availability."""
    product = db.get_product_with_inventory(product_id)
    if not product:
        return JSONResponse(
            status_code=404,
            content={"status": "ERROR", "message": f"Product '{product_id}' not found."}
        )
    return json_response({
        "status": "SUCCESS",
        "product": product
    })


@app.get("/api/categories")
def get_categories():
    """Get all unique product categories available in the SafeCart catalog."""
    categories = db.get_categories()
    return json_response({
        "status": "SUCCESS",
        "categories": categories
    })


@app.get("/api/inventory/{product_id}")
def get_inventory(product_id: str):
    """Get real-time inventory count for a specific product."""
    inv = db.get_inventory(product_id)
    if not inv:
        return JSONResponse(
            status_code=404,
            content={"status": "ERROR", "message": f"Inventory for '{product_id}' not found."}
        )
    return json_response({
        "status": "SUCCESS",
        "inventory": inv
    })


@app.post("/api/products")
def create_product(req: ProductCreateRequest):
    """Create a new product in SafeCart database and initialize inventory."""
    try:
        new_prod = db.add_product(
            product_name=req.product_name,
            category=req.category,
            price=req.price,
            description=req.description or "",
            initial_stock=req.initial_stock if req.initial_stock is not None else 10,
            product_id=req.product_id,
            image_url=req.image_url
        )
        return json_response({
            "status": "SUCCESS",
            "message": f"Product '{new_prod['product_id']}' created and synchronized with database.",
            "product": new_prod
        })
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"status": "ERROR", "message": str(ve)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "ERROR", "message": str(e)})


@app.put("/api/products/{product_id}")
@app.patch("/api/products/{product_id}")
def update_product_endpoint(product_id: str, req: ProductUpdateRequest):
    """Update product details and/or stock in SafeCart database."""
    try:
        updated = db.update_product(
            product_id=product_id,
            product_name=req.product_name,
            category=req.category,
            price=req.price,
            description=req.description,
            quantity=req.quantity,
            image_url=req.image_url
        )
        return json_response({
            "status": "SUCCESS",
            "message": f"Product '{product_id}' successfully updated in database.",
            "product": updated
        })
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"status": "ERROR", "message": str(ve)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "ERROR", "message": str(e)})


@app.put("/api/products/{product_id}/stock")
@app.patch("/api/products/{product_id}/stock")
@app.put("/api/inventory/{product_id}")
def update_stock_endpoint(product_id: str, req: StockUpdateRequest):
    """Synchronize inventory stock quantity for a product in SafeCart database."""
    try:
        prod = db.find_product(product_id)
        if not prod:
            return JSONResponse(status_code=404, content={"status": "ERROR", "message": f"Product '{product_id}' not found."})
        res = db.set_inventory(product_id, req.quantity)
        return json_response({
            "status": "SUCCESS",
            "message": f"Stock for '{product_id}' updated to {req.quantity} in database.",
            "inventory": res
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "ERROR", "message": str(e)})


@app.delete("/api/products/{product_id}")
def delete_product_endpoint(product_id: str):
    """Remove product and its inventory record from SafeCart database."""
    try:
        prod = db.find_product(product_id)
        if not prod:
            return JSONResponse(status_code=404, content={"status": "ERROR", "message": f"Product '{product_id}' not found."})
        db.delete_product(product_id)
        return json_response({
            "status": "SUCCESS",
            "message": f"Product '{product_id}' deleted from database."
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "ERROR", "message": str(e)})


@app.get("/api/orders")
def get_orders(limit: int = 50, order_id: str = None):
    """Retrieve orders from SafeCart database, optionally filtered by order_id."""
    if order_id:
        order = db.find_order(order_id)
        if not order:
            return JSONResponse(
                status_code=404,
                content={"status": "ERROR", "message": f"Order '{order_id}' not found."}
            )
        prod = db.find_product(order.get("product_id"))
        if prod:
            order["product_name"] = prod.get("product_name")
            order["price"] = prod.get("price")
        return json_response({
            "status": "SUCCESS",
            "orders": [order],
            "total": 1
        })

    orders = db.get_all_orders(limit=limit)
    return json_response({
        "status": "SUCCESS",
        "orders": orders,
        "total": len(orders)
    })


@app.get("/api/orders/{order_id}")
def get_order_by_id(order_id: str):
    """Retrieve specific order details with product information."""
    order = db.find_order(order_id)
    if not order:
        return JSONResponse(
            status_code=404,
            content={"status": "ERROR", "message": f"Order '{order_id}' not found."}
        )
    prod = db.find_product(order.get("product_id"))
    if prod:
        order["product_name"] = prod.get("product_name")
        order["price"] = prod.get("price")
        order["category"] = prod.get("category")
        order["description"] = prod.get("description")
    return json_response({
        "status": "SUCCESS",
        "order": order
    })


@app.post("/api/orders")
def place_order(order_req: OrderCreateRequest):
    """Place an order for a single product, updating SafeCart inventory safely."""
    try:
        order = db.create_order(
            product_id=order_req.product_id,
            customer_name=order_req.customer_name,
            customer_email=order_req.customer_email,
            shipping_address=order_req.shipping_address,
            quantity=order_req.quantity or 1
        )
        return json_response({
            "status": "SUCCESS",
            "message": f"Order {order['order_id']} placed successfully!",
            "order": order
        })
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"status": "ERROR", "message": str(ve)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "ERROR", "message": str(e)})


@app.post("/api/checkout")
def checkout(checkout_req: CheckoutRequest):
    """Checkout cart items: verifies prices & stock, safely updates inventory, and creates orders."""
    if not checkout_req.items:
        return JSONResponse(status_code=400, content={"status": "ERROR", "message": "Cart is empty."})

    # Step 1: Pre-verify all items exist and have enough stock
    for item in checkout_req.items:
        prod = db.find_product(item.product_id)
        if not prod:
            return JSONResponse(
                status_code=400,
                content={"status": "ERROR", "message": f"Product '{item.product_id}' not found in database."}
            )
        inv = db.get_inventory(item.product_id)
        qty = int(inv.get("quantity", 0)) if inv else 0
        requested_qty = item.quantity or 1
        if qty < requested_qty:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "ERROR",
                    "message": f"Insufficient stock for {prod.get('product_name')} ({item.product_id}). Available: {qty}, requested: {requested_qty}."
                }
            )

    # Step 2: Create each order safely
    created_orders = []
    try:
        for item in checkout_req.items:
            order = db.create_order(
                product_id=item.product_id,
                customer_name=checkout_req.customer_name,
                customer_email=checkout_req.customer_email,
                shipping_address=checkout_req.shipping_address,
                payment_method=checkout_req.payment_method or "Simulated Demo Payment",
                quantity=item.quantity or 1
            )
            order["customer_phone"] = checkout_req.customer_phone
            order["is_demo"] = True
            created_orders.append(order)

        return json_response({
            "status": "SUCCESS",
            "message": f"Successfully placed {len(created_orders)} order(s)!",
            "demo_mode": True,
            "orders": created_orders
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "ERROR", "message": str(e)})


@app.post("/api/cart/validate")
def validate_cart(items: list[dict]):
    """Validate cart items against live database prices and stock."""
    verified_items = []
    subtotal = 0
    for it in items:
        pid = it.get("product_id")
        qty = int(it.get("quantity", 1))
        prod = db.get_product_with_inventory(pid)
        if prod:
            item_price = int(prod.get("price", 0))
            available_qty = int(prod.get("quantity", 0))
            is_available = available_qty >= qty and available_qty > 0
            subtotal += item_price * qty
            verified_items.append({
                "product_id": pid,
                "product_name": prod.get("product_name"),
                "category": prod.get("category"),
                "price": item_price,
                "requested_quantity": qty,
                "available_quantity": available_qty,
                "is_available": is_available,
                "line_total": item_price * qty
            })
    return json_response({
        "status": "SUCCESS",
        "items": verified_items,
        "subtotal": subtotal,
        "all_available": all(i["is_available"] for i in verified_items) if verified_items else True
    })


@app.get("/api/policies")
def get_policies_endpoint():
    """Retrieve policies from SafeCart database."""
    policies = db.get_policies()
    return json_response({
        "status": "SUCCESS",
        "policies": policies
    })


@app.post("/api/login")
def login_endpoint(req: LoginRequest):
    """Authenticate customer against SafeCart database."""
    user = db.authenticate_user(req.email, req.password)
    if not user:
        return JSONResponse(status_code=401, content={"status": "ERROR", "message": "Invalid email or password."})
    return json_response({
        "status": "SUCCESS",
        "user": user
    })


@app.post("/api/register")
def register_endpoint(req: RegisterRequest):
    """Register customer in SafeCart database."""
    try:
        user = db.create_user(req.name, req.email, req.password, req.address or "India")
        return json_response({
            "status": "SUCCESS",
            "user": user
        })
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"status": "ERROR", "message": str(ve)})


@app.get("/api/users")
def get_users_endpoint():
    """Get registered users (without passwords) for user switching / verification."""
    df = db.load_users()
    if df.empty:
        return json_response({"status": "SUCCESS", "users": []})
    users = df.drop(columns=["password"], errors="ignore").to_dict(orient="records")
    return json_response({
        "status": "SUCCESS",
        "users": users
    })


# --------------------------------------------------
# Amazon Clone Frontend Routes & Mounts
# --------------------------------------------------

AMAZON_CLONE_DIR = (
    PROJECT_ROOT / "amazon clone"
    if (PROJECT_ROOT / "amazon clone").is_dir()
    else PROJECT_ROOT / "amazon_clone"
)


@app.get("/amazon")
@app.get("/amazon/")
@app.get("/clone")
def serve_amazon_clone():
    """Serve the integrated Amazon clone shopping frontend."""
    amazon_html = AMAZON_CLONE_DIR / "Amazon.html"
    if AMAZON_CLONE_DIR.is_dir() and amazon_html.is_file():
        return FileResponse(amazon_html)
    return JSONResponse(status_code=404, content={"message": "Amazon clone file not found."})


# Mount local verified product images directory
PRODUCT_IMAGES_DIR = (
    PROJECT_ROOT / "amazon clone" / "product_images"
    if (PROJECT_ROOT / "amazon clone" / "product_images").is_dir()
    else PROJECT_ROOT / "Frontend" / "public" / "product_images"
)

if PRODUCT_IMAGES_DIR.is_dir():
    app.mount(
        "/product_images",
        StaticFiles(directory=PRODUCT_IMAGES_DIR),
        name="product_images",
    )


# Mount Amazon clone assets directory under /amazon (and /clone-assets)
if AMAZON_CLONE_DIR.is_dir():
    app.mount(
        "/amazon",
        StaticFiles(directory=AMAZON_CLONE_DIR, html=True),
        name="amazon_clone",
    )


# The React app is built into Frontend/dist. Mount it last so API and docs
# routes (/api, /health, /docs) are not intercepted by the static file handler.
if FRONTEND_DIST_DIR.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_DIST_DIR, html=True),
        name="frontend",
    )
elif AMAZON_CLONE_DIR.is_dir():
    # If React frontend dist is not built, fallback root static files to Amazon clone
    @app.get("/{filename}")
    def serve_root_asset(filename: str):
        target = AMAZON_CLONE_DIR / filename
        if target.is_file():
            return FileResponse(target)
        return JSONResponse(status_code=404, content={"message": f"Asset '{filename}' not found."})


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("Backend.main:app", host="0.0.0.0", port=port, reload=False)

