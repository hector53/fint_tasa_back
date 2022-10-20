import pymysql
from app.conf import *

def register_user(sql, params):
    con = pymysql.connect(host=host,   user=userDb,   password=userPass,    db=database)
    try:
        with con.cursor() as cur:
            cur.execute(sql, params )
            con.commit()
            return {"status": 1, "id": cur.lastrowid}
    except pymysql.Error as e:
        print("errrorr", e)
        return {"status": 0, "error": e.args[1]}
    finally:
        con.close()

def insert_data(sql, params):
    con = pymysql.connect(host=host,   user=userDb,   password=userPass,    db=database)
    try:
        with con.cursor() as cur:
            cur.execute(sql, params )
            con.commit()
            return {"status": 1, "id": cur.lastrowid}
    except pymysql.Error as e:
        print("errrorr", e)
        return {"status": 0, "error": e.args[1]}
    finally:
        con.close()

def verificar_email(email, sql):
    con = pymysql.connect(host=host,   user=userDb,   password=userPass,    db=database)
    try:
        with con.cursor() as cur:
            cur.execute(sql, (email) )
            rows = cur.fetchone()
            return rows
    finally:
        con.close()

def getData(consulta, params):
    con = pymysql.connect(host=host,   user=userDb,   password=userPass,    db=database)
    try:
        with con.cursor() as cur:
            cur.execute(consulta, params)
            rows = cur.fetchall()
            return rows
    finally:
        con.close()
def getDataOne(consulta, params):
    con = pymysql.connect(host=host,   user=userDb,   password=userPass,    db=database)
    try:
        with con.cursor() as cur:
            cur.execute(consulta, params)
            rows = cur.fetchone()
            return rows
    finally:
        con.close()
def getDataOneOnly(consulta):
    con = pymysql.connect(host=host,   user=userDb,   password=userPass,    db=database)
    try:
        with con.cursor() as cur:
            cur.execute(consulta)
            rows = cur.fetchone()
            return rows
    finally:
        con.close()


def updateData(consulta, params):
    con = pymysql.connect(host=host,   user=userDb,   password=userPass,    db=database)
    try:
        with con.cursor() as cur:
            guardar = cur.execute(consulta, params)
            con.commit()
            return cur.lastrowid
    finally:
        con.close()