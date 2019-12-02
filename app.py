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

    plt.bar(y_pos, number, align='edge', width=0.5, alpha=0.5)
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

# Interesting Trends List
@app.route('/simple')
def simple():
    return render_template('simple.html')


# Trend Querys
@app.route('/query1', methods=['GET', 'POST'])
def query1():
    if request.method == 'GET':
        teams = []
        cur = connection.cursor()
        cur.execute('''SELECT UNIQUE name FROM acolas.team''')
        for team in cur.fetchall():
            teams.append(str(team[0]))
        return render_template('query1.html', teams=json.dumps(teams))
    elif request.method == 'POST':
        img = BytesIO()
        name = str(request.form.get("teams"))
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

        plt.plot(year, num_rush, 's-', color='r', label="rush")
        plt.plot(year, num_pass, 'o-', color='g', label="pass")
        plt.ylabel('Number of Touchdown')
        plt.xlabel('year')
        plt.title('Touchdown number of %s by rush/pass' % name)
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
        return render_template('query1.html', q1plt=q1plt, teams=json.dumps(teams))


@app.route('/query2', methods=['GET', 'POST'])
def query2():
    if request.method == 'GET':
        teams = []
        cur = connection.cursor()
        cur.execute('''SELECT UNIQUE name FROM acolas.team''')
        for team in cur.fetchall():
            teams.append(str(team[0]))
        return render_template('query2.html', teams=json.dumps(teams))
    elif request.method == 'POST':
        img = BytesIO()
        name = str(request.form.get("teams"))
        print(name)
        results = []
        cur = connection.cursor()
        cur.execute('''
        SELECT * FROM (SELECT unique(team.name) playagainst, result.no_of_home_team_win/(result.no_of_home_team_win+result.no_of_visit_team_win)*100 win_percent
                        FROM acolas.team team, (
                        SELECT visitteam.visit_team, NVL(no_of_home_team_win,0) no_of_home_team_win, NVL(no_of_visit_team_win,0) no_of_visit_team_win FROM  
                        (SELECT visit_team  FROM (
                        SELECT home.hometeamcode, home.game_code, home.points_of_home_team, game.visit_team visit_team, tgs.points points_of_visit_team
                        FROM ACOLAS.game game, ACOLAS.team_game_statistics tgs, acolas.team team, 
                        (SELECT tgs.team_code hometeamcode, game.game_code game_code, points points_of_home_team
                        FROM acolas.game game, ACOLAS.team_game_statistics tgs, acolas.team team
                        WHERE game.home_team=tgs.team_code AND game.game_code=tgs.game_code AND team.name='%s') home
                        WHERE home.game_code=game.game_code AND team.name='%s' 
                        AND tgs.game_code=game.game_code AND tgs.team_code=game.visit_team AND game.home_team=team.team_code
                        ORDER BY visit_team)
                        GROUP BY visit_team) visitteam  
                        FULL OUTER JOIN 
                        (
                        SELECT visit_team, COUNT(*) no_of_home_team_win 
                        FROM (
                        SELECT home.hometeamcode, home.game_code, home.points_of_home_team, game.visit_team visit_team, tgs.points points_of_visit_team
                        FROM ACOLAS.game game, ACOLAS.team_game_statistics tgs, acolas.team team, 
                        (SELECT tgs.team_code hometeamcode, game.game_code game_code, points points_of_home_team
                        FROM acolas.game game, ACOLAS.team_game_statistics tgs, acolas.team team
                        WHERE game.home_team=tgs.team_code AND game.game_code=tgs.game_code AND team.name='%s') home
                        WHERE home.game_code=game.game_code AND team.name='%s' 
                        AND tgs.game_code=game.game_code AND tgs.team_code=game.visit_team AND game.home_team=team.team_code
                        ORDER BY visit_team
                        )
                        WHERE points_of_home_team > points_of_visit_team
                        GROUP BY visit_team) homewin ON visitteam.visit_team=homewin.visit_team
                        FULL OUTER JOIN (
                        SELECT visit_team, COUNT(*) no_of_visit_team_win 
                        FROM (
                        SELECT home.hometeamcode, home.game_code, home.points_of_home_team, game.visit_team visit_team, tgs.points points_of_visit_team
                        FROM ACOLAS.game game, ACOLAS.team_game_statistics tgs, acolas.team team, 
                        (SELECT tgs.team_code hometeamcode, game.game_code game_code, points points_of_home_team
                        FROM acolas.game game, ACOLAS.team_game_statistics tgs, acolas.team team 
                        WHERE game.home_team=tgs.team_code AND game.game_code=tgs.game_code AND team.name='%s') home
                        WHERE home.game_code=game.game_code AND team.name='%s' 
                        AND tgs.game_code=game.game_code AND tgs.team_code=game.visit_team AND game.home_team=team.team_code 
                        ORDER BY visit_team
                        )
                        WHERE points_of_home_team <= points_of_visit_team
                        GROUP BY visit_team) visitwin 
                        ON visitteam.visit_team=visitwin.visit_team order by visitteam.visit_team) result 
                        WHERE result.visit_team=team.team_code order by playagainst) ORDER BY win_percent DESC''' % (
        name, name, name, name, name, name))
        for row in cur.fetchall():
            results.append(row)

        play_against = [result[0] for result in results]
        win_percent = [result[1] for result in results]

        # y_pos = np.arange(len(names))

        # plt.plot(play_against, win_percent, 's-', color='r')
        plt.bar(play_against, win_percent, align = 'edge', width = 0.5, alpha = 0.5)

        plt.ylabel('Win Percentage')
        plt.xticks(rotation=90, fontsize=8)
        plt.title('Opponents vs. Win Percentage of %s' % name)
        plt.tight_layout()
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)
        # buffer0 = b''.join(img)

        plot_buffer2 = base64.b64encode(img.getvalue())
        q2plt = plot_buffer2.decode('utf-8')

        teams = []
        cur = connection.cursor()
        cur.execute('''SELECT UNIQUE name FROM acolas.team''')
        for team in cur.fetchall():
            teams.append(str(team[0]))
        return render_template('query2.html', q2plt=q2plt, teams=json.dumps(teams))


