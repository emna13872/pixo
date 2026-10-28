"""`POST /session/token`: lets the app join a LiveKit room where Pixo's agent will meet it.

The app never holds LiveKit secrets. It asks the brain for a short-lived token, joins the
room with it, and the brain's agent is dispatched into the same room.
"""

from __future__ import annotations

import re
import secrets
from datetime import timedelta

from livekit import api
from pydantic import BaseModel, Field, field_validator

from .settings import Settings

TOKEN_TTL = timedelta(minutes=30)
AGENT_NAME = "pixo"
_NICKNAME = re.compile(r"^[\w' -]{1,30}$")


class TokenRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=30)
    session: str = Field(pattern=r"^u[1-9][0-9]*-s[1-9][0-9]*$")

    @field_validator("nickname")
    @classmethod
    def _clean(cls, value: str) -> str:
        value = value.strip()
        if not _NICKNAME.match(value):
            raise ValueError("letters, spaces, ' and - only")
        return value


class TokenResponse(BaseModel):
    url: str
    room: str
    token: str


def make_token(settings: Settings, request: TokenRequest) -> TokenResponse:
    """A token for one child in a new room, which asks LiveKit to dispatch the Pixo agent."""
    room = f"pixo-{request.session}-{secrets.token_hex(4)}"
    token = (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(f"child-{secrets.token_hex(4)}")
        .with_name(request.nickname)
        .with_ttl(TOKEN_TTL)
        .with_grants(api.VideoGrants(room_join=True, room=room))
        .with_room_config(
            api.RoomConfiguration(
                agents=[
                    api.RoomAgentDispatch(
                        agent_name=AGENT_NAME,
                        metadata=request.model_dump_json(),
                    )
                ]
            )
        )
    )
    return TokenResponse(url=settings.livekit_url, room=room, token=token.to_jwt())
