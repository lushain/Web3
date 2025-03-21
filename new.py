from flask import Flask
from models import db, User, Transaction, LendingRequest
from app import app  # Ensure correct import of Flask app
from models import Transaction, LendingRequest, User

def delete_all_data():
    # try:
    #     # Delete all transactions
    #     db.session.query(Transaction).delete()

    #     # Delete all lending requests
    #     db.session.query(LendingRequest).delete()

    #     # Commit changes
    #     db.session.commit()
    #     print("✅ All transactions and lending requests have been deleted successfully.")
    
    # except Exception as e:
    #     db.session.rollback()  # Rollback in case of an error
    #     print(f"❌ Error: {e}")
    users = User.query.all()
    if not users:
        print("No users found in the database.")
        return
    
    print("\nUser Details:\n" + "="*40)
    for user in users:
        print(f"ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Balance: ${user.balance}")
        print(f"Total Lent: ${sum(t.amount for t in user.transactions if t.type == 'lent')}")
        print(f"Total Borrowed: ${sum(t.amount for t in user.transactions if t.type == 'borrowed')}")
        print("-" * 40)
    

# Run inside the Flask app context
with app.app_context():
    delete_all_data()