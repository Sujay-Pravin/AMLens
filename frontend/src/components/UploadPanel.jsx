const QUERY_HINTS = [
  "Find structuring patterns in the last 30 days",
  "Is customer 4521 suspicious?",
  "Show the riskiest accounts",
  "Summarize wire transfers over $10,000",
];

function UploadPanel({ file, onFileChange, query, onQueryChange, onRun, loading }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Run an investigation</h2>
        <span className="panel-tag">Step 1</span>
      </div>

      <div className="upload-grid">
        <label className="file-drop">
          <input
            type="file"
            accept=".csv"
            onChange={(e) => onFileChange(e.target.files?.[0] ?? null)}
          />
          <span>📄</span>
          <span className="filename">{file ? file.name : "Choose transaction CSV"}</span>
        </label>

        <input
          className="query-input"
          type="text"
          placeholder='Ask something, e.g. "Find structuring patterns in the last 30 days"'
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !loading) onRun();
          }}
        />

        <button type="button" className="btn btn-accent" onClick={onRun} disabled={loading}>
          {loading ? "Running…" : "Run Investigation"}
        </button>
      </div>

      <div className="hint-row">
        {QUERY_HINTS.map((hint) => (
          <button
            key={hint}
            type="button"
            className="hint-chip"
            onClick={() => onQueryChange(hint)}
          >
            {hint}
          </button>
        ))}
      </div>
    </div>
  );
}

export default UploadPanel;
