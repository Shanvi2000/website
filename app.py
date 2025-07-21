from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('website_layout.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/appointment')
def appointment():
    return render_template('services.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)