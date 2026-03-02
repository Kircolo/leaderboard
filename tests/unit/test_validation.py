import pytest
from pydantic import TypeAdapter, ValidationError

from app.schemas.identifiers import Identifier
from app.schemas.leaderboard import SubmitScoreRequest


def test_submit_score_request_normalizes_user_id():
    payload = SubmitScoreRequest.model_validate({"user_id": "  alice  ", "score": 10})

    assert payload.user_id == "alice"


def test_submit_score_request_rejects_blank_user_id():
    with pytest.raises(ValidationError):
        SubmitScoreRequest.model_validate({"user_id": "   ", "score": 10})


def test_identifier_type_normalizes_and_trims():
    value = TypeAdapter(Identifier).validate_python("  game_1  ")

    assert value == "game_1"


def test_identifier_type_rejects_spaces_and_invalid_characters():
    with pytest.raises(ValidationError):
        TypeAdapter(Identifier).validate_python("invalid game")
