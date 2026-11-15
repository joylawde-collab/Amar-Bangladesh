import os
import sqlite3
import secrets
from functools import wraps
from flask import Flask, g, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
DB_PATH = os.environ.get("DATABASE_PATH", "amar_bangladesh.db")

SERVICES = [
    {"id": "health", "bn": "স্বাস্থ্য", "en": "Healthcare", "desc_bn": "স্বাস্থ্যসেবা ও প্রয়োজনীয় তথ্য", "desc_en": "Health services and useful information", "icon": "✚"},
    {"id": "jobs", "bn": "চাকরি", "en": "Jobs", "desc_bn": "চাকরির তথ্য ও প্রস্তুতি", "desc_en": "Job information and preparation", "icon": "▣"},
    {"id": "education", "bn": "শিক্ষা", "en": "Education", "desc_bn": "শিক্ষা ও বৃত্তির তথ্য", "desc_en": "Education and scholarship information", "icon": "✎"},
    {"id": "government", "bn": "সরকারি সেবা", "en": "Government Services", "desc_bn": "সরকারি সেবার নির্দেশনা", "desc_en": "Guides to public services", "icon": "⌂"},
    {"id": "local", "bn": "স্থানীয় সেবা", "en": "Local Services", "desc_bn": "এলাকার প্রয়োজনীয় সেবা", "desc_en": "Useful local services", "icon": "⌖"},
    {"id": "emergency", "bn": "জরুরি যোগাযোগ", "en": "Emergency Contacts", "desc_bn": "জরুরি প্রয়োজনে যোগাযোগ", "desc_en": "Contacts for urgent help", "icon": "☎"},
]

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_error):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title_bn TEXT NOT NULL,
            title_en TEXT NOT NULL,
            body_bn TEXT NOT NULL,
            body_en TEXT NOT NULL,
            category TEXT NOT NULL,
            source_url TEXT DEFAULT '',
            published INTEGER NOT NULL DEFAULT 0
        )""")

@app.before_request
def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)

def csrf_valid():
    return secrets.compare_digest(
        str(session.get("csrf_token", "")),
        str(request.form.get("csrf_token", ""))
    )

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in first.", "error")
            return redirect(url_for("home"))
        return fn(*args, **kwargs)
    return wrapped

def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            return "Forbidden", 403
        return fn(*args, **kwargs)
    return wrapped

@app.route("/")
def home():
    notices = db().execute("SELECT * FROM notices WHERE published=1 ORDER BY id DESC LIMIT 6").fetchall()
    return render_template("index.html", services=SERVICES, notices=notices)

@app.post("/signup")
def signup():
    if not csrf_valid():
        return "Invalid request token", 400
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not name or not email or len(password) < 10:
        flash("নাম, সঠিক ইমেইল এবং কমপক্ষে ১০ অক্ষরের পাসওয়ার্ড দিন।", "error")
        return redirect(url_for("home"))
    admin_email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    role = "admin" if admin_email and email == admin_email else "user"
    try:
        cur = db().execute(
            "INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
            (name, email, generate_password_hash(password), role)
        )
        db().commit()
    except sqlite3.IntegrityError:
        flash("এই ইমেইল দিয়ে আগে অ্যাকাউন্ট খোলা হয়েছে।", "error")
        return redirect(url_for("home"))
    session.update(user_id=cur.lastrowid, name=name, role=role)
    return redirect(url_for("dashboard"))

@app.post("/login")
def login():
    if not csrf_valid():
        return "Invalid request token", 400
    email = request.form.get("email", "").strip().lower()
    user = db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if not user or not check_password_hash(user["password_hash"], request.form.get("password", "")):
        flash("ইমেইল অথবা পাসওয়ার্ড সঠিক নয়।", "error")
        return redirect(url_for("home"))
    session.update(user_id=user["id"], name=user["name"], role=user["role"])
    return redirect(url_for("dashboard"))

@app.post("/logout")
@login_required
def logout():
    if not csrf_valid():
        return "Invalid request token", 400
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", name=session.get("name"), role=session.get("role"))

@app.route("/admin")
@admin_required
def admin():
    notices = db().execute("SELECT * FROM notices ORDER BY id DESC").fetchall()
    return render_template("admin.html", notices=notices)

@app.post("/admin/notices")
@admin_required
def add_notice():
    if not csrf_valid():
        return "Invalid request token", 400
    fields = [request.form.get(k, "").strip() for k in
              ("title_bn", "title_en", "body_bn", "body_en", "category", "source_url")]
    if not all(fields[:5]):
        flash("সব আবশ্যক তথ্য পূরণ করুন।", "error")
        return redirect(url_for("admin"))
    db().execute(
        "INSERT INTO notices(title_bn,title_en,body_bn,body_en,category,source_url,published) VALUES(?,?,?,?,?,?,1)",
        fields
    )
    db().commit()
    return redirect(url_for("admin"))

@app.post("/admin/notices/<int:notice_id>/toggle")
@admin_required
def toggle_notice(notice_id):
    if not csrf_valid():
        return "Invalid request token", 400
    db().execute("UPDATE notices SET published=1-published WHERE id=?", (notice_id,))
    db().commit()
    return redirect(url_for("admin"))

@app.get("/api/status")
def status():
    return jsonify({"status": "ok", "app": "Amar Bangladesh", "data_mode": "prototype"})

@app.get("/government-data")
def government_data():
    return render_template("government_data.html")

@app.get("/api/open-data/catalog")
def open_data_catalog():
    return jsonify({"datasets": [{
        "title": "GDP Growth Rate (historical)",
        "publisher": "Bangladesh Open Data Portal",
        "period": "1980–2015",
        "is_live": False,
        "source": "https://www.data.gov.bd/visualization/chart?id=2",
        "note": "Historical dataset; not a live economic indicator."
    }]})

@app.get("/api/open-data/gdp-growth")
def gdp_growth():
    return jsonify({"dataset": "GDP Growth Rate", "period": "1980–2015",
                    "live": False, "source": "https://www.data.gov.bd/visualization/chart?id=2",
                    "message": "Historical source reference. Current live values are not available in this prototype."})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
