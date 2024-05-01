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


# Felhasználó bejelentkezése API
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

# Példa védett végpont JWT token-nel
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
    if user and username == "admin":
        
        session['username'] = username
        session['userid'] = user.id
        return redirect(url_for('admin', user_id=user.id))
        
        
        
    elif user:
        
        session['username'] = username
        session['userid'] = user.id
        
        return redirect(url_for('user', user_id=user.id))
 
    else:
        
        flash('Incorrect username or password', 'error')
        return redirect(url_for('index'))


@app.route("/user/<int:user_id>")
def user(user_id):
    # Felhasználó kurzusainak lekérése az adatbázisból
    if len(session) >0:
        user = User.query.get_or_404(user_id)
        mycourses = MyCourse.query.filter_by(user_id=user_id).all()
        courses = Course.query.all()
        events = Events.query.all()
            

        degrees = ApprovedDegree.query.distinct(ApprovedDegree.degree_id).all()
        return render_template('user.html',user=user.username, user_id=user_id, mycourses=mycourses, courses=courses, degrees=degrees, events=events)
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

    # Csak az új felhasználókhoz hozzáadott sózott jelszó
    password_hash = generate_password_hash(password)

    new_user = User(username=username, password_hash=password_hash, name=name, degree_id=degree_id)
    db.session.add(new_user)
    db.session.commit()

    flash('Registration successful!', 'registration_success')
    return redirect(url_for('index', _anchor='registration'))

def convert_passwords():
    users = User.query.all()
    for user in users:
        # Csak ahol van jelszó, de nincs sózott jelszó
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
    
    # Lekérjük a felhasználót az adatbázisból a user_id alapján
    user = User.query.filter_by(id=user_id).first()

    return render_template('szures.html', user_id=user_id, degrees=degrees, filtered_courses=filtered_courses, all_courses=all_courses)



@app.route("/hallgatok")
def hallgatok():
    
    user_id = request.args.get('user_id', type=int)
    # Minden hallgató kurzusainak lekérése az adatbázisból
    student_courses = MyCourse.query.join(User).join(Course).all()
    return render_template('hallgatok.html',user_id=user_id, student_courses=student_courses)



@app.route("/hallgatok_szures", methods=['GET'])
def hallgatok_szures():
    user_id = request.args.get('user_id', type=int)
    # Szûrés a hallgatók szerint
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
        # A felhasználó által kiválasztott kurzus kódjának lekérése a formról
        course_code = request.form['course_code']
        

        # Ellenõrizzük, hogy a kurzus már fel van-e véve a felhasználó által
        user_courses = MyCourse.query.filter_by(user_id=user_id).all()
        for user_course in user_courses:
            if user_course.course.code == course_code:
                flash('A kurzust mar felvette', 'error')
                return redirect(url_for('kurzus_felvetel', user_id=user_id))
            
        # Az adott kurzus lekérése az adatbázisból a kód alapján
        course = Course.query.filter_by(code=course_code).first()


        # Új kurzus hozzáadása a felhasználó kurzusaihoz
        new_course = MyCourse(user_id=user_id, course_id=course.id)
        db.session.add(new_course)
        db.session.commit()

        flash('Sikeres kurzus felvetel: {}'.format(course_code), 'success')
        return redirect(url_for('kurzus_felvetel', user_id=user_id))

    # GET kérés esetén a kurzusfelvetel.html
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
    # Átirányítás az index oldalra
    return redirect(url_for("index"))

@app.route("/admin/<int:user_id>")
def admin(user_id):
    if len(session) >0:
            courses = Course.query.all()    
            students = User.query.all()    
            degrees = Degree.query.all()
            events = Events.query.all()
            approved = ApprovedDegree.query.all()
    
            user = User.query.get_or_404(user_id)
            return render_template('admin.html',user=user.username, user_id=user_id, students = students, courses=courses, degrees=degrees, events=events,approved=approved)
    else:
        flash('You are not logged in!', 'error')
        return redirect(url_for('index'))
 
   

@app.route("/edit_user/<int:user_id>", methods=['GET', 'POST'])
def edit_user(user_id):
    if request.method == 'POST':
        if 'edit_selected_users' in request.form:
            selected_users = request.form.getlist('selected_users[]')
            for user_id in selected_users:
                user = User.query.get_or_404(int(user_id))
                username = request.form['username_' + user_id]
                name = request.form['name_' + user_id]
                degree_id = request.form['degree_' + user_id]
                
                user.username = username
                user.name = name
                user.degree_id = degree_id
                
                db.session.commit()
            flash('Adatok frissulve!', 'success')
    
    users = User.query.all()
    return render_template('admin_user_edit.html', users=users, user_id=user_id)

@app.route("/edit_course/<int:user_id>", methods=['GET', 'POST'])
def edit_course(user_id):
    if request.method == 'POST':
        if 'edit_selected_courses' in request.form:
            selected_courses = request.form.getlist('selected_courses[]')
            for course_id in selected_courses:
                course = Course.query.get_or_404(int(course_id))
                code = request.form['code_' + course_id]
                name = request.form['name_' + course_id]
                credit = request.form['credit_' + course_id]
                
                course.code = code
                course.name = name
                course.credit = credit
                
                db.session.commit()
            flash('Adatok frissulve!', 'success')
        elif 'add_new_course' in request.form:
            new_code = request.form['new_code']
            new_name = request.form['new_name']
            new_credit = request.form['new_credit']

            # Ellenõrzés, hogy az adatok megfelelõek-e, és hozzáadás az adatbázishoz
            if new_code and new_name and new_credit:
                new_course = Course(code=new_code, name=new_name, credit=new_credit)
                db.session.add(new_course)
                db.session.commit()

                flash('Kurzus succes', 'success')
            else:
                flash('Minden adat kell!', 'error')
    
    courses = Course.query.all()
    return render_template('admin_course_edit.html', courses=courses, user_id=user_id)

@app.route("/edit_approved_degrees/<int:user_id>", methods=['GET', 'POST'])
def edit_approved_degrees(user_id):
    if request.method == 'POST':
        if 'edit_selected_degrees' in request.form:
            selected_degrees = request.form.getlist('selected_degrees')

            for degree_id in selected_degrees:
                degree = ApprovedDegree.query.get_or_404(degree_id)
                new_course_id = request.form[f'course_id_{degree_id}']
                new_degree_id = request.form[f'degree_id_{degree_id}']

                if new_course_id and new_degree_id:
                    degree.course_id = new_course_id
                    degree.degree_id = new_degree_id
                    db.session.commit()
                else:
                    flash('Minden adat kotelezo!', 'error')

        elif 'add_new_degree' in request.form:
            new_course_id = request.form['new_course_id']
            new_degree_id = request.form['new_degree_id']

            if new_course_id and new_degree_id:
                new_degree = ApprovedDegree(course_id=new_course_id, degree_id=new_degree_id)
                db.session.add(new_degree)
                db.session.commit()
                flash('Uj sor hozzaadva!', 'success')
            else:
                flash('Minden adat kotelezo!', 'error')

    approved_degrees = ApprovedDegree.query.all()
    return render_template('admin_approved.html', approved_degrees=approved_degrees, user_id=user_id)