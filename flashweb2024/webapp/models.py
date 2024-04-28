from sqlalchemy import ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from webapp import db

class User(db.Model):
    __tablename__ = 'users'  # Megadja az adatbázisban használt tábla nevét
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    degree_id = db.Column(db.Integer, db.ForeignKey('degrees.id'))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def check_password(self, password):
        return self.password == password    

class MyCourse(db.Model):
    __tablename__ = 'mycourse'  # Megadja az adatbázisban használt tábla nevét
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    
    # Kapcsolatok definiálása a User és Course modellekkel
    student = db.relationship('User', backref='courses')
    course = db.relationship('Course', backref='students')

    def __repr__(self):
        return '<MyCourse {}>'.format(self.id)
    

class Course(db.Model):
    __tablename__ = 'courses'  # Megadja az adatbázisban használt tábla nevét
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100))
    name = db.Column(db.String(100))
    credit = db.Column(db.Integer)

    def __repr__(self):
        return '<Course {}>'.format(self.name)
    

class Degree(db.Model):
    __tablename__ = 'degrees'  # Új tábla
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    def __repr__(self):
        return '<Degree {}>'.format(self.name)
    
class ApprovedDegree(db.Model):
    __tablename__ = 'approved_degrees'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    degree_id = db.Column(db.Integer, db.ForeignKey('degrees.id'))

    def __repr__(self):
        return '<ApprovedDegree {}>'.format(self.id)