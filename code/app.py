from flask import Flask, render_template, request, jsonify, redirect, session
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from werkzeug import security
from datetime import datetime
import requests
from textblob import TextBlob
import pandas as pd
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
app = Flask(__name__)

app.secret_key = 'your_secret_key'

# Connection to database - confidential 
connection_string = "postgresql://flask:kOpzov36jPst@ep-lively-sun-a2f4gm8y-pooler.eu-central-1.aws.neon.tech/cwkdb?sslmode=require"
engine = create_engine(connection_string, pool_pre_ping=True)
conn = engine.connect()

# Route for the homepage
@app.route('/')
def index():
    if 'username' in session:
        return redirect('/homepage')
    result = conn.execute(text("SELECT * FROM news ORDER BY newsdate DESC LIMIT 5"))
    recent_articles = result.mappings().all()

    companies_overview = conn.execute(text("SELECT compname, complongname, compticker, comprating, ROUND(CAST(stockclose AS NUMERIC),5) AS stockprice, ROUND(CAST(((stockclose/stockopen)-1)*100 AS NUMERIC), 2) AS growth FROM ((SELECT * FROM company) NATURAL JOIN (SELECT compname, stockclose FROM stock ORDER BY stockday DESC LIMIT (SELECT COUNT(*) FROM company)) NATURAL JOIN ((SELECT compname, stockopen FROM stock WHERE stockday <= ((SELECT stockday FROM stock ORDER BY stockday DESC LIMIT 1) -7) ORDER BY stockday DESC LIMIT (SELECT COUNT(*) FROM company)))) ORDER BY growth DESC LIMIT 4"))

    return render_template('index.html', recent_articles = recent_articles, companies_overview = companies_overview)

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirmpassword = request.form['confirmpassword']

        # Check password inputs match
        if not password == confirmpassword:
            return render_template('register.html', error='Passwords do not match')

        # Check if username is already registered
        qrytext = text("SELECT COUNT(*) FROM users WHERE username = :uname")
        qry = qrytext.bindparams(uname = username)
        result = conn.execute(qry)
        for row in result:
            namecount = row.count
        if namecount != 0:
            return render_template('register.html', error='Username not available')

        # Check if the email is already registered
        qrytext1 = text("SELECT COUNT(*) FROM users WHERE useremail = :email")
        qry1 = qrytext1.bindparams(email = email)
        result1 = conn.execute(qry1)
        for row in result1:
            emailcount = row.count
        if emailcount != 0:
            return render_template('register.html', error='Email already registered')
        
        # Insert the user 
        qrytext2 = text("INSERT INTO users (username, useremail, userpasswordhash) VALUES (:uname, :uemail, :upass) ON CONFLICT DO NOTHING")
        passwordhash = security.generate_password_hash(password)
        qry2 = qrytext2.bindparams(uname = username, uemail = email, upass = passwordhash)
        result2 = conn.execute(qry2)     
        conn.commit()

        return redirect('/login')
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect('/userdetails')
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        qrytext = text("SELECT * FROM users WHERE useremail = :email")
        qry = qrytext.bindparams(email = email)
        result = conn.execute(qry)
        for row in result:
            if security.check_password_hash(row.userpasswordhash, password):
                session['username'] = row.username
                return redirect('/homepage') 

        return render_template('login.html', error='Invalid email or password')
    return render_template('login.html')

# User details
@app.route('/userdetails')
def userdetails():
    if 'username' in session:
        username = session['username']
        qrytext = text("SELECT * FROM users WHERE username = :uname")
        qry = qrytext.bindparams(uname = username)
        userdetails = conn.execute(qry)
        return render_template('userdetails.html', userdetails = userdetails)
    return redirect("/")

# Delete account
@app.route('/deleteaccount')
def deleteaccount():
    if 'username' in session:
        username = session['username']
        session.pop('username', None)
        qrytext = text('DELETE FROM users WHERE username = :uname')
        qry = qrytext.bindparams(uname = username)
        conn.execute(qry)
        conn.commit()
        return redirect('/')
    return redirect('/')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# Route for fetching news articles
