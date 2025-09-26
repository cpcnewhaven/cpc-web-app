#!/usr/bin/env python3
"""
Smart Port Finder
Automatically finds an available port for the Flask application.
"""

import socket
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class PortFinder:
    def __init__(self, preferred_ports: List[int] = None, max_attempts: int = 20):
        """
        Initialize the port finder.
        
        Args:
            preferred_ports: List of preferred ports to try first
            max_attempts: Maximum number of ports to try
        """
        if preferred_ports is None:
            preferred_ports = [5001, 5000, 8000, 8080, 3000, 5002, 5003, 5004, 5005]
        
        self.preferred_ports = preferred_ports
        self.max_attempts = max_attempts
    
    def is_port_available(self, port: int) -> bool:
        """
        Check if a port is available.
        
        Args:
            port: Port number to check
            
        Returns:
            True if port is available, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)  # 1 second timeout
                result = s.connect_ex(('localhost', port))
                return result != 0  # Port is available if connection fails
        except Exception as e:
            logger.warning(f"Error checking port {port}: {e}")
            return False
    
    def find_available_port(self) -> Optional[int]:
        """
        Find an available port.
        
        Returns:
            Available port number or None if no port found
        """
        # First, try preferred ports
        for port in self.preferred_ports:
            if self.is_port_available(port):
                logger.info(f"Found available preferred port: {port}")
                return port
        
        # If no preferred port is available, try random ports
        logger.info("No preferred ports available, trying random ports...")
        
        for attempt in range(self.max_attempts):
            # Try ports in the range 5000-65535
            port = 5000 + (attempt % 1000)
            
            if self.is_port_available(port):
                logger.info(f"Found available port: {port}")
                return port
        
        logger.error(f"Could not find an available port after {self.max_attempts} attempts")
        return None
    
    def get_port_info(self, port: int) -> dict:
        """
        Get information about a port.
        
        Args:
            port: Port number
            
        Returns:
            Dictionary with port information
        """
        return {
            'port': port,
            'available': self.is_port_available(port),
            'url': f'http://localhost:{port}',
            'admin_url': f'http://localhost:{port}/admin'
        }

def find_available_port(preferred_ports: List[int] = None) -> int:
    """
    Convenience function to find an available port.
    
    Args:
        preferred_ports: List of preferred ports to try first
        
    Returns:
        Available port number
        
    Raises:
        RuntimeError: If no available port is found
    """
    finder = PortFinder(preferred_ports)
    port = finder.find_available_port()
    
    if port is None:
        raise RuntimeError("No available ports found. Please free up a port or try again.")
    
    return port

def main():
    """Test the port finder."""
    finder = PortFinder()
    
    print("Testing port availability...")
    
    # Test preferred ports
    for port in finder.preferred_ports:
        info = finder.get_port_info(port)
        status = "✅ Available" if info['available'] else "❌ In Use"
        print(f"Port {port}: {status}")
    
    # Find an available port
    available_port = finder.find_available_port()
    if available_port:
        print(f"\n🎉 Recommended port: {available_port}")
        print(f"   URL: http://localhost:{available_port}")
        print(f"   Admin: http://localhost:{available_port}/admin")
    else:
        print("\n❌ No available ports found")

if __name__ == "__main__":
    main()
