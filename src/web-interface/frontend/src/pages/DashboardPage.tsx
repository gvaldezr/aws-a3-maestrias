import React, { useCallback, useEffect, useRef, useState } from "react";
import { UploadSection } from "../components/UploadSection";
import { SubjectTable } from "../components/SubjectTable";

const WEB_API = "https://z1px5977b8.execute-api.us-east-1.amazonaws.com/prod";
const CHECKPOINT_API = "https://zcf0tiic2e.execute-api.us-east-1.amazonaws.com/prod";

interface Props {
  token: string;
  onCheckpoint: (subjectId: string) => void;
}

export function DashboardPage({ token, onCheckpoint }: Props) {
  const headers = { Authorization: token, "Content-Type": "application/json" };

  return (
    <div>
      <UploadSection
        onUploadSuccess={(ids) => alert(`Documentos cargados. IDs: ${ids.join(", ")}. El pipeline se ejecutara automaticamente.`)}
        apiUrl={WEB_API}
        headers={headers}
      />
      <hr style={{ margin: "30px 0" }} />
      <SubjectTable
        apiUrl={WEB_API}
        checkpointApiUrl={CHECKPOINT_API}
        headers={headers}
        onCheckpoint={onCheckpoint}
      />
    </div>
  );
}
