function Sidebar() {

  const architecture = [

    "👤 Customer",

    "⚛️ React Frontend",

    "⚡ FastAPI Backend",

    "🤖 Worker AI",

    "🐼 Pandas Database",

    "🕵️ Auditor AI",

    "✅ Approve / Correct",

    "👤 Customer",

  ];


  const rules = [

    "Never invent database values",

    "Never approve an invalid refund",

    "Never promise an unavailable delivery date",

    "Auditor must approve responses",

    "Maximum 3 correction attempts",

  ];


  return (
    <aside className="sidebar">

      <h2>
        🛒 SafeCart
      </h2>


      <h3>
        Architecture
      </h3>


      <div className="architecture">

        {architecture.map(
          (item, index) => (

            <div
              key={item}
              style={{
                width: "100%",
              }}
            >

              <div
                className="architecture-node"
              >
                {item}
              </div>


              {index <
                architecture.length - 1 && (

                <div className="arrow">
                  ↓
                </div>

              )}

            </div>

          )
        )}

      </div>


      <hr />


      <h3>
        Safety Rules
      </h3>


      <ul>

        {rules.map(
          (rule) => (

            <li key={rule}>
              ✓ {rule}
            </li>

          )
        )}

      </ul>

    </aside>
  );
}

export default Sidebar;