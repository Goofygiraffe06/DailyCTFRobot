from flask import Flask
from threading import Thread

app = Flask('')


@app.route('/')
def home():
    return "<b>Hack The Planet</b>"


def run():
    # Change it to 8080 or anything you like
    app.run(host='0.0.0.0', port=1337)


def keep_alive():
    t = Thread(target=run)
    t.start()
