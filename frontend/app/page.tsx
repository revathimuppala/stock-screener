import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 px-6 py-16">
      <div>
        <h1 className="text-3xl font-semibold">FinTech Stock Screener</h1>
        <p className="mt-2 text-zinc-500">
          Screen a curated universe of large-cap stocks by valuation, sector, and dividend
          yield — with visible degradation when the data provider misbehaves.
        </p>
      </div>
      <div className="flex gap-4">
        <Link
          href="/screener"
          className="rounded bg-zinc-900 px-4 py-2 text-sm text-white dark:bg-zinc-100 dark:text-zinc-900"
        >
          Open Screener
        </Link>
        <Link href="/watchlist" className="rounded border px-4 py-2 text-sm">
          Open Watchlist
        </Link>
      </div>
    </main>
  );
}
