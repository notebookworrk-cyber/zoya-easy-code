import sys
import os
import time
import math
import unittest
from typing import List, Optional

sys.path.insert(0, r"C:\Users\hp\zoya3")

from zoya.mobile import (
    Widget, Label, Button, TextField, Image, ListView, ScrollView,
    Column, Row, Card, Switch, Slider, ProgressBar, Spinner, Toast,
    Modal, Screen, Navigator, App, NativeBridge, IOSBridge, AndroidBridge,
    MobileError, create_mobile_app,
)
from zoya.mobile.gestures import (
    TouchEvent, GestureRecognizer, TapRecognizer, DoubleTapRecognizer,
    LongPressRecognizer, SwipeRecognizer, PinchRecognizer, PanRecognizer,
    GestureDetector,
)


class TestWidgetBase(unittest.TestCase):
    def test_widget_default_properties(self):
        w = Widget(widget_id="test1")
        self.assertEqual(w.id, "test1")
        self.assertEqual(w.x, 0)
        self.assertEqual(w.y, 0)
        self.assertEqual(w.width, 100)
        self.assertEqual(w.height, 50)
        self.assertTrue(w.visible)
        self.assertTrue(w.enabled)

    def test_widget_repr(self):
        w = Widget(widget_id="w1")
        r = repr(w)
        self.assertIn("Widget", r)
        self.assertIn("w1", r)

    def test_widget_custom_position(self):
        w = Widget(widget_id="p", x=10, y=20, width=200, height=100)
        self.assertEqual(w.x, 10)
        self.assertEqual(w.y, 20)
        self.assertEqual(w.width, 200)
        self.assertEqual(w.height, 100)


class TestLabel(unittest.TestCase):
    def test_create_label(self):
        lbl = Label("Hello", widget_id="l1")
        self.assertEqual(lbl.text, "Hello")
        self.assertEqual(lbl.font_size, 16)
        self.assertEqual(lbl.id, "l1")

    def test_label_custom_font(self):
        lbl = Label("Title", font_size=24, widget_id="title")
        self.assertEqual(lbl.font_size, 24)

    def test_label_is_widget(self):
        lbl = Label("Hi")
        self.assertIsInstance(lbl, Widget)


class TestButton(unittest.TestCase):
    def test_create_button(self):
        btn = Button("Click", widget_id="b1")
        self.assertEqual(btn.text, "Click")
        self.assertIsNone(btn.on_click)

    def test_button_on_click_fires(self):
        calls = []

        def handler():
            calls.append(True)

        btn = Button("Go", on_click=handler)
        btn.press()
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0])

    def test_button_disabled_does_not_fire(self):
        calls = []

        def handler():
            calls.append(True)

        btn = Button("Go", on_click=handler)
        btn.enabled = False
        btn.press()
        self.assertEqual(len(calls), 0)

    def test_button_press_no_callback(self):
        btn = Button("NoOp")
        btn.press()

    def test_button_is_widget(self):
        btn = Button("Hi")
        self.assertIsInstance(btn, Widget)


class TestTextField(unittest.TestCase):
    def test_create_text_field(self):
        tf = TextField(placeholder="Enter name", widget_id="tf1")
        self.assertEqual(tf.placeholder, "Enter name")
        self.assertEqual(tf.text, "")

    def test_set_text_triggers_on_change(self):
        results = []

        def handler(val):
            results.append(val)

        tf = TextField(on_change=handler)
        tf.set_text("hello")
        self.assertEqual(tf.text, "hello")
        self.assertEqual(results, ["hello"])

    def test_set_text_no_callback(self):
        tf = TextField()
        tf.set_text("world")
        self.assertEqual(tf.text, "world")

    def test_text_field_is_widget(self):
        tf = TextField()
        self.assertIsInstance(tf, Widget)


class TestImage(unittest.TestCase):
    def test_create_image(self):
        img = Image("photo.jpg", widget_id="img1")
        self.assertEqual(img.source, "photo.jpg")
        self.assertEqual(img.width, 100)
        self.assertEqual(img.height, 100)

    def test_image_is_widget(self):
        img = Image("pic.png")
        self.assertIsInstance(img, Widget)


