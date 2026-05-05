from pydantic import BaseModel, Field


class DialogueLine(BaseModel):
    """One spoken line in a dialogue card."""

    speaker: str
    text: str
    audio: str | None = None
    visual: str | None = None
    is_learner_target: bool = False


class DialogueCard(BaseModel):
    """A concrete exchange inside one scene."""

    id: str
    situation: str
    difficulty: int = 1
    lines: list[DialogueLine]
    category: str
    category_label: str
    type: str = "anchor"
    function_id: str | None = None
    target_id: str | None = None
    review_modes: list[str] = Field(default_factory=list)


class DialogueCategory(BaseModel):
    id: str
    label: str
    scenes: list[DialogueCard]


class ContentGraph(BaseModel):
    categories: list[DialogueCategory]

    @property
    def dialogues(self) -> list[DialogueCard]:
        return [scene for category in self.categories for scene in category.scenes]
