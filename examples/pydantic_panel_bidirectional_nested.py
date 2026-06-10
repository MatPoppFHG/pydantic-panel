from pydantic import BaseModel

# ── example nested model ─────────────────────────────────────────────────────────────

class SubNestedModel(BaseModel):
    a: int = 1
    b: int = 2

class NestedModel(BaseModel):
    x: float = 1.0
    y: float = 2.0
    z: SubNestedModel = SubNestedModel()

class ExampleModel(BaseModel):
    int_prop: int = 0
    int_prop_2: int = 0
    str_prop: str = "My Operator"
    list_prop: list[int] = [1, 2, 3]
    nested: NestedModel = NestedModel()


model = ExampleModel()

import panel as pn
import pydantic_panel
pn.extension()

widget = pn.panel(model, bidirectional=True)

layout = pn.Row(widget, widget.json)

pn.serve(layout, threaded=True)
