from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, emit
from functools import wraps
import os
from markupsafe import escape

app = Flask(__name__)
app.secret_key = 'd3f4ult_s3cr3t_k3y_ch4ng3_m3!'  
socketio = SocketIO(app, cors_allowed_origins="*")

def authenticated_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get('username'):
            return False
        return f(*args, **kwargs)
    return wrapped

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
    username = session.get('username', 'anon')
    emit('message', {
        'username': username,
        'msg': escape(msg)
    }, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)