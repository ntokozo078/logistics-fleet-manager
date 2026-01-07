import os
from flask import Flask, render_template, request, redirect, url_for, session, Response, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import csv
import io
import random 
import openrouteservice
from flask import jsonify
from flask import render_template
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps



app = Flask(__name__)
app.secret_key = 'kzn_logistics_enterprise_key'

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///logistics_v8_enterprise.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Where to send users if they aren't logged in

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==========================================
# 1. DATA MODELS
# ==========================================
class User(UserMixin, db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True) 
   
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    image_url = db.Column(db.String(200))
    phone = db.Column(db.String(20))

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reg_number = db.Column(db.String(20), unique=True, nullable=False) # e.g. ND 123-456
    type = db.Column(db.String(50)) # e.g. 8-Ton Truck
    base_fuel_rate = db.Column(db.Float) # Expected Liters/100km
    status = db.Column(db.String(20), default='Active') # Active, Maintenance

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    pickup = db.Column(db.String(200), nullable=False)
    dropoff = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.String(50), nullable=False)
    
    # Financials
    revenue = db.Column(db.Float, default=0.0)
    cost_fuel = db.Column(db.Float, default=0.0)
    cost_driver = db.Column(db.Float, default=0.0)
    
    # Links
    original_revenue = db.Column(db.Float, default=0.0) 
    final_revenue = db.Column(db.Float, default=0.0)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=True) # NEW
    delivery_status_detail = db.Column(db.String(50)) # e.g., "Partial Refusal", "Damaged"
    issue_notes = db.Column(db.Text)
    
    status = db.Column(db.String(50), default='Assigned')
    driver_note = db.Column(db.Text, nullable=True)
    pod_image_url = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    driver = db.relationship('User', backref='jobs')
    vehicle = db.relationship('Vehicle', backref='jobs')

    # Add these two lines for GPS tracking
    current_lat = db.Column(db.Float, nullable=True)
    current_lng = db.Column(db.Float, nullable=True)
    @property
    def profit(self):
        # Use final_revenue if set, otherwise use predicted revenue
        rev = self.final_revenue if self.final_revenue > 0 else self.revenue
        return rev - (self.cost_fuel + self.cost_driver)
    @property
    def margin_percent(self):
        if self.revenue == 0: return 0
        return round((self.profit / self.revenue) * 100, 1)

    @property
    def is_late(self):
        # SLA Logic
        if self.status in ['Delivered', 'Issue']: return False
        try:
            due = datetime.strptime(self.due_date, '%d %b %Y, %H:%M')
            return datetime.now() > due
        except: return False

# ==========================================
# 2. ROUTES
# ==========================================

@app.route('/index')
def index():
    return render_template('index.html')

# Update your existing 'home' route to look like this:
@app.route('/')
def home():
    if 'user_id' in session: 
        return redirect(url_for('dashboard'))
    return render_template('index.html') # Show landing page directly

