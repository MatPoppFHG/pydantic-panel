#!/usr/bin/env python
"""Tests for `pydantic_panel` package."""
# pylint: disable=redefined-outer-name

import pydantic_panel
import pytest
import panel as pn
from pydantic import BaseModel


class SomeModel(BaseModel):
    regular_string: str = "string"
    regular_int: int = 42
    regular_float: float = 0.999


alt_data = dict(
    regular_string="string2",
    regular_int=666,
    regular_float=0.111,
)


class LeafModel(BaseModel):
    a: int = 1
    b: int = 2


class NestedModel(BaseModel):
    x: float = 1.0
    y: float = 2.0
    leaf: LeafModel = LeafModel()


class OuterModel(BaseModel):
    name: str = "outer"
    inner: NestedModel = NestedModel()


def test_panel_model_class():
    w = pn.panel(SomeModel)
    assert isinstance(w, pydantic_panel.PydanticModelEditor)
    assert w.value == SomeModel()


def test_panel_model_instance():
    w = pn.panel(SomeModel())
    assert isinstance(w, pydantic_panel.PydanticModelEditor)
    assert w.value == SomeModel()


def test_set_data():
    m = SomeModel()
    w = pn.panel(m)
    for k, v in alt_data.items():
        w._widgets[k].value = v
        assert getattr(w.value, k) == v
    assert w.value == m


def test_bidirectional():
    m = SomeModel()
    w = pn.panel(m, bidirectional=True)
    for k, v in alt_data.items():
        setattr(m, k, v)
        assert w._widgets[k].value == v
    assert w.value == m


def test_bidirectional_nested_widget_to_model():
    """Editing a nested widget updates the underlying model in-place."""
    m = OuterModel()
    w = pydantic_panel.infer_widget(m, bidirectional=True)

    w._widgets["inner"]._widgets["x"].value = 9.9
    assert m.inner.x == 9.9

    w._widgets["inner"]._widgets["leaf"]._widgets["a"].value = 42
    assert m.inner.leaf.a == 42


def test_bidirectional_nested_model_to_widget():
    """Setting a nested model attribute from Python updates the widget."""
    m = OuterModel()
    w = pydantic_panel.infer_widget(m, bidirectional=True)

    m.inner.x = 7.77
    assert w._widgets["inner"]._widgets["x"].value == 7.77

    m.inner.leaf.b = 55
    assert w._widgets["inner"]._widgets["leaf"]._widgets["b"].value == 55
