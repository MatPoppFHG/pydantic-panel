from pydantic import BaseModel

class SomeModel(BaseModel):
    name: str
    value: float

model = SomeModel(name="meaning", value=42)

import panel as pn
import pydantic_panel
pn.extension()

#widget = pn.panel(model)
widget = pn.panel(model, bidirectional=True)

layout = pn.Column(widget, widget.json)

pn.serve(layout, threaded=True)