class TestListView(unittest.TestCase):
    def test_create_list_view(self):
        items = ["a", "b", "c"]
        lv = ListView(items, widget_id="lv1")
        self.assertEqual(lv.items, items)
        self.assertIsNone(lv.on_select)

    def test_list_view_select_triggers_callback(self):
        results = []

        def handler(item):
            results.append(item)

        lv = ListView(["x", "y", "z"], on_select=handler)
        lv.select(1)
        self.assertEqual(results, ["y"])

    def test_list_view_select_out_of_range(self):
        def handler(item):
            pass

        lv = ListView(["a"], on_select=handler)
        lv.select(99)

    def test_list_view_is_widget(self):
        lv = ListView([])
        self.assertIsInstance(lv, Widget)


class TestScrollView(unittest.TestCase):
    def test_scroll_view_wraps_content(self):
        content = Label("Scrolling", widget_id="inner")
        sv = ScrollView(content, widget_id="sv1")
        self.assertIs(sv.content, content)
        self.assertEqual(sv.id, "sv1")

    def test_scroll_view_is_widget(self):
        sv = ScrollView(Label("x"))
        self.assertIsInstance(sv, Widget)


class TestLayoutWidgets(unittest.TestCase):
    def test_column_contains_children(self):
        lbl1 = Label("A")
        lbl2 = Label("B")
        col = Column([lbl1, lbl2], widget_id="col1")
        self.assertEqual(len(col.children), 2)
        self.assertIs(col.children[0], lbl1)

    def test_column_add_child(self):
        col = Column([])
        lbl = Label("X")
        col.add(lbl)
        self.assertIn(lbl, col.children)

    def test_column_remove_child(self):
        lbl = Label("Y")
        col = Column([lbl])
        col.remove(lbl)
        self.assertNotIn(lbl, col.children)

    def test_row_contains_children(self):
        lbl1 = Label("Left")
        lbl2 = Label("Right")
        row = Row([lbl1, lbl2], widget_id="row1")
        self.assertEqual(len(row.children), 2)

    def test_row_add_child(self):
        row = Row([])
        lbl = Label("N")
        row.add(lbl)
        self.assertIn(lbl, row.children)

    def test_row_remove_child(self):
        lbl = Label("M")
        row = Row([lbl])
        row.remove(lbl)
        self.assertNotIn(lbl, row.children)

    def test_column_is_widget(self):
        col = Column([])
        self.assertIsInstance(col, Widget)

    def test_row_is_widget(self):
        row = Row([])
        self.assertIsInstance(row, Widget)


class TestCard(unittest.TestCase):
    def test_card_has_title_and_content(self):
        content = Label("Card body")
        card = Card("My Title", content, widget_id="c1")
        self.assertEqual(card.title, "My Title")
        self.assertIs(card.content, content)

    def test_card_is_widget(self):
        card = Card("T", Label("C"))
        self.assertIsInstance(card, Widget)


class TestSwitch(unittest.TestCase):
    def test_switch_default_off(self):
        sw = Switch(widget_id="sw1")
        self.assertFalse(sw.value)

    def test_switch_toggle_state(self):
        sw = Switch(value=True)
        sw.toggle()
        self.assertFalse(sw.value)
        sw.toggle()
        self.assertTrue(sw.value)

    def test_switch_toggle_triggers_callback(self):
        results = []

        def handler(val):
            results.append(val)

        sw = Switch(on_toggle=handler)
        sw.toggle()
        self.assertTrue(results[0])

    def test_switch_is_widget(self):
        sw = Switch()
        self.assertIsInstance(sw, Widget)


class TestSlider(unittest.TestCase):
    def test_slider_default_values(self):
        sl = Slider(widget_id="sl1")
        self.assertEqual(sl.min, 0)
        self.assertEqual(sl.max, 100)
        self.assertEqual(sl.value, 50)

    def test_slider_value_range(self):
        sl = Slider(min_value=0, max_value=10, value=5)
        sl.set_value(12)
        self.assertEqual(sl.value, 10)
        sl.set_value(-1)
        self.assertEqual(sl.value, 0)

    def test_slider_set_value_triggers_callback(self):
        results = []

        def handler(val):
            results.append(val)

        sl = Slider(on_change=handler)
        sl.set_value(75)
        self.assertEqual(sl.value, 75)
        self.assertEqual(results, [75])

    def test_slider_is_widget(self):
        sl = Slider()
        self.assertIsInstance(sl, Widget)


