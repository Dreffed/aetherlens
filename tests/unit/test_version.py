"""Test version information and package metadata."""

import aetherlens


def test_version_exists():
    """Test that __version__ is defined."""
    assert hasattr(aetherlens, "__version__")
    assert isinstance(aetherlens.__version__, str)
    assert aetherlens.__version__ == "1.0.0"


def test_version_format():
    """Test that version follows semantic versioning."""
    version = aetherlens.__version__
    parts = version.split(".")
    assert len(parts) == 3, "Version should be in format X.Y.Z"
    # Check all parts are numeric
    for part in parts:
        assert part.isdigit(), f"Version part '{part}' should be numeric"


def test_package_attributes():
    """Test that package has required metadata attributes."""
    assert hasattr(aetherlens, "__author__")
    assert hasattr(aetherlens, "__license__")

    assert isinstance(aetherlens.__author__, str)
    assert isinstance(aetherlens.__license__, str)

    assert aetherlens.__license__ == "MIT"
    assert len(aetherlens.__author__) > 0


def test_package_is_importable():
    """Test that main package components are importable."""
    # These should not raise ImportError
    from aetherlens import config  # noqa: F401

    # Config module should have Settings class
    assert hasattr(config, "Settings")
