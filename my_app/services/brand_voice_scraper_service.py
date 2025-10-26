import requests
from bs4 import BeautifulSoup
import re


class BrandVoiceScraperService:
    def scrape_and_analyze(self, url: str) -> dict:
        """
        Scrapes a URL, extracts text content, and analyzes it to suggest
        a brand voice profile.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ValueError(f"Could not fetch URL: {e}")

        soup = BeautifulSoup(response.content, "lxml")

        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        if not text:
            return {"error": "No text content found at the URL."}

        # Simple analysis (can be replaced with a sophisticated NLP model)
        analysis = self._analyze_text(text)

        return {
            "url": url,
            "suggested_profile": analysis,
            "sample_text": text[:1000],  # Return a sample of the scraped text
        }

    def _analyze_text(self, text: str) -> dict:
        """
        Performs a simple analysis of the text to determine brand voice characteristics.
        """
        text_lower = text.lower()
        words = re.findall(r"\b\w+\b", text_lower)
        word_count = len(words)

        # Define some simple keyword-based classifiers
        formal_words = ["sincerely", "regards", "formal", "official"]
        informal_words = ["hey", "awesome", "cool", "lol", "btw"]
        technical_words = [
            "specifications",
            "technical",
            "algorithm",
            "data",
            "feature",
        ]
        marketing_words = ["sale", "discount", "offer", "buy now", "limited time"]

        formal_score = sum(1 for word in formal_words if word in text_lower)
        informal_score = sum(1 for word in informal_words if word in text_lower)
        technical_score = sum(1 for word in technical_words if word in text_lower)
        marketing_score = sum(1 for word in marketing_words if word in text_lower)

        # Determine primary tone
        tone = "Neutral"
        scores = {
            "Formal": formal_score,
            "Informal": informal_score,
            "Technical": technical_score,
            "Marketing": marketing_score,
        }
        if any(s > 0 for s in scores.values()):
            tone = max(scores, key=scores.get)

        # Sentence length
        sentences = re.split(r"[.!?]+", text)
        avg_sentence_length = word_count / len(sentences) if sentences else 0

        # Vocabulary complexity (simple measure)
        avg_word_length = (
            sum(len(word) for word in words) / word_count if word_count > 0 else 0
        )

        complexity = "Simple"
        if avg_sentence_length > 20 or avg_word_length > 5:
            complexity = "Complex"
        elif avg_sentence_length > 15 or avg_word_length > 4.5:
            complexity = "Moderate"

        return {
            "primary_tone": tone,
            "complexity": complexity,
            "avg_sentence_length": round(avg_sentence_length, 2),
            "word_count": word_count,
        }
