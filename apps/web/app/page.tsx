"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import {
  checkHealth,
  createSessionFromFile,
  createSessionFromSample,
  getSamples,
  type CreateSessionResponse,
  type SampleMeta,
} from "@/lib/api/client";

const MAX_FILE_BYTES = 10 * 1024 * 1024;
const ALLOWED_EXTS = [".csv", ".xlsx"];

export default function Home() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const { data: healthData, isLoading: healthLoading, isError: healthError } =
    useQuery({
      queryKey: ["health"],
      queryFn: checkHealth,
      retry: 1,
    });

  const { data: samplesData } = useQuery({
    queryKey: ["samples"],
    queryFn: getSamples,
    retry: 1,
  });

  const apiStatus = healthLoading
    ? "loading\u2026"
    : healthError
      ? "offline"
      : healthData?.status === "ok"
        ? "online"
        : "offline";

  function validateFile(file: File): string | null {
    if (file.size > MAX_FILE_BYTES) return "File must be under 10 MB.";
    const lower = file.name.toLowerCase();
    if (!ALLOWED_EXTS.some((ext) => lower.endsWith(ext)))
      return "Only .csv and .xlsx files are accepted.";
    return null;
  }

  async function handleFile(file: File) {
    const err = validateFile(file);
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    setUploading(true);
    try {
      const response: CreateSessionResponse = await createSessionFromFile(file);
      sessionStorage.setItem(
        `profile:${response.id}`,
        JSON.stringify(response.profile)
      );
      router.push(`/workspace/${response.id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed.");
      setUploading(false);
    }
  }

  async function handleSample(sample: SampleMeta) {
    setError(null);
    setUploading(true);
    try {
      const response: CreateSessionResponse = await createSessionFromSample(
        sample.name
      );
      sessionStorage.setItem(
        `profile:${response.id}`,
        JSON.stringify(response.profile)
      );
      router.push(`/workspace/${response.id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load sample.");
      setUploading(false);
    }
  }

  function onFileInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-8">
      {/* API status banner */}
      <p className="text-sm text-gray-500">
        API:{" "}
        <span
          className={
            apiStatus === "online" ? "text-green-600" : "text-red-500"
          }
        >
          {apiStatus}
        </span>
      </p>

      <h1 className="text-3xl font-bold">Nova</h1>
      <p className="text-gray-500">Upload a CSV or XLSX to get started.</p>

      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`w-full max-w-lg cursor-pointer rounded-xl border-2 border-dashed p-12 text-center transition-colors ${
          dragOver
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 hover:border-blue-400"
        }`}
      >
        <p className="text-gray-600">
          Drag &amp; drop a file here, or{" "}
          <span className="text-blue-600 underline">browse</span>
        </p>
        <p className="mt-1 text-xs text-gray-400">CSV or XLSX · max 10 MB</p>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,.xlsx"
        className="hidden"
        onChange={onFileInputChange}
      />

      {error && <p className="text-sm text-red-600">{error}</p>}

      {uploading && (
        <p className="text-sm text-blue-600">Uploading and profiling\u2026</p>
      )}

      {/* Sample buttons */}
      {samplesData && samplesData.samples.length > 0 && (
        <div className="flex flex-col items-center gap-2">
          <p className="text-sm text-gray-500">Or try a sample dataset:</p>
          <div className="flex flex-wrap gap-2 justify-center">
            {samplesData.samples.map((s) => (
              <button
                key={s.name}
                onClick={() => handleSample(s)}
                disabled={uploading}
                className="rounded-lg border border-gray-200 px-4 py-2 text-sm hover:bg-gray-50 disabled:opacity-50"
                title={s.description}
              >
                {s.name}
              </button>
            ))}
          </div>
        </div>
      )}
    </main>
  );
}
