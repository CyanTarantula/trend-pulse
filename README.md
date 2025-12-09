# Trend Pulse

Trend Pulse is a real-time social signal identifier that aggregates trending topics across generations (Gen Z, Millennials, Gen Alpha) from various sources like Google Trends, Reddit, and RSS feeds.

## Features

- **Multi-Source Aggregation**: Fetches trends from Google Trends, Reddit (r/GenZ), and demographic-specific RSS feeds.
- **Semantic Keyword Extraction**: Uses AI (`sentence-transformers`) to extract concise, relevant topics from noisy headlines.
- **Generation Filtering**: Categorizes trends by generation (Gen Z, Millennials, Gen Alpha).
- **Modern UI**: A sleek, dark-mode Next.js frontend to visualize trends.
- **Automated Updates**: GitHub Actions workflow to run the aggregator daily.

## Architecture

- **Frontend**: Next.js (App Router), Tailwind CSS, Framer Motion.
- **Backend/Scripts**: Python for data fetching and processing (`get_trends.py`).
- **Data Store**: Google Sheets (used as a lightweight CMS/Database).

## Setup & Local Development

### Prerequisites

- Node.js (v18+)
- Python (3.9+)
- Google Cloud Service Account (for Sheets API)

### Installation

1.  **Clone the repo**
    ```bash
    git clone https://github.com/CyanTarantula/trend-pulse.git
    cd trend-pulse
    ```

2.  **Frontend Setup**
    ```bash
    cd src/web
    npm install
    # Create .env.local with credentials (SHEET_ID, GOOGLE_SERVICE_ACCOUNT_JSON)
    npm run dev
    ```

3.  **Python Scripts Setup**
    ```bash
    cd src/scripts
    pip install -r requirements.txt
    python get_trends.py # To fetch initial data
    ```

## Deployment

- **Frontend**: Deploy `src/web` to Vercel.
- **Automation**: The `.github/workflows/daily_update.yml` runs the Python script daily to update the Google Sheet.


## Environment Variables

You must configure the following environment variables in both **Vercel** (for the frontend) and **GitHub Actions** (for the daily aggregator script).

| Variable Name | Description |
| :--- | :--- |
| `SHEET_ID` | The ID of the Google Sheet acting as the database. |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | The full JSON content of your Google Service Account key. |

### How to set them:

1.  **Vercel**: Go to **Settings** > **Environment Variables**. Add both keys.
2.  **GitHub**: Go to your Repo **Settings** > **Secrets and variables** > **Actions**. Add them as **Repository secrets**.

