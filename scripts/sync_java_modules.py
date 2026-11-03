"""Refresh the owned helper modules; never repeat structural source migrations."""
from install_normalized_model import WORKSPACE, copy_modules


def sync(chapter: int | None = None) -> None:
    for number in ((3, 4) if chapter is None else (chapter,)):
        copy_modules(WORKSPACE / "baselines" / f"chapter{number}")


if __name__ == "__main__":
    sync()
    print("Synced model, runtime, integration and search helpers")
