from __future__ import annotations

import os

from app.conversation.coach import ConversationCoach
from app.conversation.openai_adapter import OpenAICommunicationJudge, OpenAISpeechInterpreter


def create_conversation_coach() -> ConversationCoach:
    """Use the OpenAI-backed coach when configured; otherwise stay local."""
    if os.environ.get("OPENAI_API_KEY"):
        return ConversationCoach(
            speech_interpreter=OpenAISpeechInterpreter(),
            communication_judge=OpenAICommunicationJudge(),
        )
    return ConversationCoach()
