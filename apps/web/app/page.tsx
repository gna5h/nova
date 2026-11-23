"use client";

import { useQuery } from "@tanstack/react-query";
import { checkHealth } from "@/lib/api/client";

export default function Home() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: checkHealth,
    retry: 1,
  });

  const status = isLoading
    ? "loading\u2026"
    : isError
      ? "offline"
      : data?.status === "ok"
        ? "online"
        : "offline";

  return (
    <main className="flex min-h-screen items-center justify-center">
      <p className="text-lg font-medium">
        API: <span>{status}</span>
      </p>
    </main>
  );
}
