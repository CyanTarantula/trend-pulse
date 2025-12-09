import os
import time
import json
import logging
import datetime
import re
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load env from web directory
env_path = os.path.join(os.path.dirname(__file__), "../../src/web/.env.local")
loaded = load_dotenv(env_path, verbose=True)

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import feedparser
import requests
from pytrends.request import TrendReq


# Configure Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info(f"Env loaded from {env_path}: {loaded}")

# --- Configuration ---
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
SHEET_ID = os.environ.get("SHEET_ID")
if SHEET_ID and (SHEET_ID.startswith('"') or SHEET_ID.startswith("'")):
    SHEET_ID = SHEET_ID[1:-1]

CREDS_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
if CREDS_JSON:
    logger.info(f"CREDS_JSON found. Length: {len(CREDS_JSON)}")
else:
    logger.error("CREDS_JSON is Missing or Empty!")


class TrendFetcher:
    def __init__(self):
        self.trends = []
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer

            # Load a small, fast model
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer model loaded successfully.")
        except ImportError:
            logger.warning(
                "sentence-transformers not found. Falling back to heuristics."
            )
        except Exception as e:
            logger.warning(f"Failed to load model: {e}")

    def extract_topic(self, title: str, entry: Any = None) -> str:
        """
        Extracts a short topic/keyword.
        Priority:
        1. Semantic Extraction (if model loaded)
        2. Improved Heuristics
        """
        # Clean title first
        clean_title = title.replace("&amp;", "&").replace("&quot;", '"')
        clean_title = re.split(r" [-|:] ", clean_title)[0]  # Strip " - Site Name"

        # 1. Semantic Extraction
        if self.model:
            try:
                return self.extract_topic_semantic(clean_title)
            except Exception as e:
                logger.error(f"Semantic extraction failed: {e}")

        # 2. Improved Fallback Heuristics
        return self.extract_topic_heuristic(clean_title, entry)

    def extract_topic_semantic(self, text: str) -> str:
        """
        Uses simple embedding similarity to find the most 'representative' 1-3 gram.
        Simplified KeyBERT-like approach.
        """
        from sklearn.metrics.pairwise import cosine_similarity
        from sklearn.feature_extraction.text import CountVectorizer

        # Generate candidates (n-grams)
        # We look for 1, 2, and 3-grams.
        n_gram_range = (1, 3)
        stop_words = "english"

        try:
            count = CountVectorizer(
                ngram_range=n_gram_range, stop_words=stop_words
            ).fit([text])
            candidates = count.get_feature_names_out()
        except Exception:
            # If text is too short or empty, CountVectorizer might fail or return empty
            return text

        if len(candidates) == 0:
            return text

        # Embed doc and candidates
        doc_embedding = self.model.encode([text])
        candidate_embeddings = self.model.encode(candidates)

        # Calculate distances
        distances = cosine_similarity(doc_embedding, candidate_embeddings)
        keywords = [
            candidates[index] for index in distances.argsort()[0][-1:]
        ]  # Get top 1

        topic = keywords[0]

        # Capitalize for display (Title Case)
        return topic.title()

    def extract_topic_heuristic(self, title: str, entry: Any = None) -> str:
        # 1. Try RSS Tags
        if entry and hasattr(entry, "tags"):
            tag_terms = [t.get("term", "") for t in entry.tags if t.get("term")]
            if tag_terms:
                valid_tags = [
                    t for t in tag_terms if len(t) < 20 and t.lower() != "news"
                ][:2]
                if valid_tags:
                    return " / ".join(valid_tags)

        if not title:
            return "Unknown"

        words = title.split()

        # 2. Extract Proper Nouns (Capitalized words)
        # Improved: Ignore common starting words if they are just "The" or "A"
        capitalized = [w for w in words if w[0].isupper() and len(w) > 1]

        # Filter out common capitalized stop words in titles if any (like "Why", "How")
        stop_starts = {
            "Why",
            "How",
            "What",
            "When",
            "Who",
            "Where",
            "The",
            "A",
            "An",
            "Is",
            "Are",
        }
        capitalized = [w for w in capitalized if w not in stop_starts]

        if len(capitalized) >= 1:
            return " ".join(capitalized[:3])

        # 3. Fallback: Short Truncation
        if len(words) <= 4:
            return title

        return " ".join(words[:4]) + "..."

    def fetch_google_trends(self, geo="US"):
        """Fetches daily trending searches from Google Trends RSS."""
        logger.info("Fetching Google Trends (RSS)...")
        # Try the atom feed if rss fails, or just ensure headers are good.
        rss_url = f"https://trends.google.com/trending/rss?geo={geo}"
        try:
            # Use a realistic User-Agent
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/xml,application/xhtml+xml,text/xml;q=0.9,text/plain;q=0.8",
                "Referer": "https://trends.google.com/",
            }
            response = requests.get(rss_url, headers=headers)
            if response.status_code != 200:
                logger.error(
                    f"Google Trends RSS failed with status {response.status_code} for {rss_url}"
                )
                return  # Skip if failed

            feed = feedparser.parse(response.content)

            for entry in feed.entries[:20]:
                # Extract Traffic (e.g., "50,000+")
                traffic_str = (
                    entry.get("ht_approx_traffic", "0")
                    .replace(",", "")
                    .replace("+", "")
                )
                try:
                    score = int(traffic_str)
                except ValueError:
                    score = 0

                metric_label = f"{entry.get('ht_approx_traffic', 'N/A')} Searches"

                self.trends.append(
                    {
                        "date": datetime.date.today().isoformat(),
                        "source": "Google Trends",
                        "trend": entry.title,
                        "url": f"https://trends.google.com/trends/explore?q={entry.title}",
                        "raw_text": entry.title,
                        "trend_score": score,
                        "metric_label": metric_label,
                    }
                )
        except Exception as e:
            logger.error(f"Error fetching Google Trends RSS: {e}")

    def fetch_pytrends(self):
        """Fetches realtime trends using pytrends (Secondary Source)."""
        logger.info("Fetching Google Trends (pytrends)...")
        try:
            pytrends = TrendReq(hl="en-US", tz=360)
            # Try realtime first
            realtime_trends = pytrends.realtime_trending_searches(pn="US")

            # Format: DataFrame with 'title', 'entity_names'
            if not realtime_trends.empty:
                for _, row in realtime_trends.head(20).iterrows():
                    title = row["title"]
                    # Pytrends realtime doesn't always give traffic numbers easily in this call
                    # We assign a high default score for Being Realtime

                    self.trends.append(
                        {
                            "date": datetime.date.today().isoformat(),
                            "source": "Google Trends (Live)",
                            "trend": title,
                            "url": f"https://trends.google.com/trends/explore?q={title}",
                            "raw_text": title,
                            "trend_score": 1000,  # Arbitrary 'Hot' score since no exact number
                            "metric_label": "Live Trend",
                        }
                    )
        except Exception as e:
            logger.warning(f"pytrends fetch failed (expected if API changes): {e}")

    def fetch_rss_feeds(self):
        """Fetches from Gen Z / Culture RSS feeds."""
        logger.info("Fetching RSS Feeds...")
        feeds = [
            "https://marketingdive.com/feeds/news/",
            "https://feeds.feedburner.com/TechCrunch/",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        ]
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        for url in feeds:
            try:
                # Use requests to get content first to handle headers/user-agent
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.content)
                else:
                    logger.warning(
                        f"RSS {url} failed with {resp.status_code}, trying direct parse fallback"
                    )
                    feed = feedparser.parse(url)  # Fallback

                for entry in feed.entries[:10]:
                    # Pass the full entry to use tags
                    topic = self.extract_topic(entry.title, entry)
                    self.trends.append(
                        {
                            "date": datetime.date.today().isoformat(),
                            "source": "RSS",
                            "trend": topic,
                            "url": entry.link,
                            "raw_text": entry.title,
                            "trend_score": 100,  # Default logic for RSS
                            "metric_label": "News Feature",
                        }
                    )
            except Exception as e:
                logger.error(f"Error fetching RSS {url}: {e}")

    def fetch_reddit_gen_z(self):
        """Fetches hot posts from r/GenZ using JSON endpoint."""
        logger.info("Fetching Reddit r/GenZ...")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(
                "https://www.reddit.com/r/GenZ/hot.json?limit=25", headers=headers
            )
            if resp.status_code == 200:
                data = resp.json()
                children = data.get("data", {}).get("children", [])
                for child in children:
                    post = child.get("data", {})
                    if not post.get("stickied"):
                        # Reddit doesn't have "tags" in the same way, usually just flair
                        flair = post.get("link_flair_text")
                        if flair:
                            # Maybe combine flair + shortened title? Or just shortened title.
                            # Let's stick to extract_topic with just title for now, or pass flair if we want.
                            pass

                        topic = self.extract_topic(post.get("title"))
                        score = post.get("score", 0)
                        comments = post.get("num_comments", 0)

                        self.trends.append(
                            {
                                "date": datetime.date.today().isoformat(),
                                "source": "Reddit (r/GenZ)",
                                "trend": topic,
                                "url": f"https://reddit.com{post.get('permalink')}",
                                "raw_text": post.get("title"),
                                "trend_score": score,
                                "metric_label": f"{score} Upvotes",
                            }
                        )
            else:
                logger.error(f"Reddit API returned {resp.status_code}")
        except Exception as e:
            logger.error(f"Error fetching Reddit: {e}")

    def get_all_trends(self) -> List[Dict[str, Any]]:
        self.fetch_google_trends()
        self.fetch_pytrends()
        self.fetch_rss_feeds()
        self.fetch_reddit_gen_z()
        return self.trends


