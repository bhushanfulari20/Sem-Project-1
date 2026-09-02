function ResponseCard({
  result,
}) {

  const status =
    result.status;


  const config = {

    APPROVED: {
      className: "success",
      title: "✅ Auditor Approved",
    },

    CORRECTED: {
      className: "success",
      title:
        "✅ Response corrected and approved",
    },

    ESCALATED: {
      className: "warning",
      title:
        "⚠️ Human review required.",
    },

    BLOCKED: {
      className: "blocked",
      title:
        "🚫 Worker response blocked by Auditor.",
    },

    ERROR: {
      className: "error",
      title:
        "❌ SafeCart returned an error.",
    },

  };


  const current =
    config[status] || {
      className: "error",
      title:
        "❌ SafeCart returned an unexpected status.",
    };


  return (
    <section className="result-card">

      <h2>
        SafeCart Response
      </h2>


      <div
        className={
          `alert ${current.className}`
        }
      >
        {current.title}
      </div>


      <div className="status-pill">

        STATUS:{" "}
        {status || "UNKNOWN"}

      </div>


      <div className="response">

        {result.response ||
          "No response returned."}

      </div>

    </section>
  );
}

export default ResponseCard;