from flask import render_template
from app.api.auth import auth_bp as api_bp

@api_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@api_bp.route('/results', methods=['GET'])
def results():
    return render_template('results.html')
