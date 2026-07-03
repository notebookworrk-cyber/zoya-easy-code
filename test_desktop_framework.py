"""Test the Zoya 4.0 desktop framework."""

import sys
sys.path.insert(0, r"C:\Users\hp\zoya3")

try:
    from zoya.desktop import Window, Widget, create_desktop_app

    print("[OK] All desktop imports succeeded")

    # Test creating app
    app = create_desktop_app()
    assert isinstance(app, Window)
    print("[OK] create_desktop_app returns a Window instance")

    # Test creating widgets and adding to window
    window = Window("Test")
    btn = Widget("Save")
    window.add_widget(btn)
    assert btn in window.widgets
    print("[OK] Window accepts widgets")

    # Test widget callbacks
    called = []

    def cb():
        called.append(True)

    btn.add_button("Click", cb)
    assert "_handlers" in btn.__dict__ and "button" in btn._handlers
    btn._handlers["button"]()
    assert called == [True]
    print("[OK] Widget button callback works")

    print("\n*** ALL DESKTOP TESTS PASSED ***")
except Exception as exc:
    print(f"[FAIL] {type(exc).__name__}: {exc}")
    raise
