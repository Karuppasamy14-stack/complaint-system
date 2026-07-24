from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/login')

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, "student")
        )
        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['user'] = user['username']
            session['role'] = user['role']

            if user['role'] == 'admin':
                return redirect('/admin')
            elif user['role'] == 'staff':
                return redirect('/staff')
            else:
                return redirect('/dashboard')

        return "Invalid Login"

    return render_template('login.html')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    conn = get_db()

    total = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'").fetchone()[0]
    progress = conn.execute("SELECT COUNT(*) FROM complaints WHERE status='In Progress'").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'").fetchone()[0]

    conn.close()

    return render_template('dashboard.html',
                           total=total,
                           pending=pending,
                           progress=progress,
                           resolved=resolved)

# ---------------- ADD COMPLAINT ----------------
@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if request.method == 'POST':
        try:
            problem = request.form.get('problem')
            user = session.get('user')

            if not problem or problem.strip() == "":
                return "⚠️ Please enter a complaint"

            if not user:
                return redirect('/login')

            conn = get_db()
            conn.execute(
                "INSERT INTO complaints (user, problem, status) VALUES (?, ?, ?)",
                (user, problem, "Pending")
            )
            conn.commit()
            conn.close()

            return redirect('/dashboard')

        except Exception as e:
            return f"Error: {str(e)}"

    return render_template('complaint.html')

# ---------------- ADMIN ----------------
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = get_db()

    if request.method == 'POST':
        complaint_id = request.form.get('id')
        staff = request.form.get('staff')

        conn.execute(
            "UPDATE complaints SET assigned_to=?, status='In Progress' WHERE id=?",
            (staff, complaint_id)
        )
        conn.commit()

    complaints = conn.execute("SELECT * FROM complaints").fetchall()
    conn.close()

    return render_template('admin.html', complaints=complaints)

# ---------------- STAFF ----------------
@app.route('/staff', methods=['GET', 'POST'])
def staff():
    conn = get_db()

    if request.method == 'POST':
        complaint_id = request.form.get('id')

        conn.execute(
            "UPDATE complaints SET status='Resolved' WHERE id=?",
            (complaint_id,)
        )
        conn.commit()

    complaints = conn.execute(
        "SELECT * FROM complaints WHERE status='In Progress'"
    ).fetchall()

    conn.close()

    return render_template('staff.html', complaints=complaints)

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)