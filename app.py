import os, sqlite3, secrets
from flask import Flask, request, redirect, session, flash, jsonify, render_template_string, abort
from werkzeug.security import generate_password_hash, check_password_hash

app=Flask(__name__)
app.secret_key=os.environ.get("SECRET_KEY",secrets.token_hex(32))
DB=os.environ.get("DATABASE_PATH","amar_bangladesh.db")
SERVICES=[
("health","স্বাস্থ্যসেবা","Healthcare","✚","হাসপাতাল ও স্বাস্থ্যবিষয়ক তথ্য"),
("jobs","চাকরি","Jobs","💼","চাকরি ও প্রস্তুতির তথ্য"),
("education","শিক্ষা","Education","📚","শিক্ষা, ভর্তি ও বৃত্তি"),
("government","সরকারি সেবা","Government Services","🏛️","সরকারি দপ্তর ও অনলাইন সেবা"),
("local","স্থানীয় সেবা","Local Services","📍","স্থানীয় প্রয়োজনীয় সেবা"),
("emergency","জরুরি যোগাযোগ","Emergency Contacts","☎️","জরুরি সহায়তার তথ্য")]
def connect():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
 with connect() as c:
  c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL)")
  c.execute("CREATE TABLE IF NOT EXISTS notices(id INTEGER PRIMARY KEY,category TEXT NOT NULL,title TEXT NOT NULL,body TEXT NOT NULL,url TEXT NOT NULL DEFAULT '',published INTEGER NOT NULL DEFAULT 1)")
  if c.execute("SELECT COUNT(*) FROM notices").fetchone()[0]==0:
   c.executemany("INSERT INTO notices(category,title,body,url) VALUES(?,?,?,?)",[
   ("government","বাংলাদেশ জাতীয় তথ্য বাতায়ন","সরকারি তথ্য ও সেবা খুঁজুন জাতীয় তথ্য বাতায়নে।","https://bangladesh.gov.bd/"),
   ("government","বাংলাদেশ ওপেন ডেটা","উন্মুক্ত সরকারি ডেটাসেট খুঁজুন।","https://www.data.gov.bd/"),
   ("emergency","জাতীয় জরুরি সেবা","জরুরি সহায়তার জন্য ৯৯৯ নম্বরে যোগাযোগ করুন।","https://999.gov.bd/")])
def token():
 if "csrf" not in session: session["csrf"]=secrets.token_urlsafe(24)
 return session["csrf"]
@app.before_request
def check_csrf():
 if request.method=="POST" and request.form.get("csrf")!=session.get("csrf"): abort(400,"Page expired. Please reload and try again.")
BASE="""<!doctype html><html lang="bn"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{title}} | Amar Bangladesh</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f8f5;color:#18352d;font-family:system-ui,'Noto Sans Bengali',sans-serif}header{background:#123d34;color:white;padding:16px 5%;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}header a{color:white;text-decoration:none;margin-left:12px}.brand{font-size:21px;font-weight:800}.wrap{max-width:1050px;margin:auto;padding:28px 18px}.hero{background:linear-gradient(120deg,#e1f3e7,#f5fbf6);padding:34px;border-radius:20px}.hero h1{font-size:clamp(28px,5vw,44px);margin:8px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:15px;margin:20px 0}.card,.notice{background:white;border:1px solid #e1ebe4;border-radius:15px;padding:19px}.card{color:inherit;text-decoration:none}.card:hover{border-color:#23835e}.icon{font-size:28px}.muted{color:#64766d}.btn,button{display:inline-block;background:#167a55;color:white;border:0;border-radius:9px;padding:11px 16px;text-decoration:none;font-weight:700;cursor:pointer}.btn.light{background:white;color:#167a55;border:1px solid #b8d4c4}input{display:block;width:100%;padding:12px;border:1px solid #cbd9d0;border-radius:9px;margin:6px 0 15px}label{font-weight:650}.notice{margin:12px 0;border-left:4px solid #167a55}.flash{background:#fff2d1;padding:12px;border-radius:8px;margin-bottom:12px}footer{text-align:center;color:#68786f;padding:24px}</style>
<header><a class="brand" href="/">🇧🇩 Amar Bangladesh</a><nav><a href="/">হোম</a>{% if user %}<a href="/account">আমার অ্যাকাউন্ট</a><a href="/logout">লগআউট</a>{% else %}<a href="/login">লগইন</a><a href="/signup">সাইন আপ</a>{% endif %}</nav></header><main class="wrap">{% for m in messages %}<div class="flash">{{m}}</div>{% endfor %}{{body|safe}}</main><footer>Amar Bangladesh · তথ্য ব্যবহারের আগে মূল উৎসে যাচাই করুন।</footer></html>"""
def page(title,body,**kw):
 return render_template_string(BASE,title=title,body=render_template_string(body,**kw),user=session.get("user"),messages=list(get_flashed_messages()))
