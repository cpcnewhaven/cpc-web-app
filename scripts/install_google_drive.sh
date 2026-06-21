#!/bin/bash

echo "🚀 Installing Google Drive Integration for CPC Web App"
echo "=================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

echo "✅ Python and pip are available"

# Install Google Drive dependencies
echo "📦 Installing Google Drive dependencies..."
pip3 install google-api-python-client google-auth-oauthlib google-auth

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Create a simple test script
echo "🧪 Creating test script..."
cat > test_google_drive.py << 'EOF'
#!/usr/bin/env python3
"""Test Google Drive integration"""

try:
    from google_drive_integration import GoogleDriveGalleryManager
    print("✅ Google Drive integration is ready!")
    print("📁 Next steps:")
    print("1. Set up Google Cloud Console credentials")
    print("2. Download credentials.json to project root")
    print("3. Run: python google_drive_integration.py sync")
    print("4. Or use the admin interface at /admin/google-drive")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please check your Python environment and try again.")
EOF

chmod +x test_google_drive.py

echo "✅ Test script created: test_google_drive.py"

# Run the test
echo "🧪 Testing Google Drive integration..."
python3 test_google_drive.py

echo ""
echo "🎉 Google Drive integration setup complete!"
echo ""
echo "Next steps:"
echo "1. Go to https://console.cloud.google.com/"
echo "2. Create a project and enable Google Drive API"
echo "3. Create OAuth 2.0 credentials (Desktop application)"
echo "4. Download credentials.json to your project root"
echo "5. Run: python google_drive_integration.py sync"
echo "6. Or access the admin interface at /admin/google-drive"
echo ""
echo "For help, run: python setup_google_drive.py"
