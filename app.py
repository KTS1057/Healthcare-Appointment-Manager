import sqlite3
from flask import Flask, render_template, request, redirect, session, flash

app = Flask(__name__)
app.secret_key = "healthcare_secret_key"


# ---------------- DATABASE ---------------- #

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_database():

    conn = get_db()
    cursor = conn.cursor()

    # USERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)

    # DOCTORS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialization TEXT NOT NULL,
        experience INTEGER,
        working_hours TEXT,
        slot_duration INTEGER
    )
    """)

    # APPOINTMENTS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        appointment_date TEXT,
        appointment_time TEXT,
        status TEXT DEFAULT 'Booked',
        FOREIGN KEY(patient_id) REFERENCES users(id),
        FOREIGN KEY(doctor_id) REFERENCES doctors(id)
    )
    """)

    conn.commit()
    conn.close()


create_database()


# ---------------- CREATE ADMIN ---------------- #

@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM doctors")
    total_doctors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role='patient'")
    total_patients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointments")
    total_appointments = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        name=session["name"],
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_appointments=total_appointments
    )


# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        try:

            cursor.execute("""
            INSERT INTO users(name,email,password,role)
            VALUES(?,?,?,?)
            """,
            (
                name,
                email,
                password,
                "patient"
            ))

            conn.commit()

            flash("Registration Successful")

            return redirect("/login")

        except sqlite3.IntegrityError:

            flash("Email already exists.")

        finally:

            conn.close()

    return render_template("register.html")


# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM users
        WHERE email=? AND password=?
        """, (email, password))

        user = cursor.fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin")

            elif user["role"] == "doctor":
                return redirect("/doctor")

            else:
                return redirect("/patient")

        flash("Invalid Email or Password")

    return render_template("login.html")


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")




# ---------------- DOCTOR ---------------- #

@app.route("/doctor")
def doctor():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "doctor":
        return "Access Denied"

    return render_template(
        "doctor_dashboard.html",
        name=session["name"]
    )


# ---------------- PATIENT ---------------- #

@app.route("/patient")
def patient():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "patient":
        return "Access Denied"

    return render_template(
        "patient_dashboard.html",
        name=session["name"]
    )
    # ---------------- ADD DOCTOR ---------------- #

@app.route("/add-doctor", methods=["GET", "POST"])
def add_doctor():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    if request.method == "POST":

        name = request.form["name"]
        specialization = request.form["specialization"]
        experience = request.form["experience"]
        working_hours = request.form["working_hours"]
        slot_duration = request.form["slot_duration"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO doctors
        (
            name,
            specialization,
            experience,
            working_hours,
            slot_duration
        )
        VALUES (?,?,?,?,?)
        """,
        (
            name,
            specialization,
            experience,
            working_hours,
            slot_duration
        ))

        doctor_id = cursor.lastrowid

        doctor_email = f"doctor{doctor_id}@hospital.com"

        cursor.execute("""
        INSERT INTO users
        (
            name,
            email,
            password,
            role
        )
        VALUES (?,?,?,?)
        """,
        (
            name,
            doctor_email,
            "doctor123",
            "doctor"
        ))

        conn.commit()
        conn.close()

        flash("Doctor Added Successfully")

        return redirect("/view-doctors")

    return render_template("add_doctor.html")


# ---------------- VIEW DOCTORS ---------------- #

@app.route("/view-doctors")
def view_doctors():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM doctors
    ORDER BY id DESC
    """)

    doctors = cursor.fetchall()

    conn.close()

    return render_template(
        "view_doctors.html",
        doctors=doctors
    )


# ---------------- EDIT DOCTOR ---------------- #

@app.route("/edit-doctor/<int:id>", methods=["GET", "POST"])
def edit_doctor(id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":

        cursor.execute("""
        UPDATE doctors
        SET
            name=?,
            specialization=?,
            experience=?,
            working_hours=?,
            slot_duration=?
        WHERE id=?
        """,
        (
            request.form["name"],
            request.form["specialization"],
            request.form["experience"],
            request.form["working_hours"],
            request.form["slot_duration"],
            id
        ))

        conn.commit()
        conn.close()

        flash("Doctor Updated Successfully")

        return redirect("/view-doctors")

    cursor.execute(
        "SELECT * FROM doctors WHERE id=?",
        (id,)
    )

    doctor = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_doctor.html",
        doctor=doctor
    )


# ---------------- DELETE DOCTOR ---------------- #

@app.route("/delete-doctor/<int:id>")
def delete_doctor(id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM doctors WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Doctor Deleted Successfully")

    return redirect("/view-doctors")
# ---------------- BOOK APPOINTMENT ---------------- #

@app.route("/book-appointment", methods=["GET", "POST"])
def book_appointment():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "patient":
        return "Access Denied"

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":

        doctor_id = request.form["doctor_id"]
        appointment_date = request.form["appointment_date"]
        appointment_time = request.form["appointment_time"]

        cursor.execute("""
        INSERT INTO appointments
        (
            patient_id,
            doctor_id,
            appointment_date,
            appointment_time,
            status
        )
        VALUES (?,?,?,?,?)
        """,
        (
            session["user_id"],
            doctor_id,
            appointment_date,
            appointment_time,
            "Booked"
        ))

        conn.commit()
        conn.close()

        flash("Appointment Booked Successfully")

        return redirect("/my-appointments")

    cursor.execute("""
    SELECT *
    FROM doctors
    ORDER BY name
    """)

    doctors = cursor.fetchall()

    conn.close()

    return render_template(
        "book_appointment.html",
        doctors=doctors
    )


# ---------------- MY APPOINTMENTS ---------------- #

@app.route("/my-appointments")
def my_appointments():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "patient":
        return "Access Denied"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
SELECT
    appointments.id,
    doctors.name,
    doctors.specialization,
    appointments.appointment_date,
    appointments.appointment_time,
    appointments.status
FROM appointments
JOIN doctors
ON appointments.doctor_id = doctors.id
WHERE appointments.patient_id=?
ORDER BY appointments.appointment_date DESC
""", (session["user_id"],))

    appointments = cursor.fetchall()

    conn.close()

    return render_template(
        "my_appointments.html",
        appointments=appointments
    )


