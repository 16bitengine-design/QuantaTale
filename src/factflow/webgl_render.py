"""Real-time 3D backdrops for the low-poly profile using three.js in headless Chromium.

Free and GPU-less: Chromium renders WebGL in software (SwiftShader). The bundled scene page and a
vendored copy of three.js (MIT) are served from a local loopback server. This module is optional:
if Playwright or Chromium is missing, callers fall back to the Pillow renderer.
"""
from __future__ import annotations

import functools
import http.server
import io
import threading
from pathlib import Path
from typing import Any

WEB_DIR = Path(__file__).parent / "web"
CHROMIUM_ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]


class WebGLUnavailable(RuntimeError):
    """Raised when the 3D backend cannot start; the caller should fall back."""


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args: Any) -> None:  # keep render logs clean
        pass


class WebGLBackdrop:
    """Context manager that returns a PIL image of the 3D scene for a given moment."""

    def __init__(self, width: int = 720, height: int = 1280) -> None:
        self.width, self.height = width, height
        self._scene = None

    def __enter__(self) -> "WebGLBackdrop":
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise WebGLUnavailable("Playwright is not installed (pip install playwright).") from exc
        handler = functools.partial(_Quiet, directory=str(WEB_DIR))
        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        try:
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(args=CHROMIUM_ARGS)
            self._page = self._browser.new_page(viewport={"width": self.width, "height": self.height})
            self._page.goto(f"http://127.0.0.1:{self._server.server_port}/lowpoly_scene.html?w={self.width}&h={self.height}")
            self._page.wait_for_function("window.ready === true", timeout=60000)
        except Exception as exc:  # browser missing, launch or load failure
            self.__exit__(None, None, None)
            raise WebGLUnavailable(f"Chromium WebGL backend failed to start: {exc}") from exc
        return self

    def __exit__(self, *exc: Any) -> None:
        for name, closer in (("_browser", "close"), ("_pw", "stop"), ("_server", "shutdown")):
            target = getattr(self, name, None)
            if target is not None:
                try:
                    getattr(target, closer)()
                except Exception:
                    pass

    def frame(self, motif: str, seconds: float, progress: float) -> Any:
        from PIL import Image
        if motif != self._scene:
            self._page.evaluate("name => window.setScene(name)", motif)
            self._scene = motif
        self._page.evaluate("([t, p]) => window.renderAt(t, p)", [seconds, max(0.0, min(1.0, progress))])
        return Image.open(io.BytesIO(self._page.screenshot(type="png"))).convert("RGB")
