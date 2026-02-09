#!/usr/bin/env python3
import argparse
import os
import json
import glob
import webbrowser
import threading
import time
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from pathlib import Path
import socket
import sys

DEFAULT_PORT = 8888
DEFAULT_HOST = '127.0.0.1'
LOCAL_HOSTS = {'127.0.0.1', 'localhost', '::1'}

class CCPeekHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open(os.path.join(os.path.dirname(__file__), 'index.html'), 'rb') as f:
                self.wfile.write(f.read())
        elif parsed_path.path == '/api/conversations':
            self.handle_conversations()
        elif parsed_path.path.startswith('/api/conversation/'):
            conversation_id = parsed_path.path.split('/')[-1]
            self.handle_conversation(conversation_id)
        else:
            super().do_GET()
    
    def handle_conversations(self):
        """Get list of all conversations"""
        claude_dir = os.path.expanduser('~/.claude/projects')
        conversations = []
        
        if os.path.exists(claude_dir):
            for jsonl_file in glob.glob(os.path.join(claude_dir, '**/*.jsonl'), recursive=True):
                try:
                    # Get first message to extract metadata
                    with open(jsonl_file, 'r') as f:
                        first_line = f.readline()
                        if first_line:
                            data = json.loads(first_line)
                            
                            # Get file stats
                            stats = os.stat(jsonl_file)
                            
                            # Try to find first user message for title
                            title = "Untitled Conversation"
                            f.seek(0)
                            for line in f:
                                msg_data = json.loads(line)
                                if msg_data.get('type') == 'user' and msg_data.get('message'):
                                    content = msg_data['message'].get('content', '')
                                    if isinstance(content, str):
                                        title = content[:100] + ('...' if len(content) > 100 else '')
                                    elif isinstance(content, list) and content:
                                        # Handle array format
                                        first_content = content[0]
                                        if isinstance(first_content, dict) and first_content.get('type') == 'text':
                                            text = first_content.get('text', '')
                                            title = text[:100] + ('...' if len(text) > 100 else '')
                                    break
                            
                            conversations.append({
                                'id': os.path.basename(jsonl_file).replace('.jsonl', ''),
                                'path': jsonl_file,
                                'title': title,
                                'timestamp': data.get('timestamp', ''),
                                'modified': stats.st_mtime,
                                'size': stats.st_size
                            })
                except Exception as e:
                    print(f"Error reading {jsonl_file}: {e}")
        
        # Sort by modified time (newest first)
        conversations.sort(key=lambda x: x['modified'], reverse=True)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(conversations).encode())
    
    def handle_conversation(self, conversation_id):
        """Get messages for a specific conversation"""
        claude_dir = os.path.expanduser('~/.claude/projects')
        jsonl_path = None
        
        # Find the file
        for jsonl_file in glob.glob(os.path.join(claude_dir, '**/*.jsonl'), recursive=True):
            if conversation_id in jsonl_file:
                jsonl_path = jsonl_file
                break
        
        if not jsonl_path or not os.path.exists(jsonl_path):
            self.send_error(404, 'Conversation not found')
            return
        
        messages = []
        with open(jsonl_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    messages.append(data)
                except:
                    continue
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(messages).encode())
    
    def log_message(self, format, *args):
        # Suppress request logging
        pass

def find_free_port(start_port=DEFAULT_PORT):
    """Find a free port starting from start_port"""
    port = start_port
    while port < start_port + 100:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            port += 1
    return None

def open_browser(host, port):
    """Open browser after a short delay"""
    time.sleep(0.5)
    url = f'http://{host}:{port}'
    
    # Use xdg-open to respect system's default browser
    try:
        # Use setsid to detach browser from our process group
        subprocess.Popen(['setsid', 'xdg-open', url], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL,
                        start_new_session=True)
    except:
        # Fallback to webbrowser module if xdg-open fails
        try:
            webbrowser.open(url)
        except:
            print(f"Could not auto-open browser. Please visit: {url}")

def resolve_display_host(host):
    """Provide a user-facing host string for status messages."""
    if host not in {'0.0.0.0', '::'}:
        return host

    # Try to guess a non-loopback address for convenience
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('192.0.2.1', 80))  # TEST-NET-1, no traffic sent
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return host


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    default_host = os.environ.get('CCPEEK_HOST', DEFAULT_HOST)
    default_port = int(os.environ.get('CCPEEK_PORT', DEFAULT_PORT))

    env_browser = os.environ.get('CCPEEK_OPEN_BROWSER')
    env_no_browser = os.environ.get('CCPEEK_NO_BROWSER')
    default_open_browser = True
    if env_browser is not None:
        default_open_browser = env_browser.lower() in {'1', 'true', 'yes'}
    elif env_no_browser is not None:
        default_open_browser = env_no_browser.lower() not in {'1', 'true', 'yes'}

    parser = argparse.ArgumentParser(description='Start the CCPeek server')
    parser.add_argument('--host', default=default_host, help='Interface to bind (default: %(default)s)')
    parser.add_argument('--port', type=int, default=default_port, help='Preferred port to bind (default: %(default)s)')
    parser.add_argument('--open-browser', dest='open_browser', action='store_true', help='Open a browser window after startup')
    parser.add_argument('--no-browser', dest='open_browser', action='store_false', help='Do not launch a browser window')
    parser.set_defaults(open_browser=default_open_browser)

    args = parser.parse_args(argv)

    host = args.host
    port = find_free_port(args.port)
    if not port:
        print("Could not find an available port")
        sys.exit(1)

    try:
        httpd = HTTPServer((host, port), CCPeekHandler)
    except OSError as err:
        print(f"Failed to start server on {host}:{port} -> {err}")
        sys.exit(1)

    display_host = resolve_display_host(host)
    print(f"🚀 CCPeek server starting on http://{display_host}:{port}")
    if host in {'0.0.0.0', '::'}:
        print("Listening on all network interfaces")
    print("Press Ctrl+C to stop")

    if args.open_browser and host in LOCAL_HOSTS:
        threading.Thread(target=open_browser, args=(host if host != 'localhost' else '127.0.0.1', port), daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 CCPeek server stopped")
        httpd.shutdown()

if __name__ == '__main__':
    main()
