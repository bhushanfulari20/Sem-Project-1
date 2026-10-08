import { useState } from "react";

import "./App.css";

import Header from "./Components/Header";
import CustomerForm from "./Components/CustomerForm";
import ResponseCard from "./Components/ResponseCard";
import AuditInfo from "./Components/AuditInfo";
import Sidebar from "./Components/Sidebar";


// ======================================================
// FASTAPI BACKEND
// ======================================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";


function App() {

  const [result, setResult] = useState(null);

  const [error, setError] = useState("");

  const [loading, setLoading] = useState(false);


  // ====================================================
  // SEND CUSTOMER REQUEST
  // ====================================================

  const askSafeCart = async ({
    query,
    order_id,
    product_id,
  }) => {

    setError("");

    setResult(null);


    // --------------------------------------------------
    // Validate query
    // --------------------------------------------------

    if (!query.trim()) {

      setError(
        "Please enter a customer query."
      );

      return;
    }


    try {

      setLoading(true);


      // ------------------------------------------------
      // Send request to FastAPI
      // ------------------------------------------------

      const response = await fetch(
        `${API_BASE_URL}/chat`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            query: query.trim(),

            order_id:
              order_id?.trim() || null,

            product_id:
              product_id?.trim() || null,
          }),
        }
      );


      // ------------------------------------------------
      // Read response
      // ------------------------------------------------

      let data = null;

      try {

        data = await response.json();

      } catch {

        data = null;

      }


      // ------------------------------------------------
      // Backend HTTP error
      // ------------------------------------------------

      if (!response.ok) {
        if (response.status === 500) {
          setError(
            "Backend error (HTTP 500): Cannot reach FastAPI backend. Make sure the backend server is running in a terminal: python -m uvicorn Backend.main:app --reload --port 8000"
          );
        } else {
          setError(`Backend error: HTTP ${response.status}`);
        }
        return;
      }


      // ------------------------------------------------
      // Invalid response
      // ------------------------------------------------

      if (!data) {

        setError(
          "SafeCart returned an invalid response."
        );

        return;
      }


      // ------------------------------------------------
      // Successful response
      // ------------------------------------------------

      setResult(data);

    }

    catch (err) {

      console.error(
        "SafeCart connection error:",
        err
      );


      setError(
        "Cannot connect to the SafeCart backend. " +
        "Make sure FastAPI is running on port 8000."
      );

    }

    finally {

      setLoading(false);

    }

  };


  // ====================================================
  // UI
  // ====================================================

  return (

    <div className="app">

      {/* ================================================
          HEADER
      ================================================ */}

      <Header />


      <div className="layout">

        {/* ==============================================
            MAIN CONTENT
        ============================================== */}

        <main className="main-content">


          <div className="info-box">

            <div className="info-box-header">

              <span className="badge-green">
                Live Compliance Check
              </span>

              <strong>
                SafeCart Safety System
              </strong>

            </div>

            <p>
              Worker AI proposes a response →
              Auditor AI verifies it →
              Only approved responses reach the customer.
            </p>

            <div className="stats-row">

              <div className="stat-card">
                <span className="stat-label">
                  Worker
                </span>
                <strong>
                  Response Draft
                </strong>
              </div>

              <div className="stat-card">
                <span className="stat-label">
                  Auditor
                </span>
                <strong>
                  Rules Check
                </strong>
              </div>

              <div className="stat-card">
                <span className="stat-label">
                  Outcome
                </span>
                <strong>
                  Safe Send
                </strong>
              </div>

            </div>

          </div>


          {/* ============================================
              CUSTOMER FORM
          ============================================ */}

          <CustomerForm
            onSubmit={askSafeCart}
            loading={loading}
          />


          {/* ============================================
              ERROR
          ============================================ */}

          {error && (

            <div className="alert error">

              ❌ {error}

            </div>

          )}


          {/* ============================================
              RESPONSE
          ============================================ */}

          {result && (

            <>

              <ResponseCard
                result={result}
              />

              <AuditInfo
                result={result}
              />

            </>

          )}

        </main>


        {/* ==============================================
            SIDEBAR
        ============================================== */}

        <Sidebar />

      </div>

    </div>

  );

}


export default App;
