from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import sqlite3
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key in production

# Add template filters
@app.template_filter('now')
def _now(format_='%Y'):
    return datetime.now().strftime(format_)

# Database setup
def get_db_connection():
    conn = sqlite3.connect('website.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create appointments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        meeting_type TEXT NOT NULL,
        message TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create contact messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contact_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create admin user table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Check if admin user exists, if not create default admin
    cursor.execute("SELECT * FROM admin_users WHERE username = 'admin'")
    if not cursor.fetchone():
        password_hash = generate_password_hash('admin123')
        cursor.execute("INSERT INTO admin_users (username, password_hash, email) VALUES (?, ?, ?)",
                      ('admin', password_hash, 'admin@example.com'))
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Helper function to send email
def send_email(recipient, subject, body):
    # Get email configuration
    sender_email = "your_email@example.com"  # Update with your actual email
    sender_password = "your_app_password"    # Update with your app password
    
    # Skip sending email if in development mode without credentials
    if sender_email == 'your_email@example.com':
        print("Email sending skipped - no credentials provided")
        print(f"Would send to: {recipient}")
        print(f"Subject: {subject}")
        print(f"Body: {body[:100]}...")  # Print just the start of the body
        return True
    
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient
    message["Subject"] = subject
    
    message.attach(MIMEText(body, "html"))
    
    try:
        # For Gmail, you might need to enable "Less secure app access"
        # or use app-specific passwords
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# Routes
@app.route('/')
def home():
    return render_template('website_layout.html', now=datetime.now())

@app.route('/about')
def about():
    return render_template('about.html', now=datetime.now())

@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        date = request.form['date']
        time = request.form['time']
        meeting_type = request.form['meeting-type']
        message = request.form['message']
        
        # Save to database
        conn = get_db_connection()
        conn.execute('INSERT INTO appointments (name, email, phone, date, time, meeting_type, message) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (name, email, phone, date, time, meeting_type, message))
        conn.commit()
        conn.close()
        
        # Send confirmation email to user
        email_subject = "Appointment Request Confirmation"
        email_body = f"""
        <html>
        <body>
            <h2>Thank you for your appointment request!</h2>
            <p>We have received your request for a {meeting_type} on {date} at {time}.</p>
            <p>We will review your request and get back to you shortly to confirm.</p>
            <p>Your appointment details:</p>
            <ul>
                <li><strong>Name:</strong> {name}</li>
                <li><strong>Email:</strong> {email}</li>
                <li><strong>Phone:</strong> {phone}</li>
                <li><strong>Date:</strong> {date}</li>
                <li><strong>Time:</strong> {time}</li>
                <li><strong>Meeting Type:</strong> {meeting_type}</li>
            </ul>
            <p>If you need to make any changes, please contact us.</p>
            <p>Best regards,<br>Your Name</p>
        </body>
        </html>
        """
        send_email(email, email_subject, email_body)
        
        # Send notification to admin
        admin_email = "your_email@example.com"  # Update with your actual email
        admin_subject = "New Appointment Request"
        admin_body = f"""
        <html>
        <body>
            <h2>New Appointment Request</h2>
            <p>A new appointment request has been submitted:</p>
            <ul>
                <li><strong>Name:</strong> {name}</li>
                <li><strong>Email:</strong> {email}</li>
                <li><strong>Phone:</strong> {phone}</li>
                <li><strong>Date:</strong> {date}</li>
                <li><strong>Time:</strong> {time}</li>
                <li><strong>Meeting Type:</strong> {meeting_type}</li>
                <li><strong>Message:</strong> {message}</li>
            </ul>
            <p>Please log in to the admin dashboard to manage this request.</p>
        </body>
        </html>
        """
        send_email(admin_email, admin_subject, admin_body)
        
        flash('Your appointment request has been submitted successfully! We will contact you shortly to confirm.', 'success')
        return redirect(url_for('appointment'))
        
    return render_template('services.html', now=datetime.now())  # The appointment page is named services.html

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        
        # Save to database
        conn = get_db_connection()
        conn.execute('INSERT INTO contact_messages (name, email, subject, message) VALUES (?, ?, ?, ?)',
                    (name, email, subject, message))
        conn.commit()
        conn.close()
        
        # Send confirmation email to user
        email_subject = "Contact Form Submission Confirmation"
        email_body = f"""
        <html>
        <body>
            <h2>Thank you for contacting us!</h2>
            <p>We have received your message and will get back to you as soon as possible.</p>
            <p>Your message details:</p>
            <ul>
                <li><strong>Name:</strong> {name}</li>
                <li><strong>Email:</strong> {email}</li>
                <li><strong>Subject:</strong> {subject}</li>
                <li><strong>Message:</strong> {message}</li>
            </ul>
            <p>Best regards,<br>Your Name</p>
        </body>
        </html>
        """
        send_email(email, email_subject, email_body)
        
        # Send notification to admin
        admin_email = "your_email@example.com"  # Update with your actual email
        admin_subject = "New Contact Form Submission"
        admin_body = f"""
        <html>
        <body>
            <h2>New Contact Form Submission</h2>
            <p>A new message has been submitted through the contact form:</p>
            <ul>
                <li><strong>Name:</strong> {name}</li>
                <li><strong>Email:</strong> {email}</li>
                <li><strong>Subject:</strong> {subject}</li>
                <li><strong>Message:</strong> {message}</li>
            </ul>
        </body>
        </html>
        """
        send_email(admin_email, admin_subject, admin_body)
        
        flash('Your message has been sent successfully! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
        
    return render_template('contact.html', now=datetime.now())

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM admin_users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            # In a real application, you would use Flask-Login to handle sessions
            flash('You have been logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
    
    return render_template('admin_login.html', now=datetime.now())

@app.route('/admin/dashboard')
def admin_dashboard():
    # In a real application, you would check if the user is logged in
    
    conn = get_db_connection()
    appointments = conn.execute('SELECT * FROM appointments ORDER BY date DESC').fetchall()
    messages = conn.execute('SELECT * FROM contact_messages ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return render_template('admin_dashboard.html', appointments=appointments, messages=messages, now=datetime.now())

@app.route('/admin/appointment/<int:id>', methods=['GET', 'POST'])
def admin_appointment(id):
    conn = get_db_connection()
    appointment = conn.execute('SELECT * FROM appointments WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        status = request.form['status']
        conn.execute('UPDATE appointments SET status = ? WHERE id = ?', (status, id))
        conn.commit()
        
        # Send email notification to user about status change
        if appointment:
            email = appointment['email']
            name = appointment['name']
            date = appointment['date']
            time = appointment['time']
            
            email_subject = f"Appointment Status Update: {status.capitalize()}"
            email_body = f"""
            <html>
            <body>
                <h2>Appointment Status Update</h2>
                <p>Dear {name},</p>
                <p>Your appointment scheduled for {date} at {time} has been <strong>{status}</strong>.</p>
                <p>If you have any questions, please contact us.</p>
                <p>Best regards,<br>Your Name</p>
            </body>
            </html>
            """
            send_email(email, email_subject, email_body)
        
        flash(f'Appointment status updated to {status}.', 'success')
        return redirect(url_for('admin_dashboard'))
    
    conn.close()
    return render_template('admin_appointment.html', appointment=appointment, now=datetime.now())

# API routes
@app.route('/api/appointments', methods=['GET'])
def api_appointments():
    conn = get_db_connection()
    appointments = conn.execute('SELECT id, name, date, time, status FROM appointments ORDER BY date DESC').fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    result = []
    for appointment in appointments:
        result.append({
            'id': appointment['id'],
            'name': appointment['name'],
            'date': appointment['date'],
            'time': appointment['time'],
            'status': appointment['status']
        })
    
    return jsonify({'appointments': result})

if __name__ == '__main__':
    app.run(debug=True) 