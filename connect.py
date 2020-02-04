import flask
import ibm_db
def connection():
    try:
        connect = ibm_db.pconnect(
            "DATABASE=funder;HOSTNAME=dione.is.inf.uni-due.de;PORT=50008;PROTOCOL=TCPIP;UID=dbp008;PWD=quee3ahm;", "",
            "")
    except Exception as e:
        print(e)
    return connect
