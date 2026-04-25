import React, { useCallback, useState } from "react";

const ACCEPTED = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"];

interface Props {
  onUploadSuccess: (subjectIds: string[]) => void;
  apiUrl: string;
  headers: Record<string, string>;
}

export function UploadSection({ onUploadSuccess, apiUrl, headers }: Props) {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setFiles((prev) => [...prev, ...Array.from(e.dataTransfer.files)]);
  }, []);

  const handleUpload = async () => {
    setUploading(true); setError(null);
    const ids: string[] = [];
    try {
      for (const file of files) {
        const r = await fetch(`${apiUrl}/api/upload`, {
          method: "POST", headers,
          body: JSON.stringify({ file_name: file.name, file_size_bytes: file.size, content_type: file.type }),
        });
        const data = await r.json();
        if (!r.ok) throw new Error(data.errors?.join(", ") || data.error || "Upload failed");
        await fetch(data.upload_url, { method: "PUT", body: file, headers: { "Content-Type": file.type } });
        ids.push(data.subject_id);
      }
      setFiles([]);
      onUploadSuccess(ids);
    } catch (err: any) { setError(err.message); }
    finally { setUploading(false); }
  };

  return (
    <div>
      <h2>Cargar Documentos</h2>
      <div data-testid="file-dropzone" onDrop={handleDrop} onDragOver={(e) => e.preventDefault()}
        style={{ border: "2px dashed #1565C0", borderRadius: 8, padding: 30, textAlign: "center", background: "#f5f9ff", cursor: "pointer" }}>
        <p>Arrastra archivos PDF, DOCX o XLSX aqui</p>
        <input type="file" accept=".pdf,.docx,.xlsx" multiple data-testid="file-input"
          onChange={(e) => setFiles((prev) => [...prev, ...Array.from(e.target.files || [])])} />
      </div>
      {files.length > 0 && (
        <ul data-testid="file-list">{files.map((f, i) => <li key={i}>{f.name} ({(f.size / 1024 / 1024).toFixed(1)}MB)</li>)}</ul>
      )}
      {error && <p role="alert" style={{ color: "red" }}>{error}</p>}
      <button data-testid="upload-submit-button" onClick={handleUpload} disabled={uploading || !files.length}
        style={{ marginTop: 10, padding: "10px 24px", background: "#1565C0", color: "white", border: "none", borderRadius: 4, cursor: "pointer" }}>
        {uploading ? "Cargando..." : `Cargar ${files.length} archivo(s)`}
      </button>
    </div>
  );
}
