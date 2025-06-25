# dashboard/app.py - MotorPass Admin Dashboard for Current Database Structure

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
import os
import sys
from datetime import datetime, timedelta
import hashlib
import sqlite3

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import from your existing modules
from config import SYSTEM_NAME, SYSTEM_VERSION
from database.init_database import MOTORPASS_DB
from database.db_operations import (
    get_all_time_records,
    get_students_currently_in,
    get_all_students,
    get_all_staff,
    get_all_guests,
    get_time_records_by_date,
    get_database_stats
)

app = Flask(__name__)
app.secret_key = 'motorpass-secret-key-2024'  # Change this in production
CORS(app)

# Authentication settings
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = hashlib.sha256('motorpass123'.encode()).hexdigest()

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
    """Get real-time dashboard data for all user types"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get people currently inside by type
        cursor.execute('''
            SELECT user_type, COUNT(*) as count 
            FROM current_status 
            WHERE status = 'IN' 
            GROUP BY user_type
        ''')
        
        currently_inside = {'STUDENT': 0, 'STAFF': 0, 'GUEST': 0}
        total_inside = 0
        
        for row in cursor.fetchall():
            currently_inside[row['user_type']] = row['count']
            total_inside += row['count']
        
        # Get today's actions by type
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT user_type, action, COUNT(*) as count 
            FROM time_tracking 
            WHERE date = ? 
            GROUP BY user_type, action
        ''', (today,))
        
        today_actions = {
            'STUDENT': {'IN': 0, 'OUT': 0},
            'STAFF': {'IN': 0, 'OUT': 0},
            'GUEST': {'IN': 0, 'OUT': 0}
        }
        
        for row in cursor.fetchall():
            if row['user_type'] in today_actions:
                today_actions[row['user_type']][row['action']] = row['count']
        
        # Get total counts
        cursor.execute('SELECT COUNT(*) FROM students')
        total_students = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM staff')
        total_staff = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM guests')
        total_guests = cursor.fetchone()[0]
        
        # Get people currently inside with details
        cursor.execute('''
            SELECT 
                cs.user_id,
                cs.user_name,
                cs.user_type,
                cs.last_action_time,
                CASE 
                    WHEN cs.user_type = 'STUDENT' THEN s.course
                    WHEN cs.user_type = 'STAFF' THEN st.staff_role
                    WHEN cs.user_type = 'GUEST' THEN g.office_visiting
                    ELSE 'Unknown'
                END as details
            FROM current_status cs
            LEFT JOIN students s ON cs.user_id = s.student_id AND cs.user_type = 'STUDENT'
            LEFT JOIN staff st ON cs.user_id = st.staff_no AND cs.user_type = 'STAFF'
            LEFT JOIN guests g ON cs.user_id = g.plate_number AND cs.user_type = 'GUEST'
            WHERE cs.status = 'IN'
            ORDER BY cs.last_action_time DESC
            LIMIT 20
        ''')
        
        people_inside = []
        for row in cursor.fetchall():
            people_inside.append({
                'id': row['user_id'],
                'name': row['user_name'],
                'type': row['user_type'],
                'details': row['details'] or 'N/A',
                'time_in': row['last_action_time']
            })
        
        conn.close()
        
        # Prepare response
        data = {
            'success': True,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_inside': total_inside,
                'students_inside': currently_inside['STUDENT'],
                'staff_inside': currently_inside['STAFF'],
                'guests_inside': currently_inside['GUEST'],
                'today_students_in': today_actions['STUDENT']['IN'],
                'today_students_out': today_actions['STUDENT']['OUT'],
                'today_staff_in': today_actions['STAFF']['IN'],
                'today_staff_out': today_actions['STAFF']['OUT'],
                'today_guests_in': today_actions['GUEST']['IN'],
                'today_guests_out': today_actions['GUEST']['OUT'],
                'total_students': total_students,
                'total_staff': total_staff,
                'total_guests': total_guests
            },
            'people_inside': people_inside
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
    """Get recent time records for all user types"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                user_id,
                user_name,
                user_type,
                action,
                date,
                time,
                timestamp
            FROM time_tracking
            ORDER BY timestamp DESC
            LIMIT 30
        ''')
        
        activities = []
        for row in cursor.fetchall():
            activities.append({
                'person_id': row['user_id'],
                'person_name': row['user_name'],
                'person_type': row['user_type'],
                'action': row['action'],
                'date': row['date'],
                'time': row['time'],
                'timestamp': row['timestamp']
            })
        
        conn.close()
        
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
        search_term = request.args.get('search', '')
        limit = int(request.args.get('limit', 100))
        
        conn = sqlite3.connect(MOTORPASS_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        query = '''
            SELECT 
                id,
                user_id,
                user_name,
                user_type,
                action,
                date,
                time,
                timestamp
            FROM time_tracking
            WHERE 1=1
        '''
        params = []
        
        if date_from:
            query += ' AND date >= ?'
            params.append(date_from)
        
        if date_to:
            query += ' AND date <= ?'
            params.append(date_to)
        
        if person_type:
            query += ' AND user_type = ?'
            params.append(person_type)
        
        if search_term:
            query += ' AND (user_id LIKE ? OR user_name LIKE ?)'
            params.extend([f'%{search_term}%', f'%{search_term}%'])
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'id': row['id'],
                'person_id': row['user_id'],
                'person_name': row['user_name'],
                'person_type': row['user_type'],
                'action': row['action'],
                'date': row['date'],
                'time': row['time'],
                'timestamp': row['timestamp']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'records': records
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/reports')
@login_required
def reports():
    """Reports page with support for all user types"""
    return render_template('reports.html',
                         system_name=SYSTEM_NAME)

@app.route('/api/courses')
@login_required
def get_courses():
    """Get available courses for filtering"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT course 
            FROM students 
            WHERE course IS NOT NULL AND course != ''
            ORDER BY course
        ''')
        
        courses = [row['course'] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'courses': courses})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/staff-roles')
