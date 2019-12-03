import base64
from io import BytesIO
import numpy as np
from flask import Flask, flash, render_template, url_for, request, redirect
from flask_bootstrap import Bootstrap
import time
import json
import cx_Oracle as oracle
from Configuration.Config import parse_config_input
import matplotlib.pyplot as plt
plt.rcdefaults()
from flask_toastr import Toastr



# initialize flask application
app = Flask(__name__)
toastr = Toastr()
app.config['SECRET_KEY'] = 'you-will-never-guess'

# initialize toastr on the app within create_app()
toastr.init_app(app)
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
            ''')  # EXECUTE IMMEDIATE 'DROP TABLE NCAA_PRO_USERS';
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
            cur.execute(
                "SELECT password FROM NCAA_PRO_USERS WHERE username='%s'" % username)
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
            cur.execute(
                "INSERT INTO  NCAA_PRO_USERS VALUES ('%s', '%s')" % values)
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
                cur.execute(
                    "INSERT INTO NCAA_PRO_USERS VALUES ('%s', '%s')" % values)
                connection.commit()
                cur.execute(
                    "SELECT password FROM NCAA_PRO_USERS WHERE username='%s'" % username)
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
        SELECT * FROM (SELECT unique(team.name) playagainst, result.no_of_home_team_win/(result.no_of_home_team_F+result.no_of_visit_team_win)*100 win_percent
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
        plt.bar(play_against, win_percent, align='edge', width=0.5, alpha=0.5)

        plt.ylabel('Winning Percentage')
        plt.xticks(rotation=90, fontsize=8)
        plt.title('Winning Percentage against opponents of %s' % name)
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

        correlation_coefficient = np.corrcoef(avg_attendence, win_percent, rowvar=True)
        print("correlation_coefficient: ", correlation_coefficient[0][1])

        # y_pos = np.arange(len(names))

        plt.plot(year, avg_attendence, 's-', color='r', label="Avg Attendence")
        plt.plot(year, win_percent, 'o-', color='g', label="Winning Percent*400")
        plt.text(2009, 50000, "correlation_coefficient:\n" + str(correlation_coefficient[0][1])[:5],
                 fontsize=12, horizontalalignment='center', verticalalignment='center')
        plt.ylabel('Results')
        plt.xlabel('Years')
        plt.title('Winning Percentage and Attendance throughout Time')
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
    if request.method == 'GET':
        players = []
        cur = connection.cursor()
        cur.execute('''SELECT UNIQUE(x.player_code), p.first_name, p.last_name, x.no_of_play_year From (
                        SELECT player_code, count(year) no_of_play_year from (
                        SELECT * from (
                        SELECT player_code, year, SUM(yard) yard_in_year, SUM(touchdown) touchdown_in_year FROM (
                        SELECT pgs.player_code, pgs.game_code, pgs.year, pgs.rush_yard+pgs.pass_yard as yard, pgs.rush_touchdown+pgs.pass_touchdown as touchdown
                        from ACOLAS.player_game_statistics pgs)
                        GROUP BY player_code, year order by player_code, year asc)
                        where yard_in_year>0 AND touchdown_in_year>0 order by player_code)
                        group by player_code) x, acolas.player p
                        where x.player_code=p.player_code order by no_of_play_year desc''')
        for player in cur.fetchall():
            player = str(player[1]) + ' ' + str(player[2])
            print(player)
            players.append(player)
        return render_template('query4.html', players=json.dumps(players))
    elif request.method == 'POST':
        img = BytesIO()
        name = str(request.form.get("players"))
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
        plt.plot(year, yard_in_year, 's-', color='r', label="100 Yards")
        plt.plot(year, touch_down_in_year, 'o-', color='g', label="Touchdown #")
        plt.xlabel('years')
        plt.title('Player Statistics Throughout the Time')
        plt.legend(loc="best")
        plt.xticks(np.arange(min(year), max(year) + 1, 1.0))
        plt.tight_layout()
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)
        # buffer0 = b''.join(img)
        plot_buffer4 = base64.b64encode(img.getvalue())
        q4plt = plot_buffer4.decode('utf-8')

        players = []
        cur = connection.cursor()
        cur.execute('''SELECT UNIQUE(x.player_code), p.first_name, p.last_name, x.no_of_play_year From (
                                SELECT player_code, count(year) no_of_play_year from (
                                SELECT * from (
                                SELECT player_code, year, SUM(yard) yard_in_year, SUM(touchdown) touchdown_in_year FROM (
                                SELECT pgs.player_code, pgs.game_code, pgs.year, pgs.rush_yard+pgs.pass_yard as yard, pgs.rush_touchdown+pgs.pass_touchdown as touchdown
                                from ACOLAS.player_game_statistics pgs)
                                GROUP BY player_code, year order by player_code, year asc)
                                where yard_in_year>0 AND touchdown_in_year>0 order by player_code)
                                group by player_code) x, acolas.player p
                                where x.player_code=p.player_code order by no_of_play_year desc''')
        for player in cur.fetchall():
            player = str(player[1]) + ' ' + str(player[2])
            print(player)
            players.append(player)
        return render_template('query4.html', q4plt=q4plt, players=json.dumps(players))


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

        correlation_coefficient = np.corrcoef(time_of_possession, points, rowvar=True)
        print("correlation_coefficient: ", correlation_coefficient[0][1])

        # y_pos = np.arange(len(names))
        plt.plot(year, time_of_possession, 's-',
                 color='r', label="Avg Time of Possession")
        plt.plot(year, points, 'o-', color='g', label="Avg Points*80")
        plt.text(2008, 2200, "correlation_coefficient:\n" + str(correlation_coefficient[0][1])[:5],
                 fontsize=12, horizontalalignment='center', verticalalignment='center')
        plt.ylabel('Seconds')
        plt.xlabel('Years')
        plt.title('Time of Possession and winning Percentage throughout the Years')
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


@app.route('/query8', methods=['GET', 'POST'])
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
        plt.ylabel('Winning Percentage')
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


@app.route('/query9', methods=['GET', 'POST'])
def query9():
    if request.method == 'GET':
        teams = []
        cur = connection.cursor()
        cur.execute('''SELECT UNIQUE name FROM acolas.team''')
        for team in cur.fetchall():
            teams.append(str(team[0]))
        return render_template('query9.html', teams=json.dumps(teams))
    elif request.method == 'POST':
        img = BytesIO()
        name = str(request.form.get("teams"))
        results = []
        cur = connection.cursor()
        cur.execute('''SELECT t1.year, t1.team_avg_height, t2.conference_avg_height FROM (
                        SELECT unique(taa.year), taa.avgheight team_avg_height
                        FROM acolas.team t,
                        (SELECT team_code, year, AVG(height) avgheight
                        FROM acolas.player WHERE height IS NOT NULL GROUP BY team_code, year) taa
                        WHERE t.team_code=taa.team_code AND t.name='%s' ORDER BY year) t1
                        JOIN (
                        SELECT year, AVG(height) conference_avg_height
                        FROM acolas.player
                        WHERE team_code IN (SELECT team_code FROM acolas.team WHERE conference_code=
                        (SELECT unique(conference_code) FROM acolas.team WHERE name='%s')) AND height IS NOT NULL GROUP BY year) t2
                        ON t1.year=t2.year''' % (name, name))
        for row in cur.fetchall():
            results.append(row)
        year = [result[0] for result in results]
        team_avgheight = [result[1] for result in results]
        con_avgheight = [result[2] for result in results]
        # y_pos = np.arange(len(names))
        plt.plot(year, team_avgheight, 's-', color='r', label="Team Avg Height")
        plt.plot(year, con_avgheight, 'o-', color='g', label="Conference Avg Height")
        plt.ylabel('Height')
        # plt.title('Query Nine')
        plt.legend(loc="best")
        plt.tight_layout()
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)
        # buffer0 = b''.join(img)
        plot_buffer91 = base64.b64encode(img.getvalue())
        q91plt = plot_buffer91.decode('utf-8')
        img = BytesIO()
        # name1 = str(request.form.get("teamname1"))
        results1 = []
        cur = connection.cursor()
        cur.execute('''SELECT t1.year, t1.team_avg_weight, t2.conference_avg_weight FROM (
                        SELECT unique(taa.year), taa.avgweight team_avg_weight
                        FROM acolas.team t,
                        (SELECT team_code, year, AVG(weight) avgweight
                        FROM acolas.player WHERE weight IS NOT NULL GROUP BY team_code, year) taa
                        WHERE t.team_code=taa.team_code AND t.name='%s' ORDER BY year) t1
                        JOIN (
                        SELECT year, AVG(weight) conference_avg_weight
                        FROM acolas.player
                        WHERE team_code IN (SELECT team_code FROM acolas.team WHERE conference_code=
                        (SELECT unique(conference_code) FROM acolas.team WHERE name='%s')) AND weight IS NOT NULL GROUP BY year) t2
                        ON t1.year=t2.year''' % (name, name))
        for row in cur.fetchall():
            results1.append(row)
        year1 = [result1[0] for result1 in results1]
        team_avgweight = [result1[1] for result1 in results1]
        con_avgweight = [result1[2] for result1 in results1]
        # y_pos = np.arange(len(names))
        plt.plot(year1, team_avgweight, 's-', color='r', label="Team Avg Weight")
        plt.plot(year1, con_avgweight, 'o-', color='g', label="Conference Avg Weight")
        plt.ylabel('Weight')
        # plt.title('Query Nine B')
        plt.legend(loc="best")
        plt.tight_layout()
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)
        # buffer0 = b''.join(img)
        plot_buffer92 = base64.b64encode(img.getvalue())
        q92plt = plot_buffer92.decode('utf-8')

        teams = []
        cur = connection.cursor()
        cur.execute('''SELECT UNIQUE name FROM acolas.team''')
        for team in cur.fetchall():
            teams.append(str(team[0]))
        return render_template('query9.html', q91plt=q91plt, q92plt=q92plt, teams=json.dumps(teams))


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


@app.route('/simple1', methods=['POST', 'GET'])
def simple1():
    text = request.form['text']
    print("FINNA " + str(text))


@app.route('/simple2', methods=['POST', 'GET'])
def simple2():
    results = []
    year = str(request.form['text'])
    cur = connection.cursor()
    cur.execute('''(SELECT * FROM 
                (SELECT year, last_school, COUNT(*) no_of_players FROM acolas.player 
                WHERE last_school IS NOT NULL AND year=2007
                GROUP BY year, last_school 
                ORDER BY no_of_players DESC) 
                WHERE rownum<=1)''')
    for row in cur.fetchall():
        results.append(row)
    flash("School: " + str(results[0][1]) + '<br/>' + "Players: " + str(results[0][2]))
    return render_template('simple.html')

@app.route('/simple4', methods=['POST', 'GET'])
def simple4():
    results = []
    year = str(request.form['text'])
    cur = connection.cursor()
    cur.execute('''SELECT name 
                FROM(SELECT unique(t3.year), t.name, t3.max_total_points FROM acolas.team t, (
                SELECT t1.year, t1.team_code, t2.max_total_points FROM (
                SELECT year, team_code, SUM(points) total_points 
                FROM ACOLAS.team_game_statistics GROUP BY year, team_code) t1
                JOIN (
                SELECT year, max(total_points) max_total_points FROM (
                SELECT year, team_code, SUM(points) total_points
                FROM ACOLAS.team_game_statistics 
                GROUP BY year, team_code) GROUP BY year) t2 ON t1.total_points=t2.max_total_points) t3
                WHERE t.team_code=t3.team_code ORDER BY year)
                WHERE year =%s
            '''%year)
    for row in cur.fetchall():
        results.append(row)
    print(results)
    flash("Best Team: " + str(results[0][0]))
    return render_template('simple.html')

@app.route('/simple6', methods=['POST', 'GET'])
def simple6():
    results = []
    cur = connection.cursor()
    cur.execute('''SELECT ta.total_attendance, t.name FROM acolas.team t, 
    (SELECT team, SUM(attendance) total_attendance FROM (
    SELECT visit_team team, attendance FROM acolas.game UNION
    SELECT home_team team, attendance FROM acolas.game)
    GROUP BY TEAM ORDER BY sum(attendance) desc) ta
    WHERE rownum=1''')
    for row in cur.fetchall():
        results.append(row)
    print(results)
    attendance = format(results[0][0], ",")
    flash("Team: " + str(results[0][1]) + "<br/>" + "Total Attendance: " + str(attendance))
    return render_template('simple.html')

@app.route('/simple8a', methods=['POST', 'GET'])
def simple8a():
    results = []
    cur = connection.cursor()
    cur.execute('''SELECT UNIQUE(t.name), points FROM ACOLAS.team_game_statistics tgs, acolas.team t 
                WHERE tgs.game_code=(SELECT game_code FROM 
                (SELECT game_code, SUM(points) 
                FROM ACOLAS.team_game_statistics GROUP BY game_code ORDER BY sum(points) desc)
                WHERE ROWNUM=1) 
                AND tgs.team_code=t.team_code''')
    for row in cur.fetchall():
        results.append(row)
    print(results)
    flash("Team1: " + str(results[0][0]) + " Score: " + str(results[0][1]) + "<br/>" + "Team2: " + str(results[1][0]) + " Score: " + str(results[1][1]))
    return render_template('simple.html')

@app.route('/simple8b', methods=['POST', 'GET'])
def simple8b():
    results = []
    cur = connection.cursor()
    cur.execute('''SELECT UNIQUE(t.name), points FROM ACOLAS.team_game_statistics tgs, acolas.team t 
                WHERE tgs.game_code=(SELECT game_code FROM 
                (SELECT game_code, SUM(points) 
                FROM ACOLAS.team_game_statistics GROUP BY game_code ORDER BY sum(points) asc)
                WHERE ROWNUM=1) 
                AND tgs.team_code=t.team_code''')
    for row in cur.fetchall():
        results.append(row)
    print(results)
    flash("Team1: " + str(results[0][0]) + " Score: " + str(results[0][1]) + "<br/>" + "Team2: " + str(results[1][0]) + " Score: " + str(results[1][1]))
    return render_template('simple.html')

@app.route('/simple9', methods=['POST', 'GET'])
def simple9():
    results = []
    cur = connection.cursor()
    cur.execute('''SELECT position, COUNT(*) FROM (
                SELECT UNIQUE(player_code), position, height FROM acolas.player 
                WHERE height IS NOT NULL and position IS NOT NULL AND height < 72) GROUP BY position ORDER BY COUNT(*) DESC''')
    for row in cur.fetchall():
        results.append(row)
    print(results)
    answer_list = []
    for row in results:
        answer_list.append(str(row[0])+': '+str(row[1]))
    answers = ' | '.join(answer_list)
    answers = '| ' + answers + ' |'
    flash(answers)
    return render_template('simple.html')

# Head to head page
@app.route('/head_to_head', methods=['POST', 'GET'])
def head_to_head():
    # put the sql template of head_to_head here
    query_template_for_head_to_head = ''
    results = []
    cur = connection.cursor()
    if request.method == 'POST':
        team = request.form["team"]
        print("team:", team)
        best_or_worst = request.form["best_or_worst"]
        print("best_or_worst:", best_or_worst)
        # construct the final query using the template, the team name, and the best_or_worst.
        query = ''

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
        # construct the final query using the template, the team name, and the best_or_worst.
        query = ''

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


@app.route('/goodtoknow', methods=['GET', 'POST'])
def goodtoknow():
    name = str(request.form.get("teamname"))
    results = []
    cur = connection.cursor()
    cur.execute('''SELECT unique(team.name) playagainst, result.no_of_home_team_win/(result.no_of_home_team_win+result.no_of_visit_team_win)*100 win_percent
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
                WHERE result.visit_team=team.team_code  and rownum <= 10
                order by win_percent desc, playagainst''' % (name, name, name, name, name, name))
    for row in cur.fetchall():
        results.append(row)
    return render_template('goodtoknow.html', results=results)


if __name__ == '__main__':
    app.run(host=HOST,
            debug=True,
            use_reloader=False,
            port=PORT)
