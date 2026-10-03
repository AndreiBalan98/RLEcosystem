"""The live server, end to end: a real uvicorn in a thread, talked to over HTTP and WebSocket."""

import json
import threading
import time
import urllib.request

import pytest
import uvicorn
from websockets.sync.client import connect

from rlecosystem.server import Sim, create_app
from rlecosystem.trainer import Trainer
from rlecosystem.world import WorldConfig


@pytest.fixture(scope="module")
def server():
    trainer = Trainer(WorldConfig(width=400.0, height=300.0, n_food=10), n_worlds=2, n_blues=2)
    sim = Sim(trainer)
    config = uvicorn.Config(create_app(sim), host="127.0.0.1", port=0, log_level="warning")
    srv = uvicorn.Server(config)
    thread = threading.Thread(target=srv.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not srv.started:
        assert time.monotonic() < deadline, "server did not start"
        time.sleep(0.05)
    port = srv.servers[0].sockets[0].getsockname()[1]
    yield f"127.0.0.1:{port}"
    srv.should_exit = True
    thread.join(timeout=10)


def test_page_is_served(server):
    with urllib.request.urlopen(f"http://{server}/") as response:
        assert response.status == 200
        assert "<canvas" in response.read().decode()


def test_script_is_served(server):
    with urllib.request.urlopen(f"http://{server}/static/app.js") as response:
        assert response.status == 200


def ticks_per_second(ws, seconds=1.5):
    """Let the speed settle, then read the server's measured rate from the latest frame."""
    end = time.monotonic() + seconds
    frame = None
    while time.monotonic() < end:
        frame = json.loads(ws.recv(timeout=5))
    return frame["stats"]["ticks_per_s"]


def test_frames_carry_the_world_and_speed_toggles(server):
    with connect(f"ws://{server}/ws") as ws:
        frame = json.loads(ws.recv(timeout=5))
        assert {"world", "food", "blues", "slices", "stats"} <= frame.keys()
        assert len(frame["food"]) == 10
        assert len(frame["blues"]) == 2 and len(frame["slices"][0]) == 16
        assert frame["stats"]["speed"] == "watch"

        watch = ticks_per_second(ws)
        ws.send(json.dumps({"speed": "fast"}))
        fast = ticks_per_second(ws)
        ws.send(json.dumps({"speed": "watch"}))
        print(f"ticks/s watch {watch} fast {fast}")
        assert 25 <= watch <= 35
        assert fast > 2 * watch