from flask import get_flashed_messages
@app.route("/")
def home():
 body="""<section class="hero"><p>বাংলাদেশের প্রয়োজনীয় তথ্য, এক জায়গায়</p><h1>আপনার সেবার সহজ ঠিকানা</h1><p class="muted">স্বাস্থ্য, শিক্ষা, চাকরি ও সরকারি সেবার তথ্য সহজে খুঁজুন।</p><a class="btn" href="#services">সেবা দেখুন</a> <a class="btn light" href="/government-data">ওপেন ডেটা</a></section><h2 id="services">সেবার বিভাগ</h2><section class="grid">{% for s in services %}<a class="card" href="/service/{{s[0]}}"><div class="icon">{{s[3]}}</div><h3>{{s[1]}} · {{s[2]}}</h3><p class="muted">{{s[4]}}</p></a>{% endfor %}</section><div class="card"><b>তথ্য যাচাই:</b> এটি প্রাথমিক প্রোটোটাইপ। প্রকাশের আগে প্রতিটি তথ্য সংশ্লিষ্ট কর্তৃপক্ষের ওয়েবসাইটে যাচাই করুন।</div>"""
 return page("হোম",body,services=SERVICES)
@app.route("/service/<slug>")
def service(slug):
 s=next((x for x in SERVICES if x[0]==slug),None)
 if not s: abort(404)
 with connect() as c: rows=c.execute("SELECT * FROM notices WHERE category=? AND published=1 ORDER BY id DESC",(slug,)).fetchall()
 body="""<a href="/">← হোম</a><h1>{{s[3]}} {{s[1]}} · {{s[2]}}</h1><p class="muted">{{s[4]}}</p>{% for n in rows %}<article class="notice"><h3>{{n.title}}</h3><p>{{n.body}}</p>{% if n.url %}<a href="{{n.url}}" target="_blank" rel="noopener">মূল উৎস দেখুন ↗</a>{% endif %}</article>{% else %}<div class="card">এই বিভাগে এখনো তথ্য যোগ করা হয়নি।</div>{% endfor %}"""
 return page(s[1],body,s=s,rows=rows)
@app.route("/signup",methods=["GET","POST"])
def signup():
 if request.method=="POST":
  name=request.form.get("name","").strip(); email=request.form.get("email","").strip().lower(); pw=request.form.get("password","")
  if not name or len(name)>80 or "@" not in email or len(pw)<8:
   flash("নাম, সঠিক ইমেইল এবং কমপক্ষে ৮ অক্ষরের পাসওয়ার্ড দিন।")
  else:
   try:
    with connect() as c: c.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",(name,email,generate_password_hash(pw)))
    flash("অ্যাকাউন্ট তৈরি হয়েছে। এখন লগইন করুন।"); return redirect("/login")
   except sqlite3.IntegrityError: flash("এই ইমেইলে অ্যাকাউন্ট আছে।")
 body="""<div class="card"><h1>সাইন আপ</h1><form method="post"><input type="hidden" name="csrf" value="{{csrf}}"><label>নাম</label><input name="name" required maxlength="80"><label>ইমেইল</label><input name="email" type="email" required><label>পাসওয়ার্ড (কমপক্ষে ৮ অক্ষর)</label><input name="password" type="password" minlength="8" required><button>অ্যাকাউন্ট তৈরি</button></form></div>"""
 return page("সাইন আপ",body,csrf=token())
@app.route("/login",methods=["GET","POST"])
def login():
 if request.method=="POST":
  email=request.form.get("email","").strip().lower()
  with connect() as c: u=c.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
  if u and check_password_hash(u["password"],request.form.get("password","")):
   session.clear(); session["user"]={"name":u["name"],"email":u["email"]}; token(); return redirect("/account")
  flash("ইমেইল বা পাসওয়ার্ড সঠিক নয়।")
 body="""<div class="card"><h1>লগইন</h1><form method="post"><input type="hidden" name="csrf" value="{{csrf}}"><label>ইমেইল</label><input name="email" type="email" required><label>পাসওয়ার্ড</label><input name="password" type="password" required><button>লগইন</button></form></div>"""
 return page("লগইন",body,csrf=token())
@app.route("/account")
def account():
 if not session.get("user"): return redirect("/login")
 return page("অ্যাকাউন্ট","<div class='card'><h1>স্বাগতম, {{name}}</h1><p>{{email}}</p></div>",name=session["user"]["name"],email=session["user"]["email"])
@app.route("/logout")
def logout():
 session.clear(); return redirect("/")
@app.route("/government-data")
def government_data():
 body="""<h1>সরকারি ওপেন ডেটা</h1><p class="muted">এখানে সরকারি উন্মুক্ত ডেটার উৎস দেওয়া হলো। এই প্রোটোটাইপ এখনো কোনো লাইভ সরকারি ডেটা API-তে সংযুক্ত নয়।</p><div class="notice"><h3>বাংলাদেশ ওপেন ডেটা পোর্টাল</h3><a href="https://www.data.gov.bd/" target="_blank" rel="noopener">data.gov.bd ↗</a></div><div class="notice"><h3>জাতীয় তথ্য বাতায়ন</h3><a href="https://bangladesh.gov.bd/" target="_blank" rel="noopener">bangladesh.gov.bd ↗</a></div>"""
 return page("ওপেন ডেটা",body)
@app.get("/api/status")
def status(): return jsonify(status="ok",app="Amar Bangladesh",version="0.1",live_government_api=False)
@app.get("/api/services")
def api_services(): return jsonify([{"slug":s[0],"bn":s[1],"en":s[2]} for s in SERVICES])
init_db()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