@app.route('/query3', methods=['GET', 'POST'])
def query3():
    if request.method == 'GET':
        teams = []
        cur = connection.cursor()
        cur.execute('''SELECT UNIQUE name FROM acolas.team''')
        for team in cur.fetchall():
            teams.append(str(team[0]))
        return render_template('query3.html', teams=json.dumps(teams))
    elif request.method == 'POST':
        img = BytesIO()
        name = str(request.form.get("teams"))
        results = []
        cur = connection.cursor()
        cur.execute('''SELECT hg.year, hg.avg_attendance, hw.no_of_home_win/hg.no_of_home_game*100 win_percent FROM (
                        SELECT year, AVG(attendance) avg_attendance, COUNT(*) no_of_home_game FROM 
                        (SELECT home.game_code, visit.year, visit.attendance, home.home_team_points, visit.visit_team, visit.visit_team_points FROM 
                        (SELECT unique(game.game_code), tgs.points home_team_points
                        FROM ACOLAS.game game, ACOLAS.team_game_statistics tgs, acolas.team team
                        WHERE team.name='%s' AND team.team_code=game.home_team AND game.game_code=tgs.game_code AND tgs.team_code=game.home_team) home
                        JOIN 
                        (SELECT unique(game.game_code), game.year, game.attendance, game.visit_team, tgs.points visit_team_points
                        FROM ACOLAS.game game, ACOLAS.team_game_statistics tgs, acolas.team team
                        WHERE team.name='%s' AND team.team_code=game.home_team AND game.game_code=tgs.game_code AND tgs.team_code=game.visit_team) visit
                        ON home.game_code=visit.game_code ORDER BY year)
                        GROUP BY year ORDER BY year) hg
                        JOIN (
                        SELECT year, COUNT(*) no_of_home_win FROM (
                        SELECT home.game_code, visit.year, visit.attendance, home.home_team_points, visit.visit_team, visit.visit_team_points FROM 
                        (SELECT unique(game.game_code), tgs.points home_team_points
                        FROM ACOLAS.game game, ACOLAS.team_game_statistics tgs, acolas.team team
                        WHERE team.name='%s' AND team.team_code=game.home_team AND game.game_code=tgs.game_code AND tgs.team_code=game.home_team) home
                        JOIN 
                        (SELECT unique(game.game_code), game.year, game.attendance, game.visit_team, tgs.points visit_team_points
                        FROM ACOLAS.game game, ACOLAS.team_game_statistics tgs, acolas.team team
                        WHERE team.name='%s' AND team.team_code=game.home_team AND game.game_code=tgs.game_code AND tgs.team_code=game.visit_team) visit
                        ON home.game_code=visit.game_code ORDER BY year)
                        WHERE home_team_points > visit_team_points GROUP BY year ORDER BY year) hw 
                        ON hg.year=hw.year''' % (name, name, name, name))
        for row in cur.fetchall():
            results.append(row)

        year = [result[0] for result in results]
        avg_attendence = [result[1] for result in results]
        win_percent = [result[2] * 400 for result in results]

        # y_pos = np.arange(len(names))

        plt.plot(year, avg_attendence, 's-', color='r', label="Avg Attendence")
        plt.plot(year, win_percent, 'o-', color='g', label="Win Percent*400")
        plt.ylabel('Results')
        plt.xlabel('Years')
        plt.title('Win Percentage and Attendance through Time')
        plt.legend(loc="best")
        plt.tight_layout()
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)
        # buffer0 = b''.join(img)

        plot_buffer3 = base64.b64encode(img.getvalue())
        q3plt = plot_buffer3.decode('utf-8')

        teams = []
        cur = connection.cursor()
        cur.execute('''SELECT UNIQUE name FROM acolas.team''')
        for team in cur.fetchall():
            teams.append(str(team[0]))
        return render_template('query3.html', q3plt=q3plt, teams=json.dumps(teams))


