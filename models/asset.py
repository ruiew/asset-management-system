# models/asset.py
import sqlite3
from config import Config
import datetime

class Asset:
    @staticmethod
    def get_db():
        conn = sqlite3.connect(Config.DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    
    @staticmethod
    def create(name, serial, category=None):
        """Create a new asset with duplicate check"""
        conn = Asset.get_db()
        
        # Double-check for duplicate (safety measure)
        existing = conn.execute(
            'SELECT id FROM assets WHERE serial = ? COLLATE NOCASE',
            (serial,)
        ).fetchone()
        
        if existing:
            conn.close()
            raise ValueError(f'Serial number "{serial}" already exists!')
        
        conn.execute(
            '''INSERT INTO assets (name, serial, category, status) 
               VALUES (?, ?, ?, ?)''',
            (name, serial, category, 'Available')
        )
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def delete(asset_id):
        """Delete an asset"""
        conn = Asset.get_db()
        
        # Check if asset exists
        asset = conn.execute('SELECT id FROM assets WHERE id = ?', (asset_id,)).fetchone()
        if not asset:
            conn.close()
            raise ValueError(f'Asset with ID {asset_id} not found')
        
        # Check if asset is assigned - prevent deletion if assigned
        assigned = conn.execute(
            'SELECT assigned_to FROM assets WHERE id = ? AND assigned_to IS NOT NULL',
            (asset_id,)
        ).fetchone()
        
        if assigned:
            conn.close()
            raise ValueError('Cannot delete an assigned asset. Please unassign it first.')
        
        # Delete the asset
        conn.execute('DELETE FROM assets WHERE id = ?', (asset_id,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_all():
        conn = Asset.get_db()
        assets = conn.execute(
            'SELECT * FROM assets ORDER BY id DESC'
        ).fetchall()
        conn.close()
        return assets
    
    @staticmethod
    def get_by_id(asset_id):
        conn = Asset.get_db()
        asset = conn.execute(
            'SELECT * FROM assets WHERE id = ?', (asset_id,)
        ).fetchone()
        conn.close()
        return asset
    
    @staticmethod
    def get_available():
        conn = Asset.get_db()
        assets = conn.execute(
            'SELECT * FROM assets WHERE status = "Available" OR assigned_to IS NULL'
        ).fetchall()
        conn.close()
        return assets
    
    @staticmethod
    def get_by_user(user_id):
        conn = Asset.get_db()
        assets = conn.execute(
            'SELECT * FROM assets WHERE assigned_to = ?', (user_id,)
        ).fetchall()
        conn.close()
        return assets
    
    @staticmethod
    def update(asset_id, name, serial, category, status):
        conn = Asset.get_db()
        
        # Check for duplicate serial (excluding current asset)
        existing = conn.execute(
            'SELECT id FROM assets WHERE serial = ? COLLATE NOCASE AND id != ?',
            (serial, asset_id)
        ).fetchone()
        
        if existing:
            conn.close()
            raise ValueError(f'Serial number "{serial}" already exists!')
        
        conn.execute(
            '''UPDATE assets 
               SET name = ?, serial = ?, category = ?, status = ? 
               WHERE id = ?''',
            (name, serial, category, status, asset_id)
        )
        conn.commit()
        conn.close()
    
    @staticmethod
    def assign(asset_id, user_id):
        conn = Asset.get_db()
        
        # Check if asset exists and is available
        asset = conn.execute(
            'SELECT id, status FROM assets WHERE id = ?', (asset_id,)
        ).fetchone()
        
        if not asset:
            conn.close()
            return False
        
        if asset['status'] == 'Assigned':
            conn.close()
            return False
        
        # Check if user exists
        user = conn.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            conn.close()
            return False
        
        # Removed assigned_date to match schema
        conn.execute(
            '''UPDATE assets 
               SET assigned_to = ?, status = 'Assigned' 
               WHERE id = ?''',
            (user_id, asset_id)
        )
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def unassign(asset_id):
        """Unassign an asset"""
        conn = Asset.get_db()
        conn.execute(
            '''UPDATE assets 
               SET assigned_to = NULL, status = 'Available' 
               WHERE id = ?''',
            (asset_id,)
        )
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def count_all():
        conn = Asset.get_db()
        result = conn.execute('SELECT COUNT(*) as count FROM assets').fetchone()
        conn.close()
        return result['count'] if result else 0
    
    @staticmethod
    def count_assigned():
        conn = Asset.get_db()
        result = conn.execute(
            'SELECT COUNT(*) as count FROM assets WHERE status = "Assigned"'
        ).fetchone()
        conn.close()
        return result['count'] if result else 0
    
    @staticmethod
    def count_maintenance():
        conn = Asset.get_db()
        result = conn.execute(
            'SELECT COUNT(*) as count FROM assets WHERE status = "Maintenance"'
        ).fetchone()
        conn.close()
        return result['count'] if result else 0
    
    @staticmethod
    def get_recent_activity(limit=5):
        """Get recent asset activity"""
        conn = Asset.get_db()
        activities = conn.execute('''
            SELECT 
                'A-' || substr('00' || id, -3) as asset_id,
                name || ' - ' || status as description,
                status as activity_type,
                'System' as admin,
                datetime('now') as date
            FROM assets 
            ORDER BY id DESC 
            LIMIT ?
        ''', (limit,)).fetchall()
        conn.close()
        return activities