class TestProgressBar(unittest.TestCase):
    def test_progress_default(self):
        pb = ProgressBar(widget_id="pb1")
        self.assertEqual(pb.value, 0)
        self.assertEqual(pb.max, 100)

    def test_progress_percentage(self):
        pb = ProgressBar(value=50, max_value=200)
        self.assertEqual(pb.percentage, 25.0)

    def test_progress_zero_max(self):
        pb = ProgressBar(value=10, max_value=0)
        self.assertEqual(pb.percentage, 0.0)

    def test_progress_full(self):
        pb = ProgressBar(value=100, max_value=100)
        self.assertEqual(pb.percentage, 100.0)

    def test_progress_bar_is_widget(self):
        pb = ProgressBar()
        self.assertIsInstance(pb, Widget)


class TestSpinner(unittest.TestCase):
    def test_spinner_created(self):
        sp = Spinner(widget_id="sp1")
        self.assertEqual(sp.id, "sp1")

    def test_spinner_is_widget(self):
        sp = Spinner()
        self.assertIsInstance(sp, Widget)


class TestToast(unittest.TestCase):
    def test_toast_has_message_and_duration(self):
        t = Toast("Saved!", duration=3.0, widget_id="t1")
        self.assertEqual(t.message, "Saved!")
        self.assertEqual(t.duration, 3.0)

    def test_toast_default_duration(self):
        t = Toast("Hello")
        self.assertEqual(t.duration, 2.0)

    def test_toast_is_widget(self):
        t = Toast("Msg")
        self.assertIsInstance(t, Widget)


class TestModal(unittest.TestCase):
    def test_modal_initial_state(self):
        content = Label("Modal content")
        m = Modal(content, widget_id="m1")
        self.assertIs(m.content, content)
        self.assertFalse(m.is_open)
        self.assertTrue(m.visible)

    def test_modal_open_close(self):
        m = Modal(Label("C"))
        m.open()
        self.assertTrue(m.is_open)
        self.assertTrue(m.visible)
        m.close()
        self.assertFalse(m.is_open)
        self.assertFalse(m.visible)

    def test_modal_is_widget(self):
        m = Modal(Label("C"))
        self.assertIsInstance(m, Widget)


class TestScreen(unittest.TestCase):
    def test_create_screen(self):
        s = Screen("home", title="Home Screen")
        self.assertEqual(s.name, "home")
        self.assertEqual(s.title, "Home Screen")
        self.assertEqual(len(s.widgets), 0)

    def test_screen_title_defaults_to_name(self):
        s = Screen("settings")
        self.assertEqual(s.title, "settings")

    def test_add_widget(self):
        s = Screen("test")
        lbl = Label("Hello")
        s.add_widget(lbl)
        self.assertIn(lbl, s.widgets)
        self.assertEqual(len(s.widgets), 1)

    def test_remove_widget(self):
        s = Screen("test")
        lbl = Label("Hello")
        s.add_widget(lbl)
        s.remove_widget(lbl)
        self.assertNotIn(lbl, s.widgets)

    def test_remove_nonexistent_widget(self):
        s = Screen("test")
        s.remove_widget(Label("X"))
        self.assertEqual(len(s.widgets), 0)

    def test_lifecycle_on_load(self):
        s = Screen("test")
        s.on_load()

    def test_lifecycle_on_unload(self):
        s = Screen("test")
        s.on_unload()

    def test_lifecycle_on_appear(self):
        s = Screen("test")
        s.on_appear()

    def test_lifecycle_on_disappear(self):
        s = Screen("test")
        s.on_disappear()

    def test_build_returns_widgets(self):
        s = Screen("test")
        lbl1 = Label("A")
        lbl2 = Label("B")
        s.add_widget(lbl1)
        s.add_widget(lbl2)
        widgets = s.build()
        self.assertEqual(len(widgets), 2)
        self.assertIs(widgets[0], lbl1)