@app.route('/query4', methods=['GET', 'POST'])
def query4():
    img = BytesIO()
    name = str(request.form.get("firstname"))
    key = int(name.find(" "))
    firstname = name[0:key]
    lastname = name[(key + 1):len(name)]
    results = []
    cur = connection.cursor()
    cur.execute('''SELECT UNIQUE(x.year), x.yard_in_year, x.touchdown_in_year FROM (
                SELECT player_code, year, SUM(yard) yard_in_year, SUM(touchdown) touchdown_in_year FROM (
                SELECT pgs.player_code, pgs.game_code, pgs.year, pgs.rush_yard+pgs.pass_yard as yard, pgs.rush_touchdown+pgs.pass_touchdown as touchdown
                from ACOLAS.player_game_statistics pgs)
                GROUP BY player_code, year order by player_code, year asc) x,
                acolas.player p
                WHERE x.player_code=p.player_code AND p.first_name='%s' AND p.last_name='%s' order by year''' %(firstname, lastname))
    for row in cur.fetchall():
        results.append(row)
    year = [result[0] for result in results]
    yard_in_year = [result[1]/100 for result in results]
    touch_down_in_year = [result[2] for result in results]
    # y_pos = np.arange(len(names))
    plt.plot(year, yard_in_year, 's-', color = 'r', label = "yard in year/100")
    plt.plot(year, touch_down_in_year, 'o-', color = 'g', label = "touch down in year")
    plt.ylabel('Statistic change')
    plt.title('Query four')
    plt.legend(loc = "best")
    plt.tight_layout()
    plt.savefig(img,format='png')
    plt.close()
    img.seek(0)
    # buffer0 = b''.join(img)
    plot_buffer4 = base64.b64encode(img.getvalue())
    q4plt = plot_buffer4.decode('utf-8')
    return render_template('query4.html', q4plt=q4plt)


