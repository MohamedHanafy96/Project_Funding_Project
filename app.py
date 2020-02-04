from flask import Flask
from flask import render_template, redirect, url_for, session
from decimal import Decimal
from flask import request
import ibm_db
import connect
import projects

app = Flask(__name__, template_folder='templates')
app.secret_key = "vbdgeiksgfnkeia"


@app.route('/', methods=["GET", "POST"])
def login():
    conn = connect.connection()
    myProjects = projects.getPrevProject()


    if request.method == "POST":

        mail = request.form["email"]
        password = request.form["password"]

        sql_stmt = ("select * from benutzer where email = '%s'") % mail
        benutzerResult = ibm_db.exec_immediate(conn, sql_stmt)
        ben_results = ibm_db.fetch_assoc(benutzerResult)

        sql_stmt = ("select * from konto where inhaber = '%s'") % mail
        kontoInfo = ibm_db.exec_immediate(conn, sql_stmt)
        konto_info = ibm_db.fetch_assoc(kontoInfo)

        if ben_results is not False and ben_results['EMAIL'] == mail and konto_info is not False and konto_info['GEHEIMZAHL'] == password:
            session["mail"] = mail
            session['logged_in'] = True

        else:
            session['logged_in'] = False
            session['error'] = 'Please input valid information to LOGIN'

        return redirect(url_for("project"))
    return render_template('login.html', prevProjects=myProjects)


@app.route('/logout')
def logout():
    session.pop("mail", None)
    return redirect(url_for("login"))


@app.route('/signup', methods=["GET", "POST"])
def signup():
    conn = connect.connection()
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]

        sql_stmt = "insert into benutzer (email, name) values ('" + email + "','" + username + "')"
        signupInfo = ibm_db.exec_immediate(conn, sql_stmt)

        sql_stmt = "insert into konto (inhaber, guthaben, geheimzahl) values ('" + email + "','9999','" + password + "')"
        signupInfo1 = ibm_db.exec_immediate(conn, sql_stmt)

        return redirect(url_for("login"))

    return render_template('signup.html')


@app.route('/userdetails/<email>')
def userdetails(email):
    conn = connect.connection()
    if "mail" in session:
        mail = session["mail"]
        userInfo = set()
        sql_stmt = "select * from benutzer where email = '%s'" % mail
        userInfoResult = ibm_db.exec_immediate(conn, sql_stmt)
        if userInfoResult is not None:
            row = ibm_db.fetch_tuple(userInfoResult)
            userInfo.add(row)
            while row:
                row = ibm_db.fetch_tuple(userInfoResult)
                if row:
                    userInfo.add(row)

        userInfo1 = set()  # number of created project
        sql_stmt = "select count(kennung) from projekt where ersteller = '%s'" % mail
        userInfoResult1 = ibm_db.exec_immediate(conn, sql_stmt)
        if userInfoResult1 is not None:
            row1 = ibm_db.fetch_tuple(userInfoResult1)
            userInfo1.add(row1)
            ref_info1 = row1[0]

        userInfo2 = set()  # number of donated project
        sql_stmt = "select count(projekt) from spenden where spender = '%s'" % mail
        userInfoResult2 = ibm_db.exec_immediate(conn, sql_stmt)
        if userInfoResult2 is not None:
            row2 = ibm_db.fetch_tuple(userInfoResult2)
            userInfo2.add(row2)
            ref_info2 = row2[0]

        usersProject = set()
        sql_stmt = (
                       "select kennung,titel,status,sum(spendenbetrag),ersteller,kategorie from projekt left join spenden on projekt.kennung = spenden.projekt where ersteller = '%s' group by kennung,titel,status,ersteller,kategorie ") % mail
        usersProjectResult = ibm_db.exec_immediate(conn, sql_stmt)
        if usersProjectResult is not None:
            row = ibm_db.fetch_tuple(usersProjectResult)
            usersProject.add(row)
            while row:
                row = ibm_db.fetch_tuple(usersProjectResult)
                if row:
                    usersProject.add(row)

        donatedProject = set()
        sql_stmt = "select kennung,titel,status,finanzierungslimit,kategorie,spendenbetrag from projekt inner join spenden on projekt.kennung=spenden.projekt inner join benutzer on benutzer.email=spenden.spender where benutzer.email = '%s'" % mail
        donatedProjectResult = ibm_db.exec_immediate(conn, sql_stmt)
        if donatedProjectResult is not None:
            row = ibm_db.fetch_tuple(donatedProjectResult)
            donatedProject.add(row)
            while row:
                row = ibm_db.fetch_tuple(donatedProjectResult)
                if row:
                    donatedProject.add(row)

        return render_template('userdetails.html', user_info=userInfo, users_project=usersProject, ref_info1=ref_info1,
                               ref_info2=ref_info2, donatedProject=donatedProject)
    else:
        return redirect(url_for("login"))