class TestNavigator(unittest.TestCase):
    def setUp(self):
        self.nav = Navigator()

    def test_push_adds_to_history(self):
        s = Screen("home")
        self.nav.push(s)
        self.assertEqual(self.nav.get_history(), ["home"])

    def test_get_current_returns_top(self):
        self.nav.push(Screen("a"))
        self.nav.push(Screen("b"))
        current = self.nav.get_current()
        self.assertEqual(current.name, "b")

    def test_pop_removes_last(self):
        self.nav.push(Screen("a"))
        self.nav.push(Screen("b"))
        self.nav.pop()
        self.assertEqual(self.nav.get_history(), ["a"])

    def test_replace_swaps_current(self):
        self.nav.push(Screen("a"))
        self.nav.replace(Screen("b"))
        self.assertEqual(self.nav.get_history(), ["b"])

    def test_pop_to_root(self):
        self.nav.push(Screen("a"))
        self.nav.push(Screen("b"))
        self.nav.push(Screen("c"))
        self.nav.pop_to_root()
        self.assertEqual(self.nav.get_history(), ["a"])

    def test_can_go_back_true(self):
        self.nav.push(Screen("a"))
        self.nav.push(Screen("b"))
        self.assertTrue(self.nav.can_go_back())

    def test_can_go_back_false_single(self):
        self.nav.push(Screen("a"))
        self.assertFalse(self.nav.can_go_back())

    def test_can_go_back_false_empty(self):
        self.assertFalse(self.nav.can_go_back())

    def test_pop_on_empty_does_nothing(self):
        self.nav.pop()
        self.assertIsNone(self.nav.get_current())

    def test_get_current_empty_returns_none(self):
        self.assertIsNone(self.nav.get_current())

    def test_push_pop_sequence(self):
        self.nav.push(Screen("a"))
        self.nav.push(Screen("b"))
        self.nav.push(Screen("c"))
        self.nav.pop()
        self.assertEqual(self.nav.get_current().name, "b")
        self.nav.pop()
        self.assertEqual(self.nav.get_current().name, "a")
        self.nav.pop()
        self.assertIsNone(self.nav.get_current())

    def test_replace_on_empty_stack(self):
        self.nav.replace(Screen("first"))
        self.assertEqual(self.nav.get_history(), ["first"])


class TestNavigatorLifecycle(unittest.TestCase):
    def test_push_calls_on_load_and_on_appear(self):
        nav = Navigator()
        events = []

        class TestScreen(Screen):
            def on_load(self):
                events.append("load")

            def on_appear(self):
                events.append("appear")

        s = TestScreen("test")
        nav.push(s)
        self.assertEqual(events, ["load", "appear"])

    def test_pop_calls_disappear_and_unload(self):
        nav = Navigator()
        events = []

        class TestScreen(Screen):
            def on_disappear(self):
                events.append("disappear")

            def on_unload(self):
                events.append("unload")

        s = TestScreen("test")
        nav.push(s)
        nav.pop()
        self.assertEqual(events, ["disappear", "unload"])

    def test_pop_restores_previous_appear(self):
        nav = Navigator()
        events = []

        class Tracker(Screen):
            def on_appear(self):
                events.append(f"appear_{self.name}")
            def on_disappear(self):
                events.append(f"disappear_{self.name}")

        s1 = Tracker("a")
        s2 = Tracker("b")
        nav.push(s1)
        nav.push(s2)
        nav.pop()
        self.assertIn("disappear_b", events)
        self.assertIn("appear_a", events)


class TestApp(unittest.TestCase):
    def test_create_mobile_app_returns_app(self):
        app = create_mobile_app()
        self.assertIsInstance(app, App)

    def test_create_mobile_app_with_name(self):
        app = create_mobile_app("TestApp")
        self.assertEqual(app.name, "TestApp")

    def test_app_initializes_with_defaults(self):
        app = App(name="MyApp", version="2.0.0")
        self.assertEqual(app.name, "MyApp")
        self.assertEqual(app.version, "2.0.0")
        self.assertEqual(app.initial_route, "")
        self.assertIsNotNone(app.navigator)
        self.assertIsInstance(app.screens, dict)

    def test_add_screen(self):
        app = App()
        s = Screen("home")
        app.add_screen("home", s)
        self.assertIn("home", app.screens)
        self.assertIs(app.screens["home"], s)

    def test_get_screen(self):
        app = App()
        s = Screen("home")
        app.add_screen("home", s)
        self.assertIs(app.get_screen("home"), s)

    def test_get_screen_missing(self):
        app = App()
        self.assertIsNone(app.get_screen("nonexistent"))

    def test_initial_route_default(self):
        app = App()
        self.assertEqual(app.initial_route, "")

    def test_set_initial_route(self):
        app = App()
        app.set_initial_route("home")
        self.assertEqual(app.initial_route, "home")

    def test_theme_configuration(self):
        app = App()
        self.assertEqual(app.theme["primary_color"], "#007AFF")
        self.assertEqual(app.theme["background_color"], "#FFFFFF")
        self.assertEqual(app.theme["spacing"], 8)

    def test_navigator_is_initialized(self):
        app = App()
        self.assertIsInstance(app.navigator, Navigator)

    def test_run_adds_initial_screen_to_navigator(self):
        app = App("Test")
        s = Screen("main")
        app.add_screen("main", s)
        app.set_initial_route("main")
        app.run()
        self.assertIsNotNone(app.navigator.get_current())

    def test_run_missing_route_raises(self):
        app = App()
        app.set_initial_route("missing")
        with self.assertRaises(MobileError):
            app.run()


