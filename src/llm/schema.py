from enum import Enum

from pydantic import BaseModel, Field, field_validator


class TriageCategory(str, Enum):
    billing = "billing"
    bug = "bug"
    feature = "feature"
    account = "account"
    other = "other"


class TriageUrgency(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"


class SuggestedTeam(str, Enum):
    support = "support"
    engineering = "engineering"
    billing = "billing"
    success = "success"


class TriageInput(BaseModel):
    text: str = Field(min_length=1, max_length=2000)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("text must not be blank")
        return stripped


class TriageOutput(BaseModel):
    category: TriageCategory
    urgency: TriageUrgency
    suggested_team: SuggestedTeam
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=160)


def stub_triage_response() -> TriageOutput:
    return TriageOutput(
        category=TriageCategory.other,
        urgency=TriageUrgency.normal,
        suggested_team=SuggestedTeam.support,
        confidence=0.4,
        reason="Stub mode returns the safe unsure response.",
    )
