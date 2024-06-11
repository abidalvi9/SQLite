from flask import Flask, request, jsonify, send_file
import sqlite3
import matplotlib.pyplot as plt

app = Flask(__name__)

connection = sqlite3.connect('ppp.db')
cursor = connection.cursor()
cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            UserID INTEGER PRIMARY KEY,
            Username TEXT(50) UNIQUE NOT NULL,
            Password TEXT(100) NOT NULL,
            UserRole TEXT(50) NOT NULL 
        )
    ''')

cursor.execute('''
        CREATE TABLE IF NOT EXISTS Transactions (
            TransactionID INTEGER PRIMARY KEY,
            TransactionDateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            TransactionType TEXT(50) NOT NULL,
            Amount NUMERIC(10, 2) NOT NULL,
            Party1ID INTEGER ,
            Party2ID INTEGER ,
            TransactionStatus TEXT(20) DEFAULT 'Pending',
            Category TEXT(50),
            Comments TEXT(255),
            FOREIGN KEY (Party1ID) REFERENCES Users(UserID),
            FOREIGN KEY (Party2ID) REFERENCES Users(UserID)
        )
    ''')

cursor.execute('''
        CREATE TABLE IF NOT EXISTS Rules (
            RuleID INTEGER PRIMARY KEY,
            RuleName TEXT(100) NOT NULL,
            RuleDescription TEXT(255),
            ValidationQuery TEXT(1000) NOT NULL
        )
    ''')


cursor.execute('''
        CREATE TABLE if not exists AuditTrail (
            AuditID INTEGER PRIMARY KEY,
            UserID INTEGER,
            TransactionID INTEGER,
            ActionPerformed TEXT(100) NOT NULL,
            ActionTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (UserID) REFERENCES Users(UserID),
            FOREIGN KEY (TransactionID) REFERENCES Transactions(TransactionID)
            )
        ''')


cursor.execute('''
        CREATE TABLE if not exists Reports (
            ReportID INTEGER PRIMARY KEY,
            ReportName TEXT(100) NOT NULL,
            ReportType TEXT(50) NOT NULL,
            GeneratedByUserID INTEGER,
            GeneratedDateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (GeneratedByUserID) REFERENCES Users(UserID)
            )
        ''')

connection.commit()
connection.close()


@app.route('/create-user', methods=['POST'])
def reg():
    try:
        data = request.get_json()
        connection = sqlite3.connect('ppp.db')
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Users (UserID, Username, Password, UserRole) VALUES (?, ?, ?, ?)",
                       (data['UserID'], data['Username'], data['Password'], data['UserRole']))
        connection.commit()
        connection.close()
        return "user created successfully"
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/view_user')
def view_user():
    connection = sqlite3.connect('ppp.db')
    cursor = connection.cursor()
    return {'transactions': list(cursor.execute("SELECT * FROM Users"))}

@app.route('/create-transaction', methods=['POST'])
def create_transaction():
    try:
        data = request.get_json()
        connection = sqlite3.connect('ppp.db')
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Transactions (TransactionID,TransactionType, Amount, Party1ID, Party2ID, TransactionStatus, Category, Comments) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (data['TransactionID'],data['TransactionType'], data['Amount'], data['Party1ID'], data['Party2ID'], data.get('TransactionStatus', 'Pending'), data.get('Category'), data.get('Comments')))
        connection.commit()
        connection.close()
        return "Transaction created successfully"
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/view_transaction')
def view_transaction():
    connection = sqlite3.connect('ppp.db')
    cursor = connection.cursor()
    return {'transactions': list(cursor.execute("SELECT * FROM Transactions"))}

@app.route('/view_transaction_id', methods=['POST'])
def view_transaction_id():
    try:
        data = request.get_json()
        connection = sqlite3.connect('ppp.db')
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Transactions WHERE TransactionID = ?", (data['TransactionID'],))
        transaction = cursor.fetchone()
        connection.close()

        if transaction:
            return jsonify({"transaction": transaction})
        else:
            return jsonify({"message": "Transaction not found"})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/create-fake-transaction', methods=['POST'])
def create_transaction_fake():
    try:
        data = request.get_json()
        connection = sqlite3.connect('ppp.db')
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Transactions (TransactionID,TransactionType, Amount, Party1ID, Party2ID, TransactionStatus, Category, Comments) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (data['TransactionID'],data['TransactionType'], data['Amount'], data['Party1ID'], data['Party2ID'], data.get('TransactionStatus', 'Pending'), data.get('Category'), data.get('Comments')))
        connection.commit()
        connection.close()
        return "Transaction created successfully"
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/delete-transaction', methods=['POST'])
def delete_transaction():
    try:
        data = request.get_json()
        connection = sqlite3.connect('ppp.db')
        cursor = connection.cursor()
        cursor.execute("DELETE FROM Transactions WHERE TransactionID = ?", (data["TransactionID"],))
        connection.commit()
        connection.close()
        return "Transaction deleted successfully"
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/update', methods=['POST'])
def update():
    try:
        data = request.get_json()
        connection = sqlite3.connect('ppp.db')
        cursor = connection.cursor()
        cursor.execute("UPDATE Transactions SET TransactionStatus = ?, Category = ?, Documents = ?, Comments = ? WHERE TransactionID = ?",
                       (data.get('TransactionStatus'), data.get('Category'), data.get('Documents'), data.get('Comments'), data.get('TransactionID')))
        connection.commit()
        connection.close()
        return "Details updated"
    except sqlite3.Error as e:
        return jsonify({"error": str(e)})


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        connection = sqlite3.connect('ppp.db')
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Users WHERE Username = ? AND Password = ?", (data['Username'], data['Password']))
        user = cursor.fetchone()
        connection.close()

        if user:
            return jsonify({"message": "Login successful"})
        else:
            return jsonify({"message": "Invalid username or password"})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/generate-report', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        # Sample query to fetch transaction data based on user criteria
        # Modify this query as per your actual database schema and criteria
        connection = sqlite3.connect('ppp.db')
        cursor = connection.cursor()
        cursor.execute("SELECT TransactionDateTime, Amount FROM Transactions WHERE TransactionType = ? AND TransactionDateTime BETWEEN ? AND ?",
                       (data['TransactionType'], data['StartDate'], data['EndDate']))
        transactions = cursor.fetchall()
        connection.close()

        if not transactions:
            return jsonify({"message": "No transactions found for the given criteria"})

        # Prepare data for plotting
        transaction_dates = [transaction[0] for transaction in transactions]
        transaction_amounts = [transaction[1] for transaction in transactions]

        # Create a line plot
        plt.figure(figsize=(10, 6))
        plt.plot(transaction_dates, transaction_amounts)
        plt.title('Transaction Trend')
        plt.xlabel('Date')
        plt.ylabel('Amount')
        plt.grid(True)

        # Save the plot as a temporary file
        report_filename = 'transaction_trend.png'
        plt.savefig(report_filename)

        # Close the plot to release resources
        plt.close()

        # Return the generated report file
        return send_file(report_filename, mimetype='image/png', as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/Rules', methods = ['POST'])
def Rules():
    try:
        data = request.get_json()
        connection = sqlite3.connect('ppp.db')
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Rules (RuleID, RuleName, RuleDescription, ValidationQuery) VALUES (?, ?, ?, ?)",
                       (data['RuleID'], data['RuleName'], data['RuleDescription'], data['ValidationQuery']))
        connection.commit()
        connection.close()
        return "user created successfully"
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/view_rule_id', methods=['POST'])
def view_rule_id():
    try:
        data = request.get_json()
        connection = sqlite3.connect('ppp.db')
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Rules WHERE RuleID = ?", (data['RuleID'],))
        Rules = cursor.fetchone()
        connection.close()

        if Rules:
            return jsonify({"RuleID": Rules})
        else:
            return jsonify({"message": "RuleID not found"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/Reports', methods = ['POST'])
def Reports():
    try:
        data = request.get_json()
        connection = sqlite3.connect('ppp.db')
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Reports (ReportID, ReportName, ReportType, GeneratedByUserID) VALUES (?, ?, ?, ?)",
                       (data['RuleID'], data['RuleName'], data['RuleDescription'], data['ValidationQuery']))
        connection.commit()
        connection.close()
        return "Report created successfully"
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/view_report_id', methods=['POST'])
def view_report_id():
    try:
        data = request.get_json()
        connection = sqlite3.connect('ppp.db')
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Reports WHERE ReportID = ?", (data['ReportID'],))
        Reports = cursor.fetchone()
        connection.close()

        if Reports:
            return jsonify({"RuleID": Reports})
        else:
            return jsonify({"message": "Reports not found"})
    except Exception as e:
        return jsonify({"error": str(e)})

app.run(debug=True)
