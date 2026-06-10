from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.conversation.coach import ConversationCoach
from app.conversation.factory import create_conversation_coach


def get_conversation_coach() -> ConversationCoach:
    """Build the conversation coach when a request needs it, not at import time."""
    return create_conversation_coach()


ConversationCoachDep = Annotated[ConversationCoach, Depends(get_conversation_coach)]
