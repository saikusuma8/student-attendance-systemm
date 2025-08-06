from flask import Flask, render_template, request, redirect, flash
import sqlite3
import secrets
import string
from werkzeug.security import generate_password_hash
from flask import session

app = Flask(__name__,template_folder='templates' ,static_folder='static')
app.secret_key = 'your_secret_key'
@app.route('/')
def home():
    return render_template('home.html')



# Create  teacher table
def init_db():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            subject TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

#create student table
def init_db():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll TEXT NOT NULL UNIQUE,
    section TEXT NOT NULL,
    department TEXT NOT NULL,
    year TEXT NOT NULL
)''')

#create attendance table
def init_db():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    date TEXT,
    period INTEGER,
    status TEXT,
    UNIQUE(student_id, date, period)  -- 🔐 prevents duplication
)''')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        subject = request.form['subject']
        raw_password = request.form['password']  # Now teacher enters it
        hashed_password = generate_password_hash(raw_password)

        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO teachers (name, email, department, subject, password) VALUES (?, ?, ?, ?, ?)",
                      (name, email, department, subject, hashed_password))
            conn.commit()
            flash("Registered successfully! You can now log in.", "success")
        except sqlite3.IntegrityError:
            flash("Email already exists!", "error")
        conn.close()
        return redirect('/register')

    return render_template('register.html')


from werkzeug.security import check_password_hash

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()
        c.execute("SELECT id, password, name FROM teachers WHERE email = ?", (email,))
        teacher = c.fetchone()
        conn.close()

        if teacher and check_password_hash(teacher[1], password):
            session['teacher_id'] = teacher[0]
            session['teacher_name'] = teacher[2]
            flash("Login successful!", "success")
            return redirect('/dashboard')
        else:
            flash("Invalid email or password!", "error")
            return redirect('/login')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect('/login')

@app.route('/dashboard')
def dashboard():
    if 'teacher_id' not in session:
        return redirect('/login')  # 🔒 Force login
    name = session['teacher_name']  # ✅ Safe now
    return render_template("dashboard.html")

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'teacher_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        name = request.form['name']
        roll = request.form['roll']
        section = request.form['section']
        department = request.form['department']
        year = request.form['year']

        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO students (name, roll, section, department, year) VALUES (?, ?, ?, ?, ?)",
                      (name, roll, section, department, year))
            conn.commit()
            flash("Student added successfully!", "success")
        except sqlite3.IntegrityError:
            flash("Roll number already exists!", "error")
        conn.close()
        return redirect('/add_student')

    return render_template("add_student.html")

from flask import render_template, request, redirect, session, flash
from datetime import datetime, time

def get_current_period():
    now = datetime.now().time()
    periods = {
        1: (time(9, 0), time(9, 50)),
        2: (time(9, 51), time(10, 40)),
        3: (time(10, 41), time(11, 30)),
        4: (time(11, 31), time(12, 20)),
        5: (time(12, 21), time(13, 10)),
        6: (time(13, 11), time(15, 58)),
    }
    for period, (start, end) in periods.items():
        if start <= now <= end:
            return period
    return None

@app.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    if 'teacher_id' not in session:
        return redirect('/login')

    current_period = get_current_period()
    today = datetime.now().date().isoformat()
    students = []

    if request.method == 'POST':
        section = request.form['section']
        selected_date = request.form['date']
        period = int(request.form['period'])

        if 'load_students' in request.form:
            conn = sqlite3.connect('attendance.db')
            c = conn.cursor()
            c.execute("SELECT id, name, roll FROM students WHERE section = ?", (section,))
            students = c.fetchall()
            conn.close()

            return render_template('attendance_form.html',
                                   today=today,
                                   section=section,
                                   students=students,
                                   current_period=current_period)

        elif 'submit_attendance' in request.form:
            present_ids = request.form.getlist('present[]')

            conn = sqlite3.connect('attendance.db')
            c = conn.cursor()
            c.execute("SELECT id FROM students WHERE section = ?", (request.form['section'],))
            all_ids = [str(row[0]) for row in c.fetchall()]

            for sid in all_ids:
                status = "Present" if sid in present_ids else "Absent"
                try:
                    c.execute("INSERT INTO attendance (student_id, date, period, status) VALUES (?, ?, ?, ?)",
                              (sid, today, period, status))
                except sqlite3.IntegrityError:
                    flash("Attendance already marked.", "error")
                    conn.close()
                    return redirect('/mark_attendance')

            conn.commit()
            conn.close()
            flash("Attendance marked successfully!", "success")
            return redirect('/mark_attendance')

    return render_template('attendance_form.html',
                           today=today,
                           section=None,
                           students=students,
                           current_period=current_period)          



              
from datetime import datetime, time
import pytz

def get_current_period():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)  # Automatically fetch IST time

    current_time = now.time()
    print("DEBUG: IST Time:", current_time.strftime('%H:%M'))

    periods = {
        1: (time(9, 0), time(9, 50)),
        2: (time(9, 51), time(10, 40)),
        3: (time(10, 41), time(11, 30)),
        4: (time(11, 31), time(12, 20)),
        5: (time(12, 21), time(13, 10)),
        6: (time(13, 11), time(15, 58)),
    }

    for period, (start, end) in periods.items():
        if start <= current_time <= end:
            print(f"DEBUG: Period {period} active now.")
            return period

    print("DEBUG: No active period found.")
    return None

