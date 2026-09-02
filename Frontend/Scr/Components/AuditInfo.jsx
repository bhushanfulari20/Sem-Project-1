function AuditInfo({
  result,
}) {

  let title =
    "View Audit Information";


  if (result.status === "CORRECTED") {
    title =
      "View SafeCart Process";
  }

  if (result.status === "ESCALATED") {
    title =
      "Escalation Information";
  }

  if (result.status === "BLOCKED") {
    title =
      "Audit Errors";
  }


  return (
    <section className="audit-card">

      <details>

        <summary>
          🔎 {title}
        </summary>

        <pre>
          {JSON.stringify(
            result,
            null,
            2
          )}
        </pre>

      </details>

    </section>
  );
}

export default AuditInfo;