@app.route('/news', methods=['GET'])
def get_news():
    sample_news = conn.execute(text("SELECT * FROM news WHERE newscomp is null ORDER BY newsdate DESC LIMIT 20"))
    return render_template('news.html', articles=sample_news)

# Route for the categories page
@app.route('/categories')
def categories():
    return render_template('categories.html')

# Route for a category page
@app.route('/category/<catname>')
def category(catname):
    qrytext = text("SELECT row_number() OVER (ORDER BY ROUND(CAST(((stockclose/stockopen)-1)*100 AS NUMERIC), 2) DESC) rownum, compname, complongname, compticker, comprating, ROUND(CAST(stockclose AS NUMERIC),5) AS stockprice, ROUND(CAST(((stockclose/stockopen)-1)*100 AS NUMERIC), 2) AS growth FROM ((SELECT * FROM company NATURAL JOIN (SELECT compname FROM companycategory WHERE catname = :cname)) NATURAL JOIN (SELECT compname, stockclose FROM stock ORDER BY stockday DESC LIMIT (SELECT COUNT(*) FROM company)) NATURAL JOIN ((SELECT compname, stockopen FROM stock WHERE stockday <= ((SELECT stockday FROM stock ORDER BY stockday DESC LIMIT 1) -7) ORDER BY stockday DESC LIMIT (SELECT COUNT(*) FROM company)))) ORDER BY growth DESC")
    qry = qrytext.bindparams(cname = catname)
    category_companies = conn.execute(qry)

    logged_in = False
    is_following = False

    if 'username' in session:
        username = session['username']

        logged_in = True
        qrytext1 = text("SELECT Count(*) FROM usercategory WHERE username = :uname AND catname = :catname")
        existing_follow = conn.execute(qrytext1, {"uname": username, "catname": catname}).fetchone()[0]
        if existing_follow > 0:
            is_following = True

    return render_template('category.html', catname = catname, category_companies = category_companies, logged_in = logged_in, is_following=is_following)

# Route for the companies page
@app.route('/companies', methods=['GET', 'POST'])
def companies():
    if request.method == 'POST':
        ticker = request.form['ticker']
        qrytext = text("SELECT compname FROM company WHERE compticker = :tick")
        qry = qrytext.bindparams(tick = ticker)
        result = conn.execute(qry)
        for row in result:
            qrytext1 = text("SELECT * FROM stock WHERE compname = :compname ORDER BY stockday DESC LIMIT 30")
            qry1 = qrytext1.bindparams(compname = row.compname)
            company_data = conn.execute(qry1)
            return render_template('companies.html', company_data=company_data)
        
    trending_companies = get_trending_companies()
    top_rated_companies = conn.execute(text("SELECT * FROM company ORDER BY comprating DESC LIMIT 10"))

    return render_template('companies.html',trending_companies=trending_companies, top_rated_companies = top_rated_companies)

# Retrieves the top 10 companies with the highest average stock volume from the last 5 business days
def get_trending_companies():
    try:
        trending_companies = []
        qrytext = text("SELECT stockvolume FROM stock WHERE compname = :compname ORDER BY stockday DESC LIMIT 5")
        company = conn.execute(text("SELECT compname, compticker FROM company"))
        for row in company:
            qry = qrytext.bindparams(compname = row.compname)
            result = conn.execute(qry)
            result_data = [r.stockvolume for r in result]
            length = len(result_data)
            sums = sum(result_data)
            trending_companies += [(row.compname, row.compticker, round(sums/length,2))]

        top_trending_companies = sorted(trending_companies, key=lambda x: x[2])
        top_trending_companies.reverse()
        top10_trending_companies = top_trending_companies[:10]
        print(top10_trending_companies)
        return top10_trending_companies
    except Exception as e:
        conn.rollback()
        print("Error fetching trending companies:", e)
        return None

# Route for the about page
@app.route('/about')
def about():
    return render_template('about.html')

