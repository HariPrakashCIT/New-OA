from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
import webbrowser

if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 4173), partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).parent / "website")))
    print("OsteoCare AI: http://localhost:4173 — press Ctrl+C to stop.", flush=True)
    webbrowser.open("http://localhost:4173")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
