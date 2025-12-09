import { getTrendsData } from "@/lib/google_sheets";
import { TrendsData } from "@/types";

// In-memory cache fallback (Next.js has its own caching, but this is a safety layer)
let CACHE: TrendsData | null = null;
let CACHE_TIME = 0;
const CACHE_TTL = 1000 * 60 * 15; // 15 minutes

export class TrendService {
    static async getTrends(): Promise<TrendsData> {
        const now = Date.now();

        // Simple caching mechanism
        if (CACHE && (now - CACHE_TIME < CACHE_TTL)) {
            return CACHE;
        }

        const data = await getTrendsData();

        // Update cache
        if (!data.error) {
            CACHE = data as TrendsData;
            CACHE_TIME = now;
        }

        return data as TrendsData;
    }

    static filterTrends(data: TrendsData, timeframe: 'day' | 'week' | 'month') {
        // This logic filters the *already fetched* data.
        // Since our Sheets data is likely small (hundreds of rows), filtering in-memory is fine.

        const now = new Date();
        const oneDay = 24 * 60 * 60 * 1000;

        let cutoff = new Date(now.getTime() - oneDay); // Default Day

        if (timeframe === 'week') {
            cutoff = new Date(now.getTime() - oneDay * 7);
        } else if (timeframe === 'month') {
            cutoff = new Date(now.getTime() - oneDay * 30);
        }

        // Deep copy to avoid mutating cache
        const filteredGenerations: Record<string, any[]> = {};

        Object.keys(data.generations).forEach(gen => {
            const filtered = data.generations[gen].filter(t => {
                const tDate = new Date(t.date);
                return tDate >= cutoff;
            });
            filteredGenerations[gen] = TrendService.shuffle(filtered);
        });

        return {
            ...data,
            generations: filteredGenerations
        };
    }

    // Helper to shuffle array (Fisher-Yates)
    static shuffle(array: any[]) {
        let currentIndex = array.length, randomIndex;

        while (currentIndex != 0) {
            randomIndex = Math.floor(Math.random() * currentIndex);
            currentIndex--;
            [array[currentIndex], array[randomIndex]] = [
                array[randomIndex], array[currentIndex]];
        }

        return array;
    }
}
