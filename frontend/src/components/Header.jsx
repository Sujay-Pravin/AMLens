import { API_BASE_URL } from "../api";

function Header({ backendState }) {
  const { status, detail } = backendState;
  const dotClass = status === "ok" ? "ok" : status === "error" ? "error" : "pending";
  const label = status === "ok" ? "Backend online" : status === "error" ? "Backend unreachable" : "Checking backend…";

  return (
    <header className="app-header">
      <div>
        <h1 className="app-title">
          AML<span className="accent">ens</span>
        </h1>
        <p className="app-subtitle">
          Upload a transaction CSV, ask a question, get an AI-generated AML investigation report.
        </p>
      </div>
      <div
        className="status-pill"
        title={detail ? `${API_BASE_URL} — ${detail}` : API_BASE_URL}
      >
        <span className={`status-dot ${dotClass}`} />
        {label}
      </div>
    </header>
  );
}

export default Header;
