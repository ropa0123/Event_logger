import os
import json
import csv
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from io import StringIO, BytesIO

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

USERS_FILE = 'users.json'
EVENTS_FILE = 'schedule_log.json'

def load_json_file(filename, default=None):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default if default is not None else {}
    return default if default is not None else {}

def save_json_file(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_users():
    users = load_json_file(USERS_FILE, {})
    if not users:
        users = {
            "admin": {"password": hash_password("admin123"), "role": "admin", "name": "Administrator"},
            "user": {"password": hash_password("user123"), "role": "user", "name": "Regular User"}
        }
        save_json_file(USERS_FILE, users)
    return users

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        users = load_json_file(USERS_FILE, {})
        if users.get(session['username'], {}).get('role') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users = load_json_file(USERS_FILE, {})
        if username in users and users[username]['password'] == hash_password(password):
            session['username'] = username
            session['name'] = users[username]['name']
            session['role'] = users[username]['role']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    events = load_json_file(EVENTS_FILE, [])
    
    total_events = len(events)
    clients = {}
    delivery_types = {}
    
    for event in events:
        client = event.get('client', 'Unknown')
        delivery = event.get('delivery_type', 'Unknown')
        clients[client] = clients.get(client, 0) + 1
        delivery_types[delivery] = delivery_types.get(delivery, 0) + 1
    
    recent_events = sorted(events, key=lambda x: x.get('timestamp', ''), reverse=True)[:5]
    
    stats = {
        'total_events': total_events,
        'unique_clients': len(clients),
        'delivery_types': len(delivery_types)
    }
    
    return render_template('dashboard.html', stats=stats, recent_events=recent_events)

@app.route('/events')
@login_required
def events():
    events_data = load_json_file(EVENTS_FILE, [])
    
    date_filter = request.args.get('date')
    client_filter = request.args.get('client')
    
    if date_filter:
        events_data = [e for e in events_data if e.get('date') == date_filter]
    if client_filter:
        events_data = [e for e in events_data if client_filter.lower() in e.get('client', '').lower()]
    
    events_data = sorted(events_data, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return render_template('events.html', events=events_data, date_filter=date_filter, client_filter=client_filter)

@app.route('/events/add', methods=['GET', 'POST'])
@login_required
def add_event():
    if request.method == 'POST':
        events = load_json_file(EVENTS_FILE, [])
        
        next_id = max([e['id'] for e in events], default=0) + 1
        
        try:
            alert_minutes = int(request.form.get('alert_minutes', 5))
        except ValueError:
            alert_minutes = 5
        
        event = {
            "id": next_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time_slot": request.form.get('time_slot', ''),
            "length": request.form.get('length', ''),
            "client": request.form.get('client', ''),
            "delivery_type": request.form.get('delivery_type', ''),
            "resource": request.form.get('resource', ''),
            "assigned_to": request.form.get('assigned_to', ''),
            "signature": request.form.get('signature', ''),
            "notes": request.form.get('notes', ''),
            "status": "logged",
            "alert_minutes": alert_minutes,
            "alert_triggered": False
        }
        
        events.append(event)
        save_json_file(EVENTS_FILE, events)
        
        flash('Event created successfully!', 'success')
        return redirect(url_for('events'))
    
    return render_template('add_event.html')

@app.route('/events/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    events = load_json_file(EVENTS_FILE, [])
    event = next((e for e in events if e['id'] == event_id), None)
    
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('events'))
    
    if request.method == 'POST':
        try:
            alert_minutes = int(request.form.get('alert_minutes', 5))
        except ValueError:
            alert_minutes = 5
        
        event.update({
            "time_slot": request.form.get('time_slot', ''),
            "length": request.form.get('length', ''),
            "client": request.form.get('client', ''),
            "delivery_type": request.form.get('delivery_type', ''),
            "resource": request.form.get('resource', ''),
            "assigned_to": request.form.get('assigned_to', ''),
            "notes": request.form.get('notes', ''),
            "alert_minutes": alert_minutes,
            "last_modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        save_json_file(EVENTS_FILE, events)
        flash('Event updated successfully!', 'success')
        return redirect(url_for('events'))
    
    return render_template('edit_event.html', event=event)

@app.route('/events/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    events = load_json_file(EVENTS_FILE, [])
    events = [e for e in events if e['id'] != event_id]
    save_json_file(EVENTS_FILE, events)
    
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('events'))

@app.route('/export')
@login_required
def export_csv():
    events = load_json_file(EVENTS_FILE, [])
    
    if not events:
        flash('No events to export', 'warning')
        return redirect(url_for('events'))
    
    output = StringIO()
    if events:
        fieldnames = events[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)
    
    output.seek(0)
    byte_output = BytesIO(output.getvalue().encode('utf-8'))
    byte_output.seek(0)
    
    filename = f"schedule_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        byte_output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/users')
@admin_required
def manage_users():
    users = load_json_file(USERS_FILE, {})
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['POST'])
@admin_required
def add_user():
    users = load_json_file(USERS_FILE, {})
    
    username = request.form.get('username')
    password = request.form.get('password')
    name = request.form.get('name')
    role = request.form.get('role', 'user')
    
    if not username or not password or not name:
        flash('All fields are required', 'error')
        return redirect(url_for('manage_users'))
    
    if username in users:
        flash('Username already exists', 'error')
        return redirect(url_for('manage_users'))
    
    users[username] = {
        "password": hash_password(password),
        "role": role,
        "name": name
    }
    
    save_json_file(USERS_FILE, users)
    flash('User created successfully!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/api/check-alerts')
@login_required
def check_alerts():
    events = load_json_file(EVENTS_FILE, [])
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    
    alerts = []
    
    for event in events:
        if event.get('date') != today or event.get('alert_triggered'):
            continue
        
        try:
            time_slot = event.get('time_slot', '')
            start_time = time_slot.split('-')[0].strip()
            event_time = datetime.strptime(f"{today} {start_time}", "%Y-%m-%d %H:%M")
            
            alert_minutes = event.get('alert_minutes', 5)
            alert_time = event_time - timedelta(minutes=alert_minutes)
            
            if now >= alert_time and now < event_time:
                alerts.append({
                    'id': event['id'],
                    'client': event['client'],
                    'time_slot': event['time_slot'],
                    'resource': event.get('resource', ''),
                    'delivery_type': event.get('delivery_type', ''),
                    'notes': event.get('notes', '')
                })
                
                event['alert_triggered'] = True
        except (ValueError, IndexError):
            continue
    
    if alerts:
        save_json_file(EVENTS_FILE, events)
    
    return jsonify({'alerts': alerts})

init_users()

if __name__ == '__main__':
    app.run(debug=True)
