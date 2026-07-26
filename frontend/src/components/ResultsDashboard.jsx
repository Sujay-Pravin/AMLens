import Badge from "./Badge";

const TOOL_LABELS = {
  validation: "Validation",
  eda: "EDA",
  rules: "Rule Engine",
  ml: "ML",
  fusion: "Risk Fusion",
  graph: "Graph",
};

function TraceRow({ trace }) {
  return (
    <div className="trace-row">
      {Object.entries(trace || {}).map(([tool, ran]) => (
        <span key={tool} className={`trace-item ${ran ? "ran" : "skipped"}`}>
          {ran ? "✓" : "✗"} {TOOL_LABELS[tool] || tool}
        </span>
      ))}
    </div>
  );
}

function ChipList({ items }) {
  if (!items || items.length === 0) return <span className="empty-note">none</span>;
  return (
    <div className="chip-list">
      {items.map((item) => (
        <span className="chip" key={item}>
          {item}
        </span>
      ))}
    </div>
  );
}

function TopTransactionsTable({ rows }) {
  if (!rows || rows.length === 0) return null;
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Top Suspicious Transactions ({rows.length})</h2>
        <span className="panel-tag">Ranked</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Row</th>
              <th>Sender</th>
              <th>Receiver</th>
              <th>Amount</th>
              <th>Risk</th>
              <th>Score</th>
              <th>Fraud Prob.</th>
              <th>Triggered Rules</th>
              <th>Explanation</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr key={t.row_index}>
                <td>{t.row_index}</td>
                <td>{t.sender_entity_id}</td>
                <td>{t.receiver_entity_id}</td>
                <td>{t.amount_paid.toLocaleString()}</td>
                <td>
                  <Badge level={t.risk_level} />
                </td>
                <td>{t.risk_score.toFixed(3)}</td>
                <td>{(t.fraud_probability * 100).toFixed(2)}%</td>
                <td style={{ whiteSpace: "normal", minWidth: "200px" }}>{t.triggered_rules.join(", ") || "none"}</td>
                <td style={{ whiteSpace: "normal", minWidth: "360px" }}>{t.explanation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ResultsDashboard({ data }) {
  const { parsed_intent: intent, filters_applied: filters } = data;

  return (
    <>
      <div className="panel">
        <div className="panel-header">
          <h2>Query</h2>
          <span className="panel-tag">{data.filename}</span>
        </div>
        <div className="kv-grid">
          <div className="kv-item">
            <div className="kv-label">Query</div>
            <div className="kv-value" style={{ fontSize: "0.95rem" }}>
              {data.query || "—"}
            </div>
          </div>
          <div className="kv-item">
            <div className="kv-label">Parsed intent</div>
            <div className="kv-value" style={{ fontSize: "0.95rem" }}>
              {intent?.intent || "unknown"}
              {intent?.aml_pattern ? ` (${intent.aml_pattern})` : ""}
            </div>
          </div>
          <div className="kv-item">
            <div className="kv-label">Transaction type</div>
            <div className="kv-value" style={{ fontSize: "0.95rem" }}>
              {intent?.transaction_type || "—"}
            </div>
          </div>
          <div className="kv-item">
            <div className="kv-label">Filters applied</div>
            <div className="kv-value" style={{ fontSize: "0.85rem" }}>
              {Object.keys(filters || {}).length ? JSON.stringify(filters) : "none"}
            </div>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2>Execution Plan</h2>
          <span className="panel-tag">Trace</span>
        </div>
        <TraceRow trace={data.execution_trace} />
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2>Validation Summary</h2>
        </div>
        <div className="kv-grid">
          <div className="kv-item">
            <div className="kv-label">Rows</div>
            <div className="kv-value">{data.validation.total_rows}</div>
          </div>
          <div className="kv-item">
            <div className="kv-label">Columns</div>
            <div className="kv-value">{data.validation.total_columns}</div>
          </div>
          <div className="kv-item">
            <div className="kv-label">Duplicates removed</div>
            <div className="kv-value">{data.validation.duplicate_rows}</div>
          </div>
          <div className="kv-item">
            <div className="kv-label">Missing columns</div>
            <div className="kv-value" style={{ fontSize: "0.85rem" }}>
              {data.validation.missing_columns.length ? data.validation.missing_columns.join(", ") : "none"}
            </div>
          </div>
        </div>
      </div>

      {data.eda && (
        <div className="panel">
          <div className="panel-header">
            <h2>EDA Summary</h2>
          </div>
          <div className="kv-grid">
            <div className="kv-item">
              <div className="kv-label">Rows analyzed</div>
              <div className="kv-value">{data.eda.summary?.rows ?? "—"}</div>
            </div>
            <div className="kv-item">
              <div className="kv-label">Columns</div>
              <div className="kv-value">{data.eda.summary?.columns ?? "—"}</div>
            </div>
            <div className="kv-item" style={{ gridColumn: "1 / -1" }}>
              <div className="kv-label">Class distribution (is_laundering)</div>
              <div className="kv-value" style={{ fontSize: "0.9rem" }}>
                {JSON.stringify(data.eda.class_distribution)}
              </div>
            </div>
          </div>
        </div>
      )}

      {data.risk && (
        <div className="panel">
          <div className="panel-header">
            <h2>Risk Assessment</h2>
            <Badge level={data.risk.risk_level} />
          </div>
          <div className="kv-grid">
            <div className="kv-item">
              <div className="kv-label">Final score</div>
              <div className="kv-value">{data.risk.final_score.toFixed(3)}</div>
            </div>
            <div className="kv-item">
              <div className="kv-label">Decision</div>
              <div className="kv-value" style={{ fontSize: "0.95rem" }}>
                {data.risk.decision}
              </div>
            </div>
            <div className="kv-item" style={{ gridColumn: "1 / -1" }}>
              <div className="kv-label">Reasons</div>
              <ChipList items={data.risk.reasons} />
            </div>
          </div>
        </div>
      )}

      <TopTransactionsTable rows={data.top_transactions} />

      {data.graph && (
        <div className="panel">
          <div className="panel-header">
            <h2>Graph Metrics</h2>
          </div>
          <div className="kv-grid">
            <div className="kv-item">
              <div className="kv-label">Accounts</div>
              <div className="kv-value">{data.graph.node_count}</div>
            </div>
            <div className="kv-item">
              <div className="kv-label">Transfers</div>
              <div className="kv-value">{data.graph.edge_count}</div>
            </div>
            <div className="kv-item">
              <div className="kv-label">Connected clusters</div>
              <div className="kv-value">{data.graph.num_components}</div>
            </div>
            <div className="kv-item">
              <div className="kv-label">Cycles found</div>
              <div className="kv-value">{data.graph.cycles.length}</div>
            </div>
          </div>
          <div style={{ marginTop: "0.9rem" }}>
            <div className="kv-label">Hub accounts</div>
            <ChipList items={data.graph.hub_accounts} />
          </div>
          <div style={{ marginTop: "0.9rem" }}>
            <div className="kv-label">Suspected mule accounts</div>
            <ChipList items={data.graph.mule_accounts} />
          </div>
        </div>
      )}

      <div className="panel">
        <div className="panel-header">
          <h2>Final AI Investigation Report</h2>
        </div>
        <p className="report-text">{data.investigation_report}</p>
        <div className="recommendation-box">Recommendation: {data.recommendation}</div>
      </div>
    </>
  );
}

export default ResultsDashboard;