# ---------------- CANCEL APPOINTMENT ---------------- #

@app.route("/cancel-appointment/<int:id>")
def cancel_appointment(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE appointments
    SET status='Cancelled'
    WHERE id=? AND patient_id=?
    """,
    (
        id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    flash("Appointment Cancelled")

    return redirect("/my-appointments")


# ---------------- ADMIN VIEW APPOINTMENTS ---------------- #

@app.route("/view-appointments")
def view_appointments():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        appointments.id,
        users.name,
        doctors.name,
        doctors.specialization,
        appointments.appointment_date,
        appointments.appointment_time,
        appointments.status
    FROM appointments
    INNER JOIN users
        ON appointments.patient_id = users.id
    INNER JOIN doctors
        ON appointments.doctor_id = doctors.id
    ORDER BY appointments.appointment_date DESC
    """)

    appointments = cursor.fetchall()

    conn.close()

    return render_template(
        "view_appointments.html",
        appointments=appointments
    )


# ---------------- DOCTOR APPOINTMENTS ---------------- #

@app.route("/doctor-appointments")
def doctor_appointments():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "doctor":
        return "Access Denied"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        d.id
    FROM doctors d
    INNER JOIN users u
        ON d.name = u.name
    WHERE u.id=?
    """, (session["user_id"],))

    doctor = cursor.fetchone()

    if doctor:

        cursor.execute("""
        SELECT
            appointments.id,
            users.name,
            appointments.appointment_date,
            appointments.appointment_time,
            appointments.status
        FROM appointments
        INNER JOIN users
            ON appointments.patient_id = users.id
        WHERE appointments.doctor_id=?
        ORDER BY appointments.appointment_date
        """, (doctor["id"],))

        appointments = cursor.fetchall()

    else:
        appointments = []

    conn.close()

    return render_template(
        "doctor_appointments.html",
        appointments=appointments
    ) 
    # ---------------- ADMIN DASHBOARD STATS ---------------- #

@app.route("/admin-dashboard")
def admin_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM doctors")
    total_doctors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role='patient'")
    total_patients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointments")
    total_appointments = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        name=session["name"],
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_appointments=total_appointments
    )


# ---------------- PROFILE ---------------- #

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    )

    user = cursor.fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )


# ---------------- CHANGE PASSWORD ---------------- #

@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        old_password = request.form["old_password"]
        new_password = request.form["new_password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT password FROM users WHERE id=?",
            (session["user_id"],)
        )

        current = cursor.fetchone()

        if current and current[0] == old_password:

            cursor.execute(
                "UPDATE users SET password=? WHERE id=?",
                (
                    new_password,
                    session["user_id"]
                )
            )

            conn.commit()

            flash("Password Updated Successfully")

        else:

            flash("Old Password is Incorrect")

        conn.close()

        return redirect("/profile")

    return render_template("change_password.html")


# ---------------- PAGE NOT FOUND ---------------- #

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


# ---------------- INTERNAL SERVER ERROR ---------------- #

@app.errorhandler(500)
def server_error(error):
    return render_template("500.html"), 500

#-------------------------------------------------------#
@app.route("/view-patients")
def view_patients():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, email
        FROM users
        WHERE role='patient'
        ORDER BY id DESC
    """)

    patients = cursor.fetchall()

    conn.close()

    return render_template(
        "view_patients.html",
        patients=patients
    )
# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    app.run(debug=True)