@app.route('/view_attendance', methods=['GET', 'POST'])
def view_attendance():
    if 'teacher_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        section = request.form['section']
        year = request.form['year']
        department = request.form['department']
        selected_date = request.form['date']
        period = int(request.form['period'])

        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()
        c.execute('''
            SELECT students.roll, students.name, students.section, students.year, students.department, 
                   attendance.date, attendance.period, attendance.status
            FROM students
            JOIN attendance ON students.id = attendance.student_id
            WHERE students.section=? AND students.year=? AND students.department=? 
              AND attendance.date=? AND attendance.period=?
        ''', (section, year, department, selected_date, period))

        records = c.fetchall()
        conn.close()

        return render_template('view_attendance_result.html', records=records)

    # If GET request, show selection form
    return render_template('view_attendance_form.html')

@app.route('/view_attendance_result')
def view_attendance_result():
    if 'staff_id' not in session:
        return redirect('/login')

    section = request.args.get('section')
    date = request.args.get('date')
    period = request.args.get('period')

    conn = sqlite3.connect('your_database.db')
    c = conn.cursor()
    c.execute("""
        SELECT s.roll_no, s.name, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE s.section = ? AND a.date = ? AND a.period = ?
    """, (section, date, period))
    records = c.fetchall()
    conn.close()
    return render_template('view_attendance_result.html', records=records, section=section, date=date, period=period)

    
from openpyxl import Workbook
from flask import send_file
import io

@app.route('/download_attendance', methods=['POST'])
def download_attendance():
    if 'teacher_id' not in session:
        return redirect('/login')

    date = request.form['date']
    period = request.form['period']

    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute('''SELECT s.roll, s.name, s.section, a.status
                 FROM attendance a
                 JOIN students s ON a.student_id = s.id
                 WHERE a.date = ? AND a.period = ?''', (date, period))
    records = c.fetchall()
    conn.close()

    # Create Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"

    ws.append(['Roll No', 'Name', 'Section', 'Status'])  # headers
    for row in records:
        ws.append(row)

    # Save to memory
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    filename = f"Attendance_{date}_P{period}.xlsx"
    return send_file(stream, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') 


@app.route('/attendance_stats', methods=['GET', 'POST'])
def attendance_stats():
    if 'teacher_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    # Fetch all students for autocomplete
    c.execute("SELECT name FROM students")
    all_students = [row[0] for row in c.fetchall()]

    stats = None

    if request.method == 'POST':
        name = request.form.get('student_name')
        section = request.form.get('section')
        year = request.form.get('year')
        department = request.form.get('department')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')

        query = '''
            SELECT status, COUNT(*) FROM attendance
            JOIN students ON students.id = attendance.student_id
            WHERE students.name = ? AND students.section = ? AND students.year = ? AND students.department = ?
              AND date BETWEEN ? AND ?
            GROUP BY status
        '''
        c.execute(query, (name, section, year, department, from_date, to_date))
        data = dict(c.fetchall())

        present = data.get("Present", 0)
        absent = data.get("Absent", 0)
        stats = {"present": present, "absent": absent}

    conn.close()

    return render_template("attendance_stats.html", stats=stats, all_students=all_students)


from flask import Flask, render_template, request, jsonify

@app.route('/statistics', methods=['GET'])
def statistics_page():
    return render_template('attendance_stats.html')

@app.route('/get_statistics', methods=['POST'])
def get_statistics():
    data = request.json
    student_name = data.get('student_name')
    section = data.get('section')
    year = data.get('year')
    department = data.get('department')
    from_date = data.get('from_date')
    to_date = data.get('to_date')

    # Dummy data — replace with DB query
    attendance_records = [
        {"date": "2025-07-01", "status": "Present"},
        {"date": "2025-07-02", "status": "Absent"},
        {"date": "2025-07-03", "status": "Present"},
        {"date": "2025-07-04", "status": "Absent"},
        {"date": "2025-07-05", "status": "Present"},
    ]

    total_days = len(attendance_records)
    present_days = sum(1 for record in attendance_records if record['status'] == 'Present')
    absent_days = total_days - present_days
    percentage = (present_days / total_days) * 100 if total_days else 0

    return jsonify({
        "percentage": round(percentage, 2),
        "present_days": present_days,
        "absent_days": absent_days,
        "records": attendance_records
    })


@app.route('/student_attendance', methods=['GET', 'POST'])
def student_attendance():
    if 'teacher_id' not in session:
        return redirect('/login')

    student_record = None
    student_info = None

    if request.method == 'POST':
        roll = request.form['roll']

        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()
        c.execute("SELECT id, name, section FROM students WHERE roll = ?", (roll,))
        student = c.fetchone()

        if student:
            student_id = student[0]
            student_info = {
                "roll": roll,
                "name": student[1],
                "section": student[2]
            }

            c.execute('''SELECT date, period, status FROM attendance
                         WHERE student_id = ?
                         ORDER BY date DESC, period ASC''', (student_id,))
            student_record = c.fetchall()
        conn.close()

    return render_template("student_attendance.html", record=student_record, info=student_info)   

@app.route('/view_students', methods=['GET', 'POST'])
def view_students():
    if 'teacher_id' not in session:
        return redirect('/login')

    students = []
    selected_section = None

    if request.method == 'POST':
        selected_section = request.form['section']
        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()
        c.execute("SELECT id, name, roll, section, year, department FROM students WHERE section = ? ORDER BY CAST(SUBSTR(roll, -3) AS INTEGER)", (selected_section,))
        students = c.fetchall()
        conn.close()

    return render_template("view_students.html", students=students, section=selected_section)     

  

if __name__ == '__main__':
    init_db()
        
    app.run(debug=True)