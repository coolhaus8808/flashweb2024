from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from webapp import app, socketio, db
from werkzeug.security import generate_password_hash, check_password_hash
from webapp.models import Events, User, MyCourse, Course, Degree, ApprovedDegree
from datetime import datetime, date
from flask_socketio import send, emit

@app.route("/chat/<int:user_id>")
def chat(user_id):
    user = User.query.get_or_404(user_id)
    if user.login == 1:
        username = user.username
        return render_template('chat.html', user_id=user_id, username=username)
    else:
        flash('Sign in!', 'success')  
        return redirect(url_for("index"))


@socketio.on('chat_message')
def handle_chat_message(data):
    message = data['message']
    user_id = data['user_id']
    user = User.query.get(user_id)
    username = user.username
    emit('chat_message', {'username': username, 'message': message}, broadcast=True)
    

@socketio.on('connect')
def handle_connect():
    print('A client has connected to the server!')



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
    
    degrees = Degree.query.all()
    users = User.query.all()
    return render_template('index.html', users=users, degrees=degrees)


@app.route("/login", methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = authenticate(username, password)
    if user and username == "admin":
        session['username'] = username
        session['userid'] = user.id
        user.login = 1  
        db.session.commit()  
        return redirect(url_for('admin', user_id=user.id))
    elif user:
        session['username'] = username
        session['userid'] = user.id
        user.login = 1 
        db.session.commit() 
        return redirect(url_for('user_login', user_id=user.id))
    else:
        flash('Incorrect username or password', 'error')
        return redirect(url_for('index'))
    

@app.route("/user/<int:user_id>")
def user(user_id):
    user = User.query.get_or_404(user_id)
    if user.login == 1:
        mycourses = MyCourse.query.filter_by(user_id=user_id).all()
        courses = Course.query.all()
        events = Events.query.all()


        degrees = ApprovedDegree.query.distinct(ApprovedDegree.degree_id).all()
        return render_template('user.html',user=user.username, user_id=user_id, mycourses=mycourses, courses=courses, degrees=degrees, events=events)
    else:
        flash('You are not logged in!', 'error')
        return redirect(url_for('index'))


@app.route("/user_login/<int:user_id>")
def user_login(user_id):
    user = User.query.get_or_404(user_id)
    if user.login == 1:
        mycourses = MyCourse.query.filter_by(user_id=user_id).all()
        courses = Course.query.all()
        events = Events.query.all()
        degrees = ApprovedDegree.query.distinct(ApprovedDegree.degree_id).all()

        # Ellenőrzés, hogy van-e esemény a felhasználó számára
        user_events = [event for event in events if event.course_id in [course.course_id for course in mycourses]]
        if user_events:
            mai_datum = date.today()
            mai_datum_konvert = datetime(mai_datum.year, mai_datum.month, mai_datum.day)
                
            for event in user_events:
                event_date = datetime.strptime(event.description.split(': ')[1], '%Y.%m.%d.')
                    
                if event_date > mai_datum_konvert:  
                    alert_message = "Új esemény!"
                    socketio.emit('new_event', {'message': alert_message}, room=user_id)
                    break  # ha találtunk egy jövőbeli eseményt, kilépünk a ciklusból
                else:
                    alert_message = ""
                    socketio.emit('new_event', {'message': alert_message}, room=user_id)

        
        else:
            alert_message = ""
            
        return render_template('user_login.html', user=user.username, user_id=user_id, mycourses=mycourses, courses=courses, degrees=degrees, events=events, alert_message=alert_message)
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
    selected_degree = None
    if degree_id == 0:
        filtered_courses = Course.query.all()
    elif degree_id:
        selected_degree = Degree.query.get(degree_id)
        filtered_courses = Course.query.join(ApprovedDegree).filter(ApprovedDegree.degree_id == degree_id).all()
    else:
        filtered_courses = []

    all_courses = Course.query.all()
    
    return render_template('szures.html', user_id=user_id, degrees=degrees, filtered_courses=filtered_courses, all_courses=all_courses, selected_degree=selected_degree)



@app.route("/hallgatok")
def hallgatok():
    
    user_id = request.args.get('user_id', type=int)
    degrees = Degree.query.all()
    # Minden hallgató kurzusainak lekérése az adatbázisból
    student_courses = MyCourse.query.join(User).join(Course).all()
    return render_template('hallgatok.html',user_id=user_id, student_courses=student_courses,degrees=degrees)



@app.route("/hallgatok_szures", methods=['GET'])
def hallgatok_szures():
    degrees = Degree.query.all()
    user_id = request.args.get('user_id', type=int)
    # Szűrés a hallgatók szerint
    degree_id = request.args.get('degree', type=int)
    selected_degree = None
    if degree_id == 0:
        student_courses = MyCourse.query.join(User).join(Course).all()
    elif degree_id:
        selected_degree = Degree.query.get(degree_id)
        student_courses = MyCourse.query.join(User).join(Course).join(ApprovedDegree).filter(ApprovedDegree.degree_id == degree_id).all()
    else:
        student_courses = []
    return render_template('hallgatok.html',user_id=user_id, student_courses=student_courses,degrees=degrees,selected_degree=selected_degree)



@app.route("/kurzus_felvetel/<int:user_id>", methods=['GET', 'POST'])
def kurzus_felvetel(user_id):
    if request.method == 'POST':
        # A felhasználó által kiválasztott kurzus kódjának lekérése a formról
        course_code = request.form['course_code']
        

        # Ellenőrizzük, hogy a kurzus már fel van-e véve a felhasználó által
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
    
    # Ha nincsenek elérhető kurzusok az admin számára
    if not available_courses:
        flash('Nincsenek elerheto kurzusok ehhez a szakhoz.', 'error')
        return render_template('kurzusfelvetel.html', user_id=user_id)

    return render_template('kurzusfelvetel.html', user_id=user_id, available_courses=available_courses)

@app.route("/events/<int:user_id>")
def events(user_id):

    user_id = user_id
    user_courses = MyCourse.query.filter_by(user_id=user_id).all()
    events = Events.query.all()

    return render_template('esemenyek.html',user_id=user_id, user_courses=user_courses, events=events)

@app.route("/logout/<int:user_id>", methods=["POST"])
def logout(user_id):
    user_id = user_id
    if user_id:
        user = User.query.get(user_id)
        if user:
            user.login = 0
            db.session.commit()
    session.clear()
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
            
        elif 'clear_selected_users' in request.form:
            selected_users = request.form.getlist('selected_users[]')
            for user_id in selected_users:
                if MyCourse.query.filter_by(user_id=user_id).first():
                    flash('Clean error, first Mycourse table user_id!', 'error')
                    return redirect(url_for('edit_user', user_id=user_id))
                else:
                    user = User.query.get_or_404(int(user_id))
                    db.session.delete(user)
                    db.session.commit()
            flash('User cleaned', 'success')

    
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


        if 'clear_selected_courses' in request.form:
            selected_courses = request.form.getlist('selected_courses[]')
            for course_id in selected_courses:
                if ApprovedDegree.query.filter_by(course_id=course_id).first():
                    flash('Clean error, first ApprovedDegree table course_id!', 'error')
                    return redirect(url_for('edit_course', user_id=user_id))
                else:
                    course = Course.query.get_or_404(int(course_id))
                    db.session.delete(course) 
                    db.session.commit()
                
            flash('Adatok clear!', 'success')
            
        elif 'add_new_course' in request.form:
            new_code = request.form['new_code']
            new_name = request.form['new_name']
            new_credit = request.form['new_credit']

            # Ellenőrzés, hogy az adatok megfelelőek-e, és hozzáadás az adatbázishoz
            if new_code and new_name and new_credit:
                new_course = Course(code=new_code, name=new_name, credit=new_credit)
                db.session.add(new_course)
                db.session.commit()

                flash('Kurzus added', 'success')
            else:
                flash('Minden adat kell!', 'error')
    
    courses = Course.query.all()
    return render_template('admin_course_edit.html', courses=courses, user_id=user_id)

@app.route("/edit_approved_degrees/<int:user_id>", methods=['GET', 'POST'])
def edit_approved_degrees(user_id):
    if request.method == 'POST':
        if 'edit_selected_degrees' in request.form:
            selected_degrees = request.form.getlist('selected_degrees[]')

            for degree_id in selected_degrees:
                degree = ApprovedDegree.query.get_or_404(degree_id)
                new_course_id = request.form[f'course_id_{degree_id}']
                new_degree_id = request.form[f'degree_id_{degree_id}']
                if new_course_id and new_degree_id:
                    degree.course_id = new_course_id
                    degree.degree_id = new_degree_id

                db.session.commit()
                
            flash('Adatok update!', 'success')
            
        elif 'clear_selected_degrees' in request.form:
            selected_degrees = request.form.getlist('selected_degrees[]')

            for degree_id in selected_degrees:
                degree = ApprovedDegree.query.get_or_404(degree_id)
                db.session.delete(degree)
                db.session.commit()
                
            flash('Adatok clear!', 'success')

                    
        elif 'add_new_degree' in request.form:
            new_course_id = request.form['new_course_id']
            new_course_id_in_courses = Course.query.get(new_course_id)
            if not new_course_id_in_courses:
                flash('Nincs ilyen id-val kurzus!','error')
                approved_degrees = ApprovedDegree.query.all()
                return render_template('admin_approved.html', approved_degrees=approved_degrees, user_id=user_id)
            
            new_degree_id = request.form['new_degree_id']
            new_degree = ApprovedDegree(course_id=new_course_id, degree_id=new_degree_id)
            if new_course_id and new_degree_id and new_degree:

                db.session.add(new_degree)
                db.session.commit()
                flash('Adatok added!', 'success')
            
    approved_degrees = ApprovedDegree.query.all()
    return render_template('admin_approved.html', approved_degrees=approved_degrees, user_id=user_id)

@app.route("/edit_user_event/<int:user_id>", methods=['GET', 'POST'])
def edit_user_event(user_id):
    if request.method == 'POST':
        if 'edit_selected_events' in request.form:
            selected_events = request.form.getlist('selected_events[]')

            for event_id in selected_events:
                event = Events.query.get_or_404(event_id)
                new_name = request.form[f'name_{event_id}']
                new_description = request.form[f'description_{event_id}']

                event.name = new_name
                event.description = new_description
                db.session.commit()
            flash('Adatok update!', 'success')

        elif 'add_new_event' in request.form:
            new_course_id = request.form['new_course_id']
            new_name = request.form['new_name']
            new_description = request.form['new_description']

            if new_course_id and new_name and new_description:
                new_event = Events(course_id=new_course_id, name=new_name, description=new_description)
                db.session.add(new_event)
                db.session.commit()
                flash('Events added!', 'success')
            else:
                flash('Minden adat kell!', 'error')
                
        elif 'clear_selected_events' in request.form:
            selected_events = request.form.getlist('selected_events[]')
            
            for event_id in selected_events:
                    event = Events.query.get_or_404(event_id)
                    db.session.delete(event)
                    db.session.commit()    
                    flash('Events clear!', 'success')


    events = Events.query.all()
    return render_template('admin_events_edit.html', events=events, user_id=user_id)


@app.route("/edit_degrees/<int:user_id>", methods=['GET', 'POST'])
def edit_degrees(user_id):
    if request.method == 'POST':
        if 'edit_selected_degrees' in request.form:
            selected_degrees = request.form.getlist('selected_degrees[]')

            for degree_id in selected_degrees:
                degree = Degree.query.get_or_404(degree_id)
                new_name = request.form[f'name_{degree_id}']

                degree.name = new_name
                db.session.commit()
            flash('Adatok update!', 'success')
            
        elif 'clear_selected_degrees' in request.form:
            selected_degrees = request.form.getlist('selected_degrees[]')

            for degree_id in selected_degrees:
                if ApprovedDegree.query.filter_by(degree_id=degree_id).first():
                    flash('Clean error, first ApprovedDegree table course_id!', 'error')
                    return redirect(url_for('edit_degrees', user_id=user_id))
                else:
                    degree = Degree.query.get_or_404(degree_id)
                    db.session.delete(degree)
                    db.session.commit()
            flash('Degrees clear!', 'success')


        elif 'add_new_degree' in request.form:
            new_name = request.form['new_name']

            if new_name:
                new_degree = Degree(name=new_name)
                db.session.add(new_degree)
                db.session.commit()
                flash('Szak added!', 'success')
            else:
                flash('Minden adat kell', 'error')

    degrees = Degree.query.all()
    return render_template('admin_degrees_edit.html', degrees=degrees, user_id=user_id)