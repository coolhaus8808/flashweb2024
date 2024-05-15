from werkzeug.security import generate_password_hash
from webapp import db, app
from webapp.models import User

def convert_passwords():
     with app.app_context():
        users = db.session.query(User).all()
        for user in users:
            if user.username != "admin":
                user.password_hash = generate_password_hash("asdf" + app.config['sozas'])
                db.session.commit()
if __name__ == "__main__":
    convert_passwords()
    print("Password conversion completed successfully.")
