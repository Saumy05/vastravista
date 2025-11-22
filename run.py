"""
VastraVista Application Entry Point
"""

from app import create_app
from app.models.model_loader import model_loader

app = create_app('development')

with app.app_context():
    print("\n🎨 VastraVista - Loading models...")
    model_status = model_loader.load_all_models()
    print(f"✅ Models loaded: {model_status['total_loaded']}/3\n")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True, threaded=True)
