"""Live server: the simulation runs in a background thread; browsers watch it over a WebSocket."""

import asyncio
import contextlib
import json
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from rlecosystem.trainer import Trainer

STATIC = Path(__file__).parent / "static"
FPS = 30
SPEEDS = ("watch", "fast")


class Sim:
    """Ticks the trainer: 30 ticks/s in watch mode (real time), as fast as possible in fast mode."""

    def __init__(self, trainer: Trainer):
        self.trainer = trainer
        self.speed = "watch"
        self._frame = ""
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._tick_times: deque[float] = deque()
        self._publish()

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=5)

    def set_speed(self, speed: str) -> None:
        if speed in SPEEDS:
            self.speed = speed

    def frame(self) -> str:
        with self._lock:
            return self._frame

    def _publish(self) -> None:
        snapshot = self.trainer.snapshot()
        snapshot["stats"]["speed"] = self.speed
        snapshot["stats"]["ticks_per_s"] = len(self._tick_times)
        text = json.dumps(snapshot)
        with self._lock:
            self._frame = text

    def _run(self) -> None:
        period = 1 / FPS
        next_tick = last_publish = time.monotonic()
        while not self._stop.is_set():
            if self.speed == "watch":
                wait = next_tick - time.monotonic()
                if wait > 0 and self._stop.wait(wait):
                    break
                # No catching up after a slow tick (a PPO update): blues would jump.
                next_tick = max(next_tick + period, time.monotonic())
            self.trainer.tick()
            now = time.monotonic()
            self._tick_times.append(now)
            while self._tick_times[0] < now - 1.0:
                self._tick_times.popleft()
            if self.speed == "watch" or now - last_publish >= period:
                self._publish()
                last_publish = now


def create_app(sim: Sim) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        sim.start()
        yield
        sim.stop()

    app = FastAPI(lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.websocket("/ws")
    async def watch(ws: WebSocket) -> None:
        await ws.accept()

        async def receive() -> None:
            while True:
                with contextlib.suppress(ValueError, KeyError):  # bad JSON or a binary frame
                    message = json.loads(await ws.receive_text())
                    if isinstance(message, dict):
                        sim.set_speed(message.get("speed"))

        listener = asyncio.create_task(receive())
        try:
            while not listener.done():
                await ws.send_text(sim.frame())
                await asyncio.sleep(1 / FPS)
        except WebSocketDisconnect:
            pass
        finally:
            listener.cancel()
            with contextlib.suppress(asyncio.CancelledError, WebSocketDisconnect):
                await listener

    return app
