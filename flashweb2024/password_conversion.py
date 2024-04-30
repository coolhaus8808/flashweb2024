from werkzeug.security import generate_password_hash
from webapp import db, app
from webapp.models import User

def convert_passwords():
     with app.app_context():
        users = db.session.query(User).all()
        for user in users:
            # Csak ahol van jelszó, de nincs sózott jelszó
            if user.password and user.password_hash < "A":
                print("okay")
                user.password_hash = generate_password_hash(user.password)
                db.session.commit()
if __name__ == "__main__":
    convert_passwords()
    print("Password conversion completed successfully.")