@app.route('/query6', methods=['GET','POST'])
def query6():
    if request.method == 'GET':
        teams = []
        cur = connection.cursor()
        cur.execute('''SELECT UNIQUE name FROM acolas.team''')
        for team in cur.fetchall():
            teams.append(str(team[0]))
        return render_template('query6.html', teams=json.dumps(teams))
    elif request.method == 'POST':
        img = BytesIO()
        name = str(request.form.get("teams"))
        results = []
        cur = connection.cursor()
        cur.execute('''SELECT year, AVG(time_of_possession), AVG(points) FROM (
                       SELECT tgs.year, tgs.points, tgs.time_of_possession
                       FROM acolas.team team, ACOLAS.team_game_statistics tgs
                       WHERE team.team_code=tgs.team_code AND team.name='%s')
                       GROUP BY year ORDER BY year''' % name)
        for row in cur.fetchall():
            results.append(row)
        year = [result[0] for result in results]
        time_of_possession = [result[1] for result in results]
        points = [result[2] * 80 for result in results]
        # y_pos = np.arange(len(names))
        plt.plot(year, time_of_possession, 's-', color='r', label="Avg Time of Possession")
        plt.plot(year, points, 'o-', color='g', label="Avg Points*80")
        plt.ylabel('Seconds')
        plt.xlabel('Years')
        plt.title('Time of Possession and Win Percentage through the Years')
        plt.legend(loc="best")
        plt.tight_layout()
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)
        # buffer0 = b''.join(img)
        plot_buffer6 = base64.b64encode(img.getvalue())
        q6plt = plot_buffer6.decode('utf-8')

        teams = []
        cur = connection.cursor()
        cur.execute('''SELECT UNIQUE name FROM acolas.team''')
        for team in cur.fetchall():
            teams.append(str(team[0]))
        return render_template('query6.html', q6plt=q6plt, teams=json.dumps(teams))


@app.route('/query8', methods=['GET','POST'])
def query8():
    if request.method == 'GET':
        teams = []
        cur = connection.cursor()
        cur.execute('''SELECT UNIQUE name FROM acolas.team''')
        for team in cur.fetchall():
            teams.append(str(team[0]))
        return render_template('query8.html', teams=json.dumps(teams))
    elif request.method == 'POST':
        img = BytesIO()
        name = str(request.form.get("teams"))
        results = []
        cur = connection.cursor()
        cur.execute('''SELECT t1.year, t1.no_of_game, t2.no_of_input_team_win, t2.no_of_input_team_win/t1.no_of_game*100 FROM 
                        (SELECT year, COUNT(*) no_of_game FROM (
                        SELECT ip.game_code, ip.year, ip.input_team_points, atp.against_team_points FROM 
                        (SELECT unique(tgs.game_code), tgs.year, tgs.points input_team_points
                        FROM ACOLAS.team_game_statistics tgs, acolas.team team
                        WHERE team.name='%s' AND team.team_code=tgs.team_code ORDER BY year) ip 
                        JOIN 
                        (SELECT unique(tgs.game_code), tgs.points against_team_points
                        FROM ACOLAS.team_game_statistics tgs, acolas.team team
                        WHERE team.name='%s' AND team.team_code!=tgs.team_code AND tgs.game_code 
                        IN (SELECT unique(tgs.game_code) FROM ACOLAS.team_game_statistics tgs, acolas.team team
                        WHERE team.name='%s' AND team.team_code=tgs.team_code) ) atp
                        ON ip.game_code=atp.game_code) GROUP BY year ORDER BY year) t1
                        JOIN (
                        SELECT year, COUNT(input_team_points) no_of_input_team_win FROM (
                        SELECT ip.game_code, ip.year, ip.input_team_points, atp.against_team_points FROM 
                        (SELECT unique(tgs.game_code), tgs.year, tgs.points input_team_points
                        FROM ACOLAS.team_game_statistics tgs, acolas.team team
                        WHERE team.name='%s' AND team.team_code=tgs.team_code ORDER BY year) ip 
                        JOIN 
                        (SELECT unique(tgs.game_code), tgs.points against_team_points
                        FROM ACOLAS.team_game_statistics tgs, acolas.team team
                        WHERE team.name='%s' AND team.team_code!=tgs.team_code AND tgs.game_code 
                        IN (SELECT unique(tgs.game_code) FROM ACOLAS.team_game_statistics tgs, acolas.team team
                        WHERE team.name='%s' AND team.team_code=tgs.team_code) ) atp
                        ON ip.game_code=atp.game_code)
                        WHERE input_team_points > against_team_points GROUP BY year) t2
                        ON t1.year=t2.year ORDER BY year''' % (name, name, name, name, name, name))
        for row in cur.fetchall():
            results.append(row)

        year = [result[0] for result in results]
        win_per = [result[3] for result in results]

        # y_pos = np.arange(len(names))

        plt.plot(year, win_per, 's-', color='r')
        plt.ylabel('Winnig Percentage')
        plt.xlabel('Years')
        plt.title('Winning Percentage Throughout the Years')
        plt.legend(loc="best")
        plt.tight_layout()
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)
        # buffer0 = b''.join(img)

        plot_buffer8 = base64.b64encode(img.getvalue())
        q8plt = plot_buffer8.decode('utf-8')

        teams = []
        cur = connection.cursor()
        cur.execute('''SELECT UNIQUE name FROM acolas.team''')
        for team in cur.fetchall():
            teams.append(str(team[0]))
        return render_template('query8.html', q8plt=q8plt, teams=json.dumps(teams))


