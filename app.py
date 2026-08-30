from flask import Flask, render_template, request, redirect,session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123" 

# 🔹 Database create
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        problem TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

#Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["user"] = username   # 🔥 important
            return redirect("/admin")
        else:
            return "Invalid login ❌"

    return render_template("login.html")

# 🔹 Home (Form + Save data)
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form["name"]
        problem = request.form["problem"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO complaints (name, problem) VALUES (?, ?)", (name, problem))
        conn.commit()
        conn.close()

        return render_template("success.html")

    return render_template("index.html")

# 🔹 Admin page (show all complaints)
@app.route("/admin")
def admin():
    if "user" not in session:   # 🔥 ADD THIS LINE
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints")
    data = cursor.fetchall()
    conn.close()

    return render_template("admin.html", data=data)

# Delete
@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM complaints WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return render_template("delete.html")

#Logout
@app.route("/logout")
def logout():
    session.pop("user", None)   # 🔥 session clear
    return redirect("/login")   # login page ku redirect

# 🔹 Run app
if __name__ == "__main__":
    app.run(host="10.243.127.20", port=5000,)