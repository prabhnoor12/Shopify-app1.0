from sqlalchemy.orm import Session
from openai import OpenAI
from ..models.brand_voice import BrandVoice
from typing import Optional, List


class BrandVoiceService:
    def __init__(self, db: Session, openai_client: OpenAI):
        self.db = db
        self.openai_client = openai_client

    def create_brand_voice(self, user_id: int, description: str) -> BrandVoice:
        existing_brand_voice = self.get_brand_voice_by_user_id(user_id)
        if existing_brand_voice:
            raise ValueError("Brand voice for this user already exists.")

        brand_voice = BrandVoice(user_id=user_id, description=description)
        self.db.add(brand_voice)
        self.db.commit()
        self.db.refresh(brand_voice)
        return brand_voice

    def get_brand_voice_by_user_id(self, user_id: int) -> Optional[BrandVoice]:
        return self.db.query(BrandVoice).filter(BrandVoice.user_id == user_id).first()

    def update_brand_voice(self, user_id: int, description: str) -> BrandVoice:
        brand_voice = self.get_brand_voice_by_user_id(user_id)
        if not brand_voice:
            raise ValueError("Brand voice not found for this user.")

        brand_voice.description = description
        self.db.commit()
        self.db.refresh(brand_voice)
        return brand_voice

    def delete_brand_voice(self, user_id: int):
        brand_voice = self.get_brand_voice_by_user_id(user_id)
        if not brand_voice:
            raise ValueError("Brand voice not found for this user.")

        self.db.delete(brand_voice)
        self.db.commit()

    def analyze_brand_voice(self, user_id: int) -> dict:
        brand_voice = self.get_brand_voice_by_user_id(user_id)
        if not brand_voice or not brand_voice.description:
            raise ValueError("Brand voice description not found or is empty.")

        prompt = f"""Analyze the following brand voice description for its tone, style, and consistency.
        Provide feedback on its strengths and weaknesses.

        Description: {brand_voice.description}

        Analysis:"""

        response = self.openai_client.completions.create(
            model="text-davinci-003", prompt=prompt, max_tokens=256
        )
        analysis = response.choices[0].text.strip()
        return {"analysis": analysis}

    def generate_brand_voice_suggestions(
        self, keywords: List[str], count: int = 3
    ) -> List[str]:
        if not keywords:
            raise ValueError("Keywords are required to generate suggestions.")

        prompt = f"""Generate {count} brand voice descriptions based on the following keywords.
        Each description should be distinct in its tone and style.

        Keywords: {", ".join(keywords)}

        Suggestions:"""

        response = self.openai_client.completions.create(
            model="text-davinci-003", prompt=prompt, max_tokens=512
        )
        suggestions = response.choices[0].text.strip().split("\n")
        return [s.strip() for s in suggestions if s.strip()]
