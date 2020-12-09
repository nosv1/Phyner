import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

def connectDatabase(db_name):
  class PhynerDB:
    def __init__(self, connection, cursor):
      self.connection = connection
      self.cursor = cursor
  # end PhynerDB

  db_connection = mysql.connector.connect(
    host = os.getenv("DB_HOST"),
    user = os.getenv("DB_USER"),
    password = os.getenv("DB_PASSWORD"),

    database = db_name,
    charset = "utf8mb4",
    use_unicode = True,
    buffered = True
  )
  db_cursor = db_connection.cursor()
  return PhynerDB(db_connection, db_cursor)
# end connectDatabase

def replaceChars(bad_string):
  return bad_string.replace("'", "''").replace("\\", "\\\\")
# end replaceChars