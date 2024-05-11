from sqlalchemy import ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from webapp import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(100))
    name = db.Column(db.String(100))
    degree_id = db.Column(db.Integer, db.ForeignKey('degrees.id'))
    login = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100))
    name = db.Column(db.String(100))
    credit = db.Column(db.Integer)

    def __repr__(self):
        return '<Course {}>'.format(self.name)
    
class MyCourse(db.Model):
    __tablename__ = 'mycourse'  
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    
    student = db.relationship('User', backref='courses')
    course = db.relationship('Course', backref='students')

    def __repr__(self):
        return '<MyCourse {}>'.format(self.id)

class Degree(db.Model):
    __tablename__ = 'degrees'
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

class Events(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    name = db.Column(db.String(100))
    description = db.Column(db.String(50))

    def __repr__(self):
        return '<Events {}>'.format(self.id)