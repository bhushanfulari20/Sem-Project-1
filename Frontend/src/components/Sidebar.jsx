function Sidebar() {

  const workflow = [

    "Customer request",

    "Frontend review",

    "FastAPI route",

    "Worker AI draft",

    "Audit and approval",

    "Final customer response",

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

      <div className="sidebar-panel-head">
        <span className="mini-label">
          System Flow
        </span>
        <h2>
          SafeCart Workflow
        </h2>
      </div>


      <div className="architecture">

        {workflow.map(
          (item, index) => (

            <div
              key={item}
              className="workflow-step"
            >

              <div className="step-index">
                {index + 1}
              </div>

              <div className="step-label">
                {item}
              </div>

            </div>

          )
        )}

      </div>


      <hr />


      <div className="sidebar-panel-head compact">
        <span className="mini-label">
          Guardrails
        </span>
        <h3>
          Safety Rules
        </h3>
      </div>


      <ul className="rule-list">

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