# Home route (requires login)
@app.route('/homepage')
def home():
    if 'username' in session:
        username = session['username']

        followed_companies = []
        qrytext = text("SELECT row_number() OVER (ORDER BY ROUND(CAST(((stockclose/stockopen)-1)*100 AS NUMERIC), 2) DESC) rownum, compname, complongname, compticker, comprating, ROUND(CAST(stockclose AS NUMERIC),5) AS stockprice, ROUND(CAST(((stockclose/stockopen)-1)*100 AS NUMERIC), 2) AS growth FROM ((SELECT * FROM company NATURAL JOIN (SELECT compname FROM userfollowedcompanies WHERE username = :uname)) NATURAL JOIN (SELECT compname, stockclose FROM stock ORDER BY stockday DESC LIMIT (SELECT COUNT(*) FROM company)) NATURAL JOIN ((SELECT compname, stockopen FROM stock WHERE stockday <= ((SELECT stockday FROM stock ORDER BY stockday DESC LIMIT 1) -7) ORDER BY stockday DESC LIMIT (SELECT COUNT(*) FROM company)))) ORDER BY growth DESC")
        qry = qrytext.bindparams(uname = username)
        f_companies = conn.execute(qry)
        for row in f_companies:
            followed_companies += [row]

        followed_news = []
        qrytext1 = text("SELECT * FROM news NATURAL JOIN (SELECT compname AS newscomp FROM userfollowedcompanies WHERE username = :uname) ORDER BY newsdate DESC LIMIT 10")
        qry1 = qrytext1.bindparams(uname = username)
        f_news = conn.execute(qry1)
        for row in f_news:
            followed_news += [row]

        qrytext2 = text("SELECT catname FROM usercategory WHERE username = :uname")
        qry2 = qrytext2.bindparams(uname = username)
        fcomp = conn.execute(qry2)
        followed = []
        for row in fcomp:
            followed += [row.catname]

        followed_categories = []
        for catname in ['Business', 'Entertainment', 'Health', 'Science', 'Sports', 'Technology']:
            if catname in followed:
                qrytext3 = text("SELECT row_number() OVER (ORDER BY ROUND(CAST(((stockclose/stockopen)-1)*100 AS NUMERIC), 2) DESC) rownum, catname, compname, complongname, compticker, comprating, ROUND(CAST(stockclose AS NUMERIC),5) AS stockprice, ROUND(CAST(((stockclose/stockopen)-1)*100 AS NUMERIC), 2) AS growth FROM ((SELECT * FROM company NATURAL JOIN (SELECT compname, catname FROM companycategory WHERE catname = :cname)) NATURAL JOIN (SELECT compname, stockclose FROM stock ORDER BY stockday DESC LIMIT (SELECT COUNT(*) FROM company)) NATURAL JOIN ((SELECT compname, stockopen FROM stock WHERE stockday <= ((SELECT stockday FROM stock ORDER BY stockday DESC LIMIT 1) -7) ORDER BY stockday DESC LIMIT (SELECT COUNT(*) FROM company)))) ORDER BY growth DESC LIMIT 5")
                qry3 = qrytext3.bindparams(cname = catname)
                category_companies = conn.execute(qry3)
                followed_categories += [(catname, category_companies)]

        suggested_companies = get_suggested_companies(username)

        return render_template('homepage.html', username=username, followed_companies = followed_companies, followed_categories = followed_categories, followed_news = followed_news, suggested_companies = suggested_companies)
    else:
        return redirect('/login')

