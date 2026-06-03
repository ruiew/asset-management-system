const express = require('express');
const session = require('express-session');
const bcrypt = require('bcrypt');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
const PORT = 3000;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static('templates'));
app.use(session({
    secret: 'capi-secret-key-2026',
    resave: false,
    saveUninitialized: false,
    cookie: { secure: false, maxAge: 24 * 60 * 60 * 1000 }
}));

const db = new sqlite3.Database('./database.sqlite');

db.run(`
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
`);

const demoEmail = 'admin@capi.com';
const demoPassword = 'admin123';

db.get('SELECT * FROM users WHERE email = ?', [demoEmail], async (err, user) => {
    if (!user) {
        const hashedPassword = await bcrypt.hash(demoPassword, 10);
        db.run('INSERT INTO users (email, password) VALUES (?, ?)', [demoEmail, hashedPassword]);
        console.log(' Demo user created: admin@capi.com / admin123');
    }
});

app.get('/api/check-session', (req, res) => {
    if (req.session.userId) {
        res.json({ loggedIn: true, email: req.session.email });
    } else {
        res.json({ loggedIn: false });
    }
});

app.post('/api/login', (req, res) => {
    const { email, password, remember } = req.body;
    
    if (!email || !password) {
        return res.status(400).json({ success: false, message: 'Email and password required' });
    }
    
    db.get('SELECT * FROM users WHERE email = ?', [email], async (err, user) => {
        if (err) {
            return res.status(500).json({ success: false, message: 'Database error' });
        }
        
        if (!user) {
            return res.status(401).json({ success: false, message: 'Invalid email or password' });
        }
        
        const validPassword = await bcrypt.compare(password, user.password);
        if (!validPassword) {
            return res.status(401).json({ success: false, message: 'Invalid email or password' });
        }
        
        req.session.userId = user.id;
        req.session.email = user.email;
        
        if (remember) {
            req.session.cookie.maxAge = 30 * 24 * 60 * 60 * 1000;
        }
        
        res.json({ success: true, message: 'Login successful', email: user.email });
    });
});

app.post('/api/logout', (req, res) => {
    req.session.destroy();
    res.json({ success: true, message: 'Logged out' });
});

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'login.html'));
});

app.listen(PORT, () => {
    console.log(` Server running at http://localhost:${PORT}`);
    console.log(` Demo login: admin@capi.com / admin123`);
});
