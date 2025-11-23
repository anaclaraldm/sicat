from flask import flask, render_template, request
import json

app = Flask(__name__)

#index
@app.route('/')
def index():
    return render_template('index.html')

def dashboard():
    dashboard = request.args.get("dashboard") == "1"
    return dict(dashboar=dashboard)
def pesquisa_filtro():
    termo_pesquisa = request.form.get('q', None)
    filtro_status = request.form.get('status','todos')

#login
@app.route('/')
def index():
    return render_template('index.html')

#cadastro
@app.route('/')
def index():
    return render_template('index.html')

#servidor
@app.route('/')
def index():
    return render_template('index.html')

#tutor
@app.route('/')
def index():
    return render_template('index.html')

#tutorado
@app.route('/')
def index():
    return render_template('index.html')

#professor
@app.route('/')
def index():
    return render_template('index.html')

#sessao_tutoria
@app.route('/')
def index():
    return render_template('index.html')




if __name__ == '__main__':
    app.run()