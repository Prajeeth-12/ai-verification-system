import axios, { AxiosError } from "axios";
import type {
  UploadResponse,
  ProcessCompleteResponse,
  VerificationResult,
} from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  timeout: 120000,
  headers: {
    "Content-Type": "application/json",
  },
});

export async function uploadDocument(file: File, onProgress?: (progress: number) => void): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await axios.post(
    `${api.defaults.baseURL}/upload`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (e.total && onProgress) {
          onProgress(Math.round((e.loaded * 100) / e.total));
        }
      },
    }
  );
  return response.data;
}

export async function processComplete(
  fileId: string,
  filename: string
): Promise<ProcessCompleteResponse> {
  const response = await api.post("/process-complete", {
    file_id: fileId,
    filename,
  });
  return response.data;
}

export async function semanticVerify(documentIds: string[]): Promise<VerificationResult> {
  const response = await api.post("/semantic-verify", {
    document_ids: documentIds,
  });
  return response.data;
}

export function getReportDownloadUrl(filename: string): string {
  return `${api.defaults.baseURL}/download/${filename}`;
}

export function handleApiError(error: unknown): string {
  if (error instanceof AxiosError) {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    if (error.response?.data?.message) {
      return error.response.data.message;
    }
    if (error.code === "ECONNREFUSED") {
      return "Unable to connect to the server. Please ensure the backend is running.";
    }
    if (error.code === "ERR_NETWORK") {
      return "Network error. Please check your connection and try again.";
    }
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "An unexpected error occurred.";
}

export default api;
