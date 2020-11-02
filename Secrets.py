# functions to deal with opening files in Secrets file
from os import path

def getToken(fileName):
  f = open(getFilepath(fileName), "r")
  key = f.read().strip()
  f.close()
  return key
# end getToken

def getFilepath(fileName):
  basepath = path.dirname(__file__)
  filepath = path.abspath(path.join(basepath, "..", "Secrets", fileName))
  return filepath
# end getFilepath