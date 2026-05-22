import sqlite3
import os
import json
from datetime import datetime, date, timedelta
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, g)
from werkzeug.security import generate_password_hash, check_password_hash

# ─── VIN Decoder: Chinese WMI Database ───────────────────────────────────────
VIN_WMI_DB = {
    # ── Lixiang (Li Auto) ──
    "HLX": {"brand": "Lixiang", "country": "Китай", "models": ["L6", "L7", "L8", "L9", "MEGA"]},
    "LSX": {"brand": "Lixiang", "country": "Китай", "models": ["L7", "L8", "L9"]},

    # ── Zeekr ──
    "LSN": {"brand": "Zeekr", "country": "Китай", "models": ["001", "007", "009", "X"]},
    "LPS": {"brand": "Zeekr", "country": "Китай", "models": ["001", "X"]},

    # ── Geely ──
    "LGS": {"brand": "Geely", "country": "Китай", "models": ["Atlas", "Coolray", "Tugella"]},
    "LFV": {"brand": "Geely", "country": "Китай", "models": ["Coolray", "Atlas Pro", "Monjaro"]},
    "LSG": {"brand": "Geely", "country": "Китай", "models": ["Atlas", "Emgrand"]},
    "LGB": {"brand": "Geely", "country": "Китай", "models": ["Emgrand", "GS"]},
    "LGH": {"brand": "Geely", "country": "Китай", "models": ["Emgrand X7"]},
    "LGL": {"brand": "Geely", "country": "Китай", "models": ["GX3 Pro", "Geometry"]},

    # ── BYD ──
    "LGX": {"brand": "BYD", "country": "Китай", "models": ["Han", "Tang", "Song", "Seal"]},
    "LBV": {"brand": "BYD", "country": "Китай", "models": ["Atto 3", "Dolphin", "Seal"]},
    "LB9": {"brand": "BYD", "country": "Китай", "models": ["Han EV", "Tang EV"]},
    "LL6": {"brand": "BYD", "country": "Китай", "models": ["Song Pro", "Song Max"]},
    "LFD": {"brand": "BYD", "country": "Китай", "models": ["F3", "F0"]},
    "LGR": {"brand": "BYD", "country": "Китай", "models": ["Qin Plus", "Yuan Plus"]},

    # ── Chery ──
    "LVV": {"brand": "Chery", "country": "Китай", "models": ["Tiggo 4", "Tiggo 7", "Tiggo 8"]},
    "LVS": {"brand": "Chery", "country": "Китай", "models": ["Tiggo 8 Pro", "Arrizo 8"]},
    "LHG": {"brand": "Chery", "country": "Китай", "models": ["Tiggo 7 Pro", "Tiggo 4 Pro"]},
    "L6C": {"brand": "Chery", "country": "Китай", "models": ["Tiggo 8 Plus", "Omoda 5"]},
    "LJC": {"brand": "Chery", "country": "Китай", "models": ["Exeed LX", "Exeed TX"]},

    # ── Haval / Great Wall ──
    "LGW": {"brand": "Haval", "country": "Китай", "models": ["H6", "H9", "F7"]},
    "LHG": {"brand": "Haval", "country": "Китай", "models": ["H6", "H4", "H2"]},
    "LW3": {"brand": "Haval", "country": "Китай", "models": ["Jolion", "H6 HEV"]},
    "LGR": {"brand": "Great Wall", "country": "Китай", "models": ["Poer", "Cannon"]},

    # ── AITO (Huawei) ──
    "LHH": {"brand": "AITO", "country": "Китай", "models": ["M5", "M7", "M9"]},
    "LSA": {"brand": "AITO", "country": "Китай", "models": ["M7", "M9"]},

    # ── NIO ──
    "LSK": {"brand": "NIO", "country": "Китай", "models": ["ES6", "ES8", "ET5", "ET7", "EC6"]},
    "LWP": {"brand": "NIO", "country": "Китай", "models": ["ET5", "ET7"]},

    # ── XPeng ──
    "LSX": {"brand": "XPeng", "country": "Китай", "models": ["P7", "P5", "G3", "G9"]},
    "LWP": {"brand": "XPeng", "country": "Китай", "models": ["G6", "X9"]},
    "LFX": {"brand": "XPeng", "country": "Китай", "models": ["P5", "G3i"]},

    # ── GAC (Trumpchi) ──
    "LGC": {"brand": "GAC Trumpchi", "country": "Китай", "models": ["GS4", "GS8", "M8"]},
    "LGH": {"brand": "GAC", "country": "Китай", "models": ["Aion S", "Aion Y", "Aion V"]},

    # ── SAIC / MG / Roewe ──
    "LSJ": {"brand": "SAIC MG", "country": "Китай", "models": ["MG4", "MG5", "Cyberster"]},
    "LMN": {"brand": "Roewe", "country": "Китай", "models": ["RX5", "Marvel R", "i5"]},
    "LSK": {"brand": "SAIC", "country": "Китай", "models": ["MG6", "Roewe 350"]},

    # ── Voyah (Dongfeng) ──
    "LYC": {"brand": "Voyah", "country": "Китай", "models": ["Free", "Dream", "Passion"]},
    "LDY": {"brand": "Dongfeng", "country": "Китай", "models": ["Aeolus AX7", "DFSK"]},

    # ── Hongqi (FAW) ──
    "LFN": {"brand": "Hongqi", "country": "Китай", "models": ["E-QM5", "H5", "H9", "HS5"]},
    "LFA": {"brand": "FAW", "country": "Китай", "models": ["Bestune T77", "T99"]},

    # ── JAC ──
    "LHV": {"brand": "JAC", "country": "Китай", "models": ["JS4", "JS6", "Sehol"]},

    # ── Changan ──
    "LZZ": {"brand": "Changan", "country": "Китай", "models": ["CS35 Plus", "CS75", "Uni-K"]},
    "LFP": {"brand": "Changan", "country": "Китай", "models": ["CS55 Plus", "UNI-V"]},
    "LC6": {"brand": "Avatr", "country": "Китай", "models": ["11", "12"]},

    # ── OMODA / Jaecoo (Chery sub) ──
    "LHR": {"brand": "OMODA", "country": "Китай", "models": ["C5", "C7", "S5"]},
    "LJJ": {"brand": "Jaecoo", "country": "Китай", "models": ["J7", "J8"]},

    # ── Tank (Great Wall) ──
    "LHC": {"brand": "Tank", "country": "Китай", "models": ["300", "400", "500"]},

    # ── Denza (BYD-Mercedes) ──
    "LNB": {"brand": "Denza", "country": "Китай", "models": ["D9", "N7", "Z9"]},
}

