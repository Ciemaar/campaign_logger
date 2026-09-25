"""The recursive Campaign/Player shape must parse (#90).

``Player.joined_campaigns`` was typed ``list[str]`` while the swagger declares its
items as ``$ref: Campaign``; ``Campaign.joined_players`` is a list of ``Player``,
so the two are mutually recursive. Nothing caught it because ``joined-players``
has never been seen on the wire -- the field existed to satisfy the #44 coverage
count and was never fed real data.

So these tests supply the shape the swagger describes. A field that is declared
but never exercised is a claim, not a behaviour.
"""

import pytest
from pydantic import ValidationError

from campaign_logger.models import Campaign
from campaign_logger.models import Player


def test_a_player_joined_campaign_is_a_campaign_object():
    """The swagger's ``$ref: Campaign``, fed through the model."""
    player = Player.model_validate(
        {
            "email-address": "gm@example.invalid",
            "joined-campaigns": [{"id": "c1", "type": "campaigns", "title": "Steel and Chaos"}],
        }
    )

    assert player.joined_campaigns is not None
    campaign = player.joined_campaigns[0]
    assert isinstance(campaign, Campaign)
    assert campaign.title == "Steel and Chaos"


def test_a_campaign_carrying_nested_players_parses():
    """The full recursion: campaign -> joined player -> joined campaign.

    This is the payload that raised ``ValidationError`` before the fix, and it
    would have done so on a response the server was entitled to send.
    """
    campaign = Campaign.model_validate(
        {
            "id": "c1",
            "type": "campaigns",
            "title": "Steel and Chaos",
            "joined-players": [
                {
                    "email-address": "player@example.invalid",
                    "joined-campaigns": [{"id": "c2", "type": "campaigns", "title": "Another Table"}],
                }
            ],
        }
    )

    assert campaign.joined_players is not None
    player = campaign.joined_players[0]
    assert isinstance(player, Player)
    assert player.joined_campaigns is not None
    assert player.joined_campaigns[0].title == "Another Table"


def test_a_list_of_ids_is_now_rejected():
    """Records the direction of the change.

    The old type accepted ``["c1"]`` and rejected the objects. If someone widens
    this back to ``list[str] | None`` to make a test pass, this fails and says why.
    """
    with pytest.raises(ValidationError):
        Player.model_validate({"joined-campaigns": ["c1", "c2"]})


def test_invited_players_really_is_a_list_of_strings():
    """Not every player list is objects -- ``invitedPlayers`` is genuinely strings.

    Checked against the swagger rather than assumed, so the fix to
    ``joined_campaigns`` does not get copied onto a field that was already right.
    """
    campaign = Campaign.model_validate({"id": "c1", "type": "campaigns", "invited-players": ["a@example.invalid", "b@example.invalid"]})
    assert campaign.invited_players == ["a@example.invalid", "b@example.invalid"]


def test_both_player_lists_stay_optional():
    """Neither field appears on the wire today, so absent must remain valid."""
    campaign = Campaign.model_validate({"id": "c1", "type": "campaigns", "title": "No players here"})
    assert campaign.joined_players is None
    assert campaign.invited_players is None


def test_more_than_twenty_five_players_is_accepted():
    """The swagger's ``maxItems: 25`` is deliberately not enforced on read.

    These models parse what the server sends. Enforcing a maximum would turn an
    unexpected 26th player into a client-side crash rather than data, which is a
    worse outcome than a list longer than the documentation expects.
    """
    campaign = Campaign.model_validate(
        {
            "id": "c1",
            "type": "campaigns",
            "invited-players": [f"p{n}@example.invalid" for n in range(30)],
        }
    )
    assert campaign.invited_players is not None
    assert len(campaign.invited_players) == 30


def test_to_dict_still_round_trips_with_nested_players():
    """``to_dict`` feeds ``json.dumps`` in the CLI, so nesting must stay JSON-safe."""
    import json

    campaign = Campaign.model_validate(
        {
            "id": "c1",
            "type": "campaigns",
            "created-on": "2026-09-16T02:26:10.416000",
            "joined-players": [{"email-address": "p@example.invalid", "joined-campaigns": []}],
        }
    )
    encoded = json.dumps(campaign.to_dict())
    assert "p@example.invalid" in encoded
    assert "2026-09-16T02:26:10.416000" in encoded
