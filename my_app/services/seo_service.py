import re
from typing import Dict, Any, Optional
from openai import OpenAI
import httpx
from bs4 import BeautifulSoup
import trafilatura
import spacy
from collections import Counter

# Load the spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # This happens if the model is not downloaded, provide a helpful message
    raise RuntimeError(
        "spaCy model 'en_core_web_sm' not found. "
        "Please run 'python -m spacy download en_core_web_sm' to download it."
    )

# Constants for SEO analysis
IDEAL_TITLE_LENGTH = (30, 60)
IDEAL_META_DESCRIPTION_LENGTH = (50, 160)
IDEAL_DESCRIPTION_WORD_COUNT = (100, 300)


class SEOService:
    @staticmethod
    def _count_syllables(word: str) -> int:
        """A simple heuristic to count syllables in a word."""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        if not word:
            return 0
        if word[0] in vowels:
            count += 1
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1
        if word.endswith("e"):
            count -= 1
        if count == 0:
            count += 1
        return count

    @staticmethod
    def _calculate_flesch_reading_ease(text: str) -> float:
        """Calculates Flesch Reading Ease score."""
        words = text.split()
        word_count = len(words)
        sentence_count = len(re.findall(r"[.!?]+", text))
        syllable_count = sum(SEOService._count_syllables(word) for word in words)

        if word_count == 0 or sentence_count == 0:
            return 0.0

        return (
            206.835
            - 1.015 * (word_count / sentence_count)
            - 84.6 * (syllable_count / word_count)
        )

    @staticmethod
    def analyze_links(description: str, your_domain: str) -> Dict[str, Any]:
        """Analyzes the internal and external links in the content."""
        soup = BeautifulSoup(description, "html.parser")
        links = soup.find_all("a")
        internal_links = 0
        external_links = 0
        for link in links:
            href = link.get("href")
            if href:
                if your_domain in href:
                    internal_links += 1
                else:
                    external_links += 1
        return {"internal_links": internal_links, "external_links": external_links}

    @staticmethod
    def analyze_images(description: str) -> Dict[str, Any]:
        """Analyzes the images in the content for SEO."""
        soup = BeautifulSoup(description, "html.parser")
        images = soup.find_all("img")
        images_without_alt = sum(1 for image in images if not image.get("alt"))
        return {"images_without_alt": images_without_alt, "total_images": len(images)}

    @staticmethod
    def analyze_headings(description: str) -> Dict[str, Any]:
        """Analyzes the headings in the content for SEO."""
        soup = BeautifulSoup(description, "html.parser")
        return {
            "h1": len(soup.find_all("h1")),
            "h2": len(soup.find_all("h2")),
            "h3": len(soup.find_all("h3")),
            "h4": len(soup.find_all("h4")),
            "h5": len(soup.find_all("h5")),
            "h6": len(soup.find_all("h6")),
        }

    @staticmethod
    def generate_seo_summary(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a summary of the SEO analysis with recommendations."""
        summary = {
            "overall_score": analysis_results["overall_score"],
            "recommendations": [],
        }
        for check in analysis_results["checks"]:
            if check["status"] == "fail":
                recommendation = f"Improve {check['name']}: {check['message']}"
                summary["recommendations"].append(recommendation)
        return summary

    @staticmethod
    def analyze_keywords(text: str, primary_keyword: str) -> Dict[str, Any]:
        """
        Performs keyword analysis using spaCy for TF-IDF and semantic similarity.
        """
        doc = nlp(text)

        # 1. TF-IDF implementation with spaCy
        # Filter out stop words and punctuation
        words = [
            token.text.lower()
            for token in doc
            if not token.is_stop and not token.is_punct and token.is_alpha
        ]
        word_freq = Counter(words)
        total_words = len(words)

        tfidf_keywords = {}
        for word, freq in word_freq.items():
            # A simplified TF-IDF score; for real TF-IDF, you'd need a corpus for IDF
            tf = freq / total_words
            tfidf_keywords[word] = tf  # In this context, it's just term frequency

        # Sort by frequency
        sorted_tfidf = sorted(
            tfidf_keywords.items(), key=lambda item: item[1], reverse=True
        )[:10]

        # 2. LSI/Semantic Keywords using word vectors
        primary_keyword_doc = nlp(primary_keyword)
        similar_keywords = []
        if primary_keyword_doc.has_vector:
            # Find similar words from the text
            similarities = [
                (token.text, primary_keyword_doc.similarity(token))
                for token in doc
                if token.has_vector and token.is_alpha and not token.is_stop
            ]
            # Sort by similarity and get unique top terms
            sorted_similarities = sorted(
                similarities, key=lambda item: item[1], reverse=True
            )
            unique_similar_keywords = []
            seen_words = set()
            for word, score in sorted_similarities:
                if (
                    word.lower() not in seen_words
                    and word.lower() != primary_keyword.lower()
                ):
                    unique_similar_keywords.append((word, score))
                    seen_words.add(word.lower())
                if len(unique_similar_keywords) >= 5:
                    break
            similar_keywords = unique_similar_keywords

        return {"tfidf_keywords": sorted_tfidf, "lsi_keywords": similar_keywords}

    @staticmethod
    def analyze_seo(
        primary_keyword: str,
        title: str,
        description: str,
        meta_title: Optional[str] = None,
        meta_description: Optional[str] = None,
        your_domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Performs an advanced SEO analysis of product content.
        """
        results = {"overall_score": 0, "checks": []}
        score = 0
        max_score = 0
        keyword_lower = primary_keyword.lower()

        # 1. Primary Keyword in Title
        max_score += 20
        title_check = {
            "name": "Primary Keyword in Title",
            "score": 0,
            "status": "fail",
            "message": f"Primary keyword '{primary_keyword}' not found in the title.",
        }
        if keyword_lower in title.lower():
            title_check["score"] = 20
            title_check["status"] = "pass"
            title_check["message"] = "Excellent! The primary keyword is in the title."
            score += 20
        results["checks"].append(title_check)

        # 2. Title Length
        max_score += 10
        title_len_check = {
            "name": "Title Length",
            "score": 0,
            "status": "fail",
            "message": f"Title is {len(title)} characters. Ideal is between {IDEAL_TITLE_LENGTH[0]}-{IDEAL_TITLE_LENGTH[1]}.",
        }
        if IDEAL_TITLE_LENGTH[0] <= len(title) <= IDEAL_TITLE_LENGTH[1]:
            title_len_check["score"] = 10
            title_len_check["status"] = "pass"
            title_len_check["message"] = (
                "Good job! The title length is within the ideal range."
            )
            score += 10
        results["checks"].append(title_len_check)

        # 3. Primary Keyword in Description
        max_score += 15
        desc_keyword_check = {
            "name": "Primary Keyword in Description",
            "score": 0,
            "status": "fail",
            "message": f"Primary keyword '{primary_keyword}' not found in the description.",
        }
        if keyword_lower in description.lower():
            desc_keyword_check["score"] = 15
            desc_keyword_check["status"] = "pass"
            desc_keyword_check["message"] = (
                "Great! The primary keyword is in the description."
            )
            score += 15
        results["checks"].append(desc_keyword_check)

        # 4. Description Word Count
        max_score += 10
        word_count = len(description.split())
        desc_len_check = {
            "name": "Description Word Count",
            "score": 0,
            "status": "fail",
            "message": f"Description is {word_count} words. Ideal is between {IDEAL_DESCRIPTION_WORD_COUNT[0]}-{IDEAL_DESCRIPTION_WORD_COUNT[1]}.",
        }
        if (
            IDEAL_DESCRIPTION_WORD_COUNT[0]
            <= word_count
            <= IDEAL_DESCRIPTION_WORD_COUNT[1]
        ):
            desc_len_check["score"] = 10
            desc_len_check["status"] = "pass"
            desc_len_check["message"] = (
                "Perfect! The description length is within the ideal range for engagement."
            )
            score += 10
        results["checks"].append(desc_len_check)

        # 5. Meta Title Analysis
        if meta_title:
            max_score += 10
            meta_title_check = {
                "name": "Primary Keyword in Meta Title",
                "score": 0,
                "status": "fail",
                "message": f"Primary keyword '{primary_keyword}' not found in the meta title.",
            }
            if keyword_lower in meta_title.lower():
                meta_title_check["score"] = 10
                meta_title_check["status"] = "pass"
                meta_title_check["message"] = (
                    "Excellent! The primary keyword is in the meta title."
                )
                score += 10
            results["checks"].append(meta_title_check)

        # 6. Meta Description Analysis
        if meta_description:
            max_score += 10
            meta_desc_check = {
                "name": "Meta Description Length",
                "score": 0,
                "status": "fail",
                "message": f"Meta description is {len(meta_description)} characters. Ideal is between {IDEAL_META_DESCRIPTION_LENGTH[0]}-{IDEAL_META_DESCRIPTION_LENGTH[1]}.",
            }
            if (
                IDEAL_META_DESCRIPTION_LENGTH[0]
                <= len(meta_description)
                <= IDEAL_META_DESCRIPTION_LENGTH[1]
            ):
                meta_desc_check["score"] = 10
                meta_desc_check["status"] = "pass"
                meta_desc_check["message"] = (
                    "Good! The meta description length is within the ideal range."
                )
                score += 10
            results["checks"].append(meta_desc_check)

        # 7. Heading Analysis
        max_score += 5
        headings = SEOService.analyze_headings(description)
        heading_check = {
            "name": "H1 Heading",
            "score": 0,
            "status": "fail",
            "message": "No H1 heading found. An H1 heading is crucial for SEO.",
        }
        if headings["h1"] > 0:
            heading_check["score"] = 5
            heading_check["status"] = "pass"
            heading_check["message"] = "Good, an H1 heading is present."
            score += 5
        results["checks"].append(heading_check)

        # 8. Image Analysis
        max_score += 5
        images = SEOService.analyze_images(description)
        image_check = {
            "name": "Image Alt Text",
            "score": 5,
            "status": "pass",
            "message": "All images have alt text.",
        }
        if images["images_without_alt"] > 0:
            image_check["score"] = 0
            image_check["status"] = "fail"
            image_check["message"] = (
                f"{images['images_without_alt']} out of {images['total_images']} images are missing alt text."
            )
        else:
            score += 5
        results["checks"].append(image_check)

        # 9. Link Analysis
        if your_domain:
            max_score += 15
            links = SEOService.analyze_links(description, your_domain)

            internal_link_check = {
                "name": "Internal Links",
                "score": 0,
                "status": "fail",
                "message": "No internal links found. Add some to improve site structure.",
            }
            if links["internal_links"] > 0:
                internal_link_check["score"] = 10
                internal_link_check["status"] = "pass"
                internal_link_check["message"] = (
                    f"Found {links['internal_links']} internal links. Good job!"
                )
                score += 10
            results["checks"].append(internal_link_check)

            external_link_check = {
                "name": "External Links",
                "score": 5,
                "status": "pass",
                "message": "No external links found. Consider adding relevant external links.",
            }
            if links["external_links"] > 0:
                external_link_check["message"] = (
                    f"Found {links['external_links']} external links."
                )
                score += 5
            results["checks"].append(external_link_check)

        # Final Score Calculation
        results["overall_score"] = (
            int((score / max_score) * 100) if max_score > 0 else 0
        )
        return results


def generate_seo_improvement_suggestions(
    openai_client: OpenAI, analysis_results: Dict[str, Any], **kwargs
) -> str:
    """
    Uses AI to generate actionable suggestions based on SEO analysis results.
    """
    summary = SEOService.generate_seo_summary(analysis_results)
    prompt = (
        "Based on the following SEO analysis summary, generate a concise, "
        "actionable, and friendly list of suggestions for a Shopify merchant "
        "to improve their product's SEO. Focus on the recommendations provided. "
        "Format the output as a single string with clear bullet points or numbered lists.\n\n"
        f"Overall Score: {summary['overall_score']}/100\n"
        "Recommendations:\n- " + "\n- ".join(summary["recommendations"])
    )

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert SEO assistant for e-commerce.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Could not generate AI suggestions at this time."


def analyze_product_url(url: str) -> Dict[str, Any]:
    """
    Fetches content from a product URL and performs a basic SEO analysis.
    """
    with httpx.Client() as client:
        try:
            response = client.get(url, follow_redirects=True, timeout=10)
            response.raise_for_status()
        except httpx.RequestError as e:
            return {"error": f"Could not fetch URL: {e}"}

    html_content = response.text
    downloaded = trafilatura.fetch_url(url)
    main_text = trafilatura.extract(
        downloaded, include_comments=False, include_tables=False
    )

    soup = BeautifulSoup(html_content, "html.parser")
    title = soup.find("title").string if soup.find("title") else "No title found"
    meta_description_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_description_tag["content"] if meta_description_tag else ""

    if not main_text:
        return {"error": "Could not extract main content from the URL."}

    # Use the primary keyword from the title as a default
    primary_keyword_guess = title.split("|")[0].strip()
    keyword_analysis = SEOService.analyze_keywords(main_text, primary_keyword_guess)
    readability_score = SEOService._calculate_flesch_reading_ease(main_text)

    return {
        "url": url,
        "title": title,
        "meta_description": meta_description,
        "readability_score": readability_score,
        "lsi_keywords": keyword_analysis["lsi_keywords"],
        "tfidf_keywords": keyword_analysis["tfidf_keywords"],
    }