# Extended 2-char prefix fallback
VIN_PREFIX2_DB = {
    "HL": "Lixiang",
    "LS": "Zeekr / Geely / SAIC / NIO",
    "LF": "Geely / BYD / Chery / Changan",
    "LG": "Geely / BYD / Haval / GAC",
    "LB": "BYD",
    "LV": "Chery / Volvo China",
    "LH": "Chery / Haval / JAC / AITO",
    "LW": "Haval / NIO / XPeng",
    "LY": "Voyah / Yangwang",
    "LN": "Roewe / Denza",
    "LC": "Avatr / Changan",
    "LJ": "Chery Exeed / Jaecoo",
    "LZ": "Changan / Zotye",
    "LL": "BYD",
    "LK": "SAIC-GM-Wuling",
    "LP": "Zeekr",
    "LT": "FAW / BAIC",
    "LA": "FAW",
    "LM": "Roewe",
    "LD": "Dongfeng / DFSK",
}

def decode_vin(vin: str) -> dict:
    """Decode VIN: detect brand, country, model hints."""
    vin = vin.strip().upper()
    result = {"valid": False, "brand": None, "country": None, "models": [], "wmi": None, "info": ""}

    if len(vin) != 17:
        result["info"] = "VIN должен содержать ровно 17 символов"
        return result

    # Basic character validation (I, O, Q not allowed)
    import re
    if re.search(r'[IOQ]', vin):
        result["info"] = "VIN содержит недопустимые символы (I, O, Q)"
        return result

    result["valid"] = True
    wmi = vin[:3]  # World Manufacturer Identifier
    result["wmi"] = wmi

    # 3-char WMI lookup
    if wmi in VIN_WMI_DB:
        d = VIN_WMI_DB[wmi]
        result["brand"] = d["brand"]
        result["country"] = d["country"]
        result["models"] = d.get("models", [])
        result["info"] = f"Определено по WMI-коду {wmi}"
        return result

    # 2-char prefix fallback
    prefix2 = vin[:2]
    if prefix2 in VIN_PREFIX2_DB:
        result["brand"] = VIN_PREFIX2_DB[prefix2]
        result["country"] = "Китай"
        result["info"] = f"Определено по префиксу {prefix2} (приблизительно)"
        return result

    # Check if it's a Chinese VIN by first char 'L' (all Chinese manufacturers)
    if vin[0] == 'L':
        result["country"] = "Китай"
        result["info"] = f"Китайский VIN (WMI: {wmi}), марка не определена точно"
    else:
        result["info"] = f"WMI {wmi} не найден в базе китайских производителей"

    return result

app = Flask(__name__)

# ─── ProxyFix: корректный scheme (https) за Render load balancer ──────────────
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# ─── Config from environment ──────────────────────────────────────────────────
# SECRET_KEY: задаётся через переменную окружения (Render Dashboard / .env)
# Запасной ключ используется ТОЛЬКО для локальной разработки
app.secret_key = os.environ.get(
    'SECRET_KEY',
    'dev-only-insecure-key-change-in-production-please'
)

# DATABASE_PATH: на Render указывает на /data/autoservice.db (persistent disk)
# Локально — instance/autoservice.db
_db_path_env = os.environ.get('DATABASE_PATH', '').strip()
if _db_path_env:
    DATABASE = _db_path_env
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
else:
    os.makedirs(app.instance_path, exist_ok=True)
    DATABASE = os.path.join(app.instance_path, 'autoservice.db')

# ─── DB helpers ───────────────────────────────────────────────────────────────
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid

