===============================================================================================
			FIXED ASSET MANAGEMENT SYSTEM (FAMS) - CAPI SDN. BHD
===============================================================================================



					📌 SYSTEM OVERVIEW
-----------------------------------------------------------------------------------------------
A web-based Fixed Asset Management System built with Flask, SQLite, HTML, CSS, and JavaScript. 
Manages company assets, assignments, maintenance records, and generates reports.




					🔐 LOGIN CREDENTIALS
-----------------------------------------------------------------------------------------------
ADMIN ACCOUNT:
  Email: admin@capi.com
  Password: admin123

STAFF ACCOUNT:
  Email: user@capi.com
  Password: password123



					📁 PROJECT STRUCTURE
-----------------------------------------------------------------------------------------------
asset-management-system/
├── fams.py                 	# Main Flask application (run this)
├── config.py               	# Configuration settings
├── init_db.py              	# Database setup (run once)
├── requirements.txt        	# Python dependencies
├── readme.txt              	# This file
├── models/                 	# Database models
│   ├── __init__.py
│   ├── user.py             	# User model
│   └── asset.py            	# Asset model
├── static/                 	# Static files
│   ├── css/
│   │   └── style.css       	# Main stylesheet
│   ├── js/
│   │   └── script.js       	# JavaScript
│   └── images/
│       └── capi-logo.png   	# Logo
├── templates/              	# HTML pages
│   ├── base.html           	# Base layout
│   ├── login.html          	# Login page
│   ├── admin_dashboard.html
│   ├── staff_dashboard.html
│   ├── assets.html         	# Manage assets
│   ├── add_asset.html
│   ├── edit_asset.html
│   ├── view_asset.html
│   ├── assign.html         	# Assign assets
│   ├── maintenance.html    	# Maintenance records
│   ├── edit_maintenance.html
│   ├── my_assets.html      	# Staff view
│   └── reports.html        	# Generate reports
└── .venv/                  	# Virtual environment (auto-created)




					🚀 INSTALLATION
-----------------------------------------------------------------------------------------------
1. Clone repository:
   git clone https://github.com/ruiew/asset-management-system.git

2. Create virtual environment:
   python -m venv .venv
   source .venv/Scripts/activate  # Windows
   source .venv/bin/activate      # Mac/Linux

3. Install dependencies:
   pip install -r requirements.txt

4. Initialize database (run once):
   python init_db.py

5. Run the application:
   python fams.py

6. Open browser:
   http://127.0.0.1:5000




					🛠️ FEATURES
-----------------------------------------------------------------------------------------------
ADMIN:
  ✅ Dashboard with statistics
  ✅ View all assets
  ✅ Add/Edit/Delete assets
  ✅ Assign assets to staff
  ✅ View asset details
  ✅ Maintenance management
  ✅ Generate reports (3 types)
  ✅ Export reports to CSV

STAFF:
  ✅ Dashboard with personal stats
  ✅ View assigned assets
  ✅ Search personal assets
  ✅ Request maintenance



					📊 REPORT TYPES
-----------------------------------------------------------------------------------------------
1. Asset Summary 	- By category with counts
2. Maintenance Report 	- All maintenance records
3. Assignment Report 	- All asset assignments




					🔧 TROUBLESHOOTING
----------------------------------------------------------------------------------------------
ERROR: Module not found
  → Run: pip install -r requirements.txt

ERROR: Database locked
  → Close any SQLite viewers and restart Flask

ERROR: Port 5000 in use
  → Change port in fams.py: app.run(debug=True, port=5001)

