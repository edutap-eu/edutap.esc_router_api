"""Compare every model against the router's OpenAPI document.

This is the test the previous release did not have, and the reason its models had
drifted two revisions behind the server: `AddressView` still carried fields the router
had dropped, `PointView` was missing entirely, and `fullName` was required here while
the router had made it optional and deprecated it. None of that showed up as a failure,
because nothing compared the two.

Refresh the document with `make refresh-spec` and this test says what moved.
"""

import pytest
from pydantic import BaseModel

from edutap.esc_router_api import models


def _model_classes() -> dict[str, type[BaseModel]]:
    """Every schema model the package defines, by class name."""
    return {
        name: obj
        for name, obj in vars(models).items()
        if isinstance(obj, type)
        and issubclass(obj, BaseModel)
        and obj is not BaseModel
        and obj is not models.ESCRouterModel
    }


def test_every_schema_has_a_model(spec: dict) -> None:
    missing = set(spec["components"]["schemas"]) - set(_model_classes())
    assert not missing, f"schemas without a model: {sorted(missing)}"


def test_no_model_outlives_its_schema(spec: dict) -> None:
    """A model for a schema the router no longer publishes is dead weight.

    `IssueResponseView` was exactly that: the router withdrew `POST /cards/issue`
    together with its response schema, and the client kept calling an endpoint that
    had stopped existing.
    """
    extra = set(_model_classes()) - set(spec["components"]["schemas"])
    assert not extra, f"models without a schema: {sorted(extra)}"


@pytest.mark.parametrize("schema_name", sorted(_model_classes()))
def test_fields_match_the_schema(spec: dict, schema_name: str) -> None:
    schema = spec["components"]["schemas"][schema_name]
    model = _model_classes()[schema_name]

    assert set(model.model_fields) == set(schema.get("properties", {})), (
        f"{schema_name}: field names differ from the specification"
    )


@pytest.mark.parametrize("schema_name", sorted(_model_classes()))
def test_required_fields_match_the_schema(spec: dict, schema_name: str) -> None:
    schema = spec["components"]["schemas"][schema_name]
    model = _model_classes()[schema_name]

    required_here = {name for name, field in model.model_fields.items() if field.is_required()}
    assert required_here == set(schema.get("required", [])), (
        f"{schema_name}: required fields differ from the specification"
    )


@pytest.mark.parametrize("schema_name", sorted(_model_classes()))
def test_deprecations_match_the_schema(spec: dict, schema_name: str) -> None:
    """A field the router deprecated must say so here too.

    `fullName` moved from the person to the person-organisation relation. A caller that
    keeps setting it on the person gets no error from the router -- the field is still
    accepted -- so the only warning available is this one, in the type.
    """
    schema = spec["components"]["schemas"][schema_name]
    model = _model_classes()[schema_name]

    deprecated_in_spec = {
        name for name, prop in schema.get("properties", {}).items() if prop.get("deprecated")
    }
    deprecated_here = {
        name for name, field in model.model_fields.items() if field.deprecated is not None
    }
    assert deprecated_here == deprecated_in_spec, (
        f"{schema_name}: deprecated fields differ from the specification"
    )