@app.route('/projects')
def project():
    if "mail" in session:

        conn = connect.connection()

        openProjects = set()
        sql_stmt = "select kennung,titel,finanzierungslimit,name,kategorie,status,ersteller from projekt inner join benutzer on projekt.ersteller=benutzer.email  where  ersteller = '%s' and status='offen'" % \
                   session["mail"]
        openProjectsResult = ibm_db.exec_immediate(conn, sql_stmt)
        if openProjectsResult is not None:
            row = ibm_db.fetch_tuple(openProjectsResult)
            openProjects.add(row)
            while row:
                row = ibm_db.fetch_tuple(openProjectsResult)
                if row:
                    openProjects.add(row)

        closeProjects = set()
        sql_stmt = "select kennung,titel,finanzierungslimit,name,kategorie,status,ersteller from projekt inner join benutzer on projekt.ersteller=benutzer.email  where  ersteller = '%s' and status='geschlossen'" % \
                   session["mail"]
        closeProjectsResult = ibm_db.exec_immediate(conn, sql_stmt)
        if closeProjectsResult is not None:
            row = ibm_db.fetch_tuple(closeProjectsResult)
            closeProjects.add(row)
            while row:
                row = ibm_db.fetch_tuple(closeProjectsResult)
                if row:
                    closeProjects.add(row)

        return render_template('projects.html', openProjects=openProjects, closeProjects=closeProjects,
                               ses_email=session["mail"])
    else:
        return redirect(url_for("login"))


@app.route('/projectdetails/<id>')
def projectdetails(id):
    conn = connect.connection()

    if "mail" in session:
        mail = session["mail"]
        prevProjects = set()
        sql_stmt = "select kennung,titel,name,projekt.beschreibung,finanzierungslimit,status,vorgaenger,email,kategorie,ersteller from projekt inner join benutzer on projekt.ersteller=benutzer.email  where  kennung = %s" % id
        prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt)
        if prevPorjectsResult is not None:
            row = ibm_db.fetch_tuple(prevPorjectsResult)
            prevProjects.add(row)
            ref_proj_id = row[6]
            ref_ersteller = row[9]
            ref_status = row[5]
            while row:
                row = ibm_db.fetch_tuple(prevPorjectsResult)
                if row:
                    prevProjects.add(row)

        prevProjects1 = set()
        if ref_proj_id is not None:
            sql_stmt = "select kennung,titel from projekt where kennung = %s" % ref_proj_id
            prevPorjectsResult1 = ibm_db.exec_immediate(conn, sql_stmt)
            if prevPorjectsResult1 is not None:
                row1 = ibm_db.fetch_tuple(prevPorjectsResult1)
                prevProjects1.add(row1)
                ref_proj_id = row1[0]
                ref_proj_title = row1[1]
        else:
            ref_proj_id = ''
            ref_proj_title = 'No Predecessor'

        comments = set()
        sql_stmt = "select name,text,sichtbarkeit from benutzer inner join komment on benutzer.email=komment.benutzer where komment.projekt = %s and sichtbarkeit='oeffentlich'" % id
        commentsResult = ibm_db.exec_immediate(conn, sql_stmt)
        if commentsResult is not None:
            row = ibm_db.fetch_tuple(commentsResult)
            comments.add(row)
            while row:
                row = ibm_db.fetch_tuple(commentsResult)
                if row:
                    comments.add(row)

        donationInfo = set()
        sql_stmt = "select name,spendenbetrag,sichtbarkeit from spenden inner join benutzer on spenden.spender=benutzer.email where  projekt = %s and sichtbarkeit='oeffentlich'" % id
        donationInfoResult = ibm_db.exec_immediate(conn, sql_stmt)
        if donationInfoResult is not None:
            row = ibm_db.fetch_tuple(donationInfoResult)
            donationInfo.add(row)
            while row:
                row = ibm_db.fetch_tuple(donationInfoResult)
                if row:
                    donationInfo.add(row)



        return render_template('projectdetails.html', prevProjects=prevProjects, ref_proj_title=ref_proj_title,
                               ref_proj_id=ref_proj_id, donationInfo=donationInfo, id=id, comments=comments,
                               ref_ersteller=ref_ersteller, mail=mail, ref_status=ref_status)
    else:
        return redirect(url_for("login"))


