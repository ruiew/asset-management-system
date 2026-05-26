from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from functools import wraps
from datetime import date

app = Flask(__name__)
app.secret_key = 'fams-secret-key-2026'

# Database setup
DATABASE = 'fams.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # Users table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT,
                department TEXT
            )
        ''')
        
        # Assets table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                serial_number TEXT UNIQUE,
                status TEXT DEFAULT 'Available',
                condition TEXT,
                location TEXT,
                purchase_date DATE,
                assigned_to INTEGER,
                assigned_date DATE,
                FOREIGN KEY (assigned_to) REFERENCES users(id)
            )
        ''')
        
        # Maintenance records table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS maintenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                maintenance_date DATE NOT NULL,
                maintenance_type TEXT,
                cost REAL,
                technician TEXT,
                remarks TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(id)
            )
        ''')
        
        # Insert sample admin
        conn.execute('''
            INSERT OR IGNORE INTO users (username, password, role, email, department)
            VALUES ('admin', 'admin123', 'Admin', 'admin@capi.com', 'IT')
        ''')
        
        # Insert sample staff
        conn.execute('''
            INSERT OR IGNORE INTO users (username, password, role, email, department)
            VALUES ('staff1', 'staff123', 'Staff', 'staff1@capi.com', 'Engineering')
        ''')
        
        conn.commit()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'Admin':
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with get_db() as conn:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ? AND password = ?',
                (username, password)
            ).fetchone()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    with get_db() as conn:
        total_assets = conn.execute('SELECT COUNT(*) as count FROM assets').fetchone()['count']
        assets_in_use = conn.execute('SELECT COUNT(*) as count FROM assets WHERE status = "In Use"').fetchone()['count']
        available_assets = conn.execute('SELECT COUNT(*) as count FROM assets WHERE status = "Available"').fetchone()['count']
        recent_assets = conn.execute('SELECT * FROM assets ORDER BY id DESC LIMIT 5').fetchall()
    
    return render_template('dashboard.html', 
                         total_assets=total_assets,
                         assets_in_use=assets_in_use,
                         available_assets=available_assets,
                         recent_assets=recent_assets)

@app.route('/assets')
@login_required
def assets():
    with get_db() as conn:
        all_assets = conn.execute('SELECT * FROM assets').fetchall()
    return render_template('assets.html', assets=all_assets)

@app.route('/add_asset', methods=['GET', 'POST'])
@admin_required
def add_asset():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        serial_number = request.form['serial_number']
        condition = request.form['condition']
        location = request.form['location']
        purchase_date = request.form['purchase_date']
        
        with get_db() as conn:
            conn.execute('''
                INSERT INTO assets (name, category, serial_number, condition, location, purchase_date, status)
                VALUES (?, ?, ?, ?, ?, ?, 'Available')
            ''', (name, category, serial_number, condition, location, purchase_date))
            conn.commit()
        
        return redirect(url_for('assets'))
    
    return render_template('add_asset.html')

@app.route('/edit_asset/<int:asset_id>', methods=['GET', 'POST'])
@admin_required
def edit_asset(asset_id):
    with get_db() as conn:
        asset = conn.execute('SELECT * FROM assets WHERE id = ?', (asset_id,)).fetchone()
        
        if request.method == 'POST':
            name = request.form['name']
            category = request.form['category']
            serial_number = request.form['serial_number']
            condition = request.form['condition']
            location = request.form['location']
            status = request.form['status']
            
            conn.execute('''
                UPDATE assets 
                SET name = ?, category = ?, serial_number = ?, condition = ?, location = ?, status = ?
                WHERE id = ?
            ''', (name, category, serial_number, condition, location, status, asset_id))
            conn.commit()
            
            return redirect(url_for('assets'))
    
    return render_template('edit_asset.html', asset=asset)

@app.route('/delete_asset/<int:asset_id>')
@admin_required
def delete_asset(asset_id):
    with get_db() as conn:
        conn.execute('DELETE FROM assets WHERE id = ?', (asset_id,))
        conn.commit()
    return redirect(url_for('assets'))

@app.route('/assign_asset', methods=['GET', 'POST'])
@admin_required
def assign_asset():
    with get_db() as conn:
        available_assets = conn.execute('SELECT * FROM assets WHERE status = "Available"').fetchall()
        staff_users = conn.execute('SELECT * FROM users WHERE role = "Staff"').fetchall()
        
        if request.method == 'POST':
            asset_id = request.form['asset_id']
            staff_id = request.form['staff_id']
            
            today = date.today()
            
            conn.execute('''
                UPDATE assets SET status = "In Use", assigned_to = ?, assigned_date = ?
                WHERE id = ?
            ''', (staff_id, today, asset_id))
            conn.commit()
            
            return redirect(url_for('assets'))
    
    return render_template('assign_asset.html', assets=available_assets, staff=staff_users)

@app.route('/my_assets')
@login_required
def my_assets():
    user_id = session['user_id']
    with get_db() as conn:
        my_assets = conn.execute('''
            SELECT * FROM assets WHERE assigned_to = ?
        ''', (user_id,)).fetchall()
    return render_template('my_assets.html', assets=my_assets)

@app.route('/request_return/<int:asset_id>')
@login_required
def request_return(asset_id):
    with get_db() as conn:
        conn.execute('''
            UPDATE assets SET status = "Available", assigned_to = NULL, assigned_date = NULL
            WHERE id = ?
        ''', (asset_id,))
        conn.commit()
    return redirect(url_for('my_assets'))

@app.route('/maintenance')
@admin_required
def maintenance():
    with get_db() as conn:
        records = conn.execute('''
            SELECT m.*, a.name as asset_name 
            FROM maintenance m 
            JOIN assets a ON m.asset_id = a.id
            ORDER BY m.maintenance_date DESC
        ''').fetchall()
        assets = conn.execute('SELECT id, name FROM assets').fetchall()
    return render_template('maintenance.html', records=records, assets=assets)

@app.route('/add_maintenance', methods=['POST'])
@admin_required
def add_maintenance():
    asset_id = request.form['asset_id']
    maintenance_date = request.form['maintenance_date']
    maintenance_type = request.form['maintenance_type']
    cost = request.form['cost']
    technician = request.form['technician']
    remarks = request.form['remarks']
    
    with get_db() as conn:
        conn.execute('''
            INSERT INTO maintenance (asset_id, maintenance_date, maintenance_type, cost, technician, remarks)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (asset_id, maintenance_date, maintenance_type, cost, technician, remarks))
        
        conn.execute('UPDATE assets SET condition = "Good" WHERE id = ?', (asset_id,))
        conn.commit()
    
    return redirect(url_for('maintenance'))

@app.route('/reports')
@admin_required
def reports():
    with get_db() as conn:
        asset_summary = conn.execute('''
            SELECT status, COUNT(*) as count FROM assets GROUP BY status
        ''').fetchall()
        
        assets_by_category = conn.execute('''
            SELECT category, COUNT(*) as count FROM assets GROUP BY category
        ''').fetchall()
        
        assigned_assets = conn.execute('''
            SELECT a.name, u.username as assigned_to, a.assigned_date
            FROM assets a
            JOIN users u ON a.assigned_to = u.id
            WHERE a.status = "In Use"
        ''').fetchall()
    
    return render_template('reports.html', 
                         asset_summary=asset_summary,
                         assets_by_category=assets_by_category,
                         assigned_assets=assigned_assets)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)