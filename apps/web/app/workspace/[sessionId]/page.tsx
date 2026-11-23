"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import type { ProfileResult, ResultTable } from "@/lib/api/client";

function FactsPanel({ facts }: { facts: Record<string, unknown> }) {
  return (
    <div className="rounded-lg border border-gray-200 p-4">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
        Dataset Facts
      </h2>
      <dl className="grid grid-cols-2 gap-x-6 gap-y-2">
        {Object.entries(facts).map(([key, value]) => (
          <div key={key}>
            <dt className="text-xs text-gray-400">{key.replace(/_/g, " ")}</dt>
            <dd className="text-sm font-medium">{String(value)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function ProfileTable({ table }: { table: ResultTable }) {
  return (
    <div className="rounded-lg border border-gray-200 overflow-auto">
      <h2 className="border-b border-gray-200 px-4 py-3 text-sm font-semibold">
        {table.title}
      </h2>
      <table className="w-full text-left text-sm">
        <thead className="bg-gray-50">
          <tr>
            {table.columns.map((col) => (
              <th
                key={col}
                className="px-3 py-2 text-xs font-medium uppercase tracking-wide text-gray-500"
              >
                {col.replace(/_/g, " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {table.rows.map((row, i) => (
            <tr key={i} className="hover:bg-gray-50">
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-2 text-gray-700">
                  {Array.isArray(cell) ? cell.join(", ") : String(cell ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function WorkspacePage() {
  const params = useParams();
  const sessionId = params.sessionId as string;
  const [profile, setProfile] = useState<ProfileResult | null>(null);

  useEffect(() => {
    const raw = sessionStorage.getItem(`profile:${sessionId}`);
    if (raw) {
      try {
        setProfile(JSON.parse(raw) as ProfileResult);
      } catch {
        // ignore parse errors
      }
    }
  }, [sessionId]);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-80 flex-shrink-0 border-r border-gray-200 p-4">
        <p className="text-sm font-medium text-gray-400">
          Chat &mdash; coming in M5
        </p>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-6 flex flex-col gap-6">
        {profile ? (
          <>
            <FactsPanel facts={profile.facts} />
            {profile.tables[0] && (
              <ProfileTable table={profile.tables[0]} />
            )}
          </>
        ) : (
          <p className="text-gray-400">Loading profile\u2026</p>
        )}
      </main>
    </div>
  );
}
