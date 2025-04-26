from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"


def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',  
        password='puneetha@1204',  
        database='StockManagement1'
    )
    return connection

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/users')
def users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM Users')
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_users.html', users=users)

@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    city = request.form['city']
    created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO Users (name, email, phone, city, created_at) VALUES (%s, %s, %s, %s, %s)',
                      (name, email, phone, city, created_at))
        conn.commit()
        flash('User added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('users'))


@app.route('/stocks')
def stocks():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM Stocks')
    stocks = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('stocks.html', stocks=stocks)

@app.route('/add_stock', methods=['POST'])
def add_stock():
    symbol = request.form['symbol']
    company_name = request.form['company_name']
    sector = request.form['sector']
    current_price = request.form['current_price']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO Stocks (symbol, company_name, sector, current_price) VALUES (%s, %s, %s, %s)',
                      (symbol, company_name, sector, current_price))
        conn.commit()
        flash('Stock added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('stocks'))


@app.route('/transactions')
def transactions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT t.*, u.name as user_name, s.symbol, b.name as broker_name 
        FROM Transactions t
        JOIN Users u ON t.user_id = u.user_id
        JOIN Stocks s ON t.stock_id = s.stock_id
        LEFT JOIN Brokers b ON t.broker_id = b.broker_id
    ''')
    transactions = cursor.fetchall()
    
    cursor.execute('SELECT * FROM Users')
    users = cursor.fetchall()
    
    cursor.execute('SELECT * FROM Stocks')
    stocks = cursor.fetchall()
    
    cursor.execute('SELECT * FROM Brokers')
    brokers = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('transactions.html', transactions=transactions, 
                          users=users, stocks=stocks, brokers=brokers)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    user_id = request.form['user_id']
    stock_id = request.form['stock_id']
    broker_id = request.form['broker_id']
    transaction_type = request.form['transaction_type']
    quantity = request.form['quantity']
    price = request.form['price']
    transaction_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO Transactions 
            (user_id, stock_id, broker_id, transaction_type, quantity, price, transaction_date) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, stock_id, broker_id, transaction_type, quantity, price, transaction_date))
        
       
        if transaction_type == 'BUY':
            
            cursor.execute('SELECT * FROM Portfolio_Holdings WHERE user_id = %s AND stock_id = %s', 
                          (user_id, stock_id))
            holding = cursor.fetchone()
            
            if holding:
                
                cursor.execute('''
                    UPDATE Portfolio_Holdings 
                    SET quantity = quantity + %s 
                    WHERE user_id = %s AND stock_id = %s
                ''', (quantity, user_id, stock_id))
            else:
                
                cursor.execute('''
                    INSERT INTO Portfolio_Holdings 
                    (user_id, stock_id, quantity, purchase_date) 
                    VALUES (%s, %s, %s, %s)
                ''', (user_id, stock_id, quantity, transaction_date))
        
        elif transaction_type == 'SELL':
            
            cursor.execute('''
                UPDATE Portfolio_Holdings 
                SET quantity = quantity - %s 
                WHERE user_id = %s AND stock_id = %s
            ''', (quantity, user_id, stock_id))
            
            
            cursor.execute('''
                DELETE FROM Portfolio_Holdings 
                WHERE user_id = %s AND stock_id = %s AND quantity <= 0
            ''', (user_id, stock_id))
        
        conn.commit()
        flash('Transaction recorded successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('transactions'))


@app.route('/portfolio')
def portfolio():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT p.*, u.name as user_name, s.symbol, s.company_name, s.current_price,
               (s.current_price * p.quantity) as total_value
        FROM Portfolio_Holdings p
        JOIN Users u ON p.user_id = u.user_id
        JOIN Stocks s ON p.stock_id = s.stock_id
    ''')
    holdings = cursor.fetchall()
    
    cursor.execute('SELECT * FROM Users')
    users = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('portfolio.html', holdings=holdings, users=users)


@app.route('/brokers')
def brokers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM Brokers')
    brokers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('brokers.html', brokers=brokers)

