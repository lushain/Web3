from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from models import db, User, Transaction, LendingRequest, Block, BlockchainTransaction
import random

# Initialize Flask Extensions
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "routes.login"

# Create Blueprint
routes = Blueprint("routes", __name__)

def show_dash():
    return redirect(url_for("routes.dashboard"))

# User Loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register Route
@routes.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for("routes.login"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        # Log in the user automatically after registration
        login_user(new_user)

        return show_dash()
        

    return render_template("register.html")

# Login Route
@routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return show_dash()
        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")

@routes.route('/')
def index():
    return render_template('index.html')

@routes.route('/premium')
def premium():
    return render_template('premium.html')

# Dashboard Route (Requires Login)
@routes.route("/dashboard")
@login_required
def dashboard():
    lending_requests = LendingRequest.query.all()

    # Fetch all transactions by the user of type 'lent'
    lent_transactions = Transaction.query.filter_by(user_id=current_user.id, type='lent').all()

    # Fetch all transactions by the user of type 'borrowed'
    borrowed_transactions = Transaction.query.filter_by(user_id=current_user.id, type='borrowed').all()

    # Calculate total money lent by the user
    total_lent = sum(transaction.amount for transaction in lent_transactions)

    # Calculate total money borrowed by the user
    total_borrowed = sum(transaction.amount for transaction in borrowed_transactions)

    rate = float(str(random.uniform(8,15))[:4])

    current = False

    if 'error' not in session:
        pass
    elif session['error']:
        current = session['error']
        session['error'] = False


    return render_template(
        'dashboard2.html',
        user=current_user,
        lending_requests=lending_requests,
        lent=lent_transactions,
        borrowed=borrowed_transactions,
        total_lent=total_lent,
        total_borrowed=total_borrowed,
        rate = rate,
        error = current or False
    )


# Logout Route
@routes.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect("/")


@routes.route("/add_transaction", methods=["POST"])
@login_required
def add_transaction():
    amount = float(request.form["amount"])
    type = request.form["type"]  # "lent" or "borrowed"
    person_name = request.form["person_name"]
    time_period = request.form["time_period"]
    rate = float(request.form["rate"])

    new_transaction = Transaction(
        amount=amount,
        type=type,
        person_name=person_name,
        time_period=time_period,
        rate=rate,
        user_id=current_user.id
    )

    db.session.add(new_transaction)
    db.session.commit()
    flash("Transaction added successfully!", "success")
    
    return show_dash()

@routes.route('/publish_lending_request', methods=['POST'])
@login_required
def publish_lending_request():
    amount = request.form.get('amount')
    time_period = str(request.form.get('time_value')) + " " + request.form.get('time_unit')
    rate = request.form.get("rate", type=float) 

    new_request = LendingRequest(
        user_id=current_user.id,
        amount=amount,
        time_period=time_period,
        interest_rate=float(rate),  # Default interest rate
    )
    
    db.session.add(new_request)
    db.session.commit()

    flash("Lending request published successfully!", "success")
    return show_dash()

@routes.route('/marketplace')
@login_required
def marketplace():
    lending_requests = LendingRequest.query.all()
    return render_template('marketplace.html', lending_requests=lending_requests)


@routes.route("/payments", methods=["GET", "POST"])
@login_required
def payments():
    if request.method == "POST":
        amount = int(request.form['amount'])
        if not current_user.balance:
            current_user.balance = 0.0

        if request.form['transaction_type'] == 'deposit':
            current_user.balance += amount

        elif request.form['transaction_type'] == 'withdraw':
            if current_user.balance < amount:
                flash("Insufficient balance.", "danger")
                return redirect(url_for("routes.payments"))
            current_user.balance -= amount
        db.session.commit()

        return show_dash()

        
    return render_template("payments.html")

@routes.route("/upgrade", methods=["GET", "POST"])
@login_required
def upgrade():
    if current_user.premium:
        return show_dash()
    
    if request.method == "POST":

        current_user.premium = True
        db.session.commit()

        return show_dash()

    return render_template("upgrade.html")

@routes.route('/lend/<int:lending_req_id>', methods=['GET', 'POST'])
@login_required
def lend_request(lending_req_id):

    from block import record_transaction_on_blockchain

    lending_request = LendingRequest.query.get_or_404(lending_req_id)

    if request.method == 'GET':
        return render_template('lend_confirm.html', lending_request=lending_request)
    
    # Ensure lender has enough balance
    if current_user.balance < lending_request.amount:
        flash("Insufficient balance to lend this amount.", "error")
        session['error'] = True
        return show_dash()

    borrower = User.query.get(lending_request.user_id)

    if not borrower:
        flash("Borrower not found.", "error")
        return show_dash()
        

    # Create transaction for lender
    lender_transaction = Transaction(
        user_id=current_user.id,
        amount=lending_request.amount,
        type="lent",
        person_name=borrower.username,
        time_period=lending_request.time_period,
        rate=lending_request.interest_rate-0.75,
        lend_id=lending_request.id
    )

    # Create transaction for borrower
    borrower_transaction = Transaction(
        user_id=borrower.id,
        amount=lending_request.amount,
        type="borrowed",
        person_name=current_user.username,
        time_period=lending_request.time_period,
        rate=lending_request.interest_rate,
        lend_id=lending_request.id
    )

    # Update balances
    current_user.balance -= lending_request.amount
    borrower.balance += lending_request.amount

    # Save to DB
    db.session.add(lender_transaction)
    db.session.add(borrower_transaction)

    blockchain_hash = record_transaction_on_blockchain(
        lender=current_user.username,
        borrower=borrower.username,
        amount=lending_request.amount,
        duration=lending_request.time_period,
        rate= lending_request.interest_rate
    )

    db.session.delete(lending_request)
    db.session.commit()

    flash(f"Successfully lent ${lending_request.amount} to {borrower.username}.", "success")
    return show_dash()


# @routes.route("/explorer")
# def blockchain_explorer():
#     blocks = Block.query.order_by(Block.index.asc()).all()
#     transactions = BlockchainTransaction.query.all()
    
#     return render_template("blockchain_explorer.html", blocks=blocks, transactions=transactions)

@routes.route('/users/<int:userid>')
@login_required
def view_user_profile(userid):
    user = User.query.get_or_404(userid)

    # Check if the user has an active lending request
    active_lending_requests = LendingRequest.query.filter_by(user_id=userid).all()

    if current_user.id != user.id and not active_lending_requests:
        flash("This user currently has no active lending requests.", "error")
        return show_dash()
    

    # Fetch lending and borrowing history
    lending_history = Transaction.query.filter_by(user_id=userid, type="lent").all()
    borrowing_history = Transaction.query.filter_by(user_id=userid, type="borrowed").all()

    total_lent = sum(transaction.amount for transaction in lending_history)

    # Calculate total money borrowed by the user
    total_borrowed = sum(transaction.amount for transaction in borrowing_history)

    return render_template(
        "user_profile.html",
        user=user,
        lending_requests=active_lending_requests,
        lending_history=lending_history,
        borrowing_history=borrowing_history,
        total_lent=total_lent,
        total_borrowed=total_borrowed
    )

@routes.route('/files', methods=['GET', 'POST'])
@login_required
def files():
    if request.method == 'POST':
        current_user.verified = True
        db.session.commit()

        return redirect(f"/users/{current_user.id}")
    return render_template('files.html')