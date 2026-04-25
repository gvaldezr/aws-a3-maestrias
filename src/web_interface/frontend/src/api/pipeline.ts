/**
 * API client para el pipeline académico — U7: Interfaz Web.
 * Todas las llamadas incluyen el JWT de Cognito en el header Authorization.
 */

const API_BASE = (window as any).__API_BASE__ ?? "https://z1px5977b8.execute-api.us-east-1.amazonaws.com/prod";
const CHECKPOINT_API = (window as any).__CHECKPOINT_API__ ?? "https://zcf0tiic2e.execute-api.us-east-1.amazonaws.com/prod";

async function authHeaders(): Promise<HeadersInit> {
  // En producción, obtener el token de Cognito (Amplify Auth)
  const token = localStorage.getItem("access_token") ?? "";
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export interface PipelineStatus {
  subject_id: string;
  subject_name: string;
  program_name: string;
  current_state: string;
  updated_at: string;
  pending_approval: boolean;
  canvas_course_url?: string;
}

export interface DashboardData {
  subjects: PipelineStatus[];
  total: number;
  pending_approval_count: number;
  published_count: number;
  failed_count: number;
}

export interface UploadResponse {
  subject_id: string;
  upload_url: string;
  s3_key: string;
  expires_in_seconds: number;
}

export async function getDashboard(): Promise<DashboardData> {
  const res = await fetch(`${API_BASE}/api/subjects`, {
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(`Dashboard error: ${res.status}`);
  return res.json();
}

export async function requestUploadUrl(
  fileName: string,
  fileSizeBytes: number,
  contentType: string
): Promise<UploadResponse> {
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify({ file_name: fileName, file_size_bytes: fileSizeBytes, content_type: contentType }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.errors?.join(", ") ?? `Upload error: ${res.status}`);
  }
  return res.json();
}

export async function uploadFileToS3(uploadUrl: string, file: File): Promise<void> {
  const res = await fetch(uploadUrl, {
    method: "PUT",
    headers: { "Content-Type": file.type },
    body: file,
  });
  if (!res.ok) throw new Error(`S3 upload failed: ${res.status}`);
}

export async function getCheckpointSummary(subjectId: string): Promise<Record<string, unknown>> {
  const res = await fetch(`${CHECKPOINT_API}/subjects/${subjectId}/checkpoint`, {
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(`Checkpoint error: ${res.status}`);
  return res.json();
}

export async function submitDecision(
  subjectId: string,
  decision: "APPROVED" | "REJECTED" | "EDIT",
  comments?: string,
  manualEdits?: Record<string, unknown>
): Promise<void> {
  const res = await fetch(`${CHECKPOINT_API}/subjects/${subjectId}/decision`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify({ decision, comments, manual_edits: manualEdits }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error ?? `Decision error: ${res.status}`);
  }
}
