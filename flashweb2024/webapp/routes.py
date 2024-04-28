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
    

    # Felhaszn�l� lek�r�se az adatb�zisb�l
    user = User.query.filter_by(username=username).first()
    
    # Ellen�rz�s, hogy a felhaszn�l� l�tezik �s a megadott jelsz� megfelel�
    if user and user.check_password(password):
        session['userid'] = user.id
        # Ha a felhaszn�l�n�v �s jelsz� megfelel�, �tir�ny�t�s az user.html oldalra
        return redirect(url_for('user', user_id=user.id))
    else:
        # Ha a felhaszn�l�n�v vagy jelsz� helytelen, visszair�ny�t�s az index.html oldalra
        flash('Incorrect username or password', 'error')
        return redirect(url_for('index'))
    

@app.route("/user/<int:user_id>")
def user(user_id):
    # Felhaszn�l� kurzusainak lek�r�se az adatb�zisb�l
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

    # Ellen�rizz�k, hogy a felhaszn�l�n�v m�r l�tezik-e az adatb�zisban
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('Foglalt username', 'registration_error')
        return redirect(url_for('index', _anchor='registration'))

    # Ha a felhaszn�l�n�v m�g nem l�tezik, hozz�adjuk az �j felhaszn�l�t az adatb�zishoz
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

        # GET k�r�s eset�n a kurzus felv�tele oldal megjelen�t�se
    user = User.query.get_or_404(user_id)
    user_degree_id = user.degree_id
    available_courses = Course.query.join(ApprovedDegree).filter(ApprovedDegree.degree_id == user_degree_id).all()

    return render_template('kurzusfelvetel.html', user_id=user_id, available_courses=available_courses)




@app.route("/logout", methods=["POST"])
def logout():
    

    session.clear()
    # �tir�ny�t�s az index oldalra
    return render_template("index.html")