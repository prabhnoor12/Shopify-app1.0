import requests
from bs4 import BeautifulSoup
from collections import Counter
import re


class CompetitiveAnalysisService:
    def __init__(self, db_session):
        self.db = db_session

    def fetch_page_content(self, url: str) -> str:
        """Fetches the HTML content of a given URL."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch URL {url}: {e}")

    def analyze_seo_content(self, html: str) -> dict:
        """Analyzes the on-page SEO and content of a given HTML string."""
        soup = BeautifulSoup(html, "lxml")

        # 1. Meta Tags
        title = soup.find("title").get_text(strip=True) if soup.find("title") else None
        meta_description = soup.find("meta", attrs={"name": "description"})
        description = meta_description["content"] if meta_description else None

        # 2. Headings
        headings = {
            f"h{i}": [h.get_text(strip=True) for h in soup.find_all(f"h{i}")]
            for i in range(1, 7)
        }

        # 3. Word Count and Keyword Frequency
        text_content = " ".join(soup.stripped_strings)
        words = re.findall(r"\b\w+\b", text_content.lower())
        word_count = len(words)
        keyword_frequency = Counter(words).most_common(20)

        return {
            "title": title,
            "meta_description": description,
            "headings": headings,
            "word_count": word_count,
            "keyword_frequency": keyword_frequency,
        }

    def compare_pages(self, base_url: str, competitor_urls: list[str]) -> dict:
        """Compares a base URL against a list of competitor URLs."""
        base_analysis = self.analyze_seo_content(self.fetch_page_content(base_url))

        competitor_analyses = []
        for url in competitor_urls:
            try:
                competitor_analysis = self.analyze_seo_content(
                    self.fetch_page_content(url)
                )
                competitor_analyses.append(
                    {"url": url, "analysis": competitor_analysis}
                )
            except ValueError as e:
                # Skip competitors that fail to load, but log the error
                print(f"Skipping competitor {url}: {e}")
                competitor_analyses.append(
                    {"url": url, "analysis": None, "error": str(e)}
                )

        gap_analysis = self._identify_gaps(base_analysis, competitor_analyses)

        return {
            "base_analysis": base_analysis,
            "competitor_analyses": competitor_analyses,
            "gap_analysis": gap_analysis,
        }

    def _identify_gaps(
        self, base_analysis: dict, competitor_analyses: list[dict]
    ) -> dict:
        """Identifies content and SEO gaps."""
        gaps = {"keyword_gaps": [], "content_length_comparison": {}}

        # Keyword Gaps
        base_keywords = {kw for kw, count in base_analysis["keyword_frequency"]}

        all_competitor_keywords = Counter()
        for comp in competitor_analyses:
            if comp["analysis"]:
                comp_keywords = {
                    kw for kw, count in comp["analysis"]["keyword_frequency"]
                }
                # Keywords competitors are using that the base page is not
                missing_keywords = comp_keywords - base_keywords
                if missing_keywords:
                    gaps["keyword_gaps"].append(
                        {
                            "competitor_url": comp["url"],
                            "missing_keywords": list(missing_keywords),
                        }
                    )

        # Content Length
        avg_competitor_wc = sum(
            c["analysis"]["word_count"] for c in competitor_analyses if c["analysis"]
        ) / (len(competitor_analyses) or 1)
        gaps["content_length_comparison"] = {
            "base_word_count": base_analysis["word_count"],
            "average_competitor_word_count": round(avg_competitor_wc),
            "suggestion": "Consider adding more content."
            if base_analysis["word_count"] < avg_competitor_wc
            else "Content length is competitive.",
        }

        return gaps
