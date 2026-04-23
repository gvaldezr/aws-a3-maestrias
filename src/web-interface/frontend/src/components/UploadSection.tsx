/**
 * UploadSection — Carga de documentos académicos.
 * Valida formato (PDF/DOCX/XLSX) y tamaño (≤50MB) antes de cargar.
 */
import React, { useCallback, useState } from "react";
import { requestUploadUrl, uploadFileToS3 } from "../api/pipeline";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
];
const MAX_SIZE_MB = 50;

interface Props {
  onUploadSuccess: (subjectIds: string[]) => void;
}

export function UploadSection({ onUploadSuccess }: Props) {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateFile = (file: File): string | null => {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      return `Formato no soportado: ${file.name}. Use PDF, DOCX o XLSX.`;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `Archivo demasiado grande: ${file.name}. Máximo ${MAX_SIZE_MB}MB.`;
    }
    return null;
  };

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const dropped = Array.from(e.dataTransfer.files);
    const validFiles: File[] = [];
    const errors: string[] = [];
    dropped.forEach((f) => {
      const err = validateFile(f);
      if (err) errors.push(err);
      else validFiles.push(f);
    });
    if (errors.length) setError(errors.join(" | "));
    setFiles((prev) => [...prev, ...validFiles]);
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files ?? []);
    const validFiles: File[] = [];
    const errors: string[] = [];
    selected.forEach((f) => {
      const err = validateFile(f);
      if (err) errors.push(err);
      else validFiles.push(f);
    });
    if (errors.length) setError(errors.join(" | "));
    setFiles((prev) => [...prev, ...validFiles]);
  };

  const handleUpload = async () => {
    if (!files.length) return;
    setUploading(true);
    setError(null);
    const subjectIds: string[] = [];
    try {
      for (const file of files) {
        const { subject_id, upload_url } = await requestUploadUrl(file.name, file.size, file.type);
        await uploadFileToS3(upload_url, file);
        subjectIds.push(subject_id);
      }
      setFiles([]);
      onUploadSuccess(subjectIds);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al cargar archivos");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-section">
      <div
        data-testid="file-dropzone"
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="dropzone"
        role="region"
        aria-label="Zona de carga de documentos"
      >
        <p>Arrastra archivos PDF, DOCX o XLSX aquí</p>
        <input
          type="file"
          accept=".pdf,.docx,.xlsx"
          multiple
          onChange={handleFileInput}
          data-testid="file-input"
          aria-label="Seleccionar archivos"
        />
      </div>

      {files.length > 0 && (
        <ul data-testid="file-list" aria-label="Archivos seleccionados">
          {files.map((f, i) => (
            <li key={i}>{f.name} ({(f.size / 1024 / 1024).toFixed(1)}MB)</li>
          ))}
        </ul>
      )}

      {error && (
        <p role="alert" className="error-message" data-testid="upload-error">
          {error}
        </p>
      )}

      <button
        data-testid="upload-submit-button"
        onClick={handleUpload}
        disabled={uploading || files.length === 0}
        aria-busy={uploading}
      >
        {uploading ? "Cargando..." : `Cargar ${files.length} archivo(s)`}
      </button>
    </div>
  );
}
