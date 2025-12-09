import { google } from 'googleapis';

export async function getTrendsData() {
    let serviceAccount = {};
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
        const ranges = ["Gen Z!A2:E", "Millennials!A2:E", "Gen Alpha!A2:E", "General!A2:E"];
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
                raw_text: row[4]
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
