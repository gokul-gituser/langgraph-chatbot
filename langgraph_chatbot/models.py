from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """Complete profile of a user"""
    user_name: str = Field(description="The user's preferred name")
    age: str | None = Field(default=None, description="User's age (can be exact or approximate)")
    location: str | None = Field(default=None, description="User's city/country or general location")
    interests: list[str] = Field(default_factory=list, description="A list of user's interests - capture as detailed descriptions or full sentences,or single words as provided by the user. Store exactly what the user provides. Do NOT infer reasons or add details.")
    dislikes: list[str] = Field(default_factory=list, description="A list of things the user dislikes - capture as detailed descriptions or full sentences,or single words as provided by the user. Store exactly what the user provides. Do NOT infer reasons or add details")
    additional_notes: str | None = Field(default=None, description="Any other personal details or information provided by the user.capture as detailed descriptions or sentences exactly as provided by the user. Store exactly what the user provides. Do NOT infer reasons or add details")