@app.route('/projectedit/<id>', methods=["GET", "POST"])
def projectedit(id):
    conn = connect.connection()
    if "mail" in session:
        prevProjects = set()
        sql_stmt = "select * from projekt where kennung = %s" % id
        prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt)
        if prevPorjectsResult is not None:
            row = ibm_db.fetch_tuple(prevPorjectsResult)
            prevProjects.add(row)
            while row:
                row = ibm_db.fetch_tuple(prevPorjectsResult)
                if row:
                    prevProjects.add(row)

        sql_stmt = "select id,name from kategorie"
        categoryResult = ibm_db.exec_immediate(conn, sql_stmt)
        category = set()
        if prevPorjectsResult is not None:
            row = ibm_db.fetch_tuple(categoryResult)
            category.add(row)
            while row:
                row = ibm_db.fetch_tuple(categoryResult)
                if row:
                    category.add(row)

        mail = session["mail"]
        sql_stmt = ("select kennung, titel from projekt where kennung <> '" + id + "' and ersteller = '%s'") % mail
        predecessorNameResult = ibm_db.exec_immediate(conn, sql_stmt)
        predecessorName = set()
        if prevPorjectsResult is not None:
            row = ibm_db.fetch_tuple(predecessorNameResult)
            predecessorName.add(row)
            while row:
                row = ibm_db.fetch_tuple(predecessorNameResult)
                if row:
                    predecessorName.add(row)

        if request.method == "POST":
            title = request.form["titles"]
            details = request.form["details"]
            amount = request.form["funding_limit"]
            cat_id = request.form["category_id"]
            pred_id = request.form["predecessor_id"]
            if pred_id == "":
                sql_stmt = "update projekt set titel = '" + title + "', beschreibung= '" + details + "', finanzierungslimit = '" + amount + "', kategorie = '" + cat_id + "',vorgaenger = NULL where kennung = %s" % id
                prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt)
            else:
                sql_stmt = "update projekt set titel = '" + title + "', beschreibung= '" + details + "', finanzierungslimit = '" + amount + "', kategorie = '" + cat_id + "',vorgaenger = '" + pred_id + "' where kennung = %s" % id
                prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt)

            return redirect(url_for("projectdetails", id=id))

        return render_template('projectedit.html', prevProjects=prevProjects, category_lists=category,
                               predecessor_list=predecessorName)
    else:
        return redirect(url_for("login"))


@app.route('/newproject', methods=["GET", "POST"])
def newproject():
    conn = connect.connection()
    if "mail" in session:
        if request.method == "POST":
            title = request.form["titles"]
            details = request.form["details"]
            amount = request.form["funding_limit"]
            cat_id = request.form["category_id"]
            pre_id = request.form["predecessor_id"]
            if pre_id == "":
                sql_stmt = "insert into projekt (titel, beschreibung, finanzierungslimit,ersteller,kategorie,vorgaenger) values ('" + title + "','" + details + "','" + amount + "','" + \
                           session["mail"] + "','" + cat_id + "', Null)"
                prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt)
            else:
                sql_stmt = "insert into projekt (titel, beschreibung, finanzierungslimit,ersteller,kategorie,vorgaenger) values ('" + title + "','" + details + "','" + amount + "','" + \
                           session["mail"] + "','" + cat_id + "','" + pre_id + "')"
                prevPorjectsResult1 = ibm_db.exec_immediate(conn, sql_stmt)
            return redirect(url_for("project"))

        sql_stmt = "select id,name from kategorie"
        prevCategoryResult = ibm_db.exec_immediate(conn, sql_stmt)
        prevCategory = set()
        if prevCategoryResult is not None:
            row = ibm_db.fetch_tuple(prevCategoryResult)
            prevCategory.add(row)
            while row:
                row = ibm_db.fetch_tuple(prevCategoryResult)
                if row:
                    prevCategory.add(row)

        mail = session["mail"]
        sql_stmt = ("select kennung, titel from projekt where ersteller = '%s'") % mail
        prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt)
        prevProjects = set()
        if prevPorjectsResult is not None:
            row = ibm_db.fetch_tuple(prevPorjectsResult)
            prevProjects.add(row)
            while row:
                row = ibm_db.fetch_tuple(prevPorjectsResult)
                if row:
                    prevProjects.add(row)



        return render_template('newprojects.html', category_lists=prevCategory, predecessor_list=prevProjects)
    else:
        return redirect(url_for("login"))


