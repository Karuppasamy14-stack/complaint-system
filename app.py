from flask import Flask, render_template, request, redirect, session, flash
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT,
        role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS complaints(
        id INTEGER PRIMARY KEY,
        user TEXT,
        issue TEXT,
        status TEXT,
        staff TEXT,
        image TEXT,
        notify TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (u,))
        data = cur.fetchone()
        conn.close()

        if data and check_password_hash(data[2], p):
            session["user"] = u
            session["role"] = data[3]

            if data[3] == "admin":
                return redirect("/admin")
            elif data[3] == "staff":
                return redirect("/staff")
            else:
                return redirect("/dashboard")
        else:
            flash("Invalid login")

    return render_template("login.html")

# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = generate_password_hash(request.form["password"])
        r = request.form["role"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO users VALUES(NULL,?,?,?)",(u,p,r))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # counts
    cur.execute("SELECT COUNT(*) FROM complaints")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'")
    pending = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE status='In Progress'")
    progress = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'")
    resolved = cur.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        pending=pending,
        progress=progress,
        resolved=resolved
    )

# ---------- COMPLAINT ----------
@app.route("/complaint", methods=["GET","POST"])
def complaint():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        issue = request.form["issue"]
        file = request.files.get("image")

        filename = ""
        if file and file.filename:
            filename = file.filename
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO complaints VALUES(NULL,?,?,?,?,?,?)
        """, (session["user"], issue, "Pending", "", filename, "New Complaint"))

        conn.commit()
        conn.close()

        flash("Complaint submitted!")
        return redirect("/dashboard")

    return render_template("complaint.html")

# ---------- ADMIN ----------
@app.route("/admin", methods=["GET","POST"])
def admin():

    if "role" not in session or session["role"] != "admin":
        return "Access Denied"

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if request.method == "POST":
        cid = request.form["id"]
        staff = request.form["staff"]

        cur.execute("""
        UPDATE complaints 
        SET staff=?, status='In Progress', notify='Assigned to staff'
        WHERE id=?
        """, (staff, cid))

        conn.commit()

    cur.execute("SELECT * FROM complaints")
    data = cur.fetchall()
    conn.close()

    return render_template("admin.html", data=data)

# ---------- STAFF ----------
@app.route("/staff", methods=["GET","POST"])
def staff():

    if "role" not in session or session["role"] != "staff":
        return "Access Denied"

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if request.method == "POST":
        cid = request.form["id"]

        cur.execute("""
        UPDATE complaints 
        SET status='Resolved', notify='Resolved by staff'
        WHERE id=?
        """, (cid,))

        conn.commit()

    cur.execute("SELECT * FROM complaints")
    data = cur.fetchall()
    conn.close()

    return render_template("staff.html", data=data)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)