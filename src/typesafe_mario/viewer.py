"""Stdlib window for watching the game while a human or policy plays.

nes_py's pyglet viewer does not start on Python 3.13 on Windows, so frames are
drawn with tkinter instead. Tk reads binary PPM directly, so no image library is needed.
"""

from __future__ import annotations

import tkinter as tk
from typing import Any

import numpy as np

SCALE = 2


class GameViewer:
    def __init__(self, title: str = "typesafe-mario") -> None:
        self._root = tk.Tk()
        self._root.title(title)
        self._root.resizable(False, False)
        self._label = tk.Label(self._root)
        self._label.pack()
        self._image: Any = None
        self._root.update()

    def show(self, frame: np.ndarray) -> None:
        height, width, _ = frame.shape
        ppm = (
            b"P6 %d %d 255\n" % (width, height)
            + np.ascontiguousarray(frame, dtype=np.uint8).tobytes()
        )
        image = tk.PhotoImage(data=ppm, format="PPM").zoom(SCALE)
        self._label.configure(image=image)
        self._image = image
        self._root.update()

    def close(self) -> None:
        self._root.destroy()
