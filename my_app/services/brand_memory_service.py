from sqlalchemy.orm import Session
from ..crud import brand_voice_crud


class BrandMemoryService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def get_brand_voice_prompt(self) -> str:
        brand_voice = brand_voice_crud.get_by_user(self.db, user_id=self.user_id)
        if not brand_voice:
            return ""

        prompt_parts = []
        if brand_voice.tone_of_voice:
            prompt_parts.append(f"Tone of voice: {brand_voice.tone_of_voice}")
        if brand_voice.vocabulary_preferences:
            preferred = brand_voice.vocabulary_preferences.get("preferred", [])
            avoid = brand_voice.vocabulary_preferences.get("avoid", [])
            if preferred:
                prompt_parts.append(f"Preferred vocabulary: {', '.join(preferred)}")
            if avoid:
                prompt_parts.append(f"Avoid using: {', '.join(avoid)}")
        if brand_voice.industry_jargon:
            prompt_parts.append(
                f"Industry jargon: {', '.join(brand_voice.industry_jargon)}"
            )
        if brand_voice.banned_words:
            prompt_parts.append(f"Banned words: {', '.join(brand_voice.banned_words)}")

        return "\n".join(prompt_parts)