# Retrieves suggested companies
# First finds companies belonging to categories the user follows that they do not already follow and returns the 5 with the largest growth over the last 7 days
# If this returns less than 5 companies, the list is supplemented with top ranked companies based of growth over the last 7 days
def get_suggested_companies(username):
    try:
        qrytext = text("SELECT compname, complongname, compticker, comprating, ROUND(CAST(stockclose AS NUMERIC),5) AS stockprice, ROUND(CAST(((stockclose/stockopen)-1)*100 AS NUMERIC), 2) AS growth FROM ((SELECT * FROM company) NATURAL JOIN (SELECT compname, stockclose FROM stock ORDER BY stockday DESC LIMIT (SELECT COUNT(*) FROM company)) NATURAL JOIN ((SELECT compname, stockopen FROM stock WHERE stockday <= ((SELECT stockday FROM stock ORDER BY stockday DESC LIMIT 1) -7) ORDER BY stockday DESC LIMIT (SELECT COUNT(*) FROM company)))) WHERE compname in (Select compname from company where compname in (select compname from companycategory where catname in (select catname from usercategory where username = :uname)) AND compname not in (select compname from userfollowedcompanies where username = :uname)) ORDER BY growth DESC LIMIT 5 ")
        qry = qrytext.bindparams(uname = username)
        result = conn.execute(qry)
        categorycompanies = result.mappings().all()
        if len(categorycompanies) < 5:
            qrytext1 = text("SELECT compname, complongname, compticker, comprating, ROUND(CAST(stockclose AS NUMERIC),5) AS stockprice, ROUND(CAST(((stockclose/stockopen)-1)*100 AS NUMERIC), 2) AS growth FROM ((SELECT * FROM company) NATURAL JOIN (SELECT compname, stockclose FROM stock ORDER BY stockday DESC LIMIT (SELECT COUNT(*) FROM company)) NATURAL JOIN ((SELECT compname, stockopen FROM stock WHERE stockday <= ((SELECT stockday FROM stock ORDER BY stockday DESC LIMIT 1) -7) ORDER BY stockday DESC LIMIT (SELECT COUNT(*) FROM company)))) ORDER BY growth DESC LIMIT :num")
            qry1 = qrytext1.bindparams(num = 5- len(categorycompanies))
            result1 = conn.execute(qry1)
            for row in result1:
                categorycompanies += [row]

        return categorycompanies

    except Exception as e:
        conn.rollback()
        print("Error fetching trending companies:", e)
        return None

# Route for searching companies
@app.route('/search_company')
def search_company():
    query = request.args.get('search')
    companies_list = conn.execute(text("SELECT compname, compticker FROM company"))
    search_results = []
    for row in companies_list:
        if query.lower() in row.compname.lower():
            search_results += [(row.compname, row.compticker)]

    return render_template('search.html', search_results=search_results)

