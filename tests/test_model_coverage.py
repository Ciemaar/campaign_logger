"""#44: the resource models must cover every scalar attribute the API defines.

Encoded as a test rather than a prose audit: if the API grows a scalar and the
model does not model it, this fails and names the gap. The expected sets are the
scalar attributes from the Campaign Logger v3 swagger (collections and
relationships excluded); update them together with the models when the API
changes.

Attribute keys are the kebab-case the wire uses, which is exactly what each
model's alias generator produces from its snake_case field names.
"""

import pytest

from campaign_logger.models import Campaign
from campaign_logger.models import CampaignEntry
from campaign_logger.models import Log
from campaign_logger.models import LogEntry
from campaign_logger.models import PlayerLog
from campaign_logger.models import PlayerLogEntry

# Scalar attributes per resource, kebab-case, from the swagger definition.
EXPECTED_SCALARS = {
    Campaign: [
        "created-on",
        "deleted-on",
        "description",
        "id",
        "image-url",
        "invited-players",
        "is-deleted",
        "joined-players",
        "previous-revision",
        "revision",
        "string-id",
        "title",
        "updated-on",
        "user-id",
    ],
    Log: [
        "campaign-id",
        "created-on",
        "deleted-on",
        "description",
        "id",
        "image-url",
        "is-deleted",
        "is-pinned",
        "previous-revision",
        "revision",
        "string-id",
        "title",
        "updated-on",
        "user-id",
    ],
    LogEntry: [
        "created-on",
        "deleted-on",
        "id",
        "is-deleted",
        "is-shared",
        "log-id",
        "ordering",
        "previous-revision",
        "raw-prefix",
        "raw-suffix",
        "raw-text",
        "revision",
        "string-id",
        "title",
        "updated-on",
        "user-id",
    ],
    CampaignEntry: [
        "campaign-id",
        "created-on",
        "deleted-on",
        "id",
        "is-deleted",
        "labels",
        "previous-revision",
        "raw-public",
        "raw-summary",
        "raw-text",
        "revision",
        "string-id",
        "tag-symbol",
        "tag-value",
        "tag-value-case-insensitive",
        "updated-on",
        "user-id",
    ],
    PlayerLog: [
        "campaign-id",
        "created-on",
        "deleted-on",
        "description",
        "id",
        "image-url",
        "is-deleted",
        "is-pinned",
        "previous-revision",
        "revision",
        "string-id",
        "title",
        "updated-on",
        "user-id",
    ],
    PlayerLogEntry: [
        "created-on",
        "deleted-on",
        "id",
        "is-deleted",
        "is-shared",
        "log-id",
        "ordering",
        "previous-revision",
        "raw-prefix",
        "raw-suffix",
        "raw-text",
        "revision",
        "string-id",
        "title",
        "updated-on",
        "user-id",
    ],
}


def _model_wire_keys(model) -> set[str]:
    """The wire keys a model accepts: each field's alias, or its name if none."""
    return {(field.alias or name) for name, field in model.model_fields.items()}


@pytest.mark.parametrize("model", list(EXPECTED_SCALARS), ids=lambda m: m.__name__)
def test_model_covers_every_swagger_scalar(model):
    expected = set(EXPECTED_SCALARS[model])
    actual = _model_wire_keys(model)
    missing = expected - actual
    assert not missing, f"{model.__name__} does not model these swagger scalars: {sorted(missing)}"  # nosec


@pytest.mark.parametrize("model", list(EXPECTED_SCALARS), ids=lambda m: m.__name__)
def test_no_stray_camelcase_aliases(model):
    """Every alias is kebab-case (what the wire sends), never camelCase."""
    camel = {k for k in _model_wire_keys(model) if any(c.isupper() for c in k)}
    assert not camel, f"{model.__name__} has non-kebab aliases: {sorted(camel)}"  # nosec