class TestTouchEvent(unittest.TestCase):
    def test_touch_event_creation(self):
        t = TouchEvent(x=100, y=200, timestamp=1.0, pointer_id=0, event_type="down")
        self.assertEqual(t.x, 100)
        self.assertEqual(t.y, 200)
        self.assertEqual(t.timestamp, 1.0)
        self.assertEqual(t.pointer_id, 0)
        self.assertEqual(t.event_type, "down")

    def test_touch_event_defaults(self):
        t = TouchEvent(x=0, y=0, timestamp=0.0)
        self.assertEqual(t.pointer_id, 0)
        self.assertEqual(t.event_type, "down")


class TestTapRecognizer(unittest.TestCase):
    def setUp(self):
        self.r = TapRecognizer()

    def test_detects_single_tap(self):
        down = TouchEvent(x=50, y=50, timestamp=0.0, event_type="down")
        up = TouchEvent(x=51, y=52, timestamp=0.2, event_type="up")
        result = self.r.recognize([down, up])
        self.assertEqual(result, "tap")

    def test_rejects_large_movement(self):
        down = TouchEvent(x=50, y=50, timestamp=0.0, event_type="down")
        up = TouchEvent(x=100, y=50, timestamp=0.2, event_type="up")
        result = self.r.recognize([down, up])
        self.assertIsNone(result)

    def test_rejects_long_duration(self):
        down = TouchEvent(x=50, y=50, timestamp=0.0, event_type="down")
        up = TouchEvent(x=51, y=51, timestamp=1.0, event_type="up")
        result = self.r.recognize([down, up])
        self.assertIsNone(result)

    def test_reset_clears_state(self):
        self.r.recognize([TouchEvent(x=0, y=0, timestamp=0.0, event_type="down")])
        self.r.reset()
        self.assertIsNone(self.r._start_x)

    def test_cancel_resets(self):
        down = TouchEvent(x=0, y=0, timestamp=0.0, event_type="down")
        cancel = TouchEvent(x=0, y=0, timestamp=0.1, event_type="cancel")
        result = self.r.recognize([down, cancel])
        self.assertIsNone(result)


class TestDoubleTapRecognizer(unittest.TestCase):
    def setUp(self):
        self.r = DoubleTapRecognizer()

    def test_detects_double_tap(self):
        down1 = TouchEvent(x=50, y=50, timestamp=0.0, event_type="down")
        up1 = TouchEvent(x=50, y=50, timestamp=0.1, event_type="up")
        down2 = TouchEvent(x=50, y=50, timestamp=0.25, event_type="down")
        up2 = TouchEvent(x=50, y=50, timestamp=0.35, event_type="up")
        self.assertIsNone(self.r.recognize([down1, up1]))
        result = self.r.recognize([down2, up2])
        self.assertEqual(result, "double_tap")

    def test_reset_clears_state(self):
        self.r.reset()
        self.assertIsNone(self.r._last_tap_time)


class TestLongPressRecognizer(unittest.TestCase):
    def setUp(self):
        self.r = LongPressRecognizer(min_duration=0.5)

    def test_detects_long_press(self):
        down = TouchEvent(x=10, y=10, timestamp=0.0, event_type="down")
        move = TouchEvent(x=10, y=10, timestamp=0.6, event_type="move")
        result = self.r.recognize([down, move])
        self.assertEqual(result, "long_press")

    def test_rejects_short_hold(self):
        down = TouchEvent(x=10, y=10, timestamp=0.0, event_type="down")
        move = TouchEvent(x=10, y=10, timestamp=0.1, event_type="move")
        result = self.r.recognize([down, move])
        self.assertIsNone(result)

    def test_up_cancels(self):
        down = TouchEvent(x=10, y=10, timestamp=0.0, event_type="down")
        up = TouchEvent(x=10, y=10, timestamp=0.1, event_type="up")
        result = self.r.recognize([down, up])
        self.assertIsNone(result)

    def test_reset_clears(self):
        self.r.recognize([TouchEvent(x=0, y=0, timestamp=0.0, event_type="down")])
        self.r.reset()
        self.assertFalse(self.r._touching)


