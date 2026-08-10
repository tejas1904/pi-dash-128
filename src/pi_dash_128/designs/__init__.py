"""Load dashboard page designs."""

from importlib import import_module


def load_design(name: str):
    """Load the Design class from the selected design folder."""
    if not name.isidentifier():
        raise ValueError(f"Invalid DASHBOARD_DESIGN: {name!r}")

    try:
        module = import_module(f"pi_dash_128.designs.{name}.page")
    except ModuleNotFoundError as error:
        if error.name == f"pi_dash_128.designs.{name}":
            raise ValueError(f"Unknown DASHBOARD_DESIGN: {name!r}") from error
        raise

    return module.Design()
