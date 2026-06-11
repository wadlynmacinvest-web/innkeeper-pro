"""
InnKeeper Pro — Flask Backend
Full hotel management API with PostgreSQL database
"""

from flask import Flask, jsonify, request, send_from_directory, g
import os, json, datetime, uuid, hashlib
import psycopg2
from psycopg2.extras import RealDictCursor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# PostgreSQL connection string (set this in Vercel/environment)
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()

print("DATABASE_URL =", repr(DATABASE_URL))
STATIC   = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, static_folder=STATIC, static_url_path='')

# ─── DB helpers ────────────────────────────────────────────────────────────────

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL environment variable is not set")
        db = g._database = psycopg2.connect(
    DATABASE_URL,
    sslmode="require"
)
    return db

@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, '_database', None)
    if db: db.close()

def query(sql, args=(), one=False):
    conn = get_db()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, args)
        rv = cur.fetchall()
        # Convert RealDictCursor objects to plain dicts for JSON serialization
        results = [dict(r) for r in rv]
        return (results[0] if results else None) if one else results

def execute(sql, args=()):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(sql, args)
        conn.commit()
        return None

def ref_id():
    return 'SPL-' + datetime.date.today().strftime('%Y') + '-' + str(uuid.uuid4())[:4].upper()

# ─── SCHEMA ────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS guests (
    id          VARCHAR(50) PRIMARY KEY,
    first_name  VARCHAR(100) NOT NULL,
    last_name   VARCHAR(100) NOT NULL,
    phone       VARCHAR(20),
    email       VARCHAR(100),
    dob         VARCHAR(20),
    anniversary VARCHAR(20),
    id_number   VARCHAR(50),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rooms (
    id          SERIAL PRIMARY KEY,
    number      VARCHAR(20) UNIQUE NOT NULL,
    type        VARCHAR(50) NOT NULL,
    rate        DECIMAL(10,2) NOT NULL,
    max_guests  INTEGER DEFAULT 2,
    breakfast   INTEGER DEFAULT 0,
    status      VARCHAR(20) DEFAULT 'vacant',
    notes       TEXT
);

CREATE TABLE IF NOT EXISTS bookings (
    id          VARCHAR(50) PRIMARY KEY,
    guest_id    VARCHAR(50) REFERENCES guests(id),
    room_id     INTEGER REFERENCES rooms(id),
    checkin     VARCHAR(20) NOT NULL,
    checkout    VARCHAR(20) NOT NULL,
    nights      INTEGER,
    guests_count INTEGER DEFAULT 1,
    room_rate   DECIMAL(10,2),
    subtotal    DECIMAL(10,2),
    service_fee DECIMAL(10,2),
    total       DECIMAL(10,2),
    deposit     DECIMAL(10,2) DEFAULT 0,
    balance     DECIMAL(10,2),
    pay_method  VARCHAR(50) DEFAULT 'cash',
    pay_status  VARCHAR(20) DEFAULT 'unpaid',
    status      VARCHAR(20) DEFAULT 'pending',
    source      VARCHAR(20) DEFAULT 'walkin',
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
    id          VARCHAR(50) PRIMARY KEY,
    booking_id  VARCHAR(50) REFERENCES bookings(id),
    amount      DECIMAL(10,2) NOT NULL,
    method      VARCHAR(50),
    reference   VARCHAR(100),
    paid_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes       TEXT
);

