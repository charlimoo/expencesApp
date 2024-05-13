from flask import Flask, request, jsonify, render_template, redirect, url_for
import sqlite3
from datetime import datetime
import Levenshtein

app = Flask(__name__)

# Create connection and cursor
conn = sqlite3.connect('expenses.db', check_same_thread=False)
c = conn.cursor()

# Create table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS expenses (
             id INTEGER PRIMARY KEY,
             user_id INTEGER,
             category TEXT,
             amount REAL,
             description TEXT,
             date DATE
             )''')
conn.commit()

# Function to add expense
@app.route('/add_expense', methods=['POST'])
def add_expense():
    data = request.json
    user_id = data.get('user_id')
    category = data.get('category')
    amount = data.get('amount')
    description = data.get('description')
    date = data.get('date', datetime.now().date())

    c.execute('''INSERT INTO expenses (user_id, category, amount, description, date)
                 VALUES (?, ?, ?, ?, ?)''', (user_id, category, amount, description, date))
    conn.commit()

    return jsonify({"message": "Expense added successfully"}), 200

# Function to retrieve expenses
@app.route('/get_expenses/<int:user_id>', methods=['GET'])
def get_expenses(user_id):
    c.execute('''SELECT * FROM expenses WHERE user_id = ?''', (user_id,))
    expenses = c.fetchall()

    return jsonify({"expenses": expenses}), 200

# Function to calculate expenses in a time frame or for a specific category
@app.route('/calculate_expenses', methods=['GET'])
def calculate_expenses():
    user_id = request.args.get('user_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')

    query = '''SELECT category, SUM(amount) FROM expenses WHERE user_id = ?'''
    params = [user_id]

    if start_date:
        query += ' AND date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND date <= ?'
        params.append(end_date)
    if category:
        query += ' AND category = ?'
        params.append(category)

    query += ' GROUP BY category'

    c.execute(query, params)
    expenses = c.fetchall()

    return jsonify({"expenses": expenses}), 200

# Function to get the highest expended category with its amount
@app.route('/get_highest_expense/<int:user_id>', methods=['GET'])
def get_highest_expense(user_id):
    c.execute('''SELECT category, SUM(amount) FROM expenses WHERE user_id = ? GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1''', (user_id,))
    highest_expense = c.fetchone()

    return jsonify({"highest_expense": highest_expense}), 200

# Function to modify a specific expense
@app.route('/modify_expense/<int:expense_id>', methods=['PUT'])
def modify_expense(expense_id):
    data = request.json
    amount = data.get('amount')
    category = data.get('category')
    description = data.get('description')
    date = data.get('date')

    updates = []
    params = []

    if amount is not None:
        updates.append('amount = ?')
        params.append(amount)
    if category:
        updates.append('category = ?')
        params.append(category)
    if description:
        updates.append('description = ?')
        params.append(description)
    if date:
        updates.append('date = ?')
        params.append(date)

    params.append(expense_id)

    query = '''UPDATE expenses SET {} WHERE id = ?'''.format(', '.join(updates))
    c.execute(query, params)
    conn.commit()

    return jsonify({"message": "Expense modified successfully"}), 200

# Function to get all expenses ordered by date
def get_all_expenses_ordered_by_date():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM expenses ORDER BY date DESC''')
    expenses = c.fetchall()
    conn.close()
    return expenses

# Function to add expense
def add_expense(user_id, category, amount, description='', date=None):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''INSERT INTO expenses (user_id, category, amount, description, date)
                 VALUES (?, ?, ?, ?, ?)''', (user_id, category, amount, description, date))
    conn.commit()
    conn.close()

# Function to modify expense
def modify_expense(expense_id, amount=None, category=None, description=None, date=None):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    updates = []
    params = []

    if amount is not None:
        updates.append('amount = ?')
        params.append(amount)
    if category:
        updates.append('category = ?')
        params.append(category)
    if description:
        updates.append('description = ?')
        params.append(description)
    if date:
        updates.append('date = ?')
        params.append(date)

    params.append(expense_id)

    query = '''UPDATE expenses SET {} WHERE id = ?'''.format(', '.join(updates))
    c.execute(query, params)
    conn.commit()
    conn.close()

# Function to search description and find the closest match
@app.route('/search_description', methods=['GET'])
def search_description():
    search_term = request.args.get('description')
    user_id = request.args.get('user_id')
    
    if not search_term:
        return jsonify({"error": "Description search term is required"}), 400
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    c.execute('''SELECT id, description FROM expenses WHERE user_id = ?''', (user_id,))
    expenses = c.fetchall()

    closest_match = None
    closest_distance = float('inf')

    for expense_id, description in expenses:
        distance = Levenshtein.distance(search_term, description)
        if distance < closest_distance:
            closest_distance = distance
            closest_match = expense_id
        elif distance == closest_distance:
            # If distance is same, select the one with higher ID (most recent)
            if expense_id > closest_match:
                closest_match = expense_id

    if closest_match is None:
        return jsonify({"message": "No matching description found"}), 404

    return jsonify({"closest_match_id": closest_match}), 200


# Admin route to display all expenses in timely order and handle form submissions
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    user_id = request.args.get('user_id')

    if request.method == 'POST':
        if request.form['action'] == 'add_expense':
            user_id = request.form['user_id']
            category = request.form['category']
            amount = request.form['amount']
            description = request.form['description']
            date = request.form['date']
            add_expense(user_id, category, amount, description, date)
        elif request.form['action'] == 'modify_expense':
            expense_id = request.form['expense_id']
            amount = request.form['new_amount']
            category = request.form['new_category']
            description = request.form['new_description']
            date = request.form['new_date']
            modify_expense(expense_id, amount, category, description, date)
        return redirect(url_for('admin_panel', user_id=user_id))

    expenses = get_all_expenses_ordered_by_date()
    return render_template('admin_panel.html', expenses=expenses, user_id=user_id)




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)