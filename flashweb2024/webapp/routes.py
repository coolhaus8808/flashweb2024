from flask import render_template, request, redirect, url_for, flash, session
from webapp import app, db
from webapp.models import User, MyCourse, Course, Degree, ApprovedDegree


@app.route("/")
@app.route("/index")
def index():
    
     users = User.query.all()
     return render_template('index.html', users=users)


@app.route("/login", methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    session['username'] = username
    session['password'] = password
    

    # Felhasználó lekérése az adatbázisból
    user = User.query.filter_by(username=username).first()
    
    # Ellenõrzés, hogy a felhasználó létezik és a megadott jelszó megfelelõ
    if user and user.check_password(password):
        session['userid'] = user.id
        # Ha a felhasználónév és jelszó megfelelõ, átirányítás az user.html oldalra
        return redirect(url_for('user', user_id=user.id))
    else:
        # Ha a felhasználónév vagy jelszó helytelen, visszairányítás az index.html oldalra
        flash('Incorrect username or password', 'error')
        return redirect(url_for('index'))
    

@app.route("/user/<int:user_id>")
def user(user_id):
    # Felhasználó kurzusainak lekérése az adatbázisból
    if session['username']!="":
        user = User.query.get_or_404(user_id)
        mycourses = MyCourse.query.filter_by(user_id=user_id).all()
        courses = Course.query.all()
    

        degrees = ApprovedDegree.query.distinct(ApprovedDegree.degree_id).all()
        return render_template('user.html',user=user.username, user_id=user_id, mycourses=mycourses, courses=courses, degrees=degrees)
    


@app.route("/register", methods=['POST'])
def register():
    username = request.form['reg_username']
    password = request.form['reg_password']
    name = request.form['reg_name']
    degree_id = request.form['reg_degree']

    # Ellenõrizzük, hogy a felhasználónév már létezik-e az adatbázisban
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('Foglalt username', 'registration_error')
        return redirect(url_for('index', _anchor='registration'))

    # Ha a felhasználónév még nem létezik, hozzáadjuk az új felhasználót az adatbázishoz
    new_user = User(username=username, password=password, name=name, degree_id=degree_id)
    db.session.add(new_user)
    db.session.commit()
    
    flash('Registration succes!', 'registration_success')
    return redirect(url_for('index', _anchor='registration'))


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

        # GET kérés esetén a kurzus felvétele oldal megjelenítése
    user = User.query.get_or_404(user_id)
    user_degree_id = user.degree_id
    available_courses = Course.query.join(ApprovedDegree).filter(ApprovedDegree.degree_id == user_degree_id).all()

    return render_template('kurzusfelvetel.html', user_id=user_id, available_courses=available_courses)




@app.route("/logout", methods=["POST"])
def logout():
    

    session.clear()
    # Átirányítás az index oldalra
    return render_template("index.html")