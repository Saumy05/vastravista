"""
Entry Point
"""

from app import create_app
import os

app = create_app('development')

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5002'))
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
