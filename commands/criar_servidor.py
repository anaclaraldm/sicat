from utils import db
from models import Servidor
from flask.cli import with_appcontext
import click

@click.command('criar_servidor')
@with_appcontext
def criar_servidor():
    servidor = Servidor(
        nome='Socorro',
        email='Socorro@ifrn.edu.br',
        senha='123456',
        telefone='84999999999',
        funcao='servidor'
    )

    db.session.add(servidor)
    db.session.commit()
    click.echo('Servidor ETEP criado com sucesso')