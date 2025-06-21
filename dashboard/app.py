# dashboard/app.py - Fixed MotorPass Admin Dashboard with Enhanced Reports

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
import os
import sys
from datetime import datetime, timedelta
import hashlib

# FIXED: Add project root to path for proper imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config import SYSTEM_NAME, SYSTEM_VERSION

# FIXED: Import unified database - it will use the correct path automatically
from database.unified_db import db, get_dashboard_summary

app = Flask(__name__)
app.secret_key = 'motorpass-secret-key-change-this'  # Change this to a random secret key
CORS(app)

# Simple authentication
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = hashlib.sha256('motorpass123'.encode()).hexdigest()  # Change default password

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if username == ADMIN_USERNAME and password_hash == ADMIN_PASSWORD_HASH:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', 
                         system_name=SYSTEM_NAME,
                         system_version=SYSTEM_VERSION)

@app.route('/api/dashboard-data')
@login_required
def get_dashboard_data():
    """Get real-time dashboard data"""
    try:
        # Get summary from database
        summary = db.get_dashboard_summary()
        
        # Get people currently inside
        people_inside = db.get_people_currently_inside()
        
        # Format response
        data = {
            'success': True,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_inside': summary.get('total_currently_inside', 0),
                'students_inside': summary.get('currently_inside', {}).get('STUDENT', 0),
                'guests_inside': summary.get('currently_inside', {}).get('GUEST', 0),
                'today_students_in': summary.get('today_actions', {}).get('STUDENT', {}).get('IN', 0),
                'today_students_out': summary.get('today_actions', {}).get('STUDENT', {}).get('OUT', 0),
                'today_guests_in': summary.get('today_actions', {}).get('GUEST', {}).get('IN', 0),
                'today_guests_out': summary.get('today_actions', {}).get('GUEST', {}).get('OUT', 0),
                'total_students': summary.get('total_students', 0),
                'total_guests': summary.get('total_guests', 0)
            },
            'people_inside': [
                {
                    'id': person['person_id'],
                    'name': person['person_name'],
                    'type': person['person_type'],
                    'time_in': person['last_action_time']
                } for person in people_inside[:10]  # Latest 10
            ]
        }
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/recent-activities')
@login_required
def get_recent_activities():
    """Get recent time records"""
    try:
        # Get recent records
        records = db.get_time_records(limit=20)
        
        activities = []
        for record in records:
            activities.append({
                'person_id': record['person_id'],
                'person_name': record['person_name'],
                'person_type': record['person_type'],
                'action': record['action'],
                'timestamp': record['timestamp'],
                'time': record['time']
            })
        
        return jsonify({
            'success': True,
            'activities': activities
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/time-records')
@login_required
def time_records():
    """Time records page"""
    return render_template('time_records.html',
                         system_name=SYSTEM_NAME)

@app.route('/api/time-records')
@login_required
def get_time_records():
    """Get filtered time records"""
    try:
        # Get filters from query params
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        person_type = request.args.get('person_type')
        limit = int(request.args.get('limit', 100))
        
        # Get records
        records = db.get_time_records(
            date_from=date_from,
            date_to=date_to,
            person_type=person_type,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'records': [
                {
                    'id': r['id'],
                    'person_id': r['person_id'],
                    'person_name': r['person_name'],
                    'person_type': r['person_type'],
                    'action': r['action'],
                    'date': r['date'],
                    'time': r['time'],
                    'timestamp': r['timestamp']
                } for r in records
            ]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/reports')
@login_required
def reports():
    """Reports page - ENHANCED with course statistics"""
    return render_template('reports.html',
                         system_name=SYSTEM_NAME)

# ===== NEW REPORTS API ENDPOINTS =====

@app.route('/api/courses')
@login_required
def get_courses():
    """Get available courses for filtering"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT course 
            FROM students 
            WHERE course IS NOT NULL AND course != '' AND is_active = 1
            ORDER BY course
        ''')
        
        courses = [row['course'] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'courses': courses})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate-report')
@login_required
def generate_report():
    """Generate enhanced reports with course statistics"""
    try:
        report_type = request.args.get('type', 'daily')
        target_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        course_filter = request.args.get('course')
        
        if report_type == 'daily':
            report_data = generate_daily_report(target_date, course_filter)
        elif report_type == 'course':
            report_data = generate_course_report(target_date)
        elif report_type == 'weekly':
            report_data = generate_weekly_report(target_date)
        elif report_type == 'monthly':
            report_data = generate_monthly_report(target_date)
        else:
            # Fallback to original simple report
            report_data = db.generate_daily_report(target_date)
        
        return jsonify({
            'success': True,
            'report': report_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def generate_daily_report(target_date, course_filter=None):
    """Enhanced daily report with course filtering"""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        
        # Base query with optional course filter
        if course_filter:
            student_query = '''
                SELECT tr.action, COUNT(*) as count
                FROM time_records tr
                JOIN students s ON tr.person_id = s.student_id
                WHERE tr.date = ? AND tr.person_type = 'STUDENT' AND s.course = ?
                GROUP BY tr.action
            '''
            cursor.execute(student_query, (target_date, course_filter))
        else:
            cursor.execute('''
                SELECT action, COUNT(*) as count
                FROM time_records 
                WHERE date = ? AND person_type = 'STUDENT'
                GROUP BY action
            ''', (target_date,))
        
        student_actions = {row['action']: row['count'] for row in cursor.fetchall()}
        
        # Guest actions (no course filter)
        cursor.execute('''
            SELECT action, COUNT(*) as count
            FROM time_records 
            WHERE date = ? AND person_type = 'GUEST'
            GROUP BY action
        ''', (target_date,))
        
        guest_actions = {row['action']: row['count'] for row in cursor.fetchall()}
        
        # Currently inside with course filter
        if course_filter:
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM current_status cs
                JOIN students s ON cs.person_id = s.student_id
                WHERE cs.current_status = 'IN' AND cs.person_type = 'STUDENT' AND s.course = ?
            ''', (course_filter,))
        else:
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM current_status 
                WHERE current_status = 'IN' AND person_type = 'STUDENT'
            ''')
        
        students_inside = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM current_status 
            WHERE current_status = 'IN' AND person_type = 'GUEST'
        ''')
        guests_inside = cursor.fetchone()['count']
        
        return {
            'date': target_date,
            'course_filter': course_filter,
            'students': {
                'time_in': student_actions.get('IN', 0),
                'time_out': student_actions.get('OUT', 0),
                'currently_inside': students_inside
            },
            'guests': {
                'time_in': guest_actions.get('IN', 0),
                'time_out': guest_actions.get('OUT', 0),
                'currently_inside': guests_inside
            },
            'total_currently_inside': students_inside + guests_inside
        }
        
    finally:
        conn.close()

def generate_course_report(target_date):
    """Generate course statistics report"""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        
        # Get course statistics
        cursor.execute('''
            SELECT 
                s.course,
                COUNT(DISTINCT s.student_id) as total_students,
                COALESCE(today_in.count, 0) as time_in,
                COALESCE(today_out.count, 0) as time_out,
                COALESCE(inside.count, 0) as currently_inside
            FROM students s
            LEFT JOIN (
                SELECT s2.course, COUNT(*) as count
                FROM time_records tr
                JOIN students s2 ON tr.person_id = s2.student_id
                WHERE tr.date = ? AND tr.action = 'IN' AND tr.person_type = 'STUDENT'
                GROUP BY s2.course
            ) today_in ON s.course = today_in.course
            LEFT JOIN (
                SELECT s2.course, COUNT(*) as count
                FROM time_records tr
                JOIN students s2 ON tr.person_id = s2.student_id
                WHERE tr.date = ? AND tr.action = 'OUT' AND tr.person_type = 'STUDENT'
                GROUP BY s2.course
            ) today_out ON s.course = today_out.course
            LEFT JOIN (
                SELECT s2.course, COUNT(*) as count
                FROM current_status cs
                JOIN students s2 ON cs.person_id = s2.student_id
                WHERE cs.current_status = 'IN' AND cs.person_type = 'STUDENT'
                GROUP BY s2.course
            ) inside ON s.course = inside.course
            WHERE s.course IS NOT NULL AND s.course != '' AND s.is_active = 1
            GROUP BY s.course
            ORDER BY s.course
        ''', (target_date, target_date))
        
        course_details = []
        for row in cursor.fetchall():
            course_details.append({
                'course_name': row['course'],
                'total_students': row['total_students'],
                'time_in': row['time_in'],
                'time_out': row['time_out'],
                'currently_inside': row['currently_inside']
            })
        
        return {
            'date': target_date,
            'course_details': course_details,
            'total_courses': len(course_details)
        }
        
    finally:
        conn.close()

def generate_weekly_report(target_date):
    """Generate weekly summary"""
    target_dt = datetime.strptime(target_date, '%Y-%m-%d')
    week_start = target_dt - timedelta(days=target_dt.weekday())
    week_end = week_start + timedelta(days=6)
    
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM time_records
            WHERE date BETWEEN ? AND ?
        ''', (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
        
        total_activities = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT COUNT(DISTINCT person_id) as count
            FROM time_records
            WHERE date BETWEEN ? AND ? AND person_type = 'STUDENT'
        ''', (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
        
        unique_students = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT COUNT(DISTINCT person_id) as count
            FROM time_records
            WHERE date BETWEEN ? AND ? AND person_type = 'GUEST'
        ''', (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
        
        unique_guests = cursor.fetchone()['count']
        
        return {
            'week': f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}",
            'total_activities': total_activities,
            'unique_students': unique_students,
            'unique_guests': unique_guests
        }
        
    finally:
        conn.close()

def generate_monthly_report(target_date):
    """Generate monthly summary"""
    target_dt = datetime.strptime(target_date, '%Y-%m-%d')
    month_start = target_dt.replace(day=1)
    
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
    
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM time_records
            WHERE date BETWEEN ? AND ?
        ''', (month_start.strftime('%Y-%m-%d'), month_end.strftime('%Y-%m-%d')))
        
        total_activities = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT COUNT(DISTINCT person_id) as count
            FROM time_records
            WHERE date BETWEEN ? AND ? AND person_type = 'STUDENT'
        ''', (month_start.strftime('%Y-%m-%d'), month_end.strftime('%Y-%m-%d')))
        
        unique_students = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT COUNT(DISTINCT person_id) as count
            FROM time_records
            WHERE date BETWEEN ? AND ? AND person_type = 'GUEST'
        ''', (month_start.strftime('%Y-%m-%d'), month_end.strftime('%Y-%m-%d')))
        
        unique_guests = cursor.fetchone()['count']
        
        return {
            'month': target_dt.strftime('%B %Y'),
            'total_activities': total_activities,
            'unique_students': unique_students,
            'unique_guests': unique_guests
        }
        
    finally:
        conn.close()

@app.route('/settings')
@login_required
def settings():
    """Settings page"""
    stats = db.get_database_stats()
    return render_template('settings.html',
                         system_name=SYSTEM_NAME,
                         system_version=SYSTEM_VERSION,
                         stats=stats)

@app.route('/api/system-info')
@login_required
def get_system_info():
    """Get system information"""
    try:
        stats = db.get_database_stats()
        
        # Get network info
        import socket
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        
        return jsonify({
            'success': True,
            'system': {
                'name': SYSTEM_NAME,
                'version': SYSTEM_VERSION,
                'ip_address': ip_address,
                'hostname': hostname,
                'uptime': "System running"
            },
            'database': {
                'total_students': stats.get('total_students', 0),
                'total_guests': stats.get('total_guests', 0),
                'total_time_records': stats.get('total_time_records', 0),
                'database_size': f"{stats.get('database_size', 0) / 1024 / 1024:.2f} MB"
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def run_dashboard(host='0.0.0.0', port=5000, debug=False):
    """Run the dashboard server"""
    print(f"🌐 Starting {SYSTEM_NAME} Dashboard Server...")
    print(f"📡 Access the dashboard at: http://<raspberry-pi-ip>:{port}")
    print(f"🔐 Default login: admin / motorpass123")
    print(f"⚠️  Remember to change the default password!")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_dashboard(debug=True)
