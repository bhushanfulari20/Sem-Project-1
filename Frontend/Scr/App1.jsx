import { useState } from "react";
import "./App.css";

import Header from "./components/Header";
import CustomerForm from "./components/CustomerForm";
import ResponseCard from "./components/ResponseCard";
import AuditInfo from "./components/AuditInfo";
import Sidebar from "./components/Sidebar";

const BACKEND_URL = "http://127.0.0.1:8000";

function App() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const askSafeCart = async ({
    query,
    order_id,
    product_id,
  }) => {
    setError("");
    setResult(null);

    // Frontend condition
    if (!query.trim()) {
      setError("Please enter a customer query.");
      return;
    }

    try {
      setLoading(true);

      const response = await fetch(
        `${BACKEND_URL}/chat`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            query: query.trim(),
            order_id: order_id?.trim() || null,
            product_id: product_id?.trim() || null,
          }),
        }
      );

      let data;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      // HTTP error
      if (!response.ok) {
        setError(
          `Backend error: ${response.status}`
        );
        return;
      }

      if (!data) {
        setError(
          "SafeCart returned an invalid response."
        );
        return;
      }

      setResult(data);
    } catch (err) {
      setError(
        "Cannot connect to SafeCart backend. Start FastAPI first."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">

      {/* Header */}

      <Header />


      {/* Main Layout */}

      <div className="layout">

        {/* Main Content */}

        <main className="main-content">

          {/* Information */}

          <div className="info-box">

            <strong>
              SafeCart Safety System
            </strong>

            <p>
              Worker AI proposes a response →
              Auditor AI verifies it →
              Only approved responses reach the customer.
            </p>

          </div>


          {/* Customer Form */}

          <CustomerForm
            onSubmit={askSafeCart}
            loading={loading}
          />


          {/* Error */}

          {error && (
            <div className="alert error">
              ❌ {error}
            </div>
          )}


          {/* Result */}

          {result && (
            <>
              <ResponseCard result={result} />

              <AuditInfo result={result} />
            </>
          )}

        </main>


        {/* Sidebar */}

        <Sidebar />

      </div>

    </div>
  );
}

export default App;