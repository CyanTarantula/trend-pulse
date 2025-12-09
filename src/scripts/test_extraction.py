import sys
import os

# Add the current directory to path so we can import from get_trends
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from get_trends import TrendFetcher


def test_extraction():
    fetcher = TrendFetcher()

    test_cases = [
        "Why Gen Z Can't Find Work in 2024",
        "Skims TikTok Viral Dress Review",
        "Religious Gen Z, what is a...",
        "51% of Gen Z say they are happy",
        "Taylor Swift announces new Tour dates for 2025",
        "Apple releases new iPhone 16 with AI features",
        "The rise of 'Fanum Tax' in schools",
    ]

    print(f"{'Original Title':<50} | {'Extracted Topic':<30}")
    print("-" * 85)

    for title in test_cases:
        # We are testing the CURRENT logic first (or the modified one once we save it)
        topic = fetcher.extract_topic(title)
        print(f"{title:<50} | {topic:<30}")


if __name__ == "__main__":
    test_extraction()
