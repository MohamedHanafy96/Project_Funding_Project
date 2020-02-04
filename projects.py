import ibm_db
import flask
import connect

conn = connect.connection()
def getPrevProject():
    prevProjects = set()
    sql_stmt = "select * from projekt"
    prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt)
    if prevPorjectsResult is not None:
        row = ibm_db.fetch_tuple(prevPorjectsResult)
        prevProjects.add(row)
        while row:
            row = ibm_db.fetch_tuple(prevPorjectsResult)
            if row:
                prevProjects.add(row)

    return prevProjects