class TestSwipeRecognizer(unittest.TestCase):
    def setUp(self):
        self.r = SwipeRecognizer(min_distance=50)

    def test_detects_right_swipe(self):
        down = TouchEvent(x=10, y=100, timestamp=0.0, event_type="down")
        up = TouchEvent(x=100, y=100, timestamp=0.3, event_type="up")
        result = self.r.recognize([down, up])
        self.assertEqual(result, "swipe_right")

    def test_detects_left_swipe(self):
        down = TouchEvent(x=100, y=100, timestamp=0.0, event_type="down")
        up = TouchEvent(x=10, y=100, timestamp=0.3, event_type="up")
        result = self.r.recognize([down, up])
        self.assertEqual(result, "swipe_left")

    def test_detects_down_swipe(self):
        down = TouchEvent(x=100, y=10, timestamp=0.0, event_type="down")
        up = TouchEvent(x=100, y=100, timestamp=0.3, event_type="up")
        result = self.r.recognize([down, up])
        self.assertEqual(result, "swipe_down")

    def test_detects_up_swipe(self):
        down = TouchEvent(x=100, y=100, timestamp=0.0, event_type="down")
        up = TouchEvent(x=100, y=10, timestamp=0.3, event_type="up")
        result = self.r.recognize([down, up])
        self.assertEqual(result, "swipe_up")

    def test_rejects_short_swipe(self):
        down = TouchEvent(x=50, y=50, timestamp=0.0, event_type="down")
        up = TouchEvent(x=55, y=55, timestamp=0.3, event_type="up")
        result = self.r.recognize([down, up])
        self.assertIsNone(result)

    def test_direction_filtering(self):
        r = SwipeRecognizer(min_distance=50, direction="right")
        down = TouchEvent(x=10, y=100, timestamp=0.0, event_type="down")
        up = TouchEvent(x=100, y=100, timestamp=0.3, event_type="up")
        self.assertEqual(r.recognize([down, up]), "swipe_right")
        r.reset()
        down2 = TouchEvent(x=100, y=10, timestamp=0.0, event_type="down")
        up2 = TouchEvent(x=100, y=100, timestamp=0.3, event_type="up")
        self.assertIsNone(r.recognize([down2, up2]))

    def test_cancel_resets(self):
        down = TouchEvent(x=10, y=10, timestamp=0.0, event_type="down")
        cancel = TouchEvent(x=10, y=10, timestamp=0.1, event_type="cancel")
        result = self.r.recognize([down, cancel])
        self.assertIsNone(result)

    def test_reset_clears(self):
        self.r.recognize([TouchEvent(x=0, y=0, timestamp=0.0, event_type="down")])
        self.r.reset()
        self.assertFalse(self.r._touching)


class TestPinchRecognizer(unittest.TestCase):
    def setUp(self):
        self.r = PinchRecognizer(min_scale=0.5)

    def test_detects_pinch_out(self):
        touches = [
            TouchEvent(x=50, y=50, timestamp=0.0, pointer_id=0, event_type="move"),
            TouchEvent(x=150, y=50, timestamp=0.0, pointer_id=1, event_type="move"),
        ]
        self.assertIsNone(self.r.recognize(touches))
        touches2 = [
            TouchEvent(x=20, y=50, timestamp=0.1, pointer_id=0, event_type="move"),
            TouchEvent(x=180, y=50, timestamp=0.1, pointer_id=1, event_type="move"),
        ]
        result = self.r.recognize(touches2)
        self.assertEqual(result, "pinch_out")

    def test_single_pointer_returns_none(self):
        touches = [
            TouchEvent(x=50, y=50, timestamp=0.0, pointer_id=0, event_type="move"),
        ]
        result = self.r.recognize(touches)
        self.assertIsNone(result)

    def test_up_cancels(self):
        touches = [
            TouchEvent(x=50, y=50, timestamp=0.0, pointer_id=0, event_type="down"),
            TouchEvent(x=150, y=50, timestamp=0.0, pointer_id=1, event_type="up"),
        ]
        result = self.r.recognize(touches)
        self.assertIsNone(result)

    def test_reset_clears(self):
        self.r.reset()
        self.assertIsNone(self.r._initial_distance)
        self.assertFalse(self.r._active)


