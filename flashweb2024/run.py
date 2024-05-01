from webapp import app
import mysql.connector

if __name__ == "__main__":
    try:
        mydb = mysql.connector.connect(
            host="sql.freedb.tech",
            port=3306,
            database="freedb_mysql.",
            user="freedb_mysql",
            password="JjkS2MB?65q5*bx"
        )
        print("Sikeres csatlakozas")
        
        # Ha sikeres a csatlakozás, akkor indítsuk el az alkalmazást
        app.run(host='localhost', port=5555)

    except mysql.connector.Error as err:
        print("Hiba a csatlakozaskor:", err)