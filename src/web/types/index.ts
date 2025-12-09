export interface Trend {
    date: string;
    trend: string;
    source: string;
    url: string;
    raw_text: string;
    score: number;
    metric: string;
}

export interface TrendsData {
    lastUpdated: string;
    generations: {
        [key: string]: Trend[];
    };
    error?: string;
}
