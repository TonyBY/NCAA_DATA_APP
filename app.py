from flask import Flask, render_template, url_for, request, redirect
from flask_bootstrap import Bootstrap
import time
import json
import cx_Oracle as oracle
from Configuration.Config import parse_config_input
import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# initialize flask application
app = Flask(__name__)
bootstrap = Bootstrap(app)
# declare constants for flask app
cfg = parse_config_input("./Configuration/config.yml")
HOST = cfg['HOST']
PORT = cfg['PORT']

DB_IP = cfg['DB_IP']
DB_PORT = cfg['DB_PORT']
SID = cfg['SID']
DB_USER = cfg['DB_USER']
DB_PASSWORD = cfg['DB_PASSWORD']

# make dsn and create connection to db
dsn_tns = oracle.makedsn(DB_IP, DB_PORT, SID)

connection = oracle.connect(DB_USER, DB_PASSWORD, dsn_tns)
cur = connection.cursor()

cur.execute('''
            BEGIN
                EXECUTE IMMEDIATE 'CREATE TABLE NCAA_Pro_Users ( 
                                    username varchar(255) NOT NULL PRIMARY KEY,
                                    password varchar(255) NOT NULL)';
            EXCEPTION
                WHEN OTHERS THEN NULL;
            END;
            ''')# EXECUTE IMMEDIATE 'DROP TABLE NCAA_PRO_USERS';
cur.close()


# Login Page
@app.route('/',  methods=['POST', 'GET'])
def index():
    cur = connection.cursor()
    if request.method == 'POST':
        username = request.form["email"]
        print("username:", username)
        password = request.form["pass"]
        print("password:", password)
        # date_created = time.strftime('%Y/%m/%d %H:%M:%S')
        try:
            # cur.execute("SELECT password FROM NCAA_Pro_Users WHERE username='%s'" % username)
            cur.execute("SELECT password FROM NCAA_PRO_USERS WHERE username='%s'" % username)
            print("SELECT password FROM NCAA_PRO_USERS WHERE username='%s'" % username)
            real_password = cur.fetchone()[0]
            print("real password:", real_password)
            if password == real_password:
                return render_template('home.html', user=username.split('@')[0])
            else:
                return "Wrong Password Please Try Again"
        except Exception as e:
            print(e)
            return "User Name Does Not Exist Please Try Again"
        primary_key = cur.fetchall()
        # if primary_key != []:
        #     id = primary_key[-1][0] + 1
        # else:
        #     id = 0
        values = (username, password)
        try:
            cur.execute("INSERT INTO  NCAA_PRO_USERS VALUES ('%s', '%s')" % values)
            connection.commit()
            return redirect('/')
        except:
            return 'There was an issue adding your task' + str(id)
    elif request.method == 'GET':
        return render_template('index.html')


# Signup Page
@app.route('/signup', methods=['POST', 'GET'])
def sign_up():
    cur = connection.cursor()
    if request.method == 'POST':
        username = request.form["email"]
        print("username:", username)
        password = request.form["pass"]
        print("password:", password)
        re_password = request.form["re_pass"]
        print("re_password:", re_password)
        if password != re_password:
            return "Make sure you have typed in the same password, please try again"
        else:
            values = (username, password)
            print(values)
            try:
                cur.execute("INSERT INTO NCAA_PRO_USERS VALUES ('%s', '%s')" % values)
                connection.commit()
                cur.execute("SELECT password FROM NCAA_PRO_USERS WHERE username='%s'" % username)
                real_password = cur.fetchone()[0]
                print("registered password:", real_password)
                return render_template('sign_up_success.html')
            except Exception as e:
                print(e)
                return 'User has already exist!'
    elif request.method == 'GET':
        return render_template('signup.html')


# Back to home page
@app.route('/home')
def back_home():
    return render_template('home.html')


# Sample Query Visualization
@app.route('/graph')
def hello():
    img = BytesIO()
    results = []
    cur = connection.cursor()
    cur.execute('''SELECT conference.name, count(team_code)
                from acolas.team, acolas.conference
                where team.conference_code = conference.conference_code and team.year = conference.year and conference.year = 2013 and conference.subdivision = 'FBS'
                group by conference.name''')
    for row in cur.fetchall():
        results.append(row)

    names = [result[0] for result in results]  
    number = [result[1] for result in results]

    y_pos = np.arange(len(names))

    plt.bar(y_pos, number, align='edge',width=0.5, alpha=0.5)
    plt.xticks(y_pos, names, rotation=65)
    plt.ylabel('Number of teams')
    plt.title('Number of FBS Teams in 2013')
    plt.tight_layout()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    buffer = b''.join(img)

    plot_buffer = base64.b64encode(buffer)
    barplt = plot_buffer.decode('utf-8')
    return render_template('bar.html', barplt=barplt)

