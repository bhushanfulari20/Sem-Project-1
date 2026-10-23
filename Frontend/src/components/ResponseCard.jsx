function ResponseCard({ result }) {
  const status = result?.status;
  const workerResp = result?.worker_response || result?.audit?.worker_result || {};
  const product = workerResp?.product || result?.audit?.product || null;
  const order = workerResp?.order || result?.audit?.order || null;
  const inventory = workerResp?.inventory || result?.audit?.inventory || null;
  const auditErrors = result?.audit?.errors || [];
  const corrections = result?.audit?.corrections || [];

  const config = {
    APPROVED: {
      className: "success",
      title: "✅ Auditor Approved",
      description: "Response verified against database records by SafeCart Auditor AI.",
    },
    CORRECTED: {
      className: "warning",
      title: "⚡ Response Corrected & Approved",
      description: "Worker draft had inconsistencies which Auditor AI corrected using verified database records.",
    },
    ESCALATED: {
      className: "warning",
      title: "⚠️ Human Review Required",
      description: "This customer inquiry requires manual review by a support specialist.",
    },
    BLOCKED: {
      className: "blocked",
      title: "🚫 Worker Response Blocked by Auditor",
      description: "Worker AI response violated compliance guardrails and was blocked.",
    },
    ERROR: {
      className: "error",
      title: "❌ SafeCart Returned an Error",
      description: "Unable to process request with available input.",
    },
  };

  const current = config[status] || {
    className: "error",
    title: "❌ SafeCart Status: " + (status || "UNKNOWN"),
    description: "Unexpected status returned.",
  };

  // Helper for image URL resolution
  const getProductImgSrc = (p) => {
    if (!p) return "";
    const pid = p.product_id || p.PID;
    if (p.image_url && p.image_url.startsWith("http")) return p.image_url;
    if (pid) return `/product_images/${pid}.jpg`;
    return "";
  };

  const handleImageError = (e, p) => {
    e.target.onerror = null;
    // Fallback deterministic SVG data URL
    const name = p?.product_name || "SafeCart Product";
    const cat = p?.category || "Verified";
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300">
      <rect width="300" height="300" fill="#f3f4f6"/>
      <circle cx="150" cy="130" r="50" fill="#e5e7eb"/>
      <path d="M120 120 h60 v30 h-60 z" fill="#9ca3af"/>
      <text x="150" y="210" text-anchor="middle" font-family="sans-serif" font-size="14" font-weight="bold" fill="#374151">${name.substring(0, 24)}</text>
      <text x="150" y="235" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#6b7280">${cat} • SafeCart</text>
    </svg>`;
    e.target.src = `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
  };

  return (
    <section className="result-card">
      <div className="result-header">
        <h2>SafeCart Response</h2>
        <span className={`status-pill status-pill-${(status || "UNKNOWN").toLowerCase()}`}>
          STATUS: {status || "UNKNOWN"}
        </span>
      </div>

      <div className={`alert ${current.className}`}>
        <div className="alert-title">{current.title}</div>
        <div className="alert-desc">{current.description}</div>
      </div>

      {/* Main text response */}
      <div className="response">
        {result?.response || "No response returned."}
      </div>

      {/* Audit Highlights (Corrections / Errors) */}
      {(corrections.length > 0 || auditErrors.length > 0) && (
        <div className="audit-callout">
          {corrections.length > 0 && (
            <div className="audit-corrections">
              <strong>🛠️ Auditor Corrections Applied:</strong>
              <ul>
                {corrections.map((corr, idx) => (
                  <li key={idx}>{corr}</li>
                ))}
              </ul>
            </div>
          )}
          {auditErrors.length > 0 && (
            <div className="audit-errors">
              <strong>⚠️ Flagged Discrepancies:</strong>
              <ul>
                {auditErrors.map((err, idx) => (
                  <li key={idx}>{err}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Structured Product Card (if query returned product) */}
      {product && (
        <div className="response-product-card">
          <div className="response-product-img-wrap">
            <img
              src={getProductImgSrc(product)}
              alt={product.product_name || "Product"}
              className="response-product-img"
              onError={(e) => handleImageError(e, product)}
              loading="lazy"
            />
            <span className="product-category-tag">{product.category || "General"}</span>
          </div>
          <div className="response-product-details">
            <div className="response-product-meta">
              <span className="product-pid-badge">{product.product_id}</span>
              <span className="product-verified-badge">✓ SafeCart Verified</span>
            </div>
            <h3 className="response-product-title">{product.product_name}</h3>
            <div className="response-product-pricing">
              <span className="product-price">Rs. {product.price}</span>
              {inventory?.quantity !== undefined && (
                <span className={`product-stock-tag ${Number(inventory.quantity) > 0 ? "in-stock" : "out-of-stock"}`}>
                  {Number(inventory.quantity) > 0 ? `In Stock (${inventory.quantity} units)` : "Out of Stock"}
                </span>
              )}
            </div>
            {product.description && (
              <p className="response-product-desc">{product.description}</p>
            )}
          </div>
        </div>
      )}

      {/* Structured Order Details Table (if query returned order) */}
      {order && (
        <div className="response-order-box">
          <h4 className="response-order-title">📦 Order Summary ({order.order_id})</h4>
          <div className="table-responsive-wrapper">
            <table className="order-details-table">
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Database Record</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Order ID</strong></td>
                  <td><span className="order-id-chip">{order.order_id}</span></td>
                </tr>
                {order.product_id && (
                  <tr>
                    <td><strong>Product</strong></td>
                    <td>{order.product_name || order.product_id} ({order.product_id})</td>
                  </tr>
                )}
                {order.customer_name && (
                  <tr>
                    <td><strong>Customer</strong></td>
                    <td>{order.customer_name}</td>
                  </tr>
                )}
                {order.order_date && (
                  <tr>
                    <td><strong>Order Date</strong></td>
                    <td>{order.order_date}</td>
                  </tr>
                )}
                {order.delivery_date && (
                  <tr>
                    <td><strong>Expected Delivery</strong></td>
                    <td>{order.delivery_date}</td>
                  </tr>
                )}
                {order.refundable !== undefined && (
                  <tr>
                    <td><strong>Refundable</strong></td>
                    <td>
                      <span className={`badge-pill ${String(order.refundable).toLowerCase() === "yes" ? "pill-green" : "pill-red"}`}>
                        {String(order.refundable).toUpperCase()}
                      </span>
                    </td>
                  </tr>
                )}
                {order.refunded !== undefined && (
                  <tr>
                    <td><strong>Refunded</strong></td>
                    <td>
                      <span className={`badge-pill ${String(order.refunded).toLowerCase() === "yes" ? "pill-blue" : "pill-gray"}`}>
                        {String(order.refunded).toUpperCase()}
                      </span>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}

export default ResponseCard;