import mysql.connector
import Secrets

def connectDatabase(db_name):
  class PhynerDB:
    def __init__(self, connection, cursor):
      self.connection = connection
      self.cursor = cursor
  # end PhynerDB

  db_connection = mysql.connector.connect(
    host = "10.0.0.227",
    user = "Phyner",
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