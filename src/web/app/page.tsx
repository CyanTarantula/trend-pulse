import { TrendService } from "@/services/TrendService";
import ShinyText from "@/components/react-bits/ShinyText";
import SpotlightCard from "@/components/react-bits/SpotlightCard";
import Link from "next/link";
import { cn } from "@/lib/utils";

// Server Component
export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ gen?: string; time?: string }>;
}) {
  const params = await searchParams;
  const gen = params.gen || "Gen Z";
  const time = (params.time || "day") as "day" | "week" | "month";

  // Fetch and Filter
  const allTrends = await TrendService.getTrends();
  const filteredData = TrendService.filterTrends(allTrends, time);
  const currentGenTrends = filteredData.generations[gen] || [];

  const generations = ["Gen Z", "Millennials", "Gen Alpha", "General"];
  const timeframes = ["day", "week", "month"];

  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-12 relative">
      {/* Background Gradient */}
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900/20 via-black to-black pointer-events-none" />

      {/* Header */}
      <header className="w-full max-w-5xl flex flex-col items-center mb-12 space-y-4">
        <ShinyText
          text="Trend Pulse"
          className="text-5xl md:text-7xl font-bold tracking-tighter"
          speed={5}
        />
        <p className="text-neutral-400 text-lg">
          Real-time social signals across generations
        </p>
      </header>

      {/* Filters (Generation) */}
      <div className="flex flex-wrap gap-2 mb-8 justify-center">
        {generations.map((g) => (
          <Link
            key={g}
            href={`/?gen=${encodeURIComponent(g)}&time=${time}`}
            className={cn(
              "px-6 py-2 rounded-full text-sm font-medium transition-all duration-300 border",
              gen === g
                ? "bg-white text-black border-white shadow-[0_0_20px_rgba(255,255,255,0.3)]"
                : "bg-transparent text-neutral-400 border-neutral-800 hover:border-neutral-600 hover:text-white"
            )}
          >
            {g}
          </Link>
        ))}
      </div>

      {/* Filters (Time) */}
      <div className="flex gap-4 mb-12 text-sm text-neutral-500">
        {timeframes.map((t) => (
          <Link
            key={t}
            href={`/?gen=${encodeURIComponent(gen)}&time=${t}`}
            className={cn(
              "uppercase tracking-widest hover:text-white transition-colors",
              time === t ? "text-white underline underline-offset-8 decoration-2 decoration-indigo-500" : ""
            )}
          >
            {t}
          </Link>
        ))}
      </div>

      {/* Grid */}
      <div className="w-full max-w-6xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {currentGenTrends.length > 0 ? (
          currentGenTrends.map((trend, idx) => (
            <div key={idx} className="h-48">
              <a href={trend.url} target="_blank" rel="noopener noreferrer" className="block h-full">
                <SpotlightCard className="p-6 flex flex-col justify-between group hover:border-indigo-500/50 transition-colors">
                  <div>
                    <div className="flex justify-between items-start mb-4">
                      <span className="text-xs font-mono text-indigo-400 bg-indigo-400/10 px-2 py-1 rounded">
                        {trend.source}
                      </span>
                      <span className="text-xs text-neutral-500">
                        {new Date(trend.date).toLocaleDateString()}
                      </span>
                    </div>
                    <h3 className="text-xl font-semibold text-white group-hover:text-indigo-200 transition-colors line-clamp-2">
                      {trend.trend}
                    </h3>
                  </div>
                  <div className="text-xs text-neutral-600 group-hover:text-neutral-400">
                    Tap to explore →
                  </div>
                </SpotlightCard>
              </a>
            </div>
          ))
        ) : (
          <div className="col-span-full text-center py-20 text-neutral-500">
            No trends found for this filter. Check back later or run the aggregator.
          </div>
        )}
      </div>

      <footer className="mt-20 text-neutral-600 text-sm">
        Updated: {allTrends.lastUpdated ? new Date(allTrends.lastUpdated).toLocaleString() : 'Never'}
      </footer>
    </main>
  );
}
