import { useState } from "react";

function CustomerForm({
  onSubmit,
  loading,
}) {

  const [query, setQuery] = useState("");

  const [orderId, setOrderId] =
    useState("");

  const [productId, setProductId] =
    useState("");


  const handleSubmit = (event) => {

    event.preventDefault();

    onSubmit({
      query,
      order_id: orderId,
      product_id: productId,
    });

  };


  return (
    <section className="card">

      <h2>
        Ask SafeCart
      </h2>


      <form onSubmit={handleSubmit}>

        {/* Customer Query */}

        <label>
          Customer Query{" "}
          <span className="required">
            *
          </span>
        </label>

        <textarea
          value={query}

          onChange={(e) =>
            setQuery(e.target.value)
          }

          placeholder=
            "Example: Can I get a refund for this product?"

          rows="4"
        />


        {/* Order + Product */}

        <div className="input-row">

          <div>

            <label>
              Order ID
            </label>

            <input
              type="text"

              value={orderId}

              onChange={(e) =>
                setOrderId(e.target.value)
              }

              placeholder="Example: O501"
            />

          </div>


          <div>

            <label>
              Product ID
            </label>

            <input
              type="text"

              value={productId}

              onChange={(e) =>
                setProductId(e.target.value)
              }

              placeholder="Example: P101"
            />

          </div>

        </div>


        {/* Button */}

        <button
          className="ask-button"

          type="submit"

          disabled={loading}
        >

          {loading
            ? "⏳ SafeCart is checking..."
            : "➤ Ask SafeCart"}

        </button>

      </form>

    </section>
  );
}

export default CustomerForm;