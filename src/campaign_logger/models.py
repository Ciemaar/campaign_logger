from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class VariableModel(BaseModel):
    v: Optional[Any] = Field(None, description="Gets or sets the v.")

class EntryModel(BaseModel):
    m: Optional[int] = Field(None, ge=0, le=1024, description="Gets or sets the m.")
    v: Optional[str] = Field(None, description="Gets or sets the v.")
    export: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the export.")
    set: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the set.")

class TableModel(BaseModel):
    name: Optional[str] = Field(None, description="Gets or sets the name.")
    explanation: Optional[str] = Field(None, description="Gets or sets the explanation.")
    export: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the export.")
    set: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the set.")
    entries: Optional[List[EntryModel]] = Field(None, description="Gets or sets the entries.")

class FullGeneratorModel(BaseModel):
    id: Optional[str] = Field(None, description="Gets or sets the identifier.")
    name: Optional[str] = Field(None, description="Gets or sets the name.")
    explanation: Optional[str] = Field(None, description="Gets or sets the explanation.")
    path: Optional[str] = Field(None, description="Gets or sets the path.")
    categories: Optional[List[str]] = Field(None, description="Gets or sets the categories.")
    formatting: Optional[int] = Field(None, description="Gets or sets the formatting. 0 or 1.")
    resultPattern: Optional[str] = Field(None, description="Gets or sets the result pattern.")
    wrapResultInCurlyBraces: Optional[bool] = Field(False, description="Gets or sets a value indicating whether to wrap the result in curly braces.")
    globals: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the globals.")
    variables: Optional[Dict[str, VariableModel]] = Field(None, description="Gets or sets the variables.")
    tables: Optional[List[TableModel]] = Field(None, description="Gets or sets the tables.")

class GeneratorModelContainer(BaseModel):
    pass
