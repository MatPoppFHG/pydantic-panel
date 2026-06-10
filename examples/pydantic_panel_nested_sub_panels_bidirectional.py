import threading
import time

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
    nested_1: NestedModel = NestedModel()
    nested_2: NestedModel = NestedModel()


model = ExampleModel()

import panel as pn
import pydantic_panel
pn.extension()

widget_1 = pn.panel(model.nested_1.z, bidirectional=True)
widget_2 = pn.panel(model.nested_2.z, bidirectional=True)

status = pn.pane.Markdown("**Status**: waiting for first update from Python...")

counter = [0]

def update_loop():
    """Background thread: mutates sub-model instances directly from Python.
    Because bidirectional=True, widget_1 and widget_2 update automatically.
    """
    while True:
        time.sleep(2)
        counter[0] += 1
        tick = counter[0]
        if tick % 2 == 1:
            model.nested_1.z.a = tick
            status.object = (
                f"**Tick {tick}**: set `model.nested_1.z.a = {tick}` from Python — "
                f"widget_1 'a' field should now show **{tick}**."
            )
        else:
            model.nested_2.z.b = tick
            status.object = (
                f"**Tick {tick}**: set `model.nested_2.z.b = {tick}` from Python — "
                f"widget_2 'b' field should now show **{tick}**."
            )

threading.Thread(target=update_loop, daemon=True).start()

layout = pn.Column(
    "## Bidirectional Sync: Direct Sub-Model Widgets",
    status,
    pn.Row(
        pn.Column("### nested_1.z", widget_1),
        pn.Column("### nested_2.z", widget_2),
    ),
)

pn.serve(layout, threaded=True)