@app.route('/search', methods=["GET", "POST"])
def search():
    conn = connect.connection()
    if "mail" in session:
        if request.method == "POST":
            title = request.form["title"]
            sql_stmt = "select kennung,titel,ersteller,status,sum(spendenbetrag),kategorie,name from projekt left join spenden on projekt.kennung = spenden.projekt inner join benutzer on projekt.ersteller=benutzer.email where upper(titel) like upper('" + title + "%') group by kennung,name,kategorie,titel,status,ersteller"
            searchPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt)
            searchProjects = set()
            if searchPorjectsResult is not None:
                row = ibm_db.fetch_tuple(searchPorjectsResult)
                searchProjects.add(row)
                while row:
                    row = ibm_db.fetch_tuple(searchPorjectsResult)
                    if row:
                        searchProjects.add(row)

            return render_template('search.html', searchProjects=searchProjects, search_val=title)

        return render_template('search.html')
    else:
        return redirect(url_for("login"))


@app.route('/delete/<id>', methods=["GET", "POST"])
def delete(id):
    conn = connect.connection()
    #delete = "no"
    if "mail" in session:

        prevProjects = set()
        sql_stmt = "select * from projekt where kennung = %s" % id
        prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt)
        if prevPorjectsResult is not None:
            row = ibm_db.fetch_tuple(prevPorjectsResult)
            prevProjects.add(row)
            while row:
                row = ibm_db.fetch_tuple(prevPorjectsResult)
                if row:
                    prevProjects.add(row)
        if request.method == "POST":
            sql_stmt = ("select * from projekt  where vorgaenger = '%s'") % id
            predecessorInfo = ibm_db.exec_immediate(conn, sql_stmt)
            predecessor_Info = ibm_db.fetch_assoc(predecessorInfo)
            print(predecessor_Info)
            if not predecessor_Info:
                sql_stmt1 = "delete from komment where projekt = '" + id + "'"
                prevPorjectsResult1 = ibm_db.exec_immediate(conn, sql_stmt1)

                sql_stmt2 = "delete from spenden where projekt = '" + id + "'"
                prevPorjectsResult1 = ibm_db.exec_immediate(conn, sql_stmt2)

                sql_stmt3 = "delete from projekt where kennung = %s" % id
                prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt3)
            else:
                sql_stmt1 = "delete from komment where projekt = %s" % predecessor_Info['KENNUNG']
                prevPorjectsResult1 = ibm_db.exec_immediate(conn, sql_stmt1)

                sql_stmt2 = "delete from spenden where projekt = %s" % predecessor_Info['KENNUNG']
                prevPorjectsResult1 = ibm_db.exec_immediate(conn, sql_stmt2)

                sql_stmt3 = "delete from projekt where kennung = %s" % predecessor_Info['KENNUNG']
                prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt3)

                sql_stmt1 = "delete from komment where projekt = '" + id + "'"
                prevPorjectsResult1 = ibm_db.exec_immediate(conn, sql_stmt1)

                sql_stmt2 = "delete from spenden where projekt = '" + id + "'"
                prevPorjectsResult1 = ibm_db.exec_immediate(conn, sql_stmt2)

                sql_stmt3 = "delete from projekt where kennung = %s" % id
                prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt3)
            return redirect(url_for("project", ))

        return render_template('delete.html', prevProjects=prevProjects)
    else:
        return redirect(url_for("login"))


@app.route('/comment/<id>', methods=["GET", "POST"])
def comment(id):
    conn = connect.connection()
    if "mail" in session:
        prevProjects = set()
        sql_stmt = "select * from projekt where kennung = %s" % id
        prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt)
        if prevPorjectsResult is not None:
            row = ibm_db.fetch_tuple(prevPorjectsResult)
            prevProjects.add(row)
            while row:
                row = ibm_db.fetch_tuple(prevPorjectsResult)
                if row:
                    prevProjects.add(row)

        if request.method == "POST":
            comment = request.form["comment"]
            anonymousid = request.form["anonymousid"]
            mail = session["mail"]
            if anonymousid == 'yes':
                sql_stmt1 = "insert into komment (text,benutzer,projekt,sichtbarkeit) values ('" + comment + "' , '" + mail + "', '" + id + "','privat')"
                prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt1)
            else:
                sql_stmt2 = "insert into komment (text,benutzer,projekt,sichtbarkeit) values ('" + comment + "' , '" + mail + "', '" + id + "','oeffentlich')"
                prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt2)
            return redirect(url_for("projectdetails", id=id))

        return render_template('comment.html', prevProjects=prevProjects)

    else:
        return redirect(url_for("login"))


