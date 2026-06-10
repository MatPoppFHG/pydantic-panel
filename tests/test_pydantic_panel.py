#!/usr/bin/env python
"""Tests for `pydantic_panel` package."""
# pylint: disable=redefined-outer-name

import pydantic_panel
import pytest
import panel as pn
from pydantic import BaseModel, Field


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


class ModelWithList(BaseModel):
    items: list[LeafModel] = Field(default_factory=list)


def test_panel_model_class():
    w = pn.panel(SomeModel)
    assert isinstance(w, pydantic_panel.PydanticModelEditor)
    assert w.value == SomeModel()


def test_panel_model_instance():
    w = pn.panel(SomeModel())
    assert isinstance(w, pydantic_panel.PydanticModelEditor)
    assert w.value == SomeModel()


def test_editor_infers_class_from_value():
    """PydanticModelEditor should not require class_ when value is provided."""
    m = SomeModel()
    w = pydantic_panel.PydanticModelEditor(value=m)
    assert w.class_ is SomeModel
    assert len(w.widgets) > 0


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


def test_direct_submodel_widget_bidirectional():
    """Widget created directly for a sub-model instance syncs Python→widget."""
    m = OuterModel()
    leaf = m.inner.leaf
    w = pydantic_panel.infer_widget(leaf, bidirectional=True)
    leaf.a = 99
    assert w._widgets["a"].value == 99
    leaf.b = 77
    assert w._widgets["b"].value == 77


def test_two_direct_submodel_widgets_no_crosstalk():
    """Two widgets for different instances of the same class update independently."""
    leaf1 = LeafModel(a=1, b=2)
    leaf2 = LeafModel(a=10, b=20)
    w1 = pydantic_panel.infer_widget(leaf1, bidirectional=True)
    w2 = pydantic_panel.infer_widget(leaf2, bidirectional=True)
    leaf1.a = 55
    assert w1._widgets["a"].value == 55
    assert w2._widgets["a"].value == 10  # unchanged
    leaf2.b = 88
    assert w2._widgets["b"].value == 88
    assert w1._widgets["b"].value == 2   # unchanged


def test_remove_setattr_callback_restores_class():
    """remove_setattr_callback must restore exactly the original class, not object."""
    from pydantic_panel.widgets import add_setattr_callback, remove_setattr_callback
    leaf = LeafModel()
    cb = lambda name, value: None
    add_setattr_callback(leaf, cb)
    assert issubclass(leaf.__class__, LeafModel)
    remove_setattr_callback(leaf, cb)
    assert leaf.__class__ is LeafModel


class NestedWithList(BaseModel):
    model_list: list[LeafModel] = Field(default_factory=list)


class OuterWithList(BaseModel):
    nested: NestedWithList = NestedWithList()


def test_bidirectional_list_append_from_python():
    """Appending to a list field from Python updates the ItemListEditor."""
    m = ModelWithList(items=[LeafModel(a=1)])
    w = pydantic_panel.infer_widget(m, bidirectional=True)
    list_w = w._widgets["items"]
    assert len(list_w.value) == 1
    m.items.append(LeafModel(a=2, b=3))
    assert len(list_w.value) == 2
    assert list_w.value[1].a == 2


def test_bidirectional_list_pop_from_python():
    """Popping from a list field from Python updates the ItemListEditor."""
    m = ModelWithList(items=[LeafModel(a=1), LeafModel(a=2)])
    w = pydantic_panel.infer_widget(m, bidirectional=True)
    list_w = w._widgets["items"]
    m.items.pop()
    assert len(list_w.value) == 1


def test_bidirectional_nested_list_append_from_python():
    """Appending to a list field on a nested model updates the nested ItemListEditor."""
    m = OuterWithList()
    w = pydantic_panel.infer_widget(m, bidirectional=True)
    m.nested.model_list.append(LeafModel(a=5))
    list_w = w._widgets["nested"]._widgets["model_list"]
    assert len(list_w.value) == 1
    assert list_w.value[0].a == 5


def test_list_of_models_empty():
    """An empty list[BaseModel] field creates an ItemListEditor with the correct item class."""
    m = ModelWithList()
    w = pydantic_panel.infer_widget(m)
    list_w = w._widgets["items"]
    assert isinstance(list_w, pydantic_panel.ItemListEditor)
    assert list_w.class_ is LeafModel


def test_list_of_models_nonempty():
    """A non-empty list[BaseModel] field renders each item as a PydanticModelEditor."""
    m = ModelWithList(items=[LeafModel(a=10, b=20), LeafModel(a=30, b=40)])
    w = pydantic_panel.infer_widget(m)
    list_w = w._widgets["items"]
    assert isinstance(list_w, pydantic_panel.ItemListEditor)
    assert list_w.class_ is LeafModel
    assert isinstance(list_w._widgets[0], pydantic_panel.PydanticModelEditor)
    assert list_w._widgets[0].value.a == 10
    assert list_w._widgets[1].value.b == 40
