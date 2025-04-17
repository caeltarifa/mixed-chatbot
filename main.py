import sys
import os

# Add the current directory to the path so we can import from the service folders
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask_service.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)