import { useState, useRef, useCallback } from "react";
import "./LogInputPanel.css";

const MAX_FILE_SIZE = 50 * 1024; // 50KB
const ALLOWED_TYPES = ["text/plain", "text/csv"];
const ALLOWED_EXTENSIONS = [".txt", ".csv"];
const API_URL = "http://localhost:8000/api/v1/analyze-logs";

export default function LogInputPanel() {
    const [logText, setLogText] = useState("");
    const [error, setError] = useState("");
    const [uploadStatus, setUploadStatus] = useState("idle"); // idle | loading | success | error
    const [uploadMessage, setUploadMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [apiResult, setApiResult] = useState(null);
    const [apiError, setApiError] = useState("");
    const fileInputRef = useRef(null);

    const charCount = logText.length;

    const handleTextChange = useCallback((e) => {
        setLogText(e.target.value);
        if (error) setError("");
    }, [error]);

    const handleFileUpload = useCallback((e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Reset previous state
        setError("");
        setUploadStatus("loading");
        setUploadMessage(`Reading "${file.name}"...`);

        // Validate file type
        const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
        if (!ALLOWED_TYPES.includes(file.type) && !ALLOWED_EXTENSIONS.includes(extension)) {
            setUploadStatus("error");
            setUploadMessage("Unsupported file type. Please upload a .txt or .csv file.");
            if (fileInputRef.current) fileInputRef.current.value = "";
            return;
        }

        // Validate empty file
        if (file.size === 0) {
            setUploadStatus("error");
            setUploadMessage("The uploaded file is empty.");
            if (fileInputRef.current) fileInputRef.current.value = "";
            return;
        }

        const reader = new FileReader();

        reader.onload = (event) => {
            let content = event.target?.result ?? "";

            // Truncate if over 50KB
            if (content.length > MAX_FILE_SIZE) {
                content = content.slice(0, MAX_FILE_SIZE);
                setUploadStatus("success");
                setUploadMessage(`"${file.name}" uploaded and truncated to 50KB.`);
            } else {
                setUploadStatus("success");
                setUploadMessage(`"${file.name}" uploaded successfully (${(file.size / 1024).toFixed(1)}KB).`);
            }

            setLogText(content); // Populates textarea
            if (fileInputRef.current) fileInputRef.current.value = "";
        };

        reader.onerror = () => {
            setUploadStatus("error");
            setUploadMessage("Failed to read file. Try copying and pasting the content manually.");
            if (fileInputRef.current) fileInputRef.current.value = "";
        };

        reader.readAsText(file, "UTF-8");
    }, []);

    const handleClear = useCallback(() => {
        setLogText("");
        setError("");
        setUploadStatus("idle");
        setUploadMessage("");
        setApiResult(null);
        setApiError("");
        if (fileInputRef.current) fileInputRef.current.value = "";
    }, []);

    const handleSubmit = useCallback(async () => {
        if (!logText.trim()) {
            setError("Input cannot be empty. Please paste logs or upload a file.");
            return;
        }
        setError("");
        setApiResult(null);
        setApiError("");
        setIsSubmitting(true);

        try {
            const response = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ log_data: logText, file_type: "text" }),
            });
            const json = await response.json();
            if (json.status === "success") {
                setApiResult(json.data);
            } else {
                setApiError(json.message || "Backend returned an error.");
            }
        } catch (err) {
            setApiError("Could not reach the backend. Is it running on port 8000?");
        } finally {
            setIsSubmitting(false);
        }
    }, [logText]);

    const statusClass =
        uploadStatus === "success"
            ? "upload-status success"
            : uploadStatus === "error"
                ? "upload-status error"
                : uploadStatus === "loading"
                    ? "upload-status loading"
                    : "";

    return (
        <div className="log-input-panel">
            <h2 className="panel-title">Paste or Upload Logs</h2>

            {/* File Upload */}
            <div className="file-upload-row">
                <label className="file-upload-label">
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".txt,.csv"
                        onChange={handleFileUpload}
                        className="file-input-hidden"
                        aria-label="Upload log file"
                    />
                    <span className="file-upload-btn">
                        {uploadStatus === "loading" ? "Reading..." : "📂 Upload File"}
                    </span>
                </label>
                <span className="file-types-hint">Accepts .txt and .csv</span>
            </div>

            {/* Upload Status Message */}
            {uploadStatus !== "idle" && (
                <div className={statusClass} role="status">
                    {uploadStatus === "loading" && <span className="spinner" aria-hidden="true" />}
                    {uploadMessage}
                </div>
            )}

            {/* Textarea */}
            <div className="textarea-wrapper">
                <textarea
                    className={`log-textarea${error ? " textarea-error" : ""}`}
                    value={logText}
                    onChange={handleTextChange}
                    placeholder="Paste your logs here..."
                    aria-label="Log input area"
                    spellCheck={false}
                />
                <div className="textarea-meta">
                    <span className={`char-count${charCount > MAX_FILE_SIZE ? " over-limit" : ""}`}>
                        {charCount.toLocaleString()} / {(MAX_FILE_SIZE).toLocaleString()} chars
                    </span>
                </div>
            </div>

            {/* Validation Error */}
            {error && (
                <p className="validation-error" role="alert">
                    ⚠️ {error}
                </p>
            )}

            {/* Action Row */}
            <div className="action-row">
                <button
                    className="btn btn-clear"
                    onClick={handleClear}
                    disabled={(!logText && uploadStatus === "idle") || isSubmitting}
                    type="button"
                >
                    Clear
                </button>
                <button
                    className="btn btn-submit"
                    onClick={handleSubmit}
                    disabled={isSubmitting}
                    type="button"
                >
                    {isSubmitting ? "Analyzing..." : "Analyze Logs →"}
                </button>
            </div>

            {/* API Error */}
            {apiError && (
                <div className="upload-status error" role="alert" style={{ marginTop: "16px" }}>
                    ⚠️ {apiError}
                </div>
            )}

            {/* API Result */}
            {apiResult && (
                <div className="api-result" aria-live="polite">
                    <h3 className="result-title">Analysis Results</h3>
                    <div className="result-metrics">
                        <div className="metric">
                            <span className="metric-label">Workflows Detected</span>
                            <span className="metric-value">{apiResult.workflows_detected}</span>
                        </div>
                        <div className="metric">
                            <span className="metric-label">Confidence</span>
                            <span className="metric-value">{apiResult.primary_workflow?.confidence_score}%</span>
                        </div>
                        <div className="metric">
                            <span className="metric-label">Time Saved</span>
                            <span className="metric-value">{apiResult.primary_workflow?.estimated_time_saved_mins_per_week} mins/wk</span>
                        </div>
                    </div>
                    {apiResult.primary_workflow?.steps?.length > 0 && (
                        <div className="result-steps">
                            <span className="steps-label">Workflow:</span>
                            <span>{apiResult.primary_workflow.steps.join(" ➡️ ")}</span>
                        </div>
                    )}
                    {apiResult.primary_workflow?.automation_suggestion && (
                        <div className="result-suggestion">
                            💡 {apiResult.primary_workflow.automation_suggestion}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
