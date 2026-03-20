from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
import uuid
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'secret-key')

# ---------------- AWS CONFIG ----------------
REGION = 'us-east-1'
dynamodb = boto3.resource('dynamodb', region_name=REGION)

users_table = dynamodb.Table('Users')
feedbacks_table = dynamodb.Table('Feedbacks')

analyzer = SentimentIntensityAnalyzer()

# ---------------- MOVIES (FULL LIST) ----------------
MOVIES = [
    {'id': 1, 'title': 'Blood Moon Rising', 'genre': 'Horror', 'image_url': 'static/images/BMR.jpg'},
    {'id': 2, 'title': 'Crimson Vendetta', 'genre': 'Action', 'image_url': 'static/images/cv.jpg'},
    {'id': 3, 'title': 'Scarlet Shadows', 'genre': 'Thriller', 'image_url': 'static/images/ss.jpg'},
    {'id': 4, 'title': 'Red Fury', 'genre': 'Drama', 'image_url': 'static/images/red fury.jpg'},
    {'id': 5, 'title': 'City Of Ember', 'genre': 'Adventure', 'image_url': 'static/images/city of ember.jpg'},
    {'id': 6, 'title': 'Dragon', 'genre': 'Romantic action/drama', 'image_url': 'static/images/dragon.jpeg'},
    {'id': 7, 'title': 'Jailer','genre': 'Action Thriller', 'image_url': 'static/images/jailer.jpg'},
    {'id': 8, 'title': 'Good Bad Ugly','genre': 'Action', 'image_url': 'static/images/good bad ugly.jpg'},
    {'id': 9, 'title': 'Madharaasi','genre': 'Drama', 'image_url': 'static/images/madharaasi.jpg'},
    {'id': 10, 'title': 'Tourist Family','genre': 'Family comedy/drama', 'image_url': 'static/images/tourist family.jpg'},
    {'id': 11, 'title': 'Retro','genre': 'Romantic action', 'image_url': 'static/images/Retro.jpg'},
    {'id': 12, 'title': 'Nesippaya','genre': 'Romantic thriller', 'image_url': 'static/images/nesipaaya.jpg'},
    {'id': 13, 'title': 'Kudumbasthan','genre': 'Drama','image_url': 'static/images/kudumbasthan.jpg'},         
    {'id': 14, 'title': 'Sweetheart','genre': 'Romance', 'image_url': 'static/images/sweet heart.jpg'},
    {'id': 15, 'title': 'Sirai', 'genre': 'Crime Drama', 'image_url': 'static/images/sirai.jpg'}, 
    {'id': 16, 'title': 'Bottle Radha','genre':'Drama', 'image_url':'static/images/bottle radha.jpg'},
    {'id': 17, 'title':'Gothavari','genre':'Romantic drama', 'image_url':'static/images/godavari.jpg'},
    {'id': 18, 'title':'Anand','genre':'Romantic drama', 'image_url':'static/images/anand.jpg'},
]

# ---------------- AUTH ----------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check duplicate email
        response = users_table.scan(
            FilterExpression="email = :e",
            ExpressionAttributeValues={":e": email}
        )

        if response['Items']:
            flash('❌ Email already registered!')
            return render_template('register.html')

        users_table.put_item(Item={
            'username': username,
            'email': email,
            'password': password,
            'created_at': datetime.now().isoformat()
        })

        flash('✅ Registered successfully!')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        response = users_table.scan(
            FilterExpression="email = :e",
            ExpressionAttributeValues={":e": email}
        )

        if response['Items']:
            user = response['Items'][0]

            if user.get('password') == password:
                session['username'] = user['username']
                session['email'] = user['email']
                return redirect(url_for('movies'))

        flash('❌ Invalid email or password!')
        return render_template('login.html')

    return render_template('login.html')


@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('password')

        response = users_table.scan(
            FilterExpression="email = :e",
            ExpressionAttributeValues={":e": email}
        )

        if not response['Items']:
            flash('❌ Email not found!')
            return redirect(url_for('forgot'))

        user = response['Items'][0]

        users_table.update_item(
            Key={'username': user['username']},
            UpdateExpression="SET password = :p",
            ExpressionAttributeValues={':p': new_password}
        )

        flash('✅ Password updated!')
        return redirect(url_for('login'))

    return render_template('forgot.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully')
    return redirect(url_for('login'))


# ---------------- MOVIES ----------------

@app.route('/movies')
def movies():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('movies.html', movies=MOVIES)


# ---------------- FEEDBACK ----------------

def add_feedback(movie_id, movie_title, rating, review, username):
    sentiment = analyzer.polarity_scores(review)
    sentiment_label = 'positive' if sentiment['compound'] >= 0.05 else 'neutral' if sentiment['compound'] > -0.05 else 'negative'

    feedbacks_table.put_item(Item={
        'id': str(uuid.uuid4()),
        'movie_id': movie_id,
        'movie_title': movie_title,
        'rating': int(rating),
        'review': review,
        'username': username,
        'sentiment': sentiment_label,
        'created_at': datetime.now().isoformat()
    })

    return sentiment_label


@app.route('/feedback/<int:movie_id>', methods=['GET', 'POST'])
def feedback(movie_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    movie = next((m for m in MOVIES if m['id'] == movie_id), None)

    if request.method == 'POST':
        rating = request.form.get('rating')
        review = request.form.get('review')

        sentiment = add_feedback(
            movie_id,
            movie['title'],
            rating,
            review,
            session['username']
        )

        flash(f'✅ Feedback submitted! Sentiment: {sentiment}')
        return redirect(url_for('movies'))

    return render_template('feedback.html', movie=movie)


# ---------------- OTHER ----------------

@app.route('/about')
def about():
    return render_template('about.html')


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
