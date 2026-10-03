"""Start command: `.venv/bin/python -m rlecosystem` serves the live world and opens the browser."""

import threading
import webbrowser

import torch
import uvicorn

from rlecosystem.server import Sim, create_app
from rlecosystem.trainer import Trainer

HOST, PORT = "127.0.0.1", 8000


def main() -> None:
    torch.set_num_threads(4)
    app = create_app(Sim(Trainer()))
    url = f"http://{HOST}:{PORT}/"
    print(f"RL Ecosystem running at {url}  (Ctrl+C to stop)")
    threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
