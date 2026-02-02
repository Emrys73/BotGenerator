"""Simple HTTP server to serve the space shooter game."""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys
from pathlib import Path

# Set the directory to serve files from (go up to project root)
os.chdir(Path(__file__).parent.parent.parent / "static")

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSRequestHandler)
    print(f"🎮 Game server running on http://localhost:{port}/games/space-shooter/")
    print(f"📁 Serving from: {os.getcwd()}")
    print(f"🌐 Access game at: http://localhost:{port}/games/space-shooter/index.html")
    print("\nPress Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")
        sys.exit(0)

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