@app.route('/donate/<id>', methods=["GET", "POST"])
def donate(id):
    conn = connect.connection()
    noDonation = ""
    tem_dcheque = ""
    if "mail" in session:
        mail = session["mail"]
        prevProjects = set()
        sql_stmt = "select * from projekt where kennung = %s" % id
        prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt)
        if prevPorjectsResult is not None:
            row = ibm_db.fetch_tuple(prevPorjectsResult)
            prevProjects.add(row)
            while row:
                row = ibm_db.fetch_tuple(prevPorjectsResult)
                if row:
                    prevProjects.add(row)

            sql_stmt = "select * from spenden  where  spender = '" + mail + "' and projekt = '" + id + "'"
            donationcheque = ibm_db.exec_immediate(conn, sql_stmt)
            donation_cheque = ibm_db.fetch_assoc(donationcheque)
            if donation_cheque is False:
                tem_dcheque = "possible"

            if request.method == "POST":
                donate = request.form["donate"]
                deciDeoneat = Decimal(donate)
                anonymousid = request.form["anonymousid"]


                balanceCheque = set()
                sql_stmt4 = "select * from konto  where inhaber = '" + mail + "'"
                balanceChequeResult = ibm_db.exec_immediate(conn, sql_stmt4)
                if balanceChequeResult is not None:
                    row1 = ibm_db.fetch_tuple(balanceChequeResult)
                    balanceCheque.add(row1)

                    currentBalance = Decimal(row1[1])
                    print(currentBalance, type(currentBalance))

                if currentBalance >= deciDeoneat:

                    print(deciDeoneat, type(deciDeoneat))
                    if anonymousid == 'yes':
                        sql_stmt = "insert into spenden (spender,projekt,spendenbetrag,sichtbarkeit) values ('" + mail + "','" + id + "' , '" + donate + "','privat')"
                        prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt)
                    else:
                        sql_stmt1 = "insert into spenden (spender,projekt,spendenbetrag,sichtbarkeit) values ('" + mail + "','" + id + "' , '" + donate + "','oeffentlich')"
                        prevPorjectsResult = ibm_db.exec_immediate(conn, sql_stmt1)

                    spendenInfo = set()
                    sql_stmt2 = (
                                    "select kennung,titel,sum(spendenbetrag),ersteller,finanzierungslimit from projekt left join spenden on projekt.kennung = spenden.projekt where kennung = '%s' group by kennung,titel,ersteller,finanzierungslimit ") % id
                    spendenInfoResult = ibm_db.exec_immediate(conn, sql_stmt2)
                    if spendenInfoResult is not None:
                        row1 = ibm_db.fetch_tuple(spendenInfoResult)
                        spendenInfo.add(row1)
                        ref_sum = row1[2]
                        ref_limit = row1[4]
                    tem_sum = Decimal(ref_sum)
                    tem_limit = Decimal(ref_limit)

                    if tem_sum >= tem_limit:
                        sql_stmt3 = "update projekt set status = 'geschlossen' where kennung = %s" % id
                        prorjectStatusResult = ibm_db.exec_immediate(conn, sql_stmt3)

                    balanceReduce = set()
                    sql_stmt4 = "select * from konto  where inhaber = '" + mail + "'"
                    balanceReduceResult = ibm_db.exec_immediate(conn, sql_stmt4)
                    if balanceReduceResult is not None:
                        row1 = ibm_db.fetch_tuple(balanceReduceResult)
                        balanceReduce.add(row1)
                        prev_balance = row1[1]
                        temp_bal = Decimal(prev_balance)
                        newBalance = temp_bal - deciDeoneat
                        print(newBalance, type(newBalance))
                        tempNewBal = str(newBalance)
                        print(tempNewBal, type(tempNewBal))
                        sql_stmt3 = "update konto set guthaben = '" + tempNewBal + "' where inhaber = '" + mail + "'"
                        prorjectStatusResult = ibm_db.exec_immediate(conn, sql_stmt3)

                        return redirect(url_for("projectdetails", id=id))
                else:
                    noDonation = "yes"

        return render_template('donate.html', prevProjects=prevProjects, noDonation=noDonation, tem_dcheque=tem_dcheque)

    else:
        return redirect(url_for("login"))


if __name__ == '__main__':
    app.run()
