import streamlit as st
import requests


BACKEND_URL = "http://127.0.0.1:8000"


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="SafeCart",
    page_icon="🛒",
    layout="centered"
)


# =====================================================
# PAGE HEADER
# =====================================================

st.title("🛒 SafeCart")

st.subheader(
    "Self-Calibrating AI Agent for E-Commerce Compliance"
)

st.info(
    "Worker AI proposes a response → Auditor AI verifies it → "
    "Only approved responses reach the customer."
)


# =====================================================
# USER INPUT
# =====================================================

query = st.text_input(
    "Customer Query",
    placeholder="Example: Can I get a refund?"
)

order_id = st.text_input(
    "Order ID",
    placeholder="Example: O501"
)

product_id = st.text_input(
    "Product ID",
    placeholder="Example: P101"
)


# =====================================================
# SEND REQUEST
# =====================================================

if st.button("Ask SafeCart", type="primary"):

    # -------------------------------------------------
    # FRONTEND CONDITION
    # -------------------------------------------------

    if not query.strip():

        st.error(
            "Please enter a customer query."
        )

    else:

        payload = {
            "query": query,
            "order_id": order_id.strip() or None,
            "product_id": product_id.strip() or None
        }

        try:

            # -------------------------------------------------
            # SEND REQUEST TO FASTAPI
            # -------------------------------------------------

            with st.spinner(
                "SafeCart is checking your request..."
            ):

                response = requests.post(
                    f"{BACKEND_URL}/chat",
                    json=payload,
                    timeout=30
                )


            # =================================================
            # HTTP ERROR
            # =================================================

            if response.status_code != 200:

                st.error(
                    f"Backend error: {response.status_code}"
                )

            else:

                result = response.json()

                status = result.get(
                    "status"
                )


                # =================================================
                # APPROVED
                # =================================================

                if status == "APPROVED":

                    st.success(
                        "✅ Auditor Approved"
                    )

                    st.write(
                        result.get("response")
                    )

                    with st.expander(
                        "View Audit Information"
                    ):

                        st.json(result)


                # =================================================
                # CORRECTED
                # =================================================

                elif status == "CORRECTED":

                    st.success(
                        "✅ Response corrected and approved"
                    )

                    st.write(
                        result.get("response")
                    )

                    with st.expander(
                        "View SafeCart Process"
                    ):

                        st.json(result)


                # =================================================
                # ESCALATED
                # =================================================

                elif status == "ESCALATED":

                    st.warning(
                        "⚠️ Human review required."
                    )

                    st.write(
                        result.get("response")
                    )

                    with st.expander(
                        "Escalation Information"
                    ):

                        st.json(result)


                # =================================================
                # BLOCKED
                # =================================================

                elif status == "BLOCKED":

                    st.error(
                        "🚫 Worker response blocked by Auditor."
                    )

                    st.write(
                        result.get("response")
                    )

                    with st.expander(
                        "Audit Errors"
                    ):

                        st.json(result)


                # =================================================
                # BACKEND ERROR
                # =================================================

                elif status == "ERROR":

                    st.error(
                        result.get(
                            "response",
                            "SafeCart returned an error."
                        )
                    )


                # =================================================
                # UNKNOWN STATUS
                # =================================================

                else:

                    st.error(
                        "SafeCart returned an unexpected status."
                    )

                    st.json(result)


        # =====================================================
        # CONNECTION ERROR
        # =====================================================

        except requests.exceptions.ConnectionError:

            st.error(
                "Cannot connect to SafeCart backend. "
                "Start FastAPI first."
            )


        # =====================================================
        # TIMEOUT ERROR
        # =====================================================

        except requests.exceptions.Timeout:

            st.error(
                "Backend request timed out."
            )


        # =====================================================
        # OTHER ERROR
        # =====================================================

        except Exception as e:

            st.error(
                f"Unexpected error: {str(e)}"
            )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("🛒 SafeCart")

    st.write(
        "### Architecture"
    )

    st.write(
        """
        Customer
        ->
        Streamlit Frontend
        ->
        FastAPI Backend
        ->
        Worker AI
        ->
        Pandas Database
        ->
        Auditor AI
        ->
        Approve / Correct
        ->
        Customer
        """
    )

    st.divider()

    st.write(
        "### Safety Rules"
    )

    st.write(
        """
        • Never invent database values

        • Never approve an invalid refund

        • Never promise an unavailable delivery date

        • Auditor must approve responses

        • Maximum 3 correction attempts
        """
    )