class TrendClassifier:
    def __init__(self):
        self.gen_z_keywords = [
            "tiktok",
            "skibidi",
            "rizz",
            "gyatt",
            "fanum",
            "kai cenat",
            "mrbeast",
            "roblox",
            "fortnite",
            "gen z",
            "zoomer",
        ]
        self.millennial_keywords = [
            "interest rates",
            "housing market",
            "inflation",
            "millennial",
            "90s",
            "nostalgia",
            "work from home",
            "coffee",
            "wine",
        ]
        self.gen_alpha_keywords = [
            "skibidi",
            "ipad kid",
            "cocomelon",
            "bluey",
            "alpha",
            "sigma",
        ]

    def classify(self, text: str) -> str:
        text_lower = text.lower()
        if any(k in text_lower for k in self.gen_alpha_keywords):
            return "Gen Alpha"
        if any(k in text_lower for k in self.gen_z_keywords):
            return "Gen Z"
        if any(k in text_lower for k in self.millennial_keywords):
            return "Millennials"
        return "General"  # Default


class SheetWriter:
    def __init__(self):
        self.client = None
        self.sheet = None

    def connect(self):
        try:
            creds = None
            if CREDS_JSON:
                creds_dict = json.loads(CREDS_JSON)
                creds = ServiceAccountCredentials.from_json_keyfile_dict(
                    creds_dict, SCOPE
                )
            if creds:
                self.client = gspread.authorize(creds)
                if SHEET_ID:
                    self.sheet = self.client.open_by_key(SHEET_ID)
                else:
                    logger.warning("Skipping sheet connection (No SHEET_ID).")
            else:
                logger.warning("Skipping sheet connection (No CREDS).")
        except Exception as e:
            logger.error(f"Error connecting to Sheets: {repr(e)}")

    def sync_trends(self, trends: List[Dict[str, Any]]):
        """
        Syncs new trends with existing sheet data.
        Deduplicates by Date + Trend (case-insensitive).
        Merges 'Source' fields for duplicates.
        """
        if not self.sheet:
            print(json.dumps(trends[:3], indent=2))
            return

        tabs = ["Gen Z", "Millennials", "Gen Alpha", "General"]

        for tab_name in tabs:
            try:
                worksheet = self.sheet.worksheet(tab_name)
            except gspread.WorksheetNotFound:
                worksheet = self.sheet.add_worksheet(title=tab_name, rows=1000, cols=7)
                worksheet.append_row(
                    ["Date", "Trend", "Source", "URL", "Raw Text", "Score", "Metric"]
                )

            # 1. Read ALL existing data
            try:
                existing_rows = worksheet.get_all_values()
            except Exception as e:
                logger.error(f"Failed to read worksheet {tab_name}: {e}")
                continue

            if not existing_rows:
                # Should at least have headers if newly created, but just in case
                header = [
                    "Date",
                    "Trend",
                    "Source",
                    "URL",
                    "Raw Text",
                    "Score",
                    "Metric",
                ]
            else:
                header = existing_rows[0]
                if len(header) < 7:
                    # Add missing headers if updating old sheet
                    header.extend(["Score", "Metric"])
                existing_rows = existing_rows[1:]  # Skip header

            # 2. Combine and Deduplicate
            # Key: (date, normalized_trend) -> {data_dict}
            merged_data = {}

            # Helper to normalize trend
            def normalize(t):
                return t.lower().strip()

            # Helper to merge entries
            def merge_entry(existing, new_entry):
                # Merge Source
                sources = set(
                    [s.strip() for s in existing["Source"].split(",") if s.strip()]
                )
                sources.add(new_entry["source"])
                existing["Source"] = ", ".join(sorted(list(sources)))

                # Keep first URL (or prefer new one if existing is empty? rarely empty)
                if not existing["URL"] and new_entry["url"]:
                    existing["URL"] = new_entry["url"]

                return existing

            # Process Existing
            for row in existing_rows:
                if len(row) < 5:
                    continue  # Skip malformed
                date, trend, source, url, raw_text = (
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                )
                score = int(row[5]) if len(row) > 5 and row[5].isdigit() else 0
                metric = row[6] if len(row) > 6 else ""

                key = (date, normalize(trend))
                merged_data[key] = {
                    "Date": date,
                    "Trend": trend,  # Keep original casing of first occurrence
                    "Source": source,
                    "URL": url,
                    "Raw Text": raw_text,
                    "Score": score,
                    "Metric": metric,
                }

            # Process New
            tab_new_trends = [t for t in trends if t.get("generation") == tab_name]
            for t in tab_new_trends:
                date = t["date"]
                trend = t["trend"]
                key = (date, normalize(trend))

                if key in merged_data:
                    # Merge
                    merged_data[key] = merge_entry(merged_data[key], t)
                else:
                    # Add New
                    merged_data[key] = {
                        "Date": date,
                        "Trend": trend,
                        "Source": t["source"],
                        "URL": t["url"],
                        "Raw Text": t["raw_text"],
                        "Score": t.get("trend_score", 0),
                        "Metric": t.get("metric_label", ""),
                    }

            # 3. Write Back
            # Convert back to list of lists
            # Sort by Date (descending) then Trend Score (descending)
            final_rows = list(merged_data.values())
            final_rows.sort(key=lambda x: (x["Date"], x["Score"]), reverse=True)

            rows_to_write = [header] + [
                [
                    r["Date"],
                    r["Trend"],
                    r["Source"],
                    r["URL"],
                    r["Raw Text"],
                    r["Score"],
                    r["Metric"],
                ]
                for r in final_rows
            ]

            try:
                # Clear and update
                worksheet.clear()
                worksheet.update(values=rows_to_write)
                logger.info(
                    f"Synced {tab_name}: {len(final_rows)} trends ({len(tab_new_trends)} new merged)."
                )
            except Exception as e:
                logger.error(f"Failed to write to {tab_name}: {e}")


def main():
    fetcher = TrendFetcher()
    trends = fetcher.get_all_trends()

    # Debug: Log source breakdown
    source_counts = {}
    for t in trends:
        s = t.get("source", "Unknown")
        source_counts[s] = source_counts.get(s, 0) + 1
    logger.info(f"Fetched trends breakdown: {source_counts}")

    classifier = TrendClassifier()
    for t in trends:
        t["generation"] = classifier.classify(t["raw_text"])
    writer = SheetWriter()
    writer.connect()
    writer.sync_trends(trends)
    logger.info("Done.")


if __name__ == "__main__":
    main()
