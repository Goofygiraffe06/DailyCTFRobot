from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "<b>Hack The Planet</b>"

def run():
  app.run(host='0.0.0.0',port=1337) # Change it to 8080 or anything you like

def keep_alive():
    t = Thread(target=run)
    t.start()