@app.route('/dashboard')
@login_required
def dashboard():
    # 1. DRIVER DASHBOARD (If user is a driver)
    if current_user.role == 'driver':
        # Fetch only the driver's active jobs
        active_jobs = Job.query.filter_by(driver_id=current_user.id).filter(Job.status != 'Delivered').all()
        return render_template('dashboard_driver.html', user=current_user, jobs=active_jobs)

    # 2. MANAGEMENT DASHBOARD (If user is Owner, Admin, or Ops)
    elif current_user.role in ['owner', 'admin', 'ops']:
        
        # Fetch all data for the management view
        jobs = Job.query.order_by(Job.created_at.desc()).all()
        vehicles = Vehicle.query.all()
        
        # --- ANALYTICS ENGINE ---
        
        # Calculate totals
        total_rev = sum(j.revenue for j in jobs)
        
        # Use 'final_revenue' if available (for issues), otherwise use standard revenue
        total_realized_revenue = sum((j.final_revenue if j.final_revenue > 0 else j.revenue) for j in jobs)
        total_cost = sum(j.cost_fuel + j.cost_driver for j in jobs)
        total_profit = total_realized_revenue - total_cost

        # Forecasting (Simple projection: Avg job value * 20 working days)
        avg_job_value = total_rev / len(jobs) if len(jobs) > 0 else 0
        forecast_next_month = avg_job_value * 20 
        
        # Operational Stats
        total_jobs_count = len(jobs)
        late_jobs = len([j for j in jobs if j.status == 'Issue']) 
        on_time_rate = round(((total_jobs_count - late_jobs) / total_jobs_count * 100), 1) if total_jobs_count > 0 else 100
        
        # Vehicle Health Logic (Fuel Theft Detection)
        # If fuel cost > 40% of revenue, flag it
        health_alerts = []
        for v in vehicles:
            v_jobs = [j for j in jobs if j.vehicle_id == v.id]
            v_rev = sum(j.revenue for j in v_jobs)
            v_fuel = sum(j.cost_fuel for j in v_jobs)
            
            if v_rev > 0 and (v_fuel / v_rev) > 0.40: 
                health_alerts.append(f"Vehicle {v.reg_number}: High fuel usage ({int((v_fuel/v_rev)*100)}%)")

        # --- PREPARE STATS BASED ON ROLE ---
        
        if current_user.role == 'owner':
            # OWNER SEES MONEY 💰
            stats = {
                'revenue': f"R {total_realized_revenue:,.0f}",
                'profit': f"R {total_profit:,.0f}",
                'margin': f"{(total_profit/total_realized_revenue*100):.1f}%" if total_realized_revenue > 0 else "0%",
                'forecast': f"R {forecast_next_month:,.0f}",
                'alerts': health_alerts
            }
        else:
            # ADMIN/DISPATCHER SEES OPERATIONS 🚚 (Money Hidden)
            stats = {
                'revenue': f"{total_jobs_count}",  # Shows Job Count instead of Money
                'profit': f"{len(vehicles)}",      # Shows Truck Count instead of Profit
                'margin': f"{on_time_rate}%",      # Shows SLA instead of Margin
                'forecast': "Active",              # Placeholder
                'alerts': health_alerts
            }

        # Trend Data for Chart.js (Last 7 Jobs)
        # We calculate profit per job for the chart
        chart_labels = [f"Job #{j.id}" for j in jobs[:7]][::-1]
        chart_data = [(j.final_revenue if j.final_revenue > 0 else j.revenue) - (j.cost_fuel + j.cost_driver) for j in jobs[:7]][::-1]

        return render_template('dashboard_admin.html', 
                               user=current_user, 
                               jobs=jobs, 
                               stats=stats, 
                               chart_labels=chart_labels, 
                               chart_data=chart_data, 
                               vehicles=vehicles)

    # Fallback if something goes wrong
    return redirect(url_for('login'))


@app.route('/admin/assign/<int:driver_id>', methods=['GET', 'POST'])
@login_required
def assign_load(driver_id):
    # 1. Get the Driver we are assigning to
    driver = User.query.get_or_404(driver_id)
    
    if request.method == 'POST':
        # 3. Process the form submission
        job_id = request.form.get('job_id')
        
        if job_id:
            job = Job.query.get(job_id)
            job.driver_id = driver.id
            job.status = 'Assigned' # Update status
            db.session.commit()
            flash(f'Job #{job.id} successfully assigned to {driver.username}!', 'success')
            return redirect(url_for('admin_drivers')) # Go back to fleet list
            
    # 2. Find "Unassigned" Jobs (Jobs with no driver)
    # We look for jobs where driver_id is None OR status is 'Pending'
    available_jobs = Job.query.filter(
        (Job.driver_id == None) | (Job.status == 'Pending')
    ).all()
    
    return render_template('assign_load.html', driver=driver, jobs=available_jobs)
    
