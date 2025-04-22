import os
from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, emit
from functools import wraps
from markupsafe import escape
import secrets

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Configure SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins=os.environ.get('ALLOWED_ORIGINS', '*'),
    logger=bool(os.environ.get('DEBUG')),
    engineio_logger=bool(os.environ.get('DEBUG')),
    async_mode='eventlet'
)

# Authentication decorator
def authenticated_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return f(*args, **kwargs) if session.get('username') else False
    return wrapped

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username'].strip()
        if username:
            session['username'] = escape(username)
            return redirect('/chat')
    return render_template('index.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect('/')
    return render_template('chat.html', username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# SocketIO handlers
@socketio.on('connect')
def handle_connect():
    if session.get('username'):
        emit('status', {'msg': f"{session['username']} has joined"}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if session.get('username'):
        emit('status', {'msg': f"{session['username']} has left"}, broadcast=True)

@socketio.on('message')
@authenticated_only
def handle_message(msg):
    emit('message', {
        'username': session['username'],
        'msg': escape(msg)
    }, broadcast=True)

# Start application (only for development)
if __name__ == '__main__':
    debug_mode = os.environ.get('DEBUG', 'false').lower() == 'true'
    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=debug_mode,
        allow_unsafe_werkzeug=debug_mode
    )
