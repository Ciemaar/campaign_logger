"""Pydantic models for Campaign Logger APIs."""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field


class VariableModel(BaseModel):
    """Model representing a variable."""

    v: Optional[Any] = Field(None, description="Gets or sets the v.")


class EntryModel(BaseModel):
    """Model representing an entry."""

    m: Optional[int] = Field(None, ge=0, le=1024, description="Gets or sets the m.")
    v: Optional[str] = Field(None, description="Gets or sets the v.")
    export: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the export.")
    set: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the set.")


class TableModel(BaseModel):
    """Model representing a table."""

    name: Optional[str] = Field(None, description="Gets or sets the name.")
    explanation: Optional[str] = Field(None, description="Gets or sets the explanation.")
    export: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the export.")
    set: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the set.")
    entries: Optional[List[EntryModel]] = Field(None, description="Gets or sets the entries.")


class FullGeneratorModel(BaseModel):
    """Full generator model."""

    id: Optional[str] = Field(None, description="Gets or sets the identifier.")
    name: Optional[str] = Field(None, description="Gets or sets the name.")
    explanation: Optional[str] = Field(None, description="Gets or sets the explanation.")
    path: Optional[str] = Field(None, description="Gets or sets the path.")
    categories: Optional[List[str]] = Field(None, description="Gets or sets the categories.")
    formatting: Optional[int] = Field(None, description="Gets or sets the formatting. 0 or 1.")
    resultPattern: Optional[str] = Field(None, description="Gets or sets the result pattern.")
    wrapResultInCurlyBraces: Optional[bool] = Field(
        False, description=("Gets or sets a value indicating whether to wrap the result in curly braces.")
    )
    globals: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the globals.")
    variables: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the variables.")
    tables: Optional[List[TableModel]] = Field(None, description="Gets or sets the tables.")


class GeneratorModelContainer(BaseModel):
    """Container for generator models."""


# JSON:API Models


class JsonApiResourceIdentifier(BaseModel):
    """Identifier for a JSON:API resource."""

    type: str
    id: str


class JsonApiRelationshipData(BaseModel):
    """Data for a JSON:API relationship."""

    data: Union[JsonApiResourceIdentifier, List[JsonApiResourceIdentifier]]


class JsonApiResource(BaseModel):
    """A JSON:API resource object."""

    type: str
    id: Optional[str] = None
    attributes: Optional[Dict[str, Union[str, int, float, bool, None]]] = None
    relationships: Optional[Dict[str, JsonApiRelationshipData]] = None
    links: Optional[Dict[str, str]] = None


class JsonApiResponse(BaseModel):
    """A JSON:API response document."""

    data: Union[JsonApiResource, List[JsonApiResource]]
    included: Optional[List[JsonApiResource]] = None
    meta: Optional[Dict[str, Union[str, int, float, bool, None]]] = None
    links: Optional[Dict[str, str]] = None
