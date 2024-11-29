CREATE TABLE company (
    compID SERIAL NOT NULL PRIMARY KEY,
    compName VARCHAR(100) NOT NULL UNIQUE,
    compTicker VARCHAR(10) NOT NULL UNIQUE,
    compRating INTEGER NOT NULL CHECK (comprating >= 0 AND comprating <= 100)
);
CREATE TABLE users (
    userID SERIAL NOT NULL PRIMARY KEY,
    userName VARCHAR(100) NOT NULL UNIQUE,
    userEmail VARCHAR(100) NOT NULL UNIQUE,
    userPasswordhash VARCHAR(100) NOT NULL
);
CREATE TABLE category (
    catName VARCHAR(100) NOT NULL PRIMARY KEY
);
CREATE TABLE news (
    newsID SERIAL NOT NULL PRIMARY KEY,
    newsDate DATE,
    newsTitle TEXT,
    newsLink TEXT UNIQUE,
    newsComp VARCHAR(100),
    newsCat VARCHAR(100),
    newsSentiment INTEGER,
    FOREIGN KEY (newsComp) REFERENCES company(compName),
    FOREIGN KEY (newsCat) REFERENCES category(catName)
);
CREATE TABLE stock (
    compID INTEGER,
    stockDay DATE,
    stockOpen FLOAT CHECK (stockOpen > 0),
    stockClose FLOAT CHECK (stockClose >0),
    stockDiffDay FLOAT,
    FOREIGN KEY (compID) REFERENCES company(compID),
    PRIMARY KEY (compID, stockDay)
);
CREATE TABLE UserCategory (
    userID INTEGER,
    catName VARCHAR(100),
    FOREIGN KEY (userID) REFERENCES users(userID),
    FOREIGN KEY (catName) REFERENCES category(catName),
    PRIMARY KEY (userID, catName)
);
CREATE TABLE CompanyCategory (
    compID INTEGER,
    catName VARCHAR(100),
    FOREIGN KEY (compID) REFERENCES company(compID),
    FOREIGN KEY (catName) REFERENCES category(catName),
    PRIMARY KEY (compID, catName)
);
CREATE TABLE UserFollowedCompanies (
    userID INTEGER,
    compID INTEGER,
    FOREIGN KEY (userID) REFERENCES users(userID),
    FOREIGN KEY (compID) REFERENCES company(compID),
    PRIMARY KEY (userID, compID)
);