# ─── Init DB ──────────────────────────────────────────────────────────────────
def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vin TEXT UNIQUE NOT NULL,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER,
            color TEXT,
            license_plate TEXT,
            mileage INTEGER DEFAULT 0,
            chinese_number TEXT,
            chinese_number_expiry TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS service_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            order_number TEXT UNIQUE NOT NULL,
            date TEXT NOT NULL,
            mileage INTEGER,
            description TEXT,
            status TEXT DEFAULT 'pending',
            total_cost REAL DEFAULT 0,
            technician TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS service_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            service_name TEXT NOT NULL,
            category TEXT,
            quantity REAL DEFAULT 1,
            unit_price REAL DEFAULT 0,
            total_price REAL DEFAULT 0,
            FOREIGN KEY(order_id) REFERENCES service_orders(id)
        );

        CREATE TABLE IF NOT EXISTS maintenance_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT,
            work_name TEXT NOT NULL,
            category TEXT,
            interval_km INTEGER,
            interval_months INTEGER,
            description TEXT,
            priority TEXT DEFAULT 'normal'
        );

        CREATE TABLE IF NOT EXISTS recalls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT,
            title TEXT NOT NULL,
            description TEXT,
            affected_vins TEXT,
            issue_date TEXT,
            status TEXT DEFAULT 'active',
            official_url TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sim_topup_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            sim_type TEXT NOT NULL,
            amount REAL,
            topup_date TEXT NOT NULL,
            next_topup TEXT,
            note TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vehicle_id INTEGER,
            title TEXT NOT NULL,
            message TEXT,
            type TEXT DEFAULT 'info',
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    ''')
    db.commit()

    # Migrations: add SIM card fields to vehicles if not exist
    existing_cols = [row[1] for row in db.execute("PRAGMA table_info(vehicles)").fetchall()]
    sim_migrations = [
        ("rf_sim_number", "ALTER TABLE vehicles ADD COLUMN rf_sim_number TEXT"),
        ("rf_sim_operator", "ALTER TABLE vehicles ADD COLUMN rf_sim_operator TEXT"),
        ("rf_sim_topup_date", "ALTER TABLE vehicles ADD COLUMN rf_sim_topup_date TEXT"),
        ("rf_sim_topup_days", "ALTER TABLE vehicles ADD COLUMN rf_sim_topup_days INTEGER DEFAULT 30"),
        ("esender_number", "ALTER TABLE vehicles ADD COLUMN esender_number TEXT"),
        ("esender_topup_date", "ALTER TABLE vehicles ADD COLUMN esender_topup_date TEXT"),
        ("esender_topup_days", "ALTER TABLE vehicles ADD COLUMN esender_topup_days INTEGER DEFAULT 30"),
    ]
    for col, sql in sim_migrations:
        if col not in existing_cols:
            db.execute(sql)
    db.commit()

    # Seed admin
    admin = db.execute("SELECT id FROM users WHERE email='admin@autoservice.ru'").fetchone()
    if not admin:
        db.execute("INSERT INTO users(name,email,phone,password,is_admin) VALUES(?,?,?,?,?)",
                   ('Администратор', 'admin@autoservice.ru', '+7 999 000-00-00',
                    generate_password_hash('admin123'), 1))
        db.commit()

    # Seed maintenance schedule
    if not db.execute("SELECT id FROM maintenance_schedule LIMIT 1").fetchone():
        schedules = [
            ('Lixiang', None, 'Замена моторного масла и фильтра', 'Двигатель', 10000, 12, 'Полная замена масла 0W-20', 'high'),
            ('Lixiang', None, 'Замена воздушного фильтра', 'Двигатель', 20000, 24, 'Очистка или замена фильтра', 'normal'),
            ('Lixiang', None, 'Замена тормозной жидкости', 'Тормоза', 40000, 24, 'Полная замена DOT 4', 'high'),
            ('Lixiang', None, 'Диагностика высоковольтной батареи', 'Электрика', 20000, 12, 'Проверка ячеек и BMS', 'high'),
            ('Lixiang', None, 'Проверка тормозных колодок', 'Тормоза', 15000, 6, 'Измерение остаточной толщины', 'normal'),
            ('Zeekr', None, 'Замена моторного масла', 'Двигатель', 10000, 12, 'Масло 0W-30 синтетика', 'high'),
            ('Zeekr', None, 'Обслуживание кондиционера', 'Климат', 30000, 24, 'Замена фильтра салона, дозаправка', 'normal'),
            ('Zeekr', None, 'Проверка подвески', 'Подвеска', 20000, 12, 'Все узлы и шарниры', 'normal'),
            ('Zeekr', None, 'Диагностика электродвигателя', 'Электрика', 40000, 24, 'Проверка изоляции и охлаждения', 'high'),
            ('Geely', None, 'Замена масла в АКПП', 'Трансмиссия', 60000, 36, 'Замена масла ATF', 'normal'),
            ('Geely', None, 'Замена свечей зажигания', 'Двигатель', 30000, 24, 'Иридиевые свечи', 'normal'),
            ('Geely', None, 'Обслуживание тормозной системы', 'Тормоза', 20000, 12, 'Проверка дисков и колодок', 'high'),
            ('BYD', None, 'Калибровка батарейного блока', 'Электрика', 30000, 12, 'SOC калибровка', 'high'),
            ('BYD', None, 'Проверка зарядного порта', 'Электрика', 10000, 6, 'Контакты и уплотнения', 'normal'),
            ('Chery', None, 'Замена ремня ГРМ', 'Двигатель', 80000, 48, 'Комплект ГРМ', 'high'),
            ('Haval', None, 'Обслуживание полного привода', 'Трансмиссия', 40000, 24, 'Раздаточная коробка', 'normal'),
        ]
        db.executemany(
            "INSERT INTO maintenance_schedule(brand,model,work_name,category,interval_km,interval_months,description,priority) VALUES(?,?,?,?,?,?,?,?)",
            schedules)
        db.commit()

    # Seed recalls
    if not db.execute("SELECT id FROM recalls LIMIT 1").fetchone():
        recalls = [
            ('Lixiang', 'L9', 'Отзыв: программное обеспечение системы AEB', 'Возможный сбой автоэкстренного торможения при скорости выше 120 км/ч. Требуется обновление ПО до версии 3.2.1', None, '2024-03-15', 'active', 'https://www.lixiang.com/recall'),
            ('Zeekr', '001', 'Отзыв: уплотнение высоковольтного разъёма', 'Возможное проникновение влаги в высоковольтный разъём при мойке. Требуется замена уплотнителя', None, '2024-06-20', 'active', None),
            ('Geely', 'Coolray', 'Рекомендация: обновление прошивки мультимедиа', 'Устранение зависаний системы навигации. Рекомендуется обновление до версии 5.0', None, '2024-01-10', 'completed', None),
            ('BYD', 'Han', 'Отзыв: датчик положения педали газа', 'Возможная ложная активация в режиме Sport. Замена датчика бесплатно по гарантии', None, '2024-08-05', 'active', None),
        ]
        db.executemany(
            "INSERT INTO recalls(brand,model,title,description,affected_vins,issue_date,status,official_url) VALUES(?,?,?,?,?,?,?,?)",
            recalls)
        db.commit()

    db.close()

# ─── Auth helpers ─────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = query_db("SELECT * FROM users WHERE id=?", [session['user_id']], one=True)
        if not user or not user['is_admin']:
            flash('Доступ запрещён', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

def current_user():
    if 'user_id' in session:
        return query_db("SELECT * FROM users WHERE id=?", [session['user_id']], one=True)
    return None

# ─── Routes: Auth ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if not all([name, email, password]):
            flash('Заполните все обязательные поля', 'error')
        elif password != confirm:
            flash('Пароли не совпадают', 'error')
        elif len(password) < 6:
            flash('Пароль должен быть не менее 6 символов', 'error')
        elif query_db("SELECT id FROM users WHERE email=?", [email], one=True):
            flash('Email уже зарегистрирован', 'error')
        else:
            uid = execute_db(
                "INSERT INTO users(name,email,phone,password) VALUES(?,?,?,?)",
                (name, email, phone, generate_password_hash(password)))
            session['user_id'] = uid
            session['user_name'] = name
            flash(f'Добро пожаловать, {name}!', 'success')
            return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = query_db("SELECT * FROM users WHERE email=?", [email], one=True)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['is_admin'] = bool(user['is_admin'])
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        flash('Неверный email или пароль', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ─── Routes: User Dashboard ───────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user()
    vehicles = query_db("SELECT * FROM vehicles WHERE user_id=? ORDER BY created_at DESC", [user['id']])
    
    # Unread notifications
    notifications = query_db(
        "SELECT * FROM notifications WHERE user_id=? AND is_read=0 ORDER BY created_at DESC LIMIT 5",
        [user['id']])
    
    # Stats
    total_orders = query_db(
        "SELECT COUNT(*) as cnt FROM service_orders WHERE user_id=?", [user['id']], one=True)

    # Compute SIM due days for dashboard cards
    today = date.today()
    def sim_days_left(topup_str, interval):
        if not topup_str: return None
        try:
            due = datetime.strptime(topup_str, "%Y-%m-%d").date() + timedelta(days=int(interval or 30))
            return (due - today).days
        except: return None

    vehicles_data = []
    for v in vehicles:
        vd = dict(v)
        vd['rf_sim_days_left'] = sim_days_left(v['rf_sim_topup_date'], v['rf_sim_topup_days'])
        vd['esender_days_left'] = sim_days_left(v['esender_topup_date'], v['esender_topup_days'])
        vehicles_data.append(vd)
    
    return render_template('dashboard.html', user=user, vehicles=vehicles_data,
                           notifications=notifications, total_orders=total_orders['cnt'])

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        execute_db("UPDATE users SET name=?, phone=? WHERE id=?",
                   (name, phone, user['id']))
        session['user_name'] = name
        flash('Профиль обновлён', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)

# ─── Routes: Vehicles ─────────────────────────────────────────────────────────
@app.route('/vehicles/add', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    user = current_user()
    brands = ['Lixiang', 'Zeekr', 'Geely', 'BYD', 'Chery', 'Haval', 'AITO', 'NIO', 'XPeng', 'GAC', 'SAIC']
    if request.method == 'POST':
        vin = request.form.get('vin', '').strip().upper()
        brand = request.form.get('brand', '').strip()
        model = request.form.get('model', '').strip()
        year = request.form.get('year', '')
        color = request.form.get('color', '').strip()
        license_plate = request.form.get('license_plate', '').strip().upper()
        mileage = request.form.get('mileage', 0) or 0
        chinese_number = request.form.get('chinese_number', '').strip()
        cn_expiry = request.form.get('chinese_number_expiry', '')
        notes = request.form.get('notes', '').strip()
        rf_sim_number = request.form.get('rf_sim_number', '').strip()
        rf_sim_operator = request.form.get('rf_sim_operator', '').strip()
        rf_sim_topup_date = request.form.get('rf_sim_topup_date', '') or None
        rf_sim_topup_days = request.form.get('rf_sim_topup_days', 30) or 30
        esender_number = request.form.get('esender_number', '').strip()
        esender_topup_date = request.form.get('esender_topup_date', '') or None
        esender_topup_days = request.form.get('esender_topup_days', 30) or 30

        if not vin or len(vin) != 17:
            flash('VIN должен содержать 17 символов', 'error')
        elif query_db("SELECT id FROM vehicles WHERE vin=?", [vin], one=True):
            flash('Автомобиль с таким VIN уже зарегистрирован', 'error')
        else:
            vid = execute_db(
                """INSERT INTO vehicles(user_id,vin,brand,model,year,color,license_plate,
                   mileage,chinese_number,chinese_number_expiry,notes,
                   rf_sim_number,rf_sim_operator,rf_sim_topup_date,rf_sim_topup_days,
                   esender_number,esender_topup_date,esender_topup_days)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (user['id'], vin, brand, model, year or None, color, license_plate,
                 mileage, chinese_number, cn_expiry or None, notes,
                 rf_sim_number or None, rf_sim_operator or None, rf_sim_topup_date, rf_sim_topup_days,
                 esender_number or None, esender_topup_date, esender_topup_days))
            # Check recalls for this brand
            recalls = query_db("SELECT * FROM recalls WHERE brand=? AND status='active'", [brand])
            for r in recalls:
                execute_db(
                    "INSERT INTO notifications(user_id,vehicle_id,title,message,type) VALUES(?,?,?,?,?)",
                    (user['id'], vid, f'⚠️ Отзывная кампания: {r["brand"]}',
                     r['title'], 'warning'))
            flash('Автомобиль успешно добавлен!', 'success')
            return redirect(url_for('vehicle_detail', vid=vid))

    return render_template('add_vehicle.html', user=user, brands=brands,
                           vin_result=None)

@app.route('/vehicles/<int:vid>')
@login_required
def vehicle_detail(vid):
    user = current_user()
    vehicle = query_db("SELECT * FROM vehicles WHERE id=? AND user_id=?", [vid, user['id']], one=True)
    if not vehicle:
        flash('Автомобиль не найден', 'error')
        return redirect(url_for('dashboard'))

    orders = query_db(
        """SELECT so.*, COUNT(si.id) as items_count
           FROM service_orders so
           LEFT JOIN service_items si ON si.order_id = so.id
           WHERE so.vehicle_id=? GROUP BY so.id ORDER BY so.date DESC""",
        [vid])

    schedule = query_db(
        "SELECT * FROM maintenance_schedule WHERE brand=? ORDER BY interval_km",
        [vehicle['brand']])

    recalls = query_db(
        "SELECT * FROM recalls WHERE brand=? AND status='active' ORDER BY issue_date DESC",
        [vehicle['brand']])

    # Days until Chinese number expiry
    cn_days = None
    if vehicle['chinese_number_expiry']:
        try:
            exp = datetime.strptime(vehicle['chinese_number_expiry'], '%Y-%m-%d').date()
            cn_days = (exp - date.today()).days
        except:
            pass

    # SIM card due dates
    def sim_due(topup_date_str, interval_days):
        if not topup_date_str:
            return None, None
        try:
            last = datetime.strptime(topup_date_str, '%Y-%m-%d').date()
            due = last + timedelta(days=int(interval_days or 30))
            days_left = (due - date.today()).days
            return due, days_left
        except:
            return None, None

    rf_sim_due, rf_sim_days = sim_due(vehicle['rf_sim_topup_date'], vehicle['rf_sim_topup_days'])
    esender_due, esender_days = sim_due(vehicle['esender_topup_date'], vehicle['esender_topup_days'])

    # SIM topup history
    sim_history = query_db(
        "SELECT * FROM sim_topup_history WHERE vehicle_id=? ORDER BY topup_date DESC LIMIT 20",
        [vid])

    return render_template('vehicle_detail.html', user=user, vehicle=vehicle,
                           orders=orders, schedule=schedule, recalls=recalls,
                           cn_days=cn_days,
                           rf_sim_due=rf_sim_due, rf_sim_days=rf_sim_days,
                           esender_due=esender_due, esender_days=esender_days,
                           sim_history=sim_history,
                           today_str=date.today().isoformat())

@app.route('/vehicles/<int:vid>/edit', methods=['GET', 'POST'])
@login_required
def edit_vehicle(vid):
    user = current_user()
    vehicle = query_db("SELECT * FROM vehicles WHERE id=? AND user_id=?", [vid, user['id']], one=True)
    if not vehicle:
        return redirect(url_for('dashboard'))
    brands = ['Lixiang', 'Zeekr', 'Geely', 'BYD', 'Chery', 'Haval', 'AITO', 'NIO', 'XPeng', 'GAC', 'SAIC']
    if request.method == 'POST':
        execute_db(
            """UPDATE vehicles SET brand=?,model=?,year=?,color=?,license_plate=?,
               mileage=?,chinese_number=?,chinese_number_expiry=?,notes=?,
               rf_sim_number=?,rf_sim_operator=?,rf_sim_topup_date=?,rf_sim_topup_days=?,
               esender_number=?,esender_topup_date=?,esender_topup_days=? WHERE id=?""",
            (request.form.get('brand'), request.form.get('model'),
             request.form.get('year') or None, request.form.get('color'),
             request.form.get('license_plate', '').upper(),
             request.form.get('mileage', 0) or 0,
             request.form.get('chinese_number'),
             request.form.get('chinese_number_expiry') or None,
             request.form.get('notes'),
             request.form.get('rf_sim_number') or None,
             request.form.get('rf_sim_operator') or None,
             request.form.get('rf_sim_topup_date') or None,
             request.form.get('rf_sim_topup_days') or 30,
             request.form.get('esender_number') or None,
             request.form.get('esender_topup_date') or None,
             request.form.get('esender_topup_days') or 30,
             vid))
        flash('Данные автомобиля обновлены', 'success')
        return redirect(url_for('vehicle_detail', vid=vid))
    return render_template('edit_vehicle.html', user=user, vehicle=vehicle, brands=brands)

# ─── Routes: Service Orders ───────────────────────────────────────────────────
@app.route('/orders/<int:oid>')
@login_required
def order_detail(oid):
    user = current_user()
    order = query_db(
        """SELECT so.*, v.brand, v.model, v.vin, v.license_plate
           FROM service_orders so JOIN vehicles v ON v.id=so.vehicle_id
           WHERE so.id=? AND so.user_id=?""", [oid, user['id']], one=True)
    if not order:
        flash('Заказ-наряд не найден', 'error')
        return redirect(url_for('dashboard'))
    items = query_db("SELECT * FROM service_items WHERE order_id=?", [oid])
    return render_template('order_detail.html', user=user, order=order, items=items)

# ─── Routes: Notifications ────────────────────────────────────────────────────
@app.route('/notifications/read/<int:nid>')
@login_required
def mark_notification_read(nid):
    execute_db("UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?",
               [nid, session['user_id']])
    return redirect(request.referrer or url_for('dashboard'))

# ─── Routes: Admin ────────────────────────────────────────────────────────────
@app.route('/admin')
@admin_required
def admin_dashboard():
    stats = {
        'users': query_db("SELECT COUNT(*) as c FROM users WHERE is_admin=0", one=True)['c'],
        'vehicles': query_db("SELECT COUNT(*) as c FROM vehicles", one=True)['c'],
        'orders': query_db("SELECT COUNT(*) as c FROM service_orders", one=True)['c'],
        'revenue': query_db("SELECT COALESCE(SUM(total_cost),0) as c FROM service_orders WHERE status='completed'", one=True)['c'],
    }
    recent_orders = query_db(
        """SELECT so.*, u.name as client_name, v.brand, v.model, v.license_plate
           FROM service_orders so
           JOIN users u ON u.id=so.user_id
           JOIN vehicles v ON v.id=so.vehicle_id
           ORDER BY so.created_at DESC LIMIT 10""")
    pending_orders = query_db(
        """SELECT so.*, u.name as client_name, v.brand, v.model
           FROM service_orders so
           JOIN users u ON u.id=so.user_id
           JOIN vehicles v ON v.id=so.vehicle_id
           WHERE so.status IN ('pending','in_progress')
           ORDER BY so.date DESC""")
    return render_template('admin/dashboard.html', stats=stats,
                           recent_orders=recent_orders, pending_orders=pending_orders)

@app.route('/admin/users')
@admin_required
def admin_users():
    users = query_db(
        """SELECT u.*, COUNT(v.id) as vehicle_count,
           COUNT(DISTINCT so.id) as order_count
           FROM users u
           LEFT JOIN vehicles v ON v.user_id=u.id
           LEFT JOIN service_orders so ON so.user_id=u.id
           WHERE u.is_admin=0
           GROUP BY u.id ORDER BY u.created_at DESC""")
    return render_template('admin/users.html', users=users)

@app.route('/admin/vehicles')
@admin_required
def admin_vehicles():
    vehicles = query_db(
        """SELECT v.*, u.name as owner_name, u.phone as owner_phone,
           COUNT(so.id) as order_count
           FROM vehicles v
           JOIN users u ON u.id=v.user_id
           LEFT JOIN service_orders so ON so.vehicle_id=v.id
           GROUP BY v.id ORDER BY v.created_at DESC""")
    return render_template('admin/vehicles.html', vehicles=vehicles)

@app.route('/admin/orders')
@admin_required
def admin_orders():
    status_filter = request.args.get('status', '')
    q = request.args.get('q', '')
    sql = """SELECT so.*, u.name as client_name, u.phone as client_phone,
             v.brand, v.model, v.vin, v.license_plate
             FROM service_orders so
             JOIN users u ON u.id=so.user_id
             JOIN vehicles v ON v.id=so.vehicle_id
             WHERE 1=1"""
    args = []
    if status_filter:
        sql += " AND so.status=?"; args.append(status_filter)
    if q:
        sql += " AND (so.order_number LIKE ? OR u.name LIKE ? OR v.vin LIKE ?)"
        args += [f'%{q}%', f'%{q}%', f'%{q}%']
    sql += " ORDER BY so.created_at DESC"
    orders = query_db(sql, args)
    return render_template('admin/orders.html', orders=orders,
                           status_filter=status_filter, q=q)

@app.route('/admin/orders/new', methods=['GET', 'POST'])
@admin_required
def admin_new_order():
    vehicles = query_db(
        "SELECT v.*, u.name as owner_name FROM vehicles v JOIN users u ON u.id=v.user_id ORDER BY v.brand")
    if request.method == 'POST':
        vid = request.form.get('vehicle_id')
        vehicle = query_db("SELECT * FROM vehicles WHERE id=?", [vid], one=True)
        if not vehicle:
            flash('Автомобиль не найден', 'error')
            return redirect(url_for('admin_new_order'))

        order_num = f"ОН-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        oid = execute_db(
            """INSERT INTO service_orders(vehicle_id,user_id,order_number,date,mileage,
               description,status,technician,notes)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (vid, vehicle['user_id'], order_num,
             request.form.get('date', date.today().isoformat()),
             request.form.get('mileage') or None,
             request.form.get('description'),
             request.form.get('status', 'pending'),
             request.form.get('technician'),
             request.form.get('notes')))

        # Parse service items
        names = request.form.getlist('item_name[]')
        cats = request.form.getlist('item_category[]')
        qtys = request.form.getlist('item_qty[]')
        prices = request.form.getlist('item_price[]')
        total = 0
        for i, nm in enumerate(names):
            if nm.strip():
                qty = float(qtys[i]) if i < len(qtys) and qtys[i] else 1
                price = float(prices[i]) if i < len(prices) and prices[i] else 0
                tp = qty * price
                total += tp
                execute_db(
                    "INSERT INTO service_items(order_id,service_name,category,quantity,unit_price,total_price) VALUES(?,?,?,?,?,?)",
                    (oid, nm.strip(), cats[i] if i < len(cats) else '', qty, price, tp))

        execute_db("UPDATE service_orders SET total_cost=? WHERE id=?", (total, oid))
        execute_db("UPDATE vehicles SET mileage=? WHERE id=? AND ?>(SELECT mileage FROM vehicles WHERE id=?)",
                   (request.form.get('mileage') or 0, vid, request.form.get('mileage') or 0, vid))

        # Notify user
        execute_db("INSERT INTO notifications(user_id,vehicle_id,title,message,type) VALUES(?,?,?,?,?)",
                   (vehicle['user_id'], vid, f'Создан заказ-наряд {order_num}',
                    f'Статус: {request.form.get("status","pending")}. Сумма: {total:.0f} ₽', 'info'))

        flash(f'Заказ-наряд {order_num} создан', 'success')
        return redirect(url_for('admin_orders'))

    return render_template('admin/new_order.html', vehicles=vehicles, today=date.today().isoformat())

@app.route('/admin/orders/<int:oid>/status', methods=['POST'])
@admin_required
def admin_update_order_status(oid):
    new_status = request.form.get('status')
    order = query_db("SELECT * FROM service_orders WHERE id=?", [oid], one=True)
    if order:
        execute_db("UPDATE service_orders SET status=? WHERE id=?", (new_status, oid))
        execute_db("INSERT INTO notifications(user_id,vehicle_id,title,message,type) VALUES(?,?,?,?,?)",
                   (order['user_id'], order['vehicle_id'],
                    f'Статус заказа {order["order_number"]} изменён',
                    f'Новый статус: {new_status}', 'info'))
        flash('Статус обновлён', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/orders/<int:oid>')
@admin_required
def admin_order_detail(oid):
    order = query_db(
        """SELECT so.*, u.name as client_name, u.phone as client_phone, u.email as client_email,
           v.brand, v.model, v.vin, v.license_plate, v.year, v.color
           FROM service_orders so
           JOIN users u ON u.id=so.user_id
           JOIN vehicles v ON v.id=so.vehicle_id
           WHERE so.id=?""", [oid], one=True)
    if not order:
        flash('Заказ не найден', 'error')
        return redirect(url_for('admin_orders'))
    items = query_db("SELECT * FROM service_items WHERE order_id=?", [oid])
    return render_template('admin/order_detail.html', order=order, items=items)

@app.route('/admin/recalls', methods=['GET', 'POST'])
@admin_required
def admin_recalls():
    if request.method == 'POST':
        execute_db(
            "INSERT INTO recalls(brand,model,title,description,issue_date,status,official_url) VALUES(?,?,?,?,?,?,?)",
            (request.form.get('brand'), request.form.get('model'),
             request.form.get('title'), request.form.get('description'),
             request.form.get('issue_date'), request.form.get('status','active'),
             request.form.get('official_url')))
        # Notify all owners of affected brand
        brand = request.form.get('brand')
        affected = query_db("SELECT DISTINCT v.user_id, v.id FROM vehicles v WHERE v.brand=?", [brand])
        for row in affected:
            execute_db("INSERT INTO notifications(user_id,vehicle_id,title,message,type) VALUES(?,?,?,?,?)",
                       (row['user_id'], row['id'],
                        f'⚠️ Новая отзывная кампания: {brand}',
                        request.form.get('title'), 'warning'))
        flash('Отзывная кампания добавлена', 'success')
        return redirect(url_for('admin_recalls'))

    recalls = query_db("SELECT * FROM recalls ORDER BY issue_date DESC")
    brands = ['Lixiang', 'Zeekr', 'Geely', 'BYD', 'Chery', 'Haval', 'AITO', 'NIO', 'XPeng', 'GAC', 'SAIC']
    return render_template('admin/recalls.html', recalls=recalls, brands=brands)

@app.route('/admin/schedule')
@admin_required
def admin_schedule():
    schedule = query_db("SELECT * FROM maintenance_schedule ORDER BY brand, interval_km")
    return render_template('admin/schedule.html', schedule=schedule)

# ─── Routes: SIM Topup ────────────────────────────────────────────────────────
@app.route('/vehicles/<int:vid>/sim/topup', methods=['POST'])
@login_required
def sim_topup(vid):
    user = current_user()
    vehicle = query_db("SELECT * FROM vehicles WHERE id=? AND user_id=?", [vid, user['id']], one=True)
    if not vehicle:
        return redirect(url_for('dashboard'))

    sim_type = request.form.get('sim_type')  # 'rf' or 'esender'
    topup_date = request.form.get('topup_date') or date.today().isoformat()
    topup_days = int(request.form.get('topup_days', 30) or 30)
    amount = request.form.get('amount') or None
    note = request.form.get('note', '').strip() or None

    from datetime import datetime as dt2, timedelta as td2
    next_due = (dt2.strptime(topup_date, '%Y-%m-%d').date() + td2(days=topup_days)).isoformat()

    if sim_type == 'rf':
        execute_db("UPDATE vehicles SET rf_sim_topup_date=?, rf_sim_topup_days=? WHERE id=?",
                   (topup_date, topup_days, vid))
        label = 'РФ SIM'
    else:
        execute_db("UPDATE vehicles SET esender_topup_date=?, esender_topup_days=? WHERE id=?",
                   (topup_date, topup_days, vid))
        label = 'eSender SIM'

    execute_db(
        "INSERT INTO sim_topup_history(vehicle_id,sim_type,amount,topup_date,next_topup,note) VALUES(?,?,?,?,?,?)",
        (vid, sim_type, amount, topup_date, next_due, note))

    flash(f'{label}: дата пополнения обновлена. Следующее: {next_due}', 'success')
    return redirect(url_for('vehicle_detail', vid=vid))

# ─── PWA Service Worker route ────────────────────────────────────────────────
@app.route('/sw.js')
def service_worker():
    """Serve service worker from root scope (required for PWA)."""
    from flask import send_from_directory
    return send_from_directory('static', 'sw.js',
                               mimetype='application/javascript')

# ─── Health check (for Render & load balancers) ──────────────────────────────
@app.route('/health')
def health():
    """Lightweight health-check — Render pings this to verify the service is up."""
    try:
        # Quick DB ping
        query_db("SELECT 1", one=True)
        db_ok = True
    except Exception:
        db_ok = False
    status = 200 if db_ok else 503
    return jsonify({
        "status": "ok" if db_ok else "error",
        "db": "ok" if db_ok else "error",
        "version": "4.0.0"
    }), status

# ─── API ──────────────────────────────────────────────────────────────────────
@app.route('/api/vin/decode')
@login_required
def api_vin_decode():
    vin = request.args.get('vin', '').strip().upper()
    result = decode_vin(vin)
    return jsonify(result)

@app.route('/api/notifications/count')
@login_required
def api_notif_count():
    cnt = query_db("SELECT COUNT(*) as c FROM notifications WHERE user_id=? AND is_read=0",
                   [session['user_id']], one=True)['c']
    return jsonify({'count': cnt})

@app.route('/api/sim/alerts')
@login_required
def api_sim_alerts():
    """Return SIM cards due within 1 day (for popup alert)."""
    uid = session['user_id']
    vehicles = query_db("SELECT * FROM vehicles WHERE user_id=?", [uid])
    alerts = []
    today = date.today()

    def check_sim(v, sim_type):
        if sim_type == 'rf':
            num = v['rf_sim_number']
            topup_str = v['rf_sim_topup_date']
            days_interval = v['rf_sim_topup_days'] or 30
            label = 'РФ SIM-карта'
            operator = v['rf_sim_operator'] or ''
        else:
            num = v['esender_number']
            topup_str = v['esender_topup_date']
            days_interval = v['esender_topup_days'] or 30
            label = 'eSender SIM'
            operator = 'eSender'

        if not num or not topup_str:
            return
        try:
            last = datetime.strptime(topup_str, '%Y-%m-%d').date()
            due = last + timedelta(days=int(days_interval))
            days_left = (due - today).days
            if days_left <= 1:
                alerts.append({
                    'vehicle_id': v['id'],
                    'vehicle': f"{v['brand']} {v['model']}",
                    'sim_type': sim_type,
                    'label': label,
                    'number': num,
                    'operator': operator,
                    'due_date': due.isoformat(),
                    'days_left': days_left,
                    'overdue': days_left < 0
                })
        except:
            pass

    for v in vehicles:
        check_sim(v, 'rf')
        check_sim(v, 'esender')

    return jsonify({'alerts': alerts})

# ─── Init DB on startup (works for both direct run and gunicorn) ──────────────
with app.app_context():
    init_db()

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