# Route for displaying company dashboard
@app.route('/company_dashboard/<ticker>')
def company_dashboard(ticker):
    
    logged_in = False
    is_following = False

    # Retrieve Company name
    qrytext1 =text("SELECT compname, complongname, comprating FROM company WHERE compticker = :tick")
    qry1 = qrytext1.bindparams(tick = ticker)
    res = conn.execute(qry1)
    resdata = res.mappings().all()
    company = resdata[0]['compname']
    company_name = resdata[0]['complongname']
    comprating = resdata[0]['comprating']
    # print(company_name)

    # Calculate daily growth
    qrytext = text("SELECT * FROM stock WHERE compname = (SELECT compname FROM company WHERE compticker = :tick) ORDER BY stockday DESC LIMIT 30")
    qry = qrytext.bindparams(tick = ticker)
    result = conn.execute(qry)
    resultdata = result.mappings().all()
    stock_price = round(resultdata[0]['stockclose'], 5)
    daily_growth = round(((resultdata[0]['stockclose']/resultdata[0]['stockopen']) - 1)*100, 5)

    # Construct lists of dates and stock close values for the past 30 business days
    result1 = conn.execute(qry)
    price_data_date = []
    price_data_close = []
    for row in result1:
        price_data_close += [row.stockclose]
        price_data_date += [row.stockday.strftime("%d/%m/%Y")]
    # print(price_data_date)
    # print(price_data_close)
    price_data_close.reverse()
    price_data_date.reverse()

    # Retrieve stock data
    stock_data = conn.execute(qry)

    # Retrieve company related articles
    qrytext2 = text("SELECT * FROM news WHERE newscomp = (SELECT compname FROM company WHERE compticker = :tick) ORDER BY newsdate DESC LIMIT 10")
    qry2 = qrytext2.bindparams(tick = ticker)
    top_10_articles = conn.execute(qry2)

    # Retrieve company rankings
    ranks = get_company_rankings(company)

    # Retrieve average sentiment (last 7 days)
    qrytext3 = text("select avg(newssentiment) from news where newsdate > now() - interval '7 days' AND newscomp = :cname")
    qry3 = qrytext3.bindparams(cname = company)
    averagesentiment = conn.execute(qry3).fetchone()[0]
    if averagesentiment:
        publicscorechange = round(((averagesentiment/comprating) -1)*100, 5)
    else:
        publicscorechange = None

    if 'username' in session:
        username = session['username']

        logged_in = True
        qrytext = text("SELECT Count(*) FROM userfollowedcompanies WHERE username = :uname AND compname = (SELECT compname FROM company WHERE compticker = :tick)")
        existing_follow = conn.execute(qrytext, {"uname": username, "tick": ticker}).fetchone()[0]
        if existing_follow > 0:
            is_following = True


    return render_template('company_dashboard.html', 
                           company_name=company_name,
                           ticker=ticker,
                           comprating=comprating,
                           stock_price=stock_price,
                           ranks = ranks,
                           publicscorechange = publicscorechange,
                           averagesentiment = averagesentiment,
                           daily_growth=daily_growth, 
                           articles=top_10_articles, 
                           stock_data = stock_data,
                           price_data_close = price_data_close,
                           price_data_date = price_data_date,
                           is_following = is_following,
                           logged_in = logged_in)

# Retrieves several rankings for a company against the whole database
def get_company_rankings(company):
    try:
        qrytext= text("Select compname, num, round(avg, 2) from (select compname, avg(stockvolume) as avg, row_number() over (order by avg(stockvolume) desc) as num from (select compname, stockvolume from stock order by stockday desc limit (select count(*)*5 from company)) Group by compname) where compname=:cname")
        rankvolume_result = conn.execute(qrytext, {"cname": company}).fetchone()
        rankvolume = rankvolume_result[1]
        volume = rankvolume_result[2]

        qrytext1= text("Select compname, num from (select compname, row_number() over (order by comprating desc) as num from company) where compname = :cname")
        rankrating_result = conn.execute(qrytext1, {"cname": company}).fetchone()
        rankrating = rankrating_result[1]

        qrytext2= text("Select compname, row_number, growth from (SELECT compname,  row_number() over (order by ROUND(CAST(((stockclose/stockopen)-1)*100 AS NUMERIC), 5) desc), ROUND(CAST(((stockclose/stockopen)-1)*100 AS NUMERIC), 5) as growth FROM ((SELECT * FROM company) NATURAL JOIN (SELECT compname, stockclose FROM stock ORDER BY stockday DESC LIMIT (SELECT COUNT(*) FROM company)) NATURAL JOIN ((SELECT compname, stockopen FROM stock WHERE stockday <= ((SELECT stockday FROM stock ORDER BY stockday DESC LIMIT 1) -7) ORDER BY stockday DESC LIMIT (SELECT COUNT(*) FROM company))))) WHERE compname = :cname")
        rankgrowth_result = conn.execute(qrytext2, {"cname": company}).fetchone()
        rankgrowth = rankgrowth_result[1]
        growth = rankgrowth_result[2]

        qrytext3 = text("Select compname, row_number from (select compname, row_number() over (order by dayavg desc) from (select compname, (((stockclose/stockopen)-1)*100 ) as dayavg from stock order by stockday desc limit (select count(*) from company))) where compname = :cname")
        rankdailygrowth_result = conn.execute(qrytext3, {"cname": company}).fetchone()
        rankdailygrowth = rankdailygrowth_result[1]

        return [('Average stock volume (last 5 business days)', rankvolume, volume), ('Public perception rating', rankrating), ('Growth (last 7 days)', rankgrowth, growth), ('Daily growth', rankdailygrowth)]

    except Exception as e:
        conn.rollback()
        print("Error fetching company rankings:", e)
        return None