# Interesting Trends List
@app.route('/interesting_trends_list')
def interesting_trends_list():
    return render_template('interesting_trends_list.html')

# Team List
@app.route('/team_list')
def team_list():
    if request.method == 'POST':
        data = (request.form.get("teamname", None), "trend")
        print("trend:", data)
        return render_template('team_list.html', data=data)

#Trend Query
@app.route('/query1', methods=['GET', 'POST'])
def query1():
    if request.method == 'GET':
        teams = []
        cur = connection.cursor()
        cur.execute('''SELECT UNIQUE name FROM acolas.team''')
        for team in cur.fetchall():
            teams.append(str(team[0]))
            print(team[0])
        print(teams)
        return render_template('query1.html', teams=json.dumps(teams))
    elif request.method == 'POST':
        img = BytesIO()
        name = str(request.form.get("teams"))
        print(name)
        results = []
        cur = connection.cursor()
        cur.execute('''SELECT year, SUM(rush_touchdown), SUM(pass_touchdown)
                            from acolas.team NATURAL JOIN ACOLAS.team_game_statistics
                            WHERE name='%s'
                            GROUP BY year
                            order by year asc''' % name)

        for row in cur.fetchall():
            results.append(row)

        year = [result[0] for result in results]
        num_rush = [result[1] for result in results]
        num_pass = [result[2] for result in results]

        # y_pos = np.arange(len(names))

        plt.plot(year, num_rush, 's-', color='r', label="rush number")
        plt.plot(year, num_pass, 'o-', color='g', label="pass number")
        plt.ylabel('Number of Touchdown')
        plt.title('Query one')
        plt.legend(loc="best")
        plt.tight_layout()
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)
        # buffer0 = b''.join(img)

        plot_buffer0 = base64.b64encode(img.getvalue())
        q1plt = plot_buffer0.decode('utf-8')
        teams = []
        cur = connection.cursor()
        cur.execute('''SELECT UNIQUE name FROM acolas.team''')
        for team in cur.fetchall():
            teams.append(str(team[0]))
            print(team[0])
        return render_template('query1.html', q1plt=q1plt, teams=json.dumps(teams))

# Trends Visualizations
@app.route('/trends', methods=['POST', 'GET'])
def show_trends():
    query_template_for_trends = ''  # put the sql template of trends here
    results = []
    cur = connection.cursor()
    if request.method == 'POST':
        data = (request.form.get("trends", None), "data")
        print("trend:", data)
        query = ''  # construct the final query using the template and the team name
        #
        # try:
        #     cur.execute(query)
        #     for row in cur.fetchall():
        #         results.append(row)

            # Place Holder for code for visualization

        return render_template('trends.html', data=data)
        # except Exception as e:
        #     print(e)
        #     return 'There is something wrong!'
    # elif request.method == 'GET':
    #     return render_template('trends.html')

# Head to head page
@app.route('/head_to_head', methods=['POST', 'GET'])
def head_to_head():
    query_template_for_head_to_head = ''  # put the sql template of head_to_head here
    results = []
    cur = connection.cursor()
    if request.method == 'POST':
        team = request.form["team"]
        print("team:", team)
        best_or_worst = request.form["best_or_worst"]
        print("best_or_worst:", best_or_worst)
        query = ''  # construct the final query using the template, the team name, and the best_or_worst.

        try:
            cur.execute(query)
            for row in cur.fetchall():
                results.append(row)

            # Place Holder for code for visualization

            return render_template('head_to_head.html')
        except Exception as e:
            print(e)
            return 'There is something wrong!'
    elif request.method == 'GET':
        return render_template('head_to_head.html')


# Quick QA page
@app.route('/quick_qa', methods=['POST', 'GET'])
def quick_qa():
    query_template_for_quick_qa = ''  # put the sql template of quick qa here
    results = []
    cur = connection.cursor()
    if request.method == 'POST':
        team = request.form["team"]
        print("team:", team)
        best_or_worst = request.form["best_or_worst"]
        print("best_or_worst:", best_or_worst)
        query = ''  # construct the final query using the template, the team name, and the best_or_worst.

        try:
            cur.execute(query)
            for row in cur.fetchall():
                results.append(row)

            # Place Holder for code for visualization

            return render_template('head_to_head.html')
        except Exception as e:
            print(e)
            return 'There is something wrong!'
    elif request.method == 'GET':
        return render_template('head_to_head.html')


if __name__ == '__main__':
    app.run(host=HOST,
            debug=True,
            use_reloader=False,
            port=PORT)