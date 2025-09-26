#!/bin/bash
# Fix Port Conflicts Script
# Kills processes using common Flask ports

echo "🔧 Fixing port conflicts..."

# Common Flask ports
PORTS=(5001 5000 8000 8080 3000)

for port in "${PORTS[@]}"; do
    echo "Checking port $port..."
    
    # Find processes using the port
    PIDS=$(lsof -ti :$port 2>/dev/null)
    
    if [ ! -z "$PIDS" ]; then
        echo "  Found processes on port $port: $PIDS"
        echo "  Killing processes..."
        
        # Kill each process
        for pid in $PIDS; do
            if kill -9 $pid 2>/dev/null; then
                echo "    ✅ Killed process $pid"
            else
                echo "    ❌ Failed to kill process $pid"
            fi
        done
    else
        echo "  ✅ Port $port is free"
    fi
done

echo ""
echo "🎉 Port cleanup completed!"
echo "You can now run: python start_app.py"