CREATE TABLE IF NOT EXISTS receipts (
    id          VARCHAR(50) PRIMARY KEY,
    booking_id  VARCHAR(50) REFERENCES bookings(id),
    type        VARCHAR(20) DEFAULT 'full',
    amount      DECIMAL(10,2),
    issued_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    emailed     INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS celeb_log (
    id          SERIAL PRIMARY KEY,
    guest_id    VARCHAR(50) REFERENCES guests(id),
    type        VARCHAR(20),
    channel     VARCHAR(20),
    sent_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status      VARCHAR(20) DEFAULT 'sent'
);

CREATE TABLE IF NOT EXISTS settings (
    key         VARCHAR(50) PRIMARY KEY,
    value       TEXT
);
"""

def init_db():
    with app.app_context():
        db = get_db()
        with db.cursor() as cur:
            for stmt in SCHEMA.strip().split(';'):
                s = stmt.strip()
                if s:
                    cur.execute(s)
        db.commit()
        _seed()

def _seed():
    """Insert demo data if tables are empty."""
    if query("SELECT 1 FROM rooms LIMIT 1"):
        return  # already seeded

    rooms = [
        ('01','Standard',7500,2,0),('02','Standard',7500,2,0),
        ('03','Standard',7500,2,0),('04','Standard',7500,2,0),
        ('05','Deluxe',12000,2,1),('06','Standard',7500,2,0),
        ('07','Standard',7500,2,0),('08','Deluxe',12000,2,1),
        ('09','Deluxe',12000,2,1),('10','Standard',7500,2,0),
        ('11','Standard',7500,2,0),('12','Standard',7500,2,0),
        ('13','Standard',7500,2,0),('14','Standard',7500,2,0),
        ('15','Suite',18000,4,1),('16','Standard',7500,2,0),
        ('17','Standard',7500,2,0),('18','Standard',7500,2,0),
        ('19','Deluxe',12000,2,1),('20','Suite',18000,4,1),
        ('21','Deluxe',12000,2,1),('22','Standard',7500,2,0),
        ('23','Standard',7500,2,0),('24','Standard',7500,2,0),
        ('25','Deluxe',12000,2,1),('26','Standard',7500,2,0),
        ('27','Standard',7500,2,0),('28','Standard',7500,2,0),
        ('29','Deluxe',12000,2,1),('30','Standard',7500,2,0),
    ]
    # Demo guests
    guests = [
        ('g001','Kwame','Asante','+234 80 567 8901','kwame@email.com','1985-06-15','','NGA-12345'),
        ('g002','Amara','Diallo','+225 07 654 3210','diallo@email.com','','2019-05-29','GHA-67890'),
        ('g003','Amara','Osei','+233 20 987 6543','amara@email.com','1990-05-30','','GHA-11111'),
        ('g004','Nkechi','Eze','+234 81 234 5678','nkechi@email.com','1992-08-12','','NGA-22222'),
        ('g005','Fatima','Balde','+224 62 987 6543','fatima@email.com','','2021-12-03','GUI-33333'),
    ]

    today_dt = datetime.date.today()
    d = lambda days: (today_dt + datetime.timedelta(days=days)).isoformat()

    # Demo bookings
    bookings = [
        ('SPL-2026-0087','g001',14,d(-1),d(3),4,2,7500,30000,1500,31500,7500,24000,'card','paid','checkedin','online',''),
        ('SPL-2026-0086','g002',8,d(-3),d(1),4,2,12000,48000,2400,50400,20000,30400,'bank','partial','checkedin','online','Anniversary trip'),
        ('SPL-2026-0085','g003',12,d(-2),d(0),2,1,7500,15000,750,15750,0,15750,'cash','unpaid','checkedin','walkin','Birthday today!'),
        ('SPL-2026-0084','g004',3,d(0),d(3),4,1,7500,30000,1500,31500,0,31500,'online','unpaid','pending','online',''),
        ('SPL-2026-0083','g005',17,d(0),d(2),2,2,7500,15000,750,15750,15750,0,'momo','paid','confirmed','online',''),
    ]

    db = get_db()
    with db.cursor() as cur:
        cur.executemany("INSERT INTO rooms(number,type,rate,max_guests,breakfast) VALUES(%s,%s,%s,%s,%s)", rooms)
        cur.executemany("INSERT INTO guests(id,first_name,last_name,phone,email,dob,anniversary,id_number) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)", guests)
        
        for b in bookings:
            cur.execute("""INSERT INTO bookings(id,guest_id,room_id,checkin,checkout,nights,guests_count,
                          room_rate,subtotal,service_fee,total,deposit,balance,pay_method,pay_status,status,source,notes)
                          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", b)
            # update room status
            status_map = {'checkedin':'occupied','pending':'reserved','confirmed':'reserved'}
            cur.execute("UPDATE rooms SET status=%s WHERE id=%s", (status_map.get(b[15],'vacant'), b[2]))

        # Some rooms to maintenance
        cur.execute("UPDATE rooms SET status='maintenance' WHERE number IN ('09','29')")

        # Settings defaults
        settings = [
            ('hotel_name','Sunrise Palms Inn'),
            ('hotel_address','12 Marina Road, Lagos, Nigeria'),
            ('hotel_phone','+234 80 000 0000'),
            ('hotel_email','info@sunrisepalms.com'),
            ('checkin_time','14:00'),
            ('checkout_time','12:00'),
            ('currency','NGN'),
            ('service_charge','5'),
            ('vat','7.5'),
            ('deposit_pct','30'),
            ('auto_birthday','1'),
            ('auto_anniversary','1'),
            ('whatsapp_enabled','1'),
            ('email_enabled','1'),
            ('sms_enabled','0'),
        ]
        cur.executemany("INSERT INTO settings(key,value) VALUES(%s,%s) ON CONFLICT (key) DO NOTHING", settings)
    db.commit()
    print("✅ Database seeded with demo data.")

# ─── CORS & JSON helpers ────────────────────────────────────────────────────────

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return err(str(e), 500)

@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin']  = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,PATCH,DELETE,OPTIONS'
    return resp

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """Serve the frontend SPA for any non-API route."""
    if path.startswith('api/'):
        return jsonify(error='Not found'), 404
    fp = os.path.join(STATIC, path)
    if path and os.path.exists(fp):
        return send_from_directory(STATIC, path)
    return send_from_directory(STATIC, 'index.html')

def ok(data=None, **kw):
    payload = {'ok': True}
    if data is not None: payload['data'] = data
    payload.update(kw)
    return jsonify(payload)

def err(msg, code=400):
    return jsonify({'ok': False, 'error': msg}), code

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/dashboard')
def dashboard():
    today = datetime.date.today().isoformat()
    stats = {
        'occupied_rooms':  query("SELECT COUNT(*) c FROM rooms WHERE status='occupied'",          one=True)['c'],
        'total_rooms':     query("SELECT COUNT(*) c FROM rooms",                                  one=True)['c'],
        'guests_inhouse':  query("SELECT COUNT(*) c FROM bookings WHERE status='checkedin'",      one=True)['c'],
        'arrivals_today':  query("SELECT COUNT(*) c FROM bookings WHERE checkin=%s AND status IN ('pending','confirmed')", (today,), one=True)['c'],
        'departures_today':query("SELECT COUNT(*) c FROM bookings WHERE checkout=%s AND status='checkedin'", (today,), one=True)['c'],
        'revenue_today':   query("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE paid_at::date=%s", (today,), one=True)['s'],
        'revenue_month':   query("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE to_char(paid_at, 'YYYY-MM')=to_char(CURRENT_DATE, 'YYYY-MM')", one=True)['s'],
        'pending_bookings':query("SELECT COUNT(*) c FROM bookings WHERE status='pending'",         one=True)['c'],
    }
    occ_rate = round(stats['occupied_rooms']/max(stats['total_rooms'],1)*100)
    stats['occupancy_rate'] = occ_rate

    today_bdays = query("""
        SELECT g.first_name||' '||g.last_name name, g.id, b.id booking_id,
               r.number room
        FROM guests g
        JOIN bookings b ON b.guest_id=g.id AND b.status='checkedin'
        JOIN rooms r ON r.id=b.room_id
        WHERE to_char(NULLIF(g.dob, '')::date, 'MM-DD')=to_char(CURRENT_DATE, 'MM-DD')
          AND g.dob != '' AND g.dob IS NOT NULL
    """)
    today_annivs = query("""
        SELECT g.first_name||' '||g.last_name name, g.id, b.id booking_id,
               r.number room
        FROM guests g
        JOIN bookings b ON b.guest_id=g.id AND b.status='checkedin'
        JOIN rooms r ON r.id=b.room_id
        WHERE to_char(NULLIF(g.anniversary, '')::date, 'MM-DD')=to_char(CURRENT_DATE, 'MM-DD')
          AND g.anniversary != '' AND g.anniversary IS NOT NULL
    """)

    recent = query("""
        SELECT b.id, b.status, b.checkin, b.checkout, b.total,
               g.first_name||' '||g.last_name guest_name, r.number room_number, r.type room_type
        FROM bookings b
        JOIN guests g ON g.id=b.guest_id
        JOIN rooms r ON r.id=b.room_id
        ORDER BY b.created_at DESC LIMIT 10
    """)

    return ok({
        'stats': stats,
        'today_birthdays': today_bdays,
        'today_anniversaries': today_annivs,
        'recent_bookings': recent
    })

# ═══════════════════════════════════════════════════════════════════════════════
# GUESTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/guests', methods=['GET','POST'])
def guests():
    if request.method == 'GET':
        search = request.args.get('q','')
        if search:
            g = query("SELECT * FROM guests WHERE first_name LIKE %s OR last_name LIKE %s OR email LIKE %s OR phone LIKE %s ORDER BY last_name",
                      (f'%{search}%',)*4)
        else:
            g = query("SELECT * FROM guests ORDER BY last_name")
        return ok(g)

    d = request.json or {}
    gid = 'g' + str(uuid.uuid4())[:8]
    execute("""INSERT INTO guests(id,first_name,last_name,phone,email,dob,anniversary,id_number)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
            (gid, d.get('first_name',''), d.get('last_name',''),
             d.get('phone',''), d.get('email',''), d.get('dob',''),
             d.get('anniversary',''), d.get('id_number','')))
    return ok(query("SELECT * FROM guests WHERE id=%s", (gid,), one=True), code=201)

@app.route('/api/guests/<gid>', methods=['GET','PUT','DELETE'])
def guest_detail(gid):
    g = query("SELECT * FROM guests WHERE id=%s", (gid,), one=True)
    if not g: return err('Guest not found', 404)

    if request.method == 'GET':
        bks = query("""SELECT b.*,r.number room_number,r.type room_type
                       FROM bookings b JOIN rooms r ON r.id=b.room_id
                       WHERE b.guest_id=%s ORDER BY b.checkin DESC""", (gid,))
        return ok({**g, 'bookings': bks})

    if request.method == 'PUT':
        d = request.json or {}
        execute("""UPDATE guests SET first_name=%s,last_name=%s,phone=%s,email=%s,
                   dob=%s,anniversary=%s,id_number=%s WHERE id=%s""",
                (d.get('first_name',g['first_name']), d.get('last_name',g['last_name']),
                 d.get('phone',g['phone']), d.get('email',g['email']),
                 d.get('dob',g['dob']), d.get('anniversary',g['anniversary']),
                 d.get('id_number',g['id_number']), gid))
        return ok(query("SELECT * FROM guests WHERE id=%s", (gid,), one=True))

    execute("DELETE FROM guests WHERE id=%s", (gid,))
    return ok({'deleted': gid})

# ═══════════════════════════════════════════════════════════════════════════════
# ROOMS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/rooms', methods=['GET'])
def rooms():
    status  = request.args.get('status')
    rtype   = request.args.get('type')
    checkin = request.args.get('checkin')
    checkout= request.args.get('checkout')

    sql  = "SELECT * FROM rooms"
    args = []
    conds= []
    if status: conds.append("status=%s"); args.append(status)
    if rtype:  conds.append("type=%s");   args.append(rtype)
    if checkin and checkout:
        # available = vacant AND not booked for those dates
        conds.append("""id NOT IN (
            SELECT room_id FROM bookings
            WHERE status NOT IN ('cancelled','completed')
              AND checkin < %s AND checkout > %s
        )""")
        args += [checkout, checkin]
        conds.append("status != 'maintenance'")
    if conds: sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY CAST(number AS INTEGER)"
    return ok(query(sql, args))

@app.route('/api/rooms/<int:rid>', methods=['GET','PATCH'])
def room_detail(rid):
    r = query("SELECT * FROM rooms WHERE id=%s", (rid,), one=True)
    if not r: return err('Room not found', 404)

    if request.method == 'GET':
        current = query("""SELECT b.*,g.first_name||' '||g.last_name guest_name,g.email,g.phone
                           FROM bookings b JOIN guests g ON g.id=b.guest_id
                           WHERE b.room_id=%s AND b.status='checkedin' LIMIT 1""", (rid,), one=True)
        return ok({**r, 'current_booking': current})

    d = request.json or {}
    execute("UPDATE rooms SET status=%s,notes=%s WHERE id=%s",
            (d.get('status', r['status']), d.get('notes', r['notes']), rid))
    return ok(query("SELECT * FROM rooms WHERE id=%s", (rid,), one=True))

# ═══════════════════════════════════════════════════════════════════════════════
# BOOKINGS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/bookings', methods=['GET','POST'])
def bookings():
    if request.method == 'GET':
        status = request.args.get('status')
        search = request.args.get('q','')
        sql = """SELECT b.*,
                        g.first_name||' '||g.last_name guest_name,g.email,g.phone,
                        r.number room_number, r.type room_type
                 FROM bookings b
                 JOIN guests g ON g.id=b.guest_id
                 JOIN rooms r ON r.id=b.room_id"""
        args = []
        conds = []
        if status: conds.append("b.status=%s"); args.append(status)
        if search:
            conds.append("(g.first_name||' '||g.last_name LIKE %s OR g.email LIKE %s OR b.id LIKE %s)")
            args += [f'%{search}%']*3
        if conds: sql += " WHERE " + " AND ".join(conds)
        sql += " ORDER BY b.created_at DESC"
        return ok(query(sql, args))

    d = request.json or {}

    # Validate required fields
    for f in ('guest_id','room_id','checkin','checkout'):
        if not d.get(f): return err(f'{f} is required')

    room = query("SELECT * FROM rooms WHERE id=%s", (d['room_id'],), one=True)
    if not room: return err('Room not found')
    if room['status'] == 'occupied': return err('Room is already occupied')

    try:
        ci = datetime.date.fromisoformat(d['checkin'])
        co = datetime.date.fromisoformat(d['checkout'])
    except: return err('Invalid date format (YYYY-MM-DD required)')
    if co <= ci: return err('Check-out must be after check-in')

    nights   = (co-ci).days
    rate     = d.get('room_rate', room['rate'])
    subtotal = rate * nights
    svc_pct  = float(query("SELECT value FROM settings WHERE key='service_charge'", one=True)['value'] or 5)
    svc_fee  = round(subtotal * svc_pct / 100, 2)
    total    = subtotal + svc_fee
    deposit  = float(d.get('deposit', 0))
    balance  = total - deposit

    bid = 'SPL-' + datetime.date.today().strftime('%Y') + '-' + str(uuid.uuid4())[:4].upper()

    execute("""INSERT INTO bookings(id,guest_id,room_id,checkin,checkout,nights,guests_count,
               room_rate,subtotal,service_fee,total,deposit,balance,pay_method,pay_status,status,source,notes)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (bid, d['guest_id'], d['room_id'], d['checkin'], d['checkout'],
             nights, d.get('guests_count',1), rate, subtotal, svc_fee, total,
             deposit, balance,
             d.get('pay_method','cash'),
             'paid' if balance<=0 else ('partial' if deposit>0 else 'unpaid'),
             d.get('status','confirmed'), d.get('source','walkin'), d.get('notes','')))

    if d.get('status') in ('confirmed','checkedin'):
        new_status = 'occupied' if d.get('status')=='checkedin' else 'reserved'
        execute("UPDATE rooms SET status=%s WHERE id=%s", (new_status, d['room_id']))

    return ok(query("""SELECT b.*,g.first_name||' '||g.last_name guest_name,
                              r.number room_number,r.type room_type
                       FROM bookings b JOIN guests g ON g.id=b.guest_id
                       JOIN rooms r ON r.id=b.room_id WHERE b.id=%s""", (bid,), one=True))

@app.route('/api/bookings/<bid>', methods=['GET','PATCH'])
def booking_detail(bid):
    b = query("""SELECT b.*,g.first_name||' '||g.last_name guest_name,g.email,g.phone,
                        g.dob,g.anniversary,r.number room_number,r.type room_type
                 FROM bookings b JOIN guests g ON g.id=b.guest_id
                 JOIN rooms r ON r.id=b.room_id WHERE b.id=%s""", (bid,), one=True)
    if not b: return err('Booking not found', 404)

    if request.method == 'GET':
        pmts = query("SELECT * FROM payments WHERE booking_id=%s ORDER BY paid_at DESC", (bid,))
        recs = query("SELECT * FROM receipts WHERE booking_id=%s ORDER BY issued_at DESC", (bid,))
        return ok({**b, 'payments': pmts, 'receipts': recs})

    d = request.json or {}
    old_status = b['status']
    new_status = d.get('status', old_status)

    execute("""UPDATE bookings SET status=%s,pay_status=%s,balance=%s,notes=%s,pay_method=%s
               WHERE id=%s""",
            (new_status, d.get('pay_status', b['pay_status']),
             d.get('balance', b['balance']), d.get('notes', b['notes']),
             d.get('pay_method', b['pay_method']), bid))

    # Sync room status
    if new_status != old_status:
        room_st = {'checkedin':'occupied','confirmed':'reserved',
                   'pending':'reserved','completed':'vacant','cancelled':'vacant'}.get(new_status)
        if room_st:
            execute("UPDATE rooms SET status=%s WHERE id=%s", (room_st, b['room_id']))

    return ok(query("""SELECT b.*,g.first_name||' '||g.last_name guest_name,
                              r.number room_number,r.type room_type
                       FROM bookings b JOIN guests g ON g.id=b.guest_id
                       JOIN rooms r ON r.id=b.room_id WHERE b.id=%s""", (bid,), one=True))

# ─── Check-in / Check-out shortcuts ─────────────────────────────────────────

@app.route('/api/bookings/<bid>/checkin', methods=['POST'])
def do_checkin(bid):
    b = query("SELECT * FROM bookings WHERE id=%s", (bid,), one=True)
    if not b: return err('Booking not found', 404)
    if b['status'] not in ('pending','confirmed'): return err(f"Cannot check in a booking with status '{b['status']}'")
    execute("UPDATE bookings SET status='checkedin' WHERE id=%s", (bid,))
    execute("UPDATE rooms SET status='occupied' WHERE id=%s", (b['room_id'],))
    return ok({'message': 'Checked in successfully', 'booking_id': bid})

@app.route('/api/bookings/<bid>/checkout', methods=['POST'])
def do_checkout(bid):
    b = query("SELECT * FROM bookings WHERE id=%s", (bid,), one=True)
    if not b: return err('Booking not found', 404)
    if b['status'] != 'checkedin': return err("Guest is not currently checked in")
    d = request.json or {}
    # Record final payment if provided
    if d.get('payment_amount'):
        pid = 'PAY-' + str(uuid.uuid4())[:8].upper()
        execute("INSERT INTO payments(id,booking_id,amount,method,reference) VALUES(%s,%s,%s,%s,%s)",
                (pid, bid, d['payment_amount'], d.get('method','cash'), d.get('reference','')))
        new_balance = max(0, b['balance'] - float(d['payment_amount']))
        new_pay_status = 'paid' if new_balance <= 0 else 'partial'
        execute("UPDATE bookings SET balance=%s,pay_status=%s WHERE id=%s", (new_balance, new_pay_status, bid))

    execute("UPDATE bookings SET status='completed' WHERE id=%s", (bid,))
    execute("UPDATE rooms SET status='vacant' WHERE id=%s", (b['room_id'],))

    # Auto-generate receipt
    rid = 'REC-' + str(uuid.uuid4())[:8].upper()
    execute("INSERT INTO receipts(id,booking_id,type,amount) VALUES(%s,%s,%s,%s)",
            (rid, bid, 'full', b['total']))
    return ok({'message': 'Checked out successfully', 'receipt_id': rid})

# ═══════════════════════════════════════════════════════════════════════════════
# PAYMENTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/payments', methods=['GET','POST'])
def payments():
    if request.method == 'GET':
        return ok(query("""SELECT p.*,b.id booking_ref,
                                  g.first_name||' '||g.last_name guest_name
                           FROM payments p
                           JOIN bookings b ON b.id=p.booking_id
                           JOIN guests g ON g.id=b.guest_id
                           ORDER BY p.paid_at DESC LIMIT 100"""))

    d = request.json or {}
    if not d.get('booking_id'): return err('booking_id required')
    if not d.get('amount'):     return err('amount required')

    b = query("SELECT * FROM bookings WHERE id=%s", (d['booking_id'],), one=True)
    if not b: return err('Booking not found', 404)

    pid = 'PAY-' + str(uuid.uuid4())[:8].upper()
    execute("INSERT INTO payments(id,booking_id,amount,method,reference,notes) VALUES(%s,%s,%s,%s,%s,%s)",
            (pid, d['booking_id'], float(d['amount']), d.get('method','cash'),
             d.get('reference',''), d.get('notes','')))

    new_balance = max(0, float(b['balance']) - float(d['amount']))
    pay_status  = 'paid' if new_balance <= 0 else 'partial'
    execute("UPDATE bookings SET balance=%s,pay_status=%s WHERE id=%s",
            (new_balance, pay_status, d['booking_id']))

    return ok({'payment_id': pid, 'new_balance': new_balance, 'pay_status': pay_status})

# ═══════════════════════════════════════════════════════════════════════════════
# RECEIPTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/receipts', methods=['GET','POST'])
def receipts():
    if request.method == 'GET':
        return ok(query("""SELECT r.*,b.checkin,b.checkout,b.total booking_total,
                                  g.first_name||' '||g.last_name guest_name,g.email,
                                  rm.number room_number,rm.type room_type
                           FROM receipts r
                           JOIN bookings b ON b.id=r.booking_id
                           JOIN guests g ON g.id=b.guest_id
                           JOIN rooms rm ON rm.id=b.room_id
                           ORDER BY r.issued_at DESC LIMIT 50"""))

    d = request.json or {}
    if not d.get('booking_id'): return err('booking_id required')
    b = query("SELECT * FROM bookings WHERE id=%s", (d['booking_id'],), one=True)
    if not b: return err('Booking not found', 404)

    rid = 'REC-' + str(uuid.uuid4())[:8].upper()
    execute("INSERT INTO receipts(id,booking_id,type,amount) VALUES(%s,%s,%s,%s)",
            (rid, d['booking_id'], d.get('type','full'), b['total']))
    return ok({'receipt_id': rid})

@app.route('/api/receipts/<rid>', methods=['GET'])
def receipt_detail(rid):
    r = query("""SELECT r.*,
                        b.checkin,b.checkout,b.nights,b.room_rate,b.subtotal,
                        b.service_fee,b.total,b.deposit,b.balance,b.pay_method,b.pay_status,
                        g.first_name||' '||g.last_name guest_name,g.email,g.phone,
                        rm.number room_number,rm.type room_type,
                        s.value hotel_name
                 FROM receipts r
                 JOIN bookings b ON b.id=r.booking_id
                 JOIN guests g ON g.id=b.guest_id
                 JOIN rooms rm ON rm.id=b.room_id
                 LEFT JOIN settings s ON s.key='hotel_name'
                 WHERE r.id=%s""", (rid,), one=True)
    if not r: return err('Receipt not found', 404)
    return ok(r)

# ═══════════════════════════════════════════════════════════════════════════════
# CELEBRATIONS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/celebrations')
def celebrations():
    days_ahead = int(request.args.get('days', 30))
    bdays = query("""
        SELECT g.id, g.first_name||' '||g.last_name name, g.email, g.phone, g.dob,
               to_char(NULLIF(g.dob, '')::date, 'MM-DD') md,
               b.id booking_id, r.number room_number, b.status booking_status
        FROM guests g
        LEFT JOIN bookings b ON b.guest_id=g.id AND b.status='checkedin'
        LEFT JOIN rooms r ON r.id=b.room_id
        WHERE g.dob != '' AND g.dob IS NOT NULL
        ORDER BY to_char(NULLIF(g.dob, '')::date, 'MM-DD')
    """)

    annivs = query("""
        SELECT g.id, g.first_name||' '||g.last_name name, g.email, g.phone, g.anniversary,
               to_char(NULLIF(g.anniversary, '')::date, 'MM-DD') md,
               b.id booking_id, r.number room_number, b.status booking_status
        FROM guests g
        LEFT JOIN bookings b ON b.guest_id=g.id AND b.status='checkedin'
        LEFT JOIN rooms r ON r.id=b.room_id
        WHERE g.anniversary != '' AND g.anniversary IS NOT NULL
        ORDER BY to_char(NULLIF(g.anniversary, '')::date, 'MM-DD')
    """)

    today_md = datetime.date.today().strftime('%m-%d')
    for item in bdays + annivs:
        md = item.get('md','')
        if md == today_md:
            item['when'] = 'today'
        else:
            # days until next occurrence
            try:
                m, d2 = int(md[:2]), int(md[3:])
                today = datetime.date.today()
                next_occ = datetime.date(today.year, m, d2)
                if next_occ < today:
                    next_occ = datetime.date(today.year+1, m, d2)
                item['when'] = f"in {(next_occ-today).days} days"
                item['days_away'] = (next_occ-today).days
            except:
                item['when'] = 'unknown'

    log = query("""SELECT cl.*,g.first_name||' '||g.last_name guest_name
                   FROM celeb_log cl JOIN guests g ON g.id=cl.guest_id
                   ORDER BY cl.sent_at DESC LIMIT 20""")

    return ok({'birthdays': bdays, 'anniversaries': annivs, 'log': log})

@app.route('/api/celebrations/send', methods=['POST'])
def send_celeb():
    d = request.json or {}
    if not d.get('guest_id'): return err('guest_id required')
    g = query("SELECT * FROM guests WHERE id=%s", (d['guest_id'],), one=True)
    if not g: return err('Guest not found', 404)

    execute("INSERT INTO celeb_log(guest_id,type,channel,status) VALUES(%s,%s,%s,%s)",
            (d['guest_id'], d.get('type','birthday'), d.get('channel','whatsapp'), 'sent'))
    return ok({'message': f"Wish sent to {g['first_name']} {g['last_name']}"})

# ═══════════════════════════════════════════════════════════════════════════════
# REPORTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/reports/summary')
def report_summary():
    months = []
    for i in range(5, -1, -1):
        dt  = datetime.date.today().replace(day=1) - datetime.timedelta(days=i*28)
        ym  = dt.strftime('%Y-%m')
        lbl = dt.strftime('%b')
        rev = query("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE to_char(paid_at, 'YYYY-MM')=%s", (ym,), one=True)['s']
        bks = query("SELECT COUNT(*) c FROM bookings WHERE to_char(created_at, 'YYYY-MM')=%s", (ym,), one=True)['c']
        months.append({'month': lbl, 'ym': ym, 'revenue': rev, 'bookings': bks})

    by_type = query("""SELECT r.type, COUNT(*) bookings, COALESCE(SUM(b.total),0) revenue
                       FROM bookings b JOIN rooms r ON r.id=b.room_id
                       WHERE b.status NOT IN ('cancelled')
                       GROUP BY r.type""")

    by_channel = query("""SELECT source, COUNT(*) bookings, COALESCE(SUM(total),0) revenue
                          FROM bookings WHERE status NOT IN ('cancelled')
                          GROUP BY source""")

    top_guests = query("""SELECT g.id, g.first_name||' '||g.last_name name, g.email,
                                 COUNT(*) stays, SUM(b.nights) nights, SUM(b.total) revenue,
                                 MAX(b.checkin) last_visit
                          FROM bookings b JOIN guests g ON g.id=b.guest_id
                          WHERE b.status NOT IN ('cancelled')
                          GROUP BY g.id ORDER BY revenue DESC LIMIT 10""")

    occ_days = []
    for i in range(29, -1, -1):
        dt  = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
        occ = query("""SELECT COUNT(*) c FROM bookings
                       WHERE checkin<=%s AND checkout>%s AND status NOT IN ('cancelled')""",
                    (dt, dt), one=True)['c']
        total_rooms = query("SELECT COUNT(*) c FROM rooms", one=True)['c']
        occ_days.append({'date': dt, 'occupied': occ, 'rate': round(occ/max(total_rooms,1)*100)})

    return ok({
        'monthly': months,
        'by_room_type': by_type,
        'by_channel': by_channel,
        'top_guests': top_guests,
        'occupancy_30d': occ_days
    })

# ═══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/settings', methods=['GET','POST'])
def settings_api():
    if request.method == 'GET':
        rows = query("SELECT key,value FROM settings")
        return ok({r['key']: r['value'] for r in rows})

    d = request.json or {}
    db = get_db()
    with db.cursor() as cur:
        for k, v in d.items():
            cur.execute("INSERT INTO settings(key,value) VALUES(%s,%s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value", (k, str(v)))
    db.commit()
    return ok({'updated': len(d)})

# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/health')
def health():
    return ok({'status': 'ok', 'version': '1.0.0',
               'time': datetime.datetime.now().isoformat()})

# ─── RUN ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    os.makedirs(STATIC, exist_ok=True)
    print("\n🏨 InnKeeper Pro — Starting up…")
    init_db()
    print("🌐 Server running at http://0.0.0.0:8080")
    print("📡 API available at  http://0.0.0.0:8080/api/")
    db_info = DATABASE_URL.split('@')[-1] if DATABASE_URL else "NOT SET"
    print(f"🗄️  Database at       {db_info}")
    print("⌨️  Press Ctrl+C to stop\n")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
