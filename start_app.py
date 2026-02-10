#!/usr/bin/env python3
"""
Smart Flask App Starter
Handles port conflicts and provides a better startup experience.
"""

import sys
import os
import time
import subprocess
from port_finder import PortFinder, find_available_port

def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import flask
        import flask_sqlalchemy
        import flask_migrate
        import flask_admin
        import requests
        import feedparser
        import schedule
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def kill_process_on_port(port):
    """Kill any process running on the specified port."""
    try:
        # Find process using the port
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"🔄 Killing process {pid} on port {port}")
                    subprocess.run(['kill', '-9', pid], check=False)
            time.sleep(1)  # Give it a moment to release the port
            return True
    except Exception as e:
        print(f"⚠️  Could not kill process on port {port}: {e}")
    
    return False

def start_app_with_port_management():
    """Start the Flask app with smart port management."""
    print("🎙️  CPC New Haven Podcast System")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check for port conflicts
    finder = PortFinder()
    preferred_ports = [6000, 6001, 6002, 6003, 6004, 6005, 5001, 5000, 8000, 8080, 3000]
    
    print("\n🔍 Checking port availability...")
    
    # Check preferred ports
    for port in preferred_ports:
        info = finder.get_port_info(port)
        if info['available']:
            print(f"✅ Port {port} is available")
        else:
            print(f"❌ Port {port} is in use")
    
    # Find available port
    try:
        port = find_available_port(preferred_ports)
        print(f"\n🚀 Starting Flask app on port {port}")
        
        # Set environment variables
        os.environ['FLASK_APP'] = 'app.py'
        os.environ['FLASK_ENV'] = 'development'
        
        # Start the app
        print(f"🌐 Main site: http://localhost:{port}")
        print(f"⚙️  Admin panel: http://localhost:{port}/admin")
        print(f"🔍 Enhanced search: http://localhost:{port}/sermons_enhanced")
        print(f"📊 Analytics: http://localhost:{port}/api/analytics/overview")
        print("\nPress Ctrl+C to stop the server")
        print("-" * 50)
        
        # Import and run the app
        from app import app
        app.run(debug=True, port=port, host='0.0.0.0')
        
    except RuntimeError as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 Troubleshooting options:")
        print("1. Kill processes using ports: lsof -ti :5001 | xargs kill -9")
        print("2. Try a different port range")
        print("3. Restart your terminal")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Flask app...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

def main():
    """Main function."""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--kill-ports':
            # Kill processes on common ports
            ports_to_check = [6000, 6001, 6002, 6003, 6004, 6005, 5001, 5000, 8000, 8080, 3000]
            for port in ports_to_check:
                kill_process_on_port(port)
            print("✅ Attempted to kill processes on common ports")
            return
        elif sys.argv[1] == '--check-ports':
            # Just check port availability
            finder = PortFinder()
            for port in [6000, 6001, 6002, 6003, 6004, 6005, 5001, 5000, 8000, 8080, 3000]:
                info = finder.get_port_info(port)
                status = "✅ Available" if info['available'] else "❌ In Use"
                print(f"Port {port}: {status}")
            return
        elif sys.argv[1] == '--help':
            print("CPC Podcast System - Smart Startup")
            print("Usage:")
            print("  python start_app.py              # Start the app")
            print("  python start_app.py --kill-ports # Kill processes on common ports")
            print("  python start_app.py --check-ports # Check port availability")
            print("  python start_app.py --help       # Show this help")
            return
    
    start_app_with_port_management()

if __name__ == "__main__":
    main()
