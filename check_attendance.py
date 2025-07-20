import sqlite3

# Connect to your existing database
conn = sqlite3.connect('attendance.db')
c = conn.cursor()

# ✅ Show all attendance records
print("🔍 All Attendance Records:")
c.execute("SELECT * FROM attendance")
all_rows = c.fetchall()
for row in all_rows:
    print(row)

print("\n🔍 Join students + attendance (to check if IDs match):")
c.execute("""
    SELECT a.student_id, s.id, s.name, s.roll, a.date, a.period, a.status
    FROM attendance a
    JOIN students s ON a.student_id = s.id
""")
joined = c.fetchall()
for row in joined:
    print(row)

conn.close()