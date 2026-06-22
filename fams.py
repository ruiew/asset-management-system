# fams.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from config import Config
from models.user import User
from models.asset import Asset
import bcrypt
import sqlite3
import os

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')

app.config.from_object(Config)

def get_db():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== AUTH ROUTES ====================

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        flash('Please enter both email and password')
        return redirect(url_for('login_page'))
    
    user = User.find_by_email(email)
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        session['user_id'] = user['id']
        session['email'] = user['email']
        session['role'] = user['role']
        session['name'] = user['name']
        
        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('staff_dashboard'))
    
    flash('Invalid email or password')
    return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# ==================== ADMIN ROUTES ====================

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login_page'))
    
    total_assets = Asset.count_all()
    total_users = User.count_all()
    assigned_assets = Asset.count_assigned()
    maintenance_count = Asset.count_maintenance()
    recent_activity = Asset.get_recent_activity()
    
    return render_template('admin_dashboard.html',
                         name=session.get('name'),
                         total_assets=total_assets,
                         total_users=total_users,
                         assigned_assets=assigned_assets,
                         maintenance_count=maintenance_count,
                         recent_activity=recent_activity)

@app.route('/assets')
def manage_assets():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login_page'))
    
    assets = Asset.get_all()
    return render_template('assets.html', assets=assets)

