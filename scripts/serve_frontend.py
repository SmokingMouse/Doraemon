"""Simple HTTP server for frontend."""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config


class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


if __name__ == '__main__':
    # Change to frontend directory
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    os.chdir(frontend_dir)

    port = config.FRONTEND_PORT
    server = HTTPServer(('localhost', port), CORSRequestHandler)
    print(f'Frontend server running on http://localhost:{port}')
    print(f'Open http://localhost:{port}/index.html in your browser')
    server.serve_forever()