@app.route('/query9', methods=['GET','POST'])
def query9():
    img = BytesIO()
    name = str(request.form.get("teamname"))
    results = []
    cur = connection.cursor()
    cur.execute('''SELECT UNIQUE(t.name), taa.year, taa.avgheight, taa.avgweight 
                FROM acolas.team t,
                (SELECT team_code, year, AVG(height) avgheight, AVG(weight) avgweight 
                FROM acolas.player WHERE height IS NOT NULL AND weight IS NOT NULL GROUP BY team_code, year) taa
                WHERE t.team_code=taa.team_code AND t.name='%s' ORDER BY year''' %name)
    for row in cur.fetchall():
        results.append(row)

    year = [result[1] for result in results]
    avgheight = [result[2] for result in results]
    avgweight = [result[3] for result in results]

    # y_pos = np.arange(len(names))

    plt.plot(year, avgheight, 's-', color = 'r', label = "Avg Height")
    plt.plot(year, avgweight, 'o-', color = 'g', label = "Avg Weight")
    plt.ylabel('Number')
    plt.title('Query Nine')
    plt.legend(loc = "best")
    plt.tight_layout()
    plt.savefig(img,format='png')
    plt.close()
    img.seek(0)
    # buffer0 = b''.join(img)

    plot_buffer91 = base64.b64encode(img.getvalue())
    q91plt = plot_buffer91.decode('utf-8')

    img = BytesIO()
    conference_name = str(request.form.get("conname"))
    results = []
    cur = connection.cursor()
    cur.execute('''SELECT ct.year, AVG(avgheight) avghc, AVG(avgweight) avgwc FROM (
                    SELECT unique(taa.team_code), c.name conference, taa.year, taa.avgheight, taa.avgweight FROM acolas.team t, acolas.conference c, (
                    SELECT team_code, year, AVG(height) avgheight, AVG(weight) avgweight FROM acolas.player
                    WHERE height IS NOT NULL AND weight IS NOT NULL
                    GROUP BY team_code, year) taa WHERE taa.team_code=t.team_code AND t.conference_code=c.conference_code  AND c.name='%s') ct
                    GROUP BY year ORDER BY year''' % conference_name)
    for row in cur.fetchall():
        results.append(row)

    year = [result[0] for result in results]
    avgheight = [result[1] for result in results]
    avgweight = [result[2] for result in results]

    # y_pos = np.arange(len(names))

    plt.plot(year, avgheight, 's-', color='r', label="Avg Height")
    plt.plot(year, avgweight, 'o-', color='g', label="Avg Weight")
    plt.ylabel('Number')
    plt.title('Query Nine B')
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    # buffer0 = b''.join(img)

    plot_buffer92 = base64.b64encode(img.getvalue())
    q92plt = plot_buffer92.decode('utf-8')
    return render_template('query9.html', q91plt=q91plt, q92plt=q92plt)


@app.route('/choose_trends', methods=['POST', 'GET'])
def choose_trends():
    if request.method == 'POST':
        data = (request.form.get("trends", None))
        if data in "trend1":
            return redirect(url_for('query1'))
        elif data in "trend2":
            return redirect(url_for('query2'))
        elif data in "trend3":
            return redirect(url_for('query3'))
        elif data in "trend4":
            return redirect(url_for('query4'))
        elif data in "trend5":
            return redirect(url_for('query6'))
        elif data in "trend6":
            return redirect(url_for('query8'))
        else:
            return redirect(url_for('query9'))


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