# ==================== ADD ASSET ====================
@app.route('/assets/add', methods=['GET', 'POST'])
def add_asset():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login_page'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        serial = request.form.get('serial', '').strip()
        category = request.form.get('category', '').strip()
        
        # ========== VALIDATION ==========
        errors = []
        
        if not name:
            errors.append('Asset name is required')
        
        if not serial:
            errors.append('Serial number is required')
        elif len(serial) < 3:
            errors.append('Serial number must be at least 3 characters')
        
        # ========== CHECK FOR DUPLICATE SERIAL ==========
        if serial:
            db = get_db()
            existing = db.execute(
                'SELECT id FROM assets WHERE serial = ? COLLATE NOCASE',
                (serial,)
            ).fetchone()
            if existing:
                errors.append(f'Serial number "{serial}" already exists! Please use a different serial number.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('add_asset.html'), 400
        
        # ========== SAVE TO DATABASE ==========
        try:
            Asset.create(name, serial, category)
            flash(f'✅ Asset "{name}" added successfully!', 'success')
            return redirect(url_for('manage_assets'))
        except sqlite3.IntegrityError as e:
            if 'UNIQUE constraint failed: assets.serial' in str(e):
                flash(f'❌ Serial number "{serial}" already exists! Please use a different serial number.', 'error')
            else:
                flash(f'❌ Database error: {str(e)}', 'error')
            return render_template('add_asset.html'), 400
        except ValueError as e:
            flash(f'❌ {str(e)}', 'error')
            return render_template('add_asset.html'), 400
        except Exception as e:
            flash(f'❌ Error adding asset: {str(e)}', 'error')
            return render_template('add_asset.html'), 500
    
    return render_template('add_asset.html')

# ==================== API: CHECK SERIAL ====================
@app.route('/api/check-serial')
def check_serial():
    if 'user_id' not in session:
        return jsonify({'exists': False, 'error': 'Unauthorized'})
    
    serial = request.args.get('serial', '').strip()
    if not serial:
        return jsonify({'exists': False})
    
    db = get_db()
    existing = db.execute(
        'SELECT id FROM assets WHERE serial = ? COLLATE NOCASE',
        (serial,)
    ).fetchone()
    
    return jsonify({'exists': existing is not None})

# ==================== EDIT ASSET ====================
@app.route('/assets/edit/<int:asset_id>', methods=['GET', 'POST'])
def edit_asset(asset_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login_page'))
    
    # ========== GET ASSET FROM DATABASE ==========
    db = get_db()
    asset = db.execute('SELECT * FROM assets WHERE id = ?', (asset_id,)).fetchone()
    
    if not asset:
        flash('❌ Asset not found', 'error')
        return redirect(url_for('manage_assets'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        serial = request.form.get('serial', '').strip()
        category = request.form.get('category', '').strip()
        status = request.form.get('status', 'Available')
        
        # ========== VALIDATION ==========
        errors = []
        
        if not name:
            errors.append('Asset name is required')
        
        if not serial:
            errors.append('Serial number is required')
        elif len(serial) < 3:
            errors.append('Serial number must be at least 3 characters')
        
        # ========== CHECK FOR DUPLICATE SERIAL (EXCLUDING CURRENT) ==========
        if serial:
            existing = db.execute(
                'SELECT id FROM assets WHERE serial = ? COLLATE NOCASE AND id != ?',
                (serial, asset_id)
            ).fetchone()
            if existing:
                errors.append(f'Serial number "{serial}" already exists! Please use a different serial number.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('edit_asset.html', asset=asset), 400
        
        # ========== UPDATE DATABASE ==========
        try:
            db.execute(
                '''UPDATE assets 
                   SET name = ?, serial = ?, category = ?, status = ? 
                   WHERE id = ?''',
                (name, serial, category, status, asset_id)
            )
            db.commit()
            flash(f'✅ Asset "{name}" updated successfully!', 'success')
            return redirect(url_for('manage_assets'))
        except sqlite3.IntegrityError as e:
            if 'UNIQUE constraint failed: assets.serial' in str(e):
                flash(f'❌ Serial number "{serial}" already exists! Please use a different serial number.', 'error')
            else:
                flash(f'❌ Database error: {str(e)}', 'error')
            return render_template('edit_asset.html', asset=asset), 400
        except Exception as e:
            flash(f'❌ Error updating asset: {str(e)}', 'error')
            return render_template('edit_asset.html', asset=asset), 500
    
    return render_template('edit_asset.html', asset=asset)

# ==================== DELETE ASSET ====================
@app.route('/assets/delete/<int:asset_id>', methods=['POST'])
def delete_asset(asset_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login_page'))
    
    try:
        Asset.delete(asset_id)
        flash('✅ Asset deleted successfully!', 'success')
    except ValueError as e:
        flash(f'❌ {str(e)}', 'error')
    except Exception as e:
        flash(f'❌ Error deleting asset: {str(e)}', 'error')
    
    return redirect(url_for('manage_assets'))

# ==================== VIEW ASSET ====================
@app.route('/assets/view/<int:asset_id>')
def view_asset(asset_id):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    db = get_db()
    asset = db.execute('''
        SELECT assets.*, users.name as assigned_to_name, users.email as assigned_to_email 
        FROM assets 
        LEFT JOIN users ON assets.assigned_to = users.id 
        WHERE assets.id = ?
    ''', (asset_id,)).fetchone()
    
    if not asset:
        flash('Asset not found')
        return redirect(url_for('manage_assets'))
    
    return render_template('view_asset.html', asset=asset)

# ==================== ASSIGN ASSET ====================
@app.route('/assets/assign', methods=['GET', 'POST'])
def assign_asset():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login_page'))
    
    if request.method == 'POST':
        asset_id = request.form.get('asset_id')
        user_id = request.form.get('user_id')
        
        if asset_id and user_id:
            success = Asset.assign(asset_id, user_id)
            if success:
                flash('✅ Asset assigned successfully!', 'success')
                return redirect(url_for('manage_assets'))
            else:
                flash('❌ Failed to assign asset. Please check asset and user exist.', 'error')
        else:
            flash('❌ Please select both asset and staff member', 'error')
    
    assets = Asset.get_available()
    users = User.get_all_staff()
    return render_template('assign.html', assets=assets, users=users)

# ==================== UNASSIGN ASSET ====================
@app.route('/assets/unassign/<int:asset_id>', methods=['POST'])
def unassign_asset(asset_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login_page'))
    
    try:
        Asset.unassign(asset_id)
        flash('✅ Asset unassigned successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error unassigning asset: {str(e)}', 'error')
    
    return redirect(url_for('manage_assets'))

# ==================== MAINTENANCE ROUTES ====================

@app.route('/maintenance')
def maintenance():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    db = get_db()
    records = db.execute('''
        SELECT maintenance.*, assets.name as asset_name 
        FROM maintenance 
        LEFT JOIN assets ON maintenance.asset_id = assets.id 
        ORDER BY maintenance.id DESC
    ''').fetchall()
    
    assets = Asset.get_all()
    return render_template('maintenance.html', records=records, assets=assets)

@app.route('/maintenance/add', methods=['POST'])
def add_maintenance():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    asset_id = request.form.get('asset_id')
    maintenance_date = request.form.get('maintenance_date')
    type = request.form.get('type')
    description = request.form.get('description', '')
    cost = request.form.get('cost', 0)
    status = request.form.get('status', 'Scheduled')
    
    if asset_id and maintenance_date and type:
        db = get_db()
        db.execute('''
            INSERT INTO maintenance (asset_id, maintenance_date, type, description, cost, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (asset_id, maintenance_date, type, description, cost, status))
        db.commit()
        flash('✅ Maintenance record added successfully!', 'success')
    else:
        flash('❌ Please fill in all required fields', 'error')
    
    return redirect(url_for('maintenance'))

@app.route('/maintenance/delete/<int:record_id>', methods=['POST'])
def delete_maintenance(record_id):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    db = get_db()
    db.execute('DELETE FROM maintenance WHERE id = ?', (record_id,))
    db.commit()
    flash('✅ Maintenance record deleted successfully!', 'success')
    return redirect(url_for('maintenance'))

@app.route('/maintenance/edit/<int:record_id>', methods=['GET', 'POST'])
def edit_maintenance(record_id):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    db = get_db()
    record = db.execute('''
        SELECT maintenance.*, assets.name as asset_name 
        FROM maintenance 
        LEFT JOIN assets ON maintenance.asset_id = assets.id 
        WHERE maintenance.id = ?
    ''', (record_id,)).fetchone()
    
    if not record:
        flash('Record not found')
        return redirect(url_for('maintenance'))
    
    if request.method == 'POST':
        maintenance_date = request.form.get('maintenance_date')
        type = request.form.get('type')
        description = request.form.get('description', '')
        cost = request.form.get('cost', 0)
        status = request.form.get('status')
        
        db.execute('''
            UPDATE maintenance 
            SET maintenance_date = ?, type = ?, description = ?, cost = ?, status = ?
            WHERE id = ?
        ''', (maintenance_date, type, description, cost, status, record_id))
        db.commit()
        flash('✅ Maintenance record updated successfully!', 'success')
        return redirect(url_for('maintenance'))
    
    assets = Asset.get_all()
    return render_template('edit_maintenance.html', record=record, assets=assets)

# ==================== REPORTS ROUTES ====================

@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    db = get_db()
    category_summary = db.execute('''
        SELECT category, COUNT(*) as total,
            SUM(CASE WHEN status = 'Assigned' THEN 1 ELSE 0 END) as assigned,
            SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) as available,
            SUM(CASE WHEN status = 'Maintenance' THEN 1 ELSE 0 END) as maintenance
        FROM assets 
        GROUP BY category
    ''').fetchall()
    
    total_assets = Asset.count_all()
    assigned_assets = Asset.count_assigned()
    maintenance_count = Asset.count_maintenance()
    available = total_assets - assigned_assets - maintenance_count
    
    return render_template('reports.html', 
                         category_summary=category_summary,
                         total_assets=total_assets,
                         assigned_assets=assigned_assets,
                         available=available,
                         maintenance_count=maintenance_count)

# ==================== API: REPORT ====================
@app.route('/api/report/<report_type>')
def api_report(report_type):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'})
    
    db = get_db()
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')
    
    # Build date filter
    date_filter = ""
    date_params = []
    if start_date and end_date:
        date_filter = "WHERE maintenance_date BETWEEN ? AND ?"
        date_params = [start_date, end_date]
    elif start_date:
        date_filter = "WHERE maintenance_date >= ?"
        date_params = [start_date]
    elif end_date:
        date_filter = "WHERE maintenance_date <= ?"
        date_params = [end_date]
    
    if report_type == 'asset':
        results = db.execute('''
            SELECT 
                COALESCE(category, 'Uncategorized') as category,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Assigned' THEN 1 ELSE 0 END) as assigned,
                SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) as available,
                SUM(CASE WHEN status = 'Maintenance' THEN 1 ELSE 0 END) as maintenance
            FROM assets 
            GROUP BY category
            ORDER BY category
        ''').fetchall()
        
        rows = []
        for r in results:
            rows.append([
                r['category'],
                r['assigned'] or 0,
                r['available'] or 0,
                r['maintenance'] or 0,
                r['total'] or 0
            ])
        
        total_assets = Asset.count_all()
        assigned_assets = Asset.count_assigned()
        maintenance_count = Asset.count_maintenance()
        available = total_assets - assigned_assets - maintenance_count
        
        return jsonify({
            'rows': rows,
            'summary': {
                'total': total_assets,
                'assigned': assigned_assets,
                'available': available,
                'maintenance': maintenance_count
            }
        })
    
    elif report_type == 'maintenance':
        query = '''
            SELECT 
                'M-' || substr('00' || maintenance.id, -3) as id,
                assets.name as asset_name,
                maintenance.maintenance_date,
                maintenance.type,
                maintenance.status,
                maintenance.cost
            FROM maintenance 
            LEFT JOIN assets ON maintenance.asset_id = assets.id 
        '''
        
        if date_filter:
            query += ' ' + date_filter
        
        query += ' ORDER BY maintenance.id DESC'
        
        results = db.execute(query, date_params).fetchall()
        
        rows = []
        for r in results:
            rows.append([
                r['id'] or '-',
                r['asset_name'] or 'Unknown',
                r['maintenance_date'] or '-',
                r['type'] or '-',
                r['status'] or 'Scheduled',
                f"{r['cost']:.2f}" if r['cost'] else '0.00'
            ])
        
        total = len(results)
        completed = sum(1 for r in results if r['status'] == 'Completed')
        in_progress = sum(1 for r in results if r['status'] == 'In Progress')
        scheduled = sum(1 for r in results if r['status'] == 'Scheduled')
        
        return jsonify({
            'rows': rows,
            'summary': {
                'total': total,
                'completed': completed,
                'in_progress': in_progress,
                'scheduled': scheduled
            }
        })
    
    elif report_type == 'assignment':
        results = db.execute('''
            SELECT 
                'A-' || substr('00' || assets.id, -3) as asset_id,
                assets.name as asset_name,
                COALESCE(users.name, 'Not Assigned') as assigned_to,
                assets.status,
                'N/A' as assigned_date
            FROM assets 
            LEFT JOIN users ON assets.assigned_to = users.id 
            WHERE assets.assigned_to IS NOT NULL
            ORDER BY assets.id DESC
        ''').fetchall()
        
        rows = []
        for r in results:
            rows.append([
                r['asset_id'] or '-',
                r['asset_name'] or 'Unknown',
                r['assigned_to'] or 'Not Assigned',
                r['status'] or 'Unknown',
                r['assigned_date'] or 'N/A'
            ])
        
        total = len(results)
        active = sum(1 for r in results if r['status'] == 'Assigned')
        available = sum(1 for r in results if r['status'] == 'Available')
        
        return jsonify({
            'rows': rows,
            'summary': {
                'total': total,
                'active': active,
                'available': available
            }
        })
    
    else:
        return jsonify({'error': 'Invalid report type'})

# ==================== STAFF ROUTES ====================

@app.route('/staff')
def staff_dashboard():
    if 'user_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('login_page'))
    
    my_assets = Asset.get_by_user(session['user_id'])
    maintenance_count = sum(1 for asset in my_assets if asset['status'] == 'Maintenance')
    
    return render_template('staff_dashboard.html',
                         name=session.get('name'),
                         assets=my_assets,
                         maintenance_count=maintenance_count)

@app.route('/my-assets')
def my_assets():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    assets = Asset.get_by_user(session['user_id'])
    return render_template('my_assets.html', assets=assets)

# ==================== SEARCH API ====================

@app.route('/api/search/assets')
def search_assets():
    if 'user_id' not in session:
        return jsonify([])
    
    query = request.args.get('q', '').lower()
    db = get_db()
    
    if session.get('role') == 'admin':
        results = db.execute('''
            SELECT * FROM assets 
            WHERE LOWER(name) LIKE ? OR LOWER(serial) LIKE ? OR LOWER(category) LIKE ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    else:
        results = db.execute('''
            SELECT * FROM assets 
            WHERE assigned_to = ? AND (LOWER(name) LIKE ? OR LOWER(serial) LIKE ?)
        ''', (session['user_id'], f'%{query}%', f'%{query}%')).fetchall()
    
    return jsonify([dict(row) for row in results])

if __name__ == '__main__':
    app.run(debug=True)