@app.route('/add_broker', methods=['POST'])
def add_broker():
    name = request.form['name']
    commission_rate = request.form['commission_rate']
    contact_email = request.form['contact_email']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO Brokers (name, commission_rate, contact_email) VALUES (%s, %s, %s)',
                      (name, commission_rate, contact_email))
        conn.commit()
        flash('Broker added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('brokers'))


@app.route('/watchlist')
def watchlist():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT w.*, u.name as user_name, s.symbol, s.company_name, s.current_price
        FROM Watchlist w
        JOIN Users u ON w.user_id = u.user_id
        JOIN Stocks s ON w.stock_id = s.stock_id
    ''')
    watchlist = cursor.fetchall()
    
    cursor.execute('SELECT * FROM Users')
    users = cursor.fetchall()
    
    cursor.execute('SELECT * FROM Stocks')
    stocks = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('watchlist.html', watchlist=watchlist, users=users, stocks=stocks)

@app.route('/add_to_watchlist', methods=['POST'])
def add_to_watchlist():
    user_id = request.form['user_id']
    stock_id = request.form['stock_id']
    added_on = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO Watchlist (user_id, stock_id, added_on) 
            VALUES (%s, %s, %s)
        ''', (user_id, stock_id, added_on))
        conn.commit()
        flash('Stock added to watchlist!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('watchlist'))


def log_action(action, performed_by):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Logs (action, performed_by, log_timestamp) VALUES (%s, %s, %s)',
                  (action, performed_by, timestamp))
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    app.run(debug=True)
# User update/delete routes
@app.route('/edit_user/<int:user_id>')
def edit_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('SELECT * FROM Users WHERE user_id = %s', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            flash('User not found!', 'danger')
            return redirect(url_for('users'))
            
        return render_template('edit_user.html', user=user)
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('users'))
    finally:
        cursor.close()
        conn.close()