# Follow/unfollow a company
@app.route('/toggle_follow/<compticker>', methods=['POST'])
def toggle_follow(compticker):
    if 'username' in session:
        username = session['username']
        
        try:
            # Fetch compname using compticker
            qrytext3 = text("SELECT compname FROM company WHERE compticker = :tick")
            compname_result = conn.execute(qrytext3, {"tick": compticker}).fetchone()
            
            # If compname doesn't exist, return an error
            if compname_result is None:
                return jsonify({'status': 'error', 'message': 'Company not found.'})
            
            compname = compname_result[0]
            
            # Check if the user is already following the company
            qrytext = text("SELECT COUNT(*) AS count FROM userfollowedcompanies WHERE username = :uname AND compname = :cname")
            result = conn.execute(qrytext, {"uname": username, "cname": compname}).fetchone()
            existing_follow = result[0]
            
            if existing_follow > 0:
                # Unfollow the company
                qrytext1 = text("DELETE FROM userfollowedcompanies WHERE username = :uname AND compname = :cname")
                conn.execute(qrytext1, {"uname": username, "cname": compname})
                conn.commit()
                return jsonify({'status': 'unfollowed'})
            else:
                # Follow the company
                qrytext2 = text("INSERT INTO userfollowedcompanies (username, compname) VALUES (:uname, :cname)")
                conn.execute(qrytext2, {"uname": username, "cname": compname})
                conn.commit()
                return jsonify({'status': 'followed'})

        except SQLAlchemyError as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)})

    else:
        return jsonify({'status': 'not logged in'})

# Follow/unfollow a category
@app.route('/toggle_follow_category/<category_name>', methods=['POST'])
def toggle_follow_category(category_name):
    if 'username' in session:
        username = session['username']
        
        try:
            # Check if the user is already following the category
            follow_check_query = text("""
                SELECT * FROM UserCategory 
                WHERE userName = :username AND catName = :category_name
            """)
            follow_check_result = conn.execute(follow_check_query, {"username": username, "category_name": category_name}).fetchone()
            
            if follow_check_result:
                # Unfollow the category
                unfollow_query = text("""
                    DELETE FROM UserCategory 
                    WHERE userName = :username AND catName = :category_name
                """)
                conn.execute(unfollow_query, {"username": username, "category_name": category_name})
                conn.commit()
                return jsonify({'status': 'unfollowed', 'category': category_name})
            else:
                # Follow the category
                follow_query = text("""
                    INSERT INTO UserCategory (userName, catName) 
                    VALUES (:username, :category_name)
                """)
                conn.execute(follow_query, {"username": username, "category_name": category_name})
                conn.commit()
                return jsonify({'status': 'followed', 'category': category_name})

        except SQLAlchemyError as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)})
        
    else:
        return jsonify({'status': 'not logged in'})

# Check for news updates
@app.route('/notification', methods =['POST'])
def notification():

    if 'username' in session:
        username = session['username']
        currenttime = datetime.now()
        qrytext = text("SELECT compname, ratingdrop FROM company WHERE lastupdate > (:ct - interval '10 seconds') AND compname in (SELECT compname FROM userfollowedcompanies WHERE username = :uname)")
        updates = conn.execute(qrytext, {"uname": username, "ct": currenttime}).mappings().all()
        
        if len(updates) > 0:
            data = ''
            for row in updates:
                if (row['ratingdrop']):
                    data += str(row['compname']).upper() + ": Public Perception score has fallen 10%\n"
                else:
                    data += str(row['compname']).upper() + "\n"

            response = {'status': "New", 'info': data}

            return jsonify(response)
        else:
            return jsonify({'status': 'no notifications'})

    else:
        return jsonify({'status': 'not logged in'})
        
        
if __name__ == '__main__':
    app.run(debug=True)
