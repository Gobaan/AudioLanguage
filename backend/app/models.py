from pydantic import BaseModel


class Turn(BaseModel):
    """A single exchange in a scene — who says what."""
    speaker: str
    text: str
    is_user_turn: bool = False


class Scene(BaseModel):
    """A learning scene: a situation with a dialogue."""
    id: str
    situation: str
    description: str
    image_url: str | None = None
    turns: list[Turn]