@app.route('/update_user/<int:user_id>', methods=['POST'])
def update_user(user_id):
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    city = request.form['city']
    
    # Basic validation
    if not all([name, email, phone, city]):
        flash('All fields are required!', 'danger')
        return redirect(url_for('edit_user', user_id=user_id))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if user exists
        cursor.execute('SELECT * FROM Users WHERE user_id = %s', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            flash('User not found!', 'danger')
            return redirect(url_for('users'))
            
        # Check if email is already taken by another user
        cursor.execute('SELECT * FROM Users WHERE email = %s AND user_id != %s', (email, user_id))
        if cursor.fetchone():
            flash('Email already taken by another user!', 'danger')
            return redirect(url_for('edit_user', user_id=user_id))
            
        cursor.execute('UPDATE Users SET name = %s, email = %s, phone = %s, city = %s WHERE user_id = %s',
                      (name, email, phone, city, user_id))
        conn.commit()
        flash('User updated successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('users'))

@app.route('/delete_user/<int:user_id>', methods=['GET', 'POST'])
def delete_user(user_id):
    print(f"Route accessed: /delete_user/{user_id}")  # Debug print
    print(f"Request method: {request.method}")  # Debug print
    
    if not user_id:
        print("No user_id provided")  # Debug print
        flash('Invalid user ID!', 'danger')
        return redirect(url_for('users'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # First check if user exists
        cursor.execute('SELECT * FROM Users WHERE user_id = %s', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f"User {user_id} not found")  # Debug print
            flash('User not found!', 'danger')
            return redirect(url_for('users'))
            
        # Check if user has any transactions
        cursor.execute('SELECT COUNT(*) FROM Transactions WHERE user_id = %s', (user_id,))
        transaction_count = cursor.fetchone()[0]
        
        if transaction_count > 0:
            print(f"User {user_id} has {transaction_count} transactions")  # Debug print
            flash('Cannot delete user with existing transactions!', 'danger')
            return redirect(url_for('users'))
            
        # Delete the user
        print(f"Deleting user {user_id}")  # Debug print
        cursor.execute('DELETE FROM Users WHERE user_id = %s', (user_id,))
        conn.commit()
        flash('User deleted successfully!', 'success')
    except mysql.connector.Error as err:
        print(f"Database error: {err}")  # Debug print
        flash(f'Error: {err}', 'danger')
    except Exception as e:
        print(f"Unexpected error: {e}")  # Debug print
        flash(f'An unexpected error occurred: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('users'))

# Stock update/delete routes
@app.route('/edit_stock/<int:stock_id>')
def edit_stock(stock_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM Stocks WHERE stock_id = %s', (stock_id,))
    stock = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_stock.html', stock=stock)

@app.route('/update_stock/<int:stock_id>', methods=['POST'])
def update_stock(stock_id):
    symbol = request.form['symbol']
    company_name = request.form['company_name']
    sector = request.form['sector']
    current_price = request.form['current_price']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE Stocks SET symbol = %s, company_name = %s, sector = %s, current_price = %s WHERE stock_id = %s',
                      (symbol, company_name, sector, current_price, stock_id))
        conn.commit()
        flash('Stock updated successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('stocks'))

@app.route('/delete_stock/<int:stock_id>')
def delete_stock(stock_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM Stocks WHERE stock_id = %s', (stock_id,))
        conn.commit()
        flash('Stock deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('stocks'))

# Broker update/delete routes
@app.route('/edit_broker/<int:broker_id>')
def edit_broker(broker_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM Brokers WHERE broker_id = %s', (broker_id,))
    broker = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_broker.html', broker=broker)

@app.route('/update_broker/<int:broker_id>', methods=['POST'])
def update_broker(broker_id):
    name = request.form['name']
    commission_rate = request.form['commission_rate']
    contact_email = request.form['contact_email']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE Brokers SET name = %s, commission_rate = %s, contact_email = %s WHERE broker_id = %s',
                      (name, commission_rate, contact_email, broker_id))
        conn.commit()
        flash('Broker updated successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('brokers'))

@app.route('/delete_broker/<int:broker_id>')
def delete_broker(broker_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM Brokers WHERE broker_id = %s', (broker_id,))
        conn.commit()
        flash('Broker deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('brokers'))

# Delete watchlist item
@app.route('/delete_watchlist_item/<int:watchlist_id>')
def delete_watchlist_item(watchlist_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM Watchlist WHERE watchlist_id = %s', (watchlist_id,))
        conn.commit()
        flash('Watchlist item removed successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('watchlist'))

# Delete transaction
@app.route('/delete_transaction/<int:transaction_id>')
def delete_transaction(transaction_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get transaction details before deleting
    cursor.execute('SELECT * FROM Transactions WHERE transaction_id = %s', (transaction_id,))
    transaction = cursor.fetchone()
    
    if transaction:
        try:
            # If it's a BUY transaction, we need to update the portfolio
            if transaction['transaction_type'] == 'BUY':
                cursor.execute('''
                    UPDATE Portfolio_Holdings 
                    SET quantity = quantity - %s 
                    WHERE user_id = %s AND stock_id = %s
                ''', (transaction['quantity'], transaction['user_id'], transaction['stock_id']))
                
                # Remove if quantity becomes 0 or negative
                cursor.execute('''
                    DELETE FROM Portfolio_Holdings 
                    WHERE user_id = %s AND stock_id = %s AND quantity <= 0
                ''', (transaction['user_id'], transaction['stock_id']))
            
            # If it's a SELL transaction, we need to increase the portfolio
            elif transaction['transaction_type'] == 'SELL':
                # Check if user already has this stock
                cursor.execute('SELECT * FROM Portfolio_Holdings WHERE user_id = %s AND stock_id = %s', 
                              (transaction['user_id'], transaction['stock_id']))
                holding = cursor.fetchone()
                
                if holding:
                    # Update existing holding
                    cursor.execute('''
                        UPDATE Portfolio_Holdings 
                        SET quantity = quantity + %s 
                        WHERE user_id = %s AND stock_id = %s
                    ''', (transaction['quantity'], transaction['user_id'], transaction['stock_id']))
                else:
                    # Create new holding
                    cursor.execute('''
                        INSERT INTO Portfolio_Holdings 
                        (user_id, stock_id, quantity, purchase_date) 
                        VALUES (%s, %s, %s, %s)
                    ''', (transaction['user_id'], transaction['stock_id'], transaction['quantity'], transaction['transaction_date']))
            
            # Now delete the transaction
            cursor.execute('DELETE FROM Transactions WHERE transaction_id = %s', (transaction_id,))
            conn.commit()
            flash('Transaction deleted successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
    else:
        flash('Transaction not found!', 'danger')
    
    cursor.close()
    conn.close()
    return redirect(url_for('transactions'))