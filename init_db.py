# init_db.py
import sqlite3
import bcrypt
from config import Config

def init_db():
    conn = sqlite3.connect(Config.DATABASE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT DEFAULT 'staff'
    )
    ''')
    
    # Create assets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        serial TEXT UNIQUE NOT NULL,
        category TEXT,
        assigned_to INTEGER,
        status TEXT DEFAULT 'Available',
        FOREIGN KEY (assigned_to) REFERENCES users(id)
    )
    ''')
    
    # Create maintenance table - removed performed_by since not used
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS maintenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        maintenance_date DATE NOT NULL,
        type TEXT NOT NULL,
        description TEXT,
        cost REAL DEFAULT 0,
        status TEXT DEFAULT 'Scheduled',
        FOREIGN KEY (asset_id) REFERENCES assets(id)
    )
    ''')
    
    # Create activity_log table for recent activity
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER,
        activity_type TEXT NOT NULL,
        description TEXT,
        performed_by INTEGER,
        performed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(id),
        FOREIGN KEY (performed_by) REFERENCES users(id)
    )
    ''')
    
    # Create demo users
    hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
    cursor.execute('INSERT OR IGNORE INTO users (email, password, name, role) VALUES (?, ?, ?, ?)',
                   ('admin@capi.com', hashed.decode('utf-8'), 'Admin User', 'admin'))
    
    hashed2 = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt())
    cursor.execute('INSERT OR IGNORE INTO users (email, password, name, role) VALUES (?, ?, ?, ?)',
                   ('user@capi.com', hashed2.decode('utf-8'), 'Staff User', 'staff'))
    
    # Sample assets
    assets = [
        ('Dell XPS Laptop', 'DELL-XPS-001', 'Laptop'),
        ('MacBook Pro', 'MBP-001', 'Laptop'),
        ('Monitor 24-inch', 'MON-001', 'Monitor'),
        ('HP Printer', 'HP-456', 'Printer'),
        ('iPad Air 128GB', 'IPAD-001', 'Tablet'),
        ('Epson Projector', 'EPSON-001', 'Projector'),
    ]
    
    for name, serial, category in assets:
        cursor.execute('INSERT OR IGNORE INTO assets (name, serial, category) VALUES (?, ?, ?)',
                       (name, serial, category))
    
    # Assign some assets to staff
    cursor.execute('UPDATE assets SET assigned_to = 2, status = "Assigned" WHERE id = 1')
    cursor.execute('UPDATE assets SET assigned_to = 2, status = "Assigned" WHERE id = 3')
    
    # Insert sample maintenance records
    cursor.execute('''
    INSERT OR IGNORE INTO maintenance (asset_id, maintenance_date, type, description, cost, status)
    VALUES (1, '2026-05-25', 'Repair', 'Battery replacement', 250.00, 'Completed')
    ''')
    cursor.execute('''
    INSERT OR IGNORE INTO maintenance (asset_id, maintenance_date, type, description, cost, status)
    VALUES (2, '2026-05-28', 'Preventive', 'Cleaning and inspection', 0.00, 'Scheduled')
    ''')
    cursor.execute('''
    INSERT OR IGNORE INTO maintenance (asset_id, maintenance_date, type, description, cost, status)
    VALUES (4, '2026-06-02', 'Calibration', 'Printer calibration', 120.00, 'In Progress')
    ''')
    
    # Insert sample activity log
    cursor.execute('''
    INSERT OR IGNORE INTO activity_log (asset_id, activity_type, description, performed_by)
    VALUES (1, 'Assign', 'Assigned Dell XPS Laptop to Staff User', 1)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")
    print("👤 Admin: admin@capi.com / admin123")
    print("👤 Staff: user@capi.com / password123")

if __name__ == '__main__':
    init_db()