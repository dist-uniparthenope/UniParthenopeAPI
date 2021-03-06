from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(80), index=True, unique=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    nome_bar = db.Column(db.String(120), index=True, unique=True)

    def __repr__(self):
        return '<User {}>'.format(self.username) + '<Id {}>'.format(self.id) + '<Email {}>'.format(self.email) + '<Password {}>'.format(self.password_hash)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120))
    image = db.Column(db.BLOB)
    tipologia = db.Column(db.String(120))
    descrizione = db.Column(db.String(120))
    prezzo = db.Column(db.Integer)
    sempre_attivo = db.Column(db.Boolean)
    data = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    nome_food = db.Column(db.String(120), db.ForeignKey('user.nome_bar'))

    def __repr__(self):
        return '<Primo piatto {}>'.format(self.nome) + '<Id {}>'.format(self.id)


class Building(db.Model):
    id_corso = db.Column(db.Integer, primary_key=True)
    struttura_des = db.Column(db.String(120))
    struttura_id = db.Column(db.String(10))
    struttura_ga_id = db.Column(db.Integer)
    corso_ga_id = db.Column(db.String(10))

    def __repr__(self):
        return '<Id Corso {}>'.format(self.id_corso)