from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# In-memory database (dictionary)
users = {}


@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users:
            return "User already exists!"
        
        users[username] = password
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('home'))
        return "Invalid credentials!"
    return render_template('login.html')

@app.route('/home')
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/movies')
def select_movie():
    return render_template('movies.html')

@app.route('/feedback/<movie>', methods=['GET', 'POST'])
def feedback(movie):
    if request.method == 'POST':
        review = request.form['review']
        rating = request.form['rating']

        # For now just print (later store in DB / CSV)
        print(movie, review, rating)

        return redirect(url_for('dashboard'))

    return render_template('feedback.html', movie=movie)

@app.route('/analysis')
def view_analysis():
    return render_template('analysis.html')

if __name__ == '__main__':
    app.run(debug=True, port=8000)