from flask_sqlalchemy import SQLAlchemy

# creating the database
db = SQLAlchemy()

# for login requirements
from flask_login import UserMixin

class Company(db.Model):
    __tablename__='company'
    id = db.Column(db.Integer, primary_key = True)
    compName = db.Column(db.String(100), unique=True)
    compRating = db.Column(db.Integer)
    compRanking = db.Column(db.Integer, unique=True)

    def __init__(self, compName, compRating, compRanking):  
        self.compName = compName
        self.compRating = compRating
        self.compRanking = compRanking


class User(UserMixin, db.Model):
    __tablename__='user'
    id = db.Column(db.Integer, primary_key = True)
    userName = db.Column(db.String(100), unique = True)
    userEmail = db.Column(db.String(100), unique = True)
    userPassword = db.Column(db.String(100))

    def __init__(self, userName, userEmail, userPassword):  
        self.userName = userName
        self.userEmail = userEmail
        self.userPassword = userPassword
        
        
class Category(db.Model):
    __tablename__='category'
    id = db.Column(db.Integer, primary_key=True)
    categName = db.Column(db.String(100), unique = True)

    def __init__(self, categName):  
        self.categName = categName
        
        
class News(db.Model):
    __tablename__='news'
    id = db.Column(db.Integer, primary_key=True)
    newsDate = db.Column(db.Text())
    newsTitle = db.Column(db.String(1000))
    newsLink = db.Column(db.String(2000), unique = True)
    newsComp = db.Column(db.String(100), db.ForeignKey('company.compName'))
    newsCateg = db.Column(db.String(100), db.ForeignKey('category.categName'))

    def __init__(self, newsDate, newsTitle, newsLink, newsComp, newsCateg):  
        self.newsDate = newsDate
        self.newsTitle = newsTitle
        self.newsLink = newsLink
        self.newsComp = newsComp
        self.newsCateg = newsCateg
        
        
class Stock(db.Model):
    __tablename__='stock'
    compID = db.Column(db.Integer, db.ForeignKey('company.id'), primary_key = True)
    stockDay = db.Column(db.Text(), primary_key = True)
    stockOpen = db.Column(db.Float())
    stockClose = db.Column(db.Float())
    stockDiffDay = db.Column(db.Float())

    def __init__(self, compID, stockDay, stockOpen, stockClose, stockDiffDay):  
        self.compID = compID
        self.stockDay = stockDay
        self.stockOpen = stockOpen
        self.stockClose = stockClose
        self.stockDiffDay = stockDiffDay   


class UserCategory(db.Model):
    __tablename__='usercategory'
    userID = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key = True)
    categID = db.Column(db.Integer, db.ForeignKey('category.id'), primary_key = True)
    categName = db.Column(db.String(100))

    def __init__(self, userID, categID, categName):  
        self.userID = userID
        self.categID = categID
        self.categName = categName
        
        
class CompanyCategory(db.Model):
    __tablename__='companycategory'
    compID = db.Column(db.Integer, db.ForeignKey('company.id'), primary_key = True)
    categID = db.Column(db.Integer, db.ForeignKey('category.id'), primary_key = True)
    categName = db.Column(db.String(100))

    def __init__(self, compID, categID, categName):  
        self.compID = compID
        self.categID = categID
        self.categName = categName
        
        
class UserFollowedCompanies(db.Model):
    __tablename__='userfollowedcompany'
    userID = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key = True)
    compID = db.Column(db.Integer, db.ForeignKey('company.id'), primary_key = True)
    categName = db.Column(db.String(100))

    def __init__(self, userID, compID, categName):  
        self.userID = userID
        self.compID = compID
        self.categName = categName