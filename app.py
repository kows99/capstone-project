from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import time
import random
import json
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

feedback_count = 0

app = Flask(__name__)
app.secret_key = 'cinemapulse-redblack-2026-secret-key-change-this!'

users_db = []  
feedback_db = []

MOVIES = [
    {'id': 1, 'title': 'Blood Moon Rising', 'genre': 'Horror' , 'image_url': 'static/images/BMR.jpg'},
    {'id': 2, 'title': 'Crimson Vendetta', 'genre': 'Action' , 'image_url': 'static/images/cv.jpg'},
    {'id': 3, 'title': 'Scarlet Shadows', 'genre': 'Thriller' , 'image_url': 'static/images/ss.jpg'},
    {'id': 4, 'title': 'Red Fury', 'genre': 'Drama' , 'image_url': 'static/images/red fury.jpg'},
    {'id': 5, 'title': 'City Of Ember', 'genre': 'Adventure', 'image_url': 'static/images/city of ember.jpg'},
    {'id': 6, 'title': 'Dragon', 'genre': 'Romantic action/drama' , 'image_url': 'static/images/dragon.jpeg'},
    {'id': 7, 'title': 'Jailer','genre': 'Action Thriller', 'image_url': 'static/images/jailer.jpg'},
    {'id': 8, 'title': 'Good Bad Ugly','genre': 'Action', 'image_url': 'static/images/good bad ugly.jpg'},
    {'id': 9, 'title': 'Madharaasi','genre': 'Drama', 'image_url': 'static/images/madharaasi.jpg'},
    {'id': 10, 'title': 'Tourist Family','genre': 'Family comedy/drama', 'image_url': 'static/images/tourist family.jpg'},
    {'id': 11, 'title': 'Retro','genre': 'Romantic action', 'image_url': 'static/images/Retro.jpg'},
    {'id': 12, 'title': 'Nesippaya','genre': 'Romantic thriller', 'image_url': 'static/images/nesipaaya.jpg'},
    {'id': 13, 'title': 'Kudumbasthan','genre': 'Drama' ,'image_url': 'static/images/kudumbasthan.jpg'},         
    {'id': 14, 'title': 'Sweetheart','genre': 'Romance', 'image_url': 'static/images/sweet heart.jpg'},
    {'id': 15, 'title': 'Sirai', 'genre': 'Crime Drama', 'image_url': 'static/images/sirai.jpg'}, 
    {'id': 16, 'title': 'Bottle Radha','genre':'Drama', 'image_url':'static/images/bottle radha.jpg'},
    {'id': 17,	'title':'Gothavari','genre':'Romantic drama', 'image_url':'static/images/godavari.jpg'},
    {'id': 18,	'title':'Anand','genre':'Romantic drama', 'image_url':'static/images/anand.jpg'}
    
]

analyzer = SentimentIntensityAnalyzer()
FEEDBACK_FILE = 'feedbacks.json'

def load_feedbacks():
    try:
        with open(FEEDBACK_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_feedback(movie_title, rating, review, username):
    sentiment = analyzer.polarity_scores(review)
    feedback = {
        'movie': movie_title, 'rating': int(rating), 'review': review,
        'user': username, 
        'sentiment': 'positive' if sentiment['compound'] >= 0.05 else 'neutral' if sentiment['compound'] > -0.05 else 'negative',
        'time': datetime.now().isoformat()
    }
    feedbacks = load_feedbacks()
    feedbacks.append(feedback)
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(feedbacks, f, indent=2)
    return feedback
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')

        users = load_users()

        # Check duplicate username
        for user in users:
            if user['username'] == username:
                flash('❌ Username already exists!')
                return render_template('register.html')

            if user['email'] == email:
                flash('❌ Email already registered!')
                return render_template('register.html')

        new_user = {
            'username': username,
            'email': email,
            'signup_date': datetime.now().isoformat()
        }

        users.append(new_user)
        save_users(users)

        flash('✅ Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')


def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=2)

@app.route('/')
def home():
    return render_template('home.html')  # Landing page with Register/Login links

@app.route('/movies')
def movies():
    if 'username' not in session:
        return redirect(url_for('login'))  # ✅ CHANGED FROM 'home'
    return render_template('movies.html', movies=MOVIES, feedback_count=feedback_count())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        # ✅ LOCAL JSON verification
        users = load_users()
        for user in users:
            if user['username'] == username and user['email'] == email:
                session['username'] = username
                flash('✅ Login successful!')
                return redirect(url_for('movies'))
        
        flash('❌ Invalid credentials!')
    
    return render_template('login.html')



@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))  # ✅ Changed from 'home'

    
    feedbacks = load_feedbacks()
    total_feedback = len(feedbacks) 
    
    # Sentiment analysis
    sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
    for fb in feedbacks:
        sentiments[fb.get('sentiment', 'neutral')] += 1
    
    rating = session.get('rating', 0)
    review = session.get('review', '')
    movie = session.get('selected_movie', 'No movie')
    
    return render_template('dashboard.html',
                         rating=rating, review=review, movie=movie,
                         total_feedback=total_feedback, 
                         sentiments=sentiments,
                         feedbacks=feedbacks[-10:]) 

@app.route('/feedback/<int:movie_id>', methods=['GET', 'POST'])
def feedback(movie_id):
    global feedback_count  
    
    if request.method == 'POST':
        feedback = save_feedback(
            MOVIES[movie_id-1]['title'],
            request.form['rating'],
            request.form['review'],
            session.get('username', 'Anonymous')
        )
        feedback_count += 1 
        session['rating'] = feedback['rating']
        session['review'] = feedback['review']
        session['selected_movie'] = feedback['movie']
        flash(f'✅ {feedback["movie"]}: {feedback["rating"]}⭐ | {feedback["sentiment"].upper()} | Total: {feedback_count}')
        return redirect(url_for('dashboard'))
    
    if 'username' not in session:
        return redirect(url_for('login'))
    movie = MOVIES[movie_id-1]
    return render_template('feedback.html', movie=movie)

@app.route('/analysis')
def analysis():
    if 'username' not in session:
        return redirect(url_for('login'))
    feedbacks = load_feedbacks()
    sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
    total_feedbacks = len(feedbacks)
    average_rating = round(sum(fb['rating'] for fb in feedbacks) / total_feedbacks, 1) if total_feedbacks > 0 else 0
    for fb in feedbacks:
        sentiments[fb.get('sentiment', 'neutral')] += 1
    
    return render_template('analysis.html',
                         rating=session.get('rating', 0),
                         review=session.get('review', 'No review yet'),
                         movie=session.get('selected_movie', 'No movie'),
                         sentiments=sentiments,
                         total_feedbacks=total_feedbacks,
                         average_rating=average_rating)


@app.route('/thankyou')
def thank_you(): 
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('thankyou.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
