"""
WSGI Entry Point for Production
"""

from app import create_app
from app.models.model_loader import model_loader

app = create_app('production')

with app.app_context():
    model_status = model_loader.load_all_models()
    print(f"✅ Models loaded: {model_status['total_loaded']}/3")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