class TestPanRecognizer(unittest.TestCase):
    def setUp(self):
        self.r = PanRecognizer(min_distance=10)

    def test_detects_pan(self):
        down = TouchEvent(x=10, y=10, timestamp=0.0, event_type="down")
        move = TouchEvent(x=50, y=50, timestamp=0.1, event_type="move")
        result = self.r.recognize([down, move])
        self.assertEqual(result, "pan")

    def test_rejects_small_move(self):
        down = TouchEvent(x=10, y=10, timestamp=0.0, event_type="down")
        move = TouchEvent(x=12, y=12, timestamp=0.1, event_type="move")
        result = self.r.recognize([down, move])
        self.assertIsNone(result)

    def test_up_cancels(self):
        down = TouchEvent(x=10, y=10, timestamp=0.0, event_type="down")
        up = TouchEvent(x=50, y=50, timestamp=0.1, event_type="up")
        result = self.r.recognize([down, up])
        self.assertIsNone(result)

    def test_cancel_cancels(self):
        down = TouchEvent(x=10, y=10, timestamp=0.0, event_type="down")
        cancel = TouchEvent(x=10, y=10, timestamp=0.1, event_type="cancel")
        result = self.r.recognize([down, cancel])
        self.assertIsNone(result)

    def test_reset_clears(self):
        self.r.recognize([TouchEvent(x=0, y=0, timestamp=0.0, event_type="down")])
        self.r.reset()
        self.assertFalse(self.r._touching)


class TestGestureDetector(unittest.TestCase):
    def setUp(self):
        self.detector = GestureDetector()

    def test_process_touches_returns_matched_gesture(self):
        tap = TapRecognizer()
        self.detector.add_recognizer(tap)
        touches = [
            TouchEvent(x=50, y=50, timestamp=0.0, event_type="down"),
            TouchEvent(x=51, y=51, timestamp=0.2, event_type="up"),
        ]
        result = self.detector.process_touches(touches)
        self.assertIsNotNone(result)
        gesture, params = result
        self.assertEqual(gesture, "tap")
        self.assertIn("x", params)
        self.assertIn("y", params)
        self.assertIn("timestamp", params)

    def test_no_match_returns_none(self):
        self.detector.add_recognizer(TapRecognizer())
        touches = [
            TouchEvent(x=0, y=0, timestamp=0.0, event_type="down"),
        ]
        result = self.detector.process_touches(touches)
        self.assertIsNone(result)

    def test_recognizer_priority_order(self):
        self.detector.add_recognizer(TapRecognizer())
        self.detector.add_recognizer(SwipeRecognizer(min_distance=50))
        touches = [
            TouchEvent(x=50, y=50, timestamp=0.0, event_type="down"),
            TouchEvent(x=52, y=52, timestamp=0.2, event_type="up"),
        ]
        result = self.detector.process_touches(touches)
        gesture, _ = result
        self.assertEqual(gesture, "tap")

    def test_reset_all_recognizers(self):
        tap = TapRecognizer()
        self.detector.add_recognizer(tap)
        self.detector.recognizers[0]._touching = True
        self.detector.reset()
        self.assertFalse(self.detector.recognizers[0]._touching)


class TestNativeBridge(unittest.TestCase):
    def test_ios_bridge(self):
        bridge = IOSBridge()
        self.assertTrue(bridge.request_permission("camera"))
        info = bridge.get_device_info()
        self.assertEqual(info["platform"], "iOS")
        self.assertIsNotNone(bridge.take_photo())
        self.assertIsNotNone(bridge.pick_file())

    def test_android_bridge(self):
        bridge = AndroidBridge()
        self.assertTrue(bridge.request_permission("location"))
        info = bridge.get_device_info()
        self.assertEqual(info["platform"], "Android")
        self.assertEqual(info["model"], "Pixel 8")

    def test_ios_open_url(self):
        bridge = IOSBridge()
        bridge.open_url("https://example.com")

    def test_android_share_text(self):
        bridge = AndroidBridge()
        bridge.share_text("Hello!")


if __name__ == "__main__":
    unittest.main()
