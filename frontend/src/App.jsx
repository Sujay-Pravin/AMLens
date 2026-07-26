import { useEffect, useState } from "react";
import Header from "./components/Header";
import UploadPanel from "./components/UploadPanel";
import ResultsDashboard from "./components/ResultsDashboard";
import { getHealth, runInvestigation } from "./api";

function App() {
  const [file, setFile] = useState(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [backendState, setBackendState] = useState({ status: "pending", detail: "" });

  useEffect(() => {
    let cancelled = false;
    getHealth()
      .then(() => {
        if (!cancelled) setBackendState({ status: "ok", detail: "" });
      })
      .catch((err) => {
        if (!cancelled) setBackendState({ status: "error", detail: err.message });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleRun() {
    if (!file) {
      setError("Please choose a CSV file first.");
      return;
    }
    setError(null);
    setLoading(true);
    setResult(null);
    try {
      const data = await runInvestigation(file, query.trim());
      setResult(data);
    } catch (err) {
      setError(err.message || "Investigation failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <Header backendState={backendState} />

      <UploadPanel
        file={file}
        onFileChange={setFile}
        query={query}
        onQueryChange={setQuery}
        onRun={handleRun}
        loading={loading}
      />

      {error && <div className="error-banner">⚠ {error}</div>}

      {loading && (
        <div className="progress-banner">
          <span className="spinner" />
          Running investigation — validation, rules, ML + SHAP, risk fusion, graph analytics…
        </div>
      )}

      {result && <ResultsDashboard data={result} />}

      <p className="footer-note">AMLens — AI-powered AML investigation dashboard</p>
    </div>
  );
}

export default App;
