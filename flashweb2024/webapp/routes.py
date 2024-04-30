from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from webapp import app, db
from werkzeug.security import generate_password_hash, check_password_hash
from webapp.models import Events, User, MyCourse, Course, Degree, ApprovedDegree

def authenticate(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        return user
    

def identity(payload):
    user_id = payload['identity']
    return User.query.get(user_id)

jwt = JWTManager(app)

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# Felhaszn�l� bejelentkez�se API
@app.route("/api/login", methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username', None)
    password = data.get('password', None)
    
    user = authenticate(username, password)
    if user:
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

# P�lda v�dett v�gpont JWT token-nel
@app.route("/api/protected", methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route("/")
@app.route("/index")
def index():
    
    users = User.query.all()
    return render_template('index.html', users=users)


@app.route("/login", methods=['POST'])
def login():
    
    username = request.form['username']
    password = request.form['password']
    user = authenticate(username, password)
    if user:
        
        session['username'] = username
        session['userid'] = user.id
        
        return redirect(url_for('user', user_id=user.id))
 
    else:
        
        flash('Incorrect username or password', 'error')
        return redirect(url_for('index'))


@app.route("/user/<int:user_id>")
def user(user_id):
    # Felhaszn�l� kurzusainak lek�r�se az adatb�zisb�l
    if len(session) >0:
        user = User.query.get_or_404(user_id)
        mycourses = MyCourse.query.filter_by(user_id=user_id).all()
        courses = Course.query.all()
    

        degrees = ApprovedDegree.query.distinct(ApprovedDegree.degree_id).all()
        return render_template('user.html',user=user.username, user_id=user_id, mycourses=mycourses, courses=courses, degrees=degrees)
    else:
        flash('You are not logged in!', 'error')
        return redirect(url_for('index'))

@app.route("/register", methods=['POST'])
def register():
    username = request.form['reg_username']
    password = request.form['reg_password']
    name = request.form['reg_name']
    degree_id = request.form['reg_degree']
    

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('Username already taken', 'registration_error')
        return redirect(url_for('index', _anchor='registration'))

    # Csak az �j felhaszn�l�khoz hozz�adott s�zott jelsz�
    password_hash = generate_password_hash(password)

    new_user = User(username=username, password=password, password_hash=password_hash, name=name, degree_id=degree_id)
    db.session.add(new_user)
    db.session.commit()

    flash('Registration successful!', 'registration_success')
    return redirect(url_for('index', _anchor='registration'))

def convert_passwords():
    users = User.query.all()
    for user in users:
        # Csak ahol van jelsz�, de nincs s�zott jelsz�
        if user.password and not user.password_hash:
            user.password_hash = generate_password_hash(user.password)
            db.session.commit()



@app.route("/szuro")
def szuro():
    
    user_id = request.args.get('user_id', type=int)
    degrees = Degree.query.all()
    degree_id = request.args.get('degree', type=int)
    if degree_id == 0:
        filtered_courses = Course.query.all()
    elif degree_id:
        filtered_courses = Course.query.join(ApprovedDegree).filter(ApprovedDegree.degree_id == degree_id).all()
    else:
        filtered_courses = []

    all_courses = Course.query.all()
    
    # Lek�rj�k a felhaszn�l�t az adatb�zisb�l a user_id alapj�n
    user = User.query.filter_by(id=user_id).first()

    return render_template('szures.html', user_id=user_id, degrees=degrees, filtered_courses=filtered_courses, all_courses=all_courses)



@app.route("/hallgatok")
def hallgatok():
    
    user_id = request.args.get('user_id', type=int)
    # Minden hallgat� kurzusainak lek�r�se az adatb�zisb�l
    student_courses = MyCourse.query.join(User).join(Course).all()
    return render_template('hallgatok.html',user_id=user_id, student_courses=student_courses)



@app.route("/hallgatok_szures", methods=['GET'])
def hallgatok_szures():
    user_id = request.args.get('user_id', type=int)
    # Sz�r�s a hallgat�k szerint
    degree_id = request.args.get('degree', type=int)
    if degree_id == 0:
        student_courses = MyCourse.query.join(User).join(Course).all()
    elif degree_id:
        student_courses = MyCourse.query.join(User).join(Course).join(ApprovedDegree).filter(ApprovedDegree.degree_id == degree_id).all()
    else:
        student_courses = []
    return render_template('hallgatok.html',user_id=user_id, student_courses=student_courses)



@app.route("/kurzus_felvetel/<int:user_id>", methods=['GET', 'POST'])
def kurzus_felvetel(user_id):
    if request.method == 'POST':
        # A felhaszn�l� �ltal kiv�lasztott kurzus k�dj�nak lek�r�se a formr�l
        course_code = request.form['course_code']
        

        # Ellen�rizz�k, hogy a kurzus m�r fel van-e v�ve a felhaszn�l� �ltal
        user_courses = MyCourse.query.filter_by(user_id=user_id).all()
        for user_course in user_courses:
            if user_course.course.code == course_code:
                flash('A kurzust mar felvette', 'error')
                return redirect(url_for('kurzus_felvetel', user_id=user_id))
            
        # Az adott kurzus lek�r�se az adatb�zisb�l a k�d alapj�n
        course = Course.query.filter_by(code=course_code).first()


        # �j kurzus hozz�ad�sa a felhaszn�l� kurzusaihoz
        new_course = MyCourse(user_id=user_id, course_id=course.id)
        db.session.add(new_course)
        db.session.commit()

        flash('Sikeres kurzus felvetel: {}'.format(course_code), 'success')
        return redirect(url_for('kurzus_felvetel', user_id=user_id))

    # GET k�r�s eset�n a kurzusfelvetel.html
    user = User.query.get_or_404(user_id)
    user_degree_id = user.degree_id
    available_courses = Course.query.join(ApprovedDegree).filter(ApprovedDegree.degree_id == user_degree_id).all()

    return render_template('kurzusfelvetel.html', user_id=user_id, available_courses=available_courses)

@app.route("/events")
def events():

    user_id = session.get('userid')
    user_courses = MyCourse.query.filter_by(user_id=user_id).all()
    events = Events.query.all()

    return render_template('esemenyek.html',user_id=user_id, user_courses=user_courses, events=events)

@app.route("/logout", methods=["POST"])
def logout():
    

    session.clear()
    # �tir�ny�t�s az index oldalra
    return redirect(url_for("index"))
