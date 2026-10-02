from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import requests

app = Flask(__name__)
app.secret_key = "secret123"

# Alpha Vantage API Key
API_KEY = "YOUR_ALPHA_VANTAGE_API_KEY"

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Home -> Dashboard
@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')
    return redirect('/dashboard')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error="Username already exists!")
        conn.close()
        return redirect('/login')

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['user'] = user['username']
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return render_template('dashboard.html', user=session['user'])

# Recommendation AI Model
@app.route('/recommend', methods=['POST'])
def recommend():
    if 'user' not in session:
        return redirect('/login')

    income = int(request.form['income'])
    risk = request.form['risk']
    duration = request.form['duration']
    goal = request.form['goal']

    # Income score
    if income < 20000:
        income_score = 20
    elif income < 50000:
        income_score = 50
    else:
        income_score = 80

    # Risk score
    if risk == "Low":
        risk_score = 30
    elif risk == "Medium":
        risk_score = 60
    else:
        risk_score = 90

    # Duration score
    if duration == "Short Term":
        duration_score = 30
    else:
        duration_score = 70

    # Goal score
    goal_lower = goal.lower()
    if "retirement" in goal_lower:
        goal_score = 80
    elif "wealth" in goal_lower:
        goal_score = 70
    elif "saving" in goal_lower:
        goal_score = 50
    else:
        goal_score = 40

    # Final AI score
    final_score = (income_score + risk_score + duration_score + goal_score) / 4

    # Recommendation based on AI score
    if final_score <= 40:
        recommendation = "Fixed Deposit + SIP + Debt Mutual Funds"
        expected_return = "6% - 8%"
    elif final_score <= 65:
        recommendation = "Index Funds + Blue Chip Stocks + Mutual Funds"
        expected_return = "10% - 14%"
    else:
        recommendation = "Mid Cap / Small Cap Stocks + ETFs + Growth Funds"
        expected_return = "15% - 22%"

    conn = get_db()
    conn.execute("""
        INSERT INTO recommendations
        (username, income, risk, duration, goal, recommendation, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session['user'],
        income,
        risk,
        duration,
        goal,
        recommendation,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

    return render_template(
        'result.html',
        user=session['user'],
        recommendation=recommendation,
        risk_score=int(final_score),
        expected_return=expected_return
    )
# History
@app.route('/history')
def history():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()
    rows = conn.execute("""
        SELECT income, risk, duration, goal, recommendation, created_at
        FROM recommendations
        WHERE username=?
        ORDER BY id DESC
    """, (session['user'],)).fetchall()
    conn.close()

    return render_template('history.html', user=session['user'], rows=rows)

# Portfolio Calculator
@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    if 'user' not in session:
        return redirect('/login')

    result = None

    if request.method == 'POST':
        principal = float(request.form['principal'])
        monthly = float(request.form['monthly'])
        years = int(request.form['years'])
        annual_rate = float(request.form['annual_rate'])

        r = (annual_rate / 100) / 12
        n = years * 12

        if r != 0:
            fv_principal = principal * ((1 + r) ** n)
            fv_monthly = monthly * (((1 + r) ** n - 1) / r) * (1 + r)
        else:
            fv_principal = principal
            fv_monthly = monthly * n

        total = fv_principal + fv_monthly
        invested = principal + (monthly * n)
        profit = total - invested

        result = {
            'invested': round(invested, 2),
            'future_value': round(total, 2),
            'profit': round(profit, 2)
        }

    return render_template('calculator.html', user=session['user'], result=result)

# Profile
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()
    user = conn.execute("""
        SELECT username, email
        FROM users
        WHERE username=?
    """, (session['user'],)).fetchone()
    conn.close()

    return render_template('profile.html', user=user)

# Live Stock Price
@app.route('/live-stock', methods=['GET', 'POST'])
def live_stock():
    if 'user' not in session:
        return redirect('/login')

    stock = None
    error = None

    if request.method == 'POST':
        symbol = request.form['symbol'].strip().upper()

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": API_KEY
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            quote = data.get("Global Quote", {})

            if quote and quote.get("05. price"):
                stock = {
                    "symbol": quote.get("01. symbol"),
                    "open": quote.get("02. open"),
                    "high": quote.get("03. high"),
                    "low": quote.get("04. low"),
                    "price": quote.get("05. price"),
                    "volume": quote.get("06. volume"),
                    "latest_day": quote.get("07. latest trading day"),
                    "previous_close": quote.get("08. previous close"),
                    "change": quote.get("09. change"),
                    "change_percent": quote.get("10. change percent")
                }
            else:
                error = "Stock data not found. Please enter a valid stock symbol."
        except Exception as e:
            error = f"Error fetching stock data: {str(e)}"

    return render_template('live_stock.html', user=session['user'], stock=stock, error=error)

if __name__ == '__main__':
    app.run(debug=True)