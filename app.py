import os
from flask import Flask, render_template, request, redirect, url_for, session, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import csv
import io

app = Flask(__name__)
app.secret_key = 'kzn_logistics_secure_key'

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///logistics_v6.db' # NEW DB VERSION
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ==========================================
# 1. DATA MODELS (SIMPLIFIED)
# ==========================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    image_url = db.Column(db.String(200))

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # BACK TO SIMPLE TEXT - NO IDs
    client_name = db.Column(db.String(100), nullable=False) 
    pickup = db.Column(db.String(200), nullable=False)
    dropoff = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.String(50), nullable=False)
    
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(50), default='Created') 
    driver_note = db.Column(db.Text, nullable=True)
    pod_image_url = db.Column(db.String(200), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    driver = db.relationship('User', backref='jobs')

    @property
    def is_late(self):
        if self.status in ['Delivered', 'Issue']:
            return False
        try:
            job_due = datetime.strptime(self.due_date, '%d %b %Y, %H:%M')
            return datetime.now() > job_due
        except:
            return False

# ==========================================
# 2. ROUTES
# ==========================================

@app.route('/')
def home():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    
    if user.role in ['admin', 'ops']:
        all_jobs = Job.query.order_by(Job.created_at.desc()).all()
        all_drivers = User.query.filter_by(role='driver').all()
        
        stats = {
            'active': Job.query.filter(Job.status.notin_(['Delivered', 'Created'])).count(),
            'delayed': Job.query.filter_by(status='Issue').count(),
            'completed': Job.query.filter_by(status='Delivered').count()
        }
        return render_template('dashboard_admin.html', user=user, jobs=all_jobs, stats=stats, drivers=all_drivers)
    else:
        active_jobs = Job.query.filter_by(driver_id=user.id).filter(Job.status != 'Delivered').order_by(Job.due_date).all()
        history_jobs = Job.query.filter_by(driver_id=user.id, status='Delivered').order_by(Job.created_at.desc()).all()
        return render_template('dashboard_driver.html', user=user, jobs=active_jobs, history=history_jobs)

@app.route('/create_job', methods=['GET', 'POST'])
def create_job():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Simple Date Formatting
        raw_date = request.form['date']
        try:
            dt_obj = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M')
            formatted_date = dt_obj.strftime('%d %b %Y, %H:%M')
        except:
            formatted_date = raw_date

        new_job = Job(
            client_name=request.form['client'], # DIRECT TEXT SAVE
            pickup=request.form['pickup'],
            dropoff=request.form['dropoff'],
            due_date=formatted_date,
            driver_id=request.form['driver_id'],
            status='Assigned'
        )
        db.session.add(new_job)
        db.session.commit()
        return redirect(url_for('dashboard'))

    drivers = User.query.filter_by(role='driver').all()
    return render_template('create_job.html', drivers=drivers)

@app.route('/job_details/<int:job_id>')
def job_details(job_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    job = Job.query.get_or_404(job_id)
    return render_template('job_details.html', job=job, user=user)

@app.route('/export_csv')
def export_csv():
    if session.get('role') == 'driver': return redirect(url_for('dashboard'))
    
    period = request.args.get('period', 'all')
    query = Job.query
    
    now = datetime.now()
    if period == 'week':
        start_date = now - timedelta(days=7)
        query = query.filter(Job.created_at >= start_date)
    elif period == 'month':
        start_date = now - timedelta(days=30)
        query = query.filter(Job.created_at >= start_date)
    
    jobs = query.order_by(Job.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Job ID', 'Client', 'Driver', 'Pickup', 'Dropoff', 'Status', 'Date', 'Note', 'POD Link'])
    
    for job in jobs:
        d_name = job.driver.username if job.driver else "Unassigned"
        pod_link = "Yes" if job.pod_image_url else "No"
        # DIRECT TEXT EXPORT
        writer.writerow([job.id, job.client_name, d_name, job.pickup, job.dropoff, job.status, job.due_date, job.driver_note, pod_link])
        
    filename = f"logistics_report_{period}_{now.strftime('%Y-%m-%d')}.csv"
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename={filename}"})

# ... (Keep create_driver, update_job, login, logout SAME AS BEFORE) ...

# Keep create_driver, update_job, login, logout exactly as they were. 
# I am re-pasting create_driver here for safety since you need it.

@app.route('/create_driver', methods=['GET', 'POST'])
def create_driver():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.role != 'admin': return redirect(url_for('dashboard'))

    if request.method == 'POST':
        image_url = 'https://images.unsplash.com/photo-1633332755192-727a05c4013d?fit=crop&w=100&h=100'
        if 'driver_photo' in request.files:
            file = request.files['driver_photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                new_filename = f"driver_{request.form['username']}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                image_url = f"/static/uploads/{new_filename}"

        new_driver = User(
            username=request.form['username'],
            password=request.form['password'],
            role='driver',
            image_url=image_url
        )
        try:
            db.session.add(new_driver)
            db.session.commit()
            return redirect(url_for('dashboard'))
        except:
            return "Error: Username already exists!"

    return render_template('create_driver.html')

@app.route('/update_job/<int:job_id>', methods=['GET', 'POST'])
def update_job(job_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    job = Job.query.get_or_404(job_id)
    
    if request.method == 'POST':
        job.status = request.form['status']
        job.driver_note = request.form['note']
        if 'pod_photo' in request.files:
            file = request.files['pod_photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                new_filename = f"pod_{job.id}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                job.pod_image_url = f"/static/uploads/{new_filename}"
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('update_job.html', job=job)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

def seed():
    with app.app_context():
        db.create_all()
        if not User.query.first():
            db.session.add(User(username='admin', password='123', role='admin', image_url='https://images.unsplash.com/photo-1560250097-0b93528c311a?fit=crop&w=100&h=100'))
            db.session.commit()

if __name__ == '__main__':
    seed()
    app.run(debug=True, port=5001)