"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { CompanyDetailContent } from "@/components/company/CompanyDetailContent";

export default function CompanyDetailPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = params.symbol;

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-6 px-6 py-10">
      <div>
        <Link href="/" className="text-sm text-zinc-500 underline hover:no-underline">
          ← Back to screener
        </Link>
        <h1 className="mt-1 text-2xl font-semibold">{symbol}</h1>
      </div>

      {/* Keyed by symbol so navigating between two company pages remounts
       * this view and its state resets naturally. */}
      <CompanyDetailContent key={symbol} symbol={symbol} />
    </main>
  );
}
