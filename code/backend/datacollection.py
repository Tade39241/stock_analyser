from sqlalchemy import create_engine

# Connection to database - confidential 
connection_string = "postgresql://datacollection:LG2XSktO1YcJ@ep-lively-sun-a2f4gm8y-pooler.eu-central-1.aws.neon.tech/cwkdb?options=endpoint%3Dep-lively-sun-a2f4gm8y"
engine = create_engine(connection_string)

# Example for inserting and querying the database
with engine.connect() as conn:
   conn.execute(
       ("INSERT INTO company (compname, comprating, compranking) VALUES ('Apple', 80, 1)")
   )
   conn.execute(
       ("INSERT INTO company (compname, comprating, compranking) VALUES ('Microsoft', 40, 2)")
   )

   result = conn.execute(("SELECT * FROM company"))
   for row in result:
       print(f"Id: {row.compid} Name: {row.compname}  Rating: {row.comprating} Ranking: {row.compranking}")