# --- PUBLIC CLIENT VISIBILITY ---
@app.route('/track/<int:job_id>')
def public_track(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('track_public.html', job=job)


def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # If user is not the required role (and not an owner, who can see all), kick them out
            if current_user.role != required_role and current_user.role != 'owner':
                flash("⛔ You do not have permission to view this page.", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/admin/drivers')
def admin_drivers():
    drivers = User.query.filter_by(role='driver').all()
    driver_data = []
    
    for driver in drivers:
        # Check for active job
        active_job = Job.query.filter(
            Job.driver_id == driver.id,
            Job.status.in_(['Assigned', 'In Transit', 'Pick-up'])
        ).first()
        
        status = 'Busy' if active_job else 'Available'
        
        # --- THE FIX IS HERE ---
        # If they have a job, get that job's vehicle. If not, show "None"
        current_vehicle = "None"
        if active_job and active_job.vehicle:
            current_vehicle = active_job.vehicle.reg_number
        
        driver_data.append({
            'id': driver.id,
            'name': driver.username,
            'phone': driver.phone,
            'vehicle': current_vehicle, # Now uses the logic above
            'status': status,
            'current_load': active_job.client_name if active_job else "No active load"
        })

    return render_template('drivers_list.html', drivers=driver_data)

# --- FLEET MANAGEMENT ---
@app.route('/vehicles', methods=['GET', 'POST'])
def manage_vehicles():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_v = Vehicle(
            reg_number=request.form['reg'],
            type=request.form['type'],
            base_fuel_rate=float(request.form['rate']),
            status='Active'
        )
        db.session.add(new_v)
        db.session.commit()
        return redirect(url_for('manage_vehicles'))
        
    vehicles = Vehicle.query.all()
    return render_template('vehicles.html', vehicles=vehicles)

@app.route('/create_job', methods=['GET', 'POST'])
def create_job():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    if request.method == 'POST':
        # (Date formatting logic)
        formatted_date = request.form['date'].replace('T', ', ')
        
        # --- SAFE VEHICLE HANDLING (The Fix) ---
        # We use .get() instead of brackets []. This returns None if missing, preventing the crash.
        v_id = request.form.get('vehicle_id') 
        
        new_job = Job(
            client_name=request.form['client'],
            pickup=request.form['pickup'],
            dropoff=request.form['dropoff'],
            due_date=formatted_date,
            driver_id=request.form['driver_id'],
            
            vehicle_id=v_id, # Use the safe variable
            
            # Safely handle numbers too (default to 0.0 if empty)
            revenue=float(request.form.get('revenue', 0)),
            cost_fuel=float(request.form.get('fuel', 0)),
            cost_driver=float(request.form.get('driver_cost', 0)),
            
            status='Assigned'
        )
        db.session.add(new_job)
        db.session.commit()
        return redirect(url_for('dashboard'))

    drivers = User.query.filter_by(role='driver').all()
    vehicles = Vehicle.query.filter_by(status='Active').all()
    return render_template('create_job.html', drivers=drivers, vehicles=vehicles)


# REPLACE 'ey...your_copied_key_here' with the real long text you copied
ors_client = openrouteservice.Client(key='eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImJlZWYxMzlhYjE4ZDQ5MTQ5ZTI5ZThiOTcwMDlkNDQxIiwiaCI6Im11cm11cjY0In0=')

@app.route('/api/optimize-route', methods=['POST'])
def optimize_route():
    data = request.get_json()
    
    # Input: list of coordinates [[lon, lat], [lon, lat], ...]
    # The first one is the Start (Driver location)
    coordinates = data.get('coordinates') 
    
    if not coordinates or len(coordinates) < 2:
        return jsonify({"error": "Need at least 2 locations"}), 400

    # Define the "jobs" (deliveries) and "vehicle" (driver)
    # This is how the VRP (Vehicle Routing Problem) math works
    jobs = []
    for i, coord in enumerate(coordinates[1:]): # Skip the first one (Driver)
        jobs.append({
            "id": i + 1,
            "location": coord,
            "service": 300 # Assume 5 mins (300s) to unload per stop
        })

    vehicle = {
        "id": 1,
        "profile": "driving-car",
        "start": coordinates[0], # Driver starts here
        "end": coordinates[0]    # Driver returns here (remove if not round-trip)
    }

    try:
        # The 'optimization' function solves the math
        optimized = ors_client.optimization(
            jobs=jobs,
            vehicles=[vehicle],
            geometry=True # Gives us the shape to draw on map
        )
        
        # Parse the messy response into something clean for frontend
        routes = optimized['routes'][0]
        
        return jsonify({
            "status": "success",
            "total_distance": routes['distance'], # meters
            "total_duration": routes['duration'], # seconds
            "order": [step['id'] for step in routes['steps'] if step['type'] == 'job'],
            "geometry": routes['geometry'] # Encoded string for the map
        })

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

def get_coordinates(address_text):
    """
    Converts 'Spar Manguzi' into [32.7, -26.9]
    """
    try:
        results = ors_client.geocode(query=address_text)
        # Get the first result's coordinates
        coords = results['features'][0]['geometry']['coordinates']
        return coords # Returns [longitude, latitude]
    except:
        return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            # Check if password matches the Hash OR matches plain text (for old admin accounts)
            if check_password_hash(user.password, password) or user.password == password:
                login_user(user)
                session['user_id'] = user.id
                session['role'] = user.role
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid password', 'danger')
        else:
            flash('User not found', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # THIS IS THE KEY FIX: Properly clear the Flask-Login session
    logout_user()
    session.clear() 
    return redirect(url_for('login'))

import os
from werkzeug.utils import secure_filename

# ... existing imports ...

@app.route('/create_driver', methods=['GET', 'POST'])
@login_required
def create_driver():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        # Check for existing user
        if User.query.filter((User.username==username) | (User.email==email)).first():
            flash('Username or Email already taken.', 'danger')
            return redirect(url_for('create_driver'))

        # --- NEW: IMAGE UPLOAD LOGIC ---
        image_url = '/static/default_avatar.png' # Default if no picture is uploaded
        
        if 'driver_photo' in request.files:
            file = request.files['driver_photo']
            if file and file.filename != '':
                # 1. Create a safe filename
                filename = secure_filename(file.filename)
                # 2. Make it unique (e.g., add username to start)
                new_filename = f"{username}_{filename}"
                # 3. Define the full path
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                # 4. Save the file
                file.save(file_path)
                # 5. Set the URL for the database
                image_url = f"/static/uploads/{new_filename}"
        # --------------------------------

        new_driver = User(
            username=username,
            password=generate_password_hash(password),
            role='driver',
            phone=phone,
            email=email,
            image_url=image_url # <-- Save the path here
        )
        
        db.session.add(new_driver)
        db.session.commit()
        
        # This addresses the "no feedback" issue
        flash('Driver account created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('create_driver.html')

def seed():
    with app.app_context():
        db.create_all()
        if not User.query.first():
            db.session.add(User(username='admin', password='123', role='admin', image_url=''))
            db.session.commit()
            
@app.route('/owner_report')
@login_required
@role_required('owner')
def owner_report():
    """Generates the printable 'Money Report' for the owner."""
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # 1. Fetch Data (e.g., Last 7 Days)
    start_date = datetime.now() - timedelta(days=7)
    jobs = Job.query.filter(Job.created_at >= start_date).all()
    
    # 2. Aggregates
    total_rev = sum(j.revenue for j in jobs)
    total_cost = sum(j.cost_fuel + j.cost_driver for j in jobs)
    net_profit = total_rev - total_cost
    margin = (net_profit / total_rev * 100) if total_rev > 0 else 0
    
    # 3. Driver Performance Analysis
    drivers = User.query.filter_by(role='driver').all()
    driver_stats = []
    for d in drivers:
        d_jobs = [j for j in jobs if j.driver_id == d.id]
        if d_jobs:
            d_rev = sum(j.revenue for j in d_jobs)
            d_profit = sum(j.profit for j in d_jobs)
            driver_stats.append({
                'name': d.username,
                'jobs': len(d_jobs),
                'revenue': d_rev,
                'profit': d_profit,
                'is_problem': d_profit < (d_rev * 0.15) # Flag if driver margin < 15%
            })
            
    return render_template('owner_report.html', 
                         jobs=jobs, 
                         stats={'rev': total_rev, 'cost': total_cost, 'profit': net_profit, 'margin': margin},
                         driver_stats=driver_stats,
                         date_range="Last 7 Days")

# --- MISSING JOB DETAILS ROUTE ---
@app.route('/job_details/<int:job_id>')
def job_details(job_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # Get the job or show 404 if not found
    job = Job.query.get_or_404(job_id)
    
    return render_template('job_details.html', job=job)

@app.route('/update_job/<int:job_id>', methods=['GET', 'POST'])
def update_job(job_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    job = Job.query.get_or_404(job_id)
    
    if request.method == 'POST':
        # 1. Update Status & Notes
        job.status = request.form.get('status')
        job.driver_note = request.form.get('note')
        
        # 2. SAVE GPS COORDINATES (New Feature)
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        if lat and lng:
            try:
                job.current_lat = float(lat)
                job.current_lng = float(lng)
            except ValueError:
                pass # Ignore if GPS data is corrupt

        # 3. Update Driver (Admin Override)
        new_driver_id = request.form.get('driver_id')
        if new_driver_id:
            job.driver_id = int(new_driver_id)
            
        # 4. Update Vehicle (Admin Override)
        new_vehicle_id = request.form.get('vehicle_id')
        if new_vehicle_id:
            job.vehicle_id = int(new_vehicle_id)

        # 5. Handle POD Upload
        if 'pod_photo' in request.files:
            file = request.files['pod_photo']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                
                # Create uploads folder if not exists
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                    
                new_filename = f"pod_{job.id}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                job.pod_image_url = f"/static/uploads/{new_filename}"
                
        db.session.commit()
        return redirect(url_for('dashboard'))

    # Load list of drivers and vehicles so we can show them in the dropdown
    drivers = User.query.filter_by(role='driver').all()
    vehicles = Vehicle.query.filter_by(status='Active').all()
    
    return render_template('update_job.html', job=job, drivers=drivers, vehicles=vehicles)                        
if __name__ == '__main__':
    seed()
    app.run(debug=True, port=5001)