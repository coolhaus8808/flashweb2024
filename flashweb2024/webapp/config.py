import os

class Config(object):
    SECRET_KEY = os.environ.get('b_5#y2L"F4Q8z\n\xec]/') or 'hard_to_guess_secret'
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://freedb_mysql:JjkS2MB?65q5*bx@sql.freedb.tech:3306/freedb_mysql."
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    sozas = "fuszeres_vaj"