import { google } from 'googleapis';

export async function getTrendsData() {
    let serviceAccount: Record<string, any> = {};
    try {
        serviceAccount = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_JSON || '{}');
    } catch (e) {
        console.error("Failed to parse GOOGLE_SERVICE_ACCOUNT_JSON:", e);
        // Fallback to empty -> will trigger missing credentials check below
        serviceAccount = {};
    }

    const sheetId = process.env.SHEET_ID;

    // Check for essential fields (project_id) or just existence of keys
    if (!serviceAccount['project_id'] || !sheetId) {
        console.warn("Missing Google Sheets credentials or Sheet ID.");
        return {
            lastUpdated: new Date().toISOString(),
            generations: {
                "Gen Z": [],
                "Millennials": [],
                "Gen Alpha": [],
                "General": []
            }
        };
    }

    try {
        const auth = new google.auth.GoogleAuth({
            credentials: serviceAccount,
            scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
        });

        const sheets = google.sheets({ version: 'v4', auth });

        // Fetch all tabs
        const ranges = ["Gen Z!A2:G", "Millennials!A2:G", "Gen Alpha!A2:G", "General!A2:G"];
        const response = await sheets.spreadsheets.values.batchGet({
            spreadsheetId: sheetId,
            ranges: ranges,
        });

        const data = response.data.valueRanges;
        const result: Record<string, any[]> = {};

        const genMap = ["Gen Z", "Millennials", "Gen Alpha", "General"];

        data?.forEach((range, index) => {
            const genName = genMap[index];
            const rows = range.values || [];
            // Row format: [Date, Trend, Source, URL, Raw Text]
            result[genName] = rows.map(row => ({
                date: row[0],
                trend: row[1],
                source: row[2],
                url: row[3],
                raw_text: row[4],
                score: parseInt(row[5] || "0", 10),
                metric: row[6] || ""
            })).reverse(); // Newest first
        });

        return {
            lastUpdated: new Date().toISOString(),
            generations: result
        };

    } catch (error) {
        console.error("Error fetching sheets data:", error);
        // RETURN VALID EMPTY DATA ON ERROR to prevent app crash
        return {
            lastUpdated: new Date().toISOString(),
            generations: {
                "Gen Z": [],
                "Millennials": [],
                "Gen Alpha": [],
                "General": []
            },
            error: "Failed to fetch data"
        };
    }
}

let KEY_CACHE: string[] | null = null;
let KEY_CACHE_TIME = 0;
const KEY_CACHE_TTL = 1000 * 60 * 10; // 10 minutes

export async function getApiKeys(): Promise<string[]> {
    const now = Date.now();
    if (KEY_CACHE && (now - KEY_CACHE_TIME < KEY_CACHE_TTL)) {
        return KEY_CACHE;
    }

    let serviceAccount: Record<string, any> = {};
    try {
        serviceAccount = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_JSON || '{}');
    } catch (e) {
        console.error("Failed to parse GOOGLE_SERVICE_ACCOUNT_JSON:", e);
        return [];
    }

    const sheetId = process.env.SHEET_ID;

    if (!serviceAccount['project_id'] || !sheetId) {
        return [];
    }

    try {
        const auth = new google.auth.GoogleAuth({
            credentials: serviceAccount,
            scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
        });

        const sheets = google.sheets({ version: 'v4', auth });

        // Fetch ApiKeys tab
        const response = await sheets.spreadsheets.values.get({
            spreadsheetId: sheetId,
            range: "ApiKeys!A2:D", // ApiKey, AppName, OwnerEmail, Active
        });

        const rows = response.data.values || [];
        const validKeys: string[] = [];

        rows.forEach(row => {
            const [apiKey, _appName, _email, active] = row;
            // distinct check for "TRUE" string or logic
            if (apiKey && active && active.toString().toUpperCase() === 'TRUE') {
                validKeys.push(apiKey);
            }
        });

        KEY_CACHE = validKeys;
        KEY_CACHE_TIME = now;

        return validKeys;

    } catch (error) {
        console.error("Error fetching API keys:", error);
        return [];
    }
}
