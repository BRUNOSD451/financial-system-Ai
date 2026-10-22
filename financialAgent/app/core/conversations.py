"""Historico por conversa, limitado a 12 mensagens e mantido neste processo."""
from collections import deque
from dataclasses import dataclass, field
from time import monotonic
from uuid import uuid4

from fastapi import HTTPException

HISTORY_LIMIT = 12
CONVERSATION_TTL = 24 * 60 * 60
MAX_CONVERSATIONS = 1000


@dataclass
class Conversation:
    messages: deque = field(default_factory=lambda: deque(maxlen=HISTORY_LIMIT))
    touched: float = field(default_factory=monotonic)
    busy: bool = False


class ConversationStore:
    def __init__(self):
        self.conversations: dict[str, Conversation] = {}

    def prune(self):
        now = monotonic()
        for key, conversation in list(self.conversations.items()):
            if not conversation.busy and now - conversation.touched >= CONVERSATION_TTL:
                del self.conversations[key]

    def begin(self, conversation_id: str | None):
        self.prune()
        if conversation_id is None:
            if len(self.conversations) >= MAX_CONVERSATIONS:
                raise HTTPException(503, "Limite de conversas atingido. Tente mais tarde.")
            conversation_id = str(uuid4())
            self.conversations[conversation_id] = Conversation()
        conversation = self.conversations.get(conversation_id)
        if conversation is None:
            raise HTTPException(404, "Conversa expirada ou inexistente. Limpe a conversa para iniciar outra.")
        if conversation.busy:
            raise HTTPException(409, "Aguarde a resposta anterior desta conversa.")
        conversation.busy = True
        return conversation_id, conversation

    def delete(self, conversation_id: str):
        conversation = self.conversations.get(conversation_id)
        if conversation and conversation.busy:
            raise HTTPException(409, "Aguarde a resposta antes de limpar a conversa.")
        self.conversations.pop(conversation_id, None)


conversation_store = ConversationStore()
