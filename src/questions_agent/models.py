from pydantic import BaseModel, Field, AliasChoices, field_validator
from typing import List, Optional


class GiftDependencies(BaseModel):
    age: int
    gender: str
    occasion: str
    relationship: str
    budget: Optional[str] = None


class GiftQuestions(BaseModel):
    class QuestionItem(BaseModel):
        question: str = Field(
            description="A concise, clear question phrased in the third person (he/she)",
            validation_alias=AliasChoices("question", "queation"),
        )
        choices: List[str] = Field(
            description=(
                "Clickable suggestions/options for the question, 3-5 short, mutually exclusive items. "
                "These are UI-friendly answer options, not free text."
            )
        )

        @field_validator("choices", mode="before")
        @classmethod
        def ensure_three_clean_choices(cls, v):
            if not isinstance(v, list):
                return ["Yes", "Maybe", "No"]
            # sanitize, dedupe preserving order, drop empties, strip punctuation tail
            seen = set()
            cleaned = []
            for item in v:
                if not isinstance(item, str):
                    continue
                s = item.strip()
                if not s:
                    continue
                # remove trailing punctuation like '.', '?', '!'
                while s and s[-1] in ".?!":
                    s = s[:-1]
                    s = s.rstrip()
                if s.lower() in seen:
                    continue
                seen.add(s.lower())
                cleaned.append(s)
                if len(cleaned) == 3:
                    break
            # pad if less than 3
            defaults = ["Yes", "Maybe", "No"]
            i = 0
            while len(cleaned) < 3 and i < len(defaults):
                if defaults[i].lower() not in seen:
                    cleaned.append(defaults[i])
                i += 1
            # ensure exactly 3
            return cleaned[:3]

    questions: List[QuestionItem] = Field(
        description="List of smart questions with suggested clickable choices"
    )
    detective_comment: str = Field(description="Brief reasoning behind the chosen questions and choices")