@login_required
def get_staff_roles():
    """Get available staff roles for filtering"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT staff_role 
            FROM staff 
            WHERE staff_role IS NOT NULL AND staff_role != ''
            ORDER BY staff_role
        ''')
        
        roles = [row['staff_role'] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'roles': roles})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate-report')
@login_required
def generate_report():
    """Generate reports with support for all user types"""
    try:
        report_type = request.args.get('type', 'daily')
        target_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        course_filter = request.args.get('course')
        role_filter = request.args.get('role')
        
        if report_type == 'daily':
            report_data = generate_daily_report(target_date)
        elif report_type == 'course':
            report_data = generate_course_report(target_date, course_filter)
        elif report_type == 'staff':
            report_data = generate_staff_report(target_date, role_filter)
        elif report_type == 'guest':
            report_data = generate_guest_report(target_date)
        elif report_type == 'weekly':
            report_data = generate_weekly_report(target_date)
        elif report_type == 'monthly':
            report_data = generate_monthly_report(target_date)
        else:
            report_data = {'error': 'Invalid report type'}
        
        return jsonify({
            'success': True,
            'report': report_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def generate_daily_report(target_date):
    """Generate comprehensive daily report for all user types"""
    conn = sqlite3.connect(MOTORPASS_DB)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        
        # Get actions by user type
        cursor.execute('''
            SELECT user_type, action, COUNT(*) as count
            FROM time_tracking 
            WHERE date = ?
            GROUP BY user_type, action
        ''', (target_date,))
        
        actions = {
            'STUDENT': {'IN': 0, 'OUT': 0},
            'STAFF': {'IN': 0, 'OUT': 0},
            'GUEST': {'IN': 0, 'OUT': 0}
        }
        
        for row in cursor.fetchall():
            if row['user_type'] in actions:
                actions[row['user_type']][row['action']] = row['count']
        
        # Get currently inside by type
        cursor.execute('''
            SELECT user_type, COUNT(*) as count
            FROM current_status 
            WHERE status = 'IN'
            GROUP BY user_type
        ''')
        
        currently_inside = {'STUDENT': 0, 'STAFF': 0, 'GUEST': 0}
        for row in cursor.fetchall():
            currently_inside[row['user_type']] = row['count']
        
        # Get peak hour
        cursor.execute('''
            SELECT strftime('%H', time) as hour, COUNT(*) as count
            FROM time_tracking
            WHERE date = ? AND action = 'IN'
            GROUP BY hour
            ORDER BY count DESC
            LIMIT 1
        ''', (target_date,))
        
        peak_row = cursor.fetchone()
        peak_hour = f"{peak_row['hour']}:00" if peak_row else "N/A"
        
        return {
            'date': target_date,
            'students': {
                'time_in': actions['STUDENT']['IN'],
                'time_out': actions['STUDENT']['OUT'],
                'currently_inside': currently_inside['STUDENT']
            },
            'staff': {
                'time_in': actions['STAFF']['IN'],
                'time_out': actions['STAFF']['OUT'],
                'currently_inside': currently_inside['STAFF']
            },
            'guests': {
                'time_in': actions['GUEST']['IN'],
                'time_out': actions['GUEST']['OUT'],
                'currently_inside': currently_inside['GUEST']
            },
            'total_currently_inside': sum(currently_inside.values()),
            'peak_hour': peak_hour
        }
        
    finally:
        conn.close()

def generate_course_report(target_date, course_filter=None):
    """Generate course statistics report"""
    conn = sqlite3.connect(MOTORPASS_DB)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        
        # Build course filter
        course_condition = ''
        params = [target_date, target_date]
        
        if course_filter:
            course_condition = 'AND s.course = ?'
            params.extend([course_filter, course_filter])
        
        # Get course statistics
        cursor.execute(f'''
            SELECT 
                s.course,
                COUNT(DISTINCT s.student_id) as total_students,
                COALESCE(today_in.count, 0) as time_in,
                COALESCE(today_out.count, 0) as time_out,
                COALESCE(inside.count, 0) as currently_inside
            FROM students s
            LEFT JOIN (
                SELECT s2.course, COUNT(*) as count
                FROM time_tracking tr
                JOIN students s2 ON tr.user_id = s2.student_id
                WHERE tr.date = ? AND tr.action = 'IN' AND tr.user_type = 'STUDENT'
                {course_condition if course_filter else ''}
                GROUP BY s2.course
            ) today_in ON s.course = today_in.course
            LEFT JOIN (
                SELECT s2.course, COUNT(*) as count
                FROM time_tracking tr
                JOIN students s2 ON tr.user_id = s2.student_id
                WHERE tr.date = ? AND tr.action = 'OUT' AND tr.user_type = 'STUDENT'
                {course_condition if course_filter else ''}
                GROUP BY s2.course
            ) today_out ON s.course = today_out.course
            LEFT JOIN (
                SELECT s2.course, COUNT(*) as count
                FROM current_status cs
                JOIN students s2 ON cs.user_id = s2.student_id
                WHERE cs.status = 'IN' AND cs.user_type = 'STUDENT'
                GROUP BY s2.course
            ) inside ON s.course = inside.course
            WHERE s.course IS NOT NULL AND s.course != ''
            {course_condition if course_filter else ''}
            GROUP BY s.course
            ORDER BY s.course
        ''', params[:2] if not course_filter else params)
        
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
            'course_filter': course_filter,
            'course_details': course_details,
            'total_courses': len(course_details)
        }
        
    finally:
        conn.close()

def generate_staff_report(target_date, role_filter=None):
    """Generate staff statistics report"""
    conn = sqlite3.connect(MOTORPASS_DB)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        
        # Get staff statistics by role
        role_condition = 'AND st.staff_role = ?' if role_filter else ''
        params = [target_date, target_date]
        if role_filter:
            params.extend([role_filter] * 2)
        
        cursor.execute(f'''
            SELECT 
                st.staff_role,
                COUNT(DISTINCT st.staff_no) as total_staff,
                COALESCE(today_in.count, 0) as time_in,
                COALESCE(today_out.count, 0) as time_out,
                COALESCE(inside.count, 0) as currently_inside
            FROM staff st
            LEFT JOIN (
                SELECT s2.staff_role, COUNT(*) as count
                FROM time_tracking tr
                JOIN staff s2 ON tr.user_id = s2.staff_no
                WHERE tr.date = ? AND tr.action = 'IN' AND tr.user_type = 'STAFF'
                {role_condition}
                GROUP BY s2.staff_role
            ) today_in ON st.staff_role = today_in.staff_role
            LEFT JOIN (
                SELECT s2.staff_role, COUNT(*) as count
                FROM time_tracking tr
                JOIN staff s2 ON tr.user_id = s2.staff_no
                WHERE tr.date = ? AND tr.action = 'OUT' AND tr.user_type = 'STAFF'
                {role_condition}
                GROUP BY s2.staff_role
            ) today_out ON st.staff_role = today_out.staff_role
            LEFT JOIN (
                SELECT s2.staff_role, COUNT(*) as count
                FROM current_status cs
                JOIN staff s2 ON cs.user_id = s2.staff_no
                WHERE cs.status = 'IN' AND cs.user_type = 'STAFF'
                GROUP BY s2.staff_role
            ) inside ON st.staff_role = inside.staff_role
            WHERE st.staff_role IS NOT NULL AND st.staff_role != ''
            {role_condition.replace('AND', 'AND', 1) if role_filter else ''}
            GROUP BY st.staff_role
            ORDER BY st.staff_role
        ''', params)
        
        role_details = []
        for row in cursor.fetchall():
            role_details.append({
                'role_name': row['staff_role'],
                'total_staff': row['total_staff'],
                'time_in': row['time_in'],
                'time_out': row['time_out'],
                'currently_inside': row['currently_inside']
            })
        
        return {
            'date': target_date,
            'role_filter': role_filter,
            'role_details': role_details,
            'total_roles': len(role_details)
        }
        
    finally:
        conn.close()

def generate_guest_report(target_date):
    """Generate guest statistics report"""
    conn = sqlite3.connect(MOTORPASS_DB)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        
        # Get guest statistics by office
        cursor.execute('''
            SELECT 
                g.office_visiting,
                COUNT(DISTINCT g.guest_id) as unique_guests,
                COALESCE(visits.count, 0) as visits_today
            FROM (
                SELECT DISTINCT office_visiting
                FROM guests
                WHERE office_visiting IS NOT NULL
            ) offices
            LEFT JOIN guests g ON offices.office_visiting = g.office_visiting
            LEFT JOIN (
                SELECT 
                    g2.office_visiting, 
                    COUNT(*) as count
                FROM time_tracking tr
                JOIN guests g2 ON tr.user_id = ('GUEST_' || g2.plate_number)
                WHERE tr.date = ? AND tr.action = 'IN' AND tr.user_type = 'GUEST'
                GROUP BY g2.office_visiting
            ) visits ON offices.office_visiting = visits.office_visiting
            GROUP BY g.office_visiting
            ORDER BY visits_today DESC
        ''', (target_date,))
        
        office_details = []
        for row in cursor.fetchall():
            if row['office_visiting']:
                office_details.append({
                    'office_name': row['office_visiting'],
                    'unique_guests': row['unique_guests'],
                    'visits_today': row['visits_today']
                })
        
        # Get overall guest stats
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT user_id) as unique_guests_today,
                COUNT(*) as total_visits
            FROM time_tracking
            WHERE date = ? AND user_type = 'GUEST' AND action = 'IN'
        ''', (target_date,))
        
        overall = cursor.fetchone()
        
        return {
            'date': target_date,
            'office_details': office_details,
            'unique_guests_today': overall['unique_guests_today'] or 0,
            'total_visits': overall['total_visits'] or 0
        }
        
    finally:
        conn.close()

def generate_weekly_report(target_date):
    """Generate weekly summary for all user types"""
    target_dt = datetime.strptime(target_date, '%Y-%m-%d')
    week_start = target_dt - timedelta(days=target_dt.weekday())
    week_end = week_start + timedelta(days=6)
    
    conn = sqlite3.connect(MOTORPASS_DB)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        
        # Get statistics by user type
        cursor.execute('''
            SELECT 
                user_type,
                COUNT(*) as total_activities,
                COUNT(DISTINCT user_id) as unique_users
            FROM time_tracking
            WHERE date BETWEEN ? AND ?
            GROUP BY user_type
        ''', (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
        
        stats = {'STUDENT': {}, 'STAFF': {}, 'GUEST': {}}
        total_activities = 0
        
        for row in cursor.fetchall():
            stats[row['user_type']] = {
                'activities': row['total_activities'],
                'unique_users': row['unique_users']
            }
            total_activities += row['total_activities']
        
        return {
            'week': f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}",
            'total_activities': total_activities,
            'by_type': stats
        }
        
    finally:
        conn.close()

def generate_monthly_report(target_date):
    """Generate monthly summary for all user types"""
    target_dt = datetime.strptime(target_date, '%Y-%m-%d')
    month_start = target_dt.replace(day=1)
    
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
    
    conn = sqlite3.connect(MOTORPASS_DB)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        
        # Get statistics by user type
        cursor.execute('''
            SELECT 
                user_type,
                COUNT(*) as total_activities,
                COUNT(DISTINCT user_id) as unique_users
            FROM time_tracking
            WHERE date BETWEEN ? AND ?
            GROUP BY user_type
        ''', (month_start.strftime('%Y-%m-%d'), month_end.strftime('%Y-%m-%d')))
        
        stats = {'STUDENT': {}, 'STAFF': {}, 'GUEST': {}}
        total_activities = 0
        
        for row in cursor.fetchall():
            stats[row['user_type']] = {
                'activities': row['total_activities'],
                'unique_users': row['unique_users']
            }
            total_activities += row['total_activities']
        
        return {
            'month': target_dt.strftime('%B %Y'),
            'total_activities': total_activities,
            'by_type': stats
        }
        
    finally:
        conn.close()

@app.route('/users')
@login_required
def users():
    """Users management page"""
    return render_template('users.html',
                         system_name=SYSTEM_NAME)

@app.route('/api/users')
@login_required
def get_users():
    """Get all users by type"""
    try:
        user_type = request.args.get('type', 'all')
        search_term = request.args.get('search', '')
        
        users = []
        
        # Get students
        if user_type in ['all', 'student']:
            students = get_all_students()
            for s in students:
                if not search_term or search_term.lower() in s['full_name'].lower() or search_term in s['student_id']:
                    users.append({
                        'id': s['student_id'],
                        'name': s['full_name'],
                        'type': 'STUDENT',
                        'details': s['course'],
                        'plate': s.get('plate_number', 'N/A')
                    })
        
        # Get staff
        if user_type in ['all', 'staff']:
            staff_list = get_all_staff()
            for s in staff_list:
                if not search_term or search_term.lower() in s['full_name'].lower() or search_term in s['staff_no']:
                    users.append({
                        'id': s['staff_no'],
                        'name': s['full_name'],
                        'type': 'STAFF',
                        'details': s['staff_role'],
                        'plate': s.get('plate_number', 'N/A')
                    })
        
        # Get guests
        if user_type in ['all', 'guest']:
            guests = get_all_guests()
            for g in guests:
                if not search_term or search_term.lower() in g['full_name'].lower() or search_term in g['plate_number']:
                    users.append({
                        'id': f"GUEST_{g['plate_number']}",
                        'name': g['full_name'],
                        'type': 'GUEST',
                        'details': g['office_visiting'],
                        'plate': g['plate_number']
                    })
        
        return jsonify({
            'success': True,
            'users': users
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/settings')
@login_required
def settings():
    """Settings page"""
    stats = get_database_stats()
    return render_template('settings.html',
                         system_name=SYSTEM_NAME,
                         system_version=SYSTEM_VERSION,
                         stats=stats)

@app.route('/api/system-info')
@login_required
def get_system_info():
    """Get system information"""
    try:
        stats = get_database_stats()
        
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
                'database_path': MOTORPASS_DB
            },
            'database': stats
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
