from flask import Flask, Blueprint, url_for, jsonify, current_app, abort
from flask_restplus import Api, Resource, reqparse
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
import requests
import json

import os
UPLOAD_FOLDER = '/files'

app = Flask(__name__)
url = "https://uniparthenope.esse3.cineca.it/e3rest/api/"
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

import models


class BaseConfig(object):
    DATA_FOLDER="data_folder"


config = {
    "default": BaseConfig
}


def configure_app(app):
    config_name = os.getenv('FLASK_CONFIGURATION', 'default')
    app.config.from_object(config[config_name]) # object-based default configuration
    app.config.from_pyfile('config.cfg', silent=True) # instance-folders configuration


configure_app(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

api = Api(app)


@api.route('/api/uniparthenope/login/<token>',methods=['GET'])
class Login(Resource):
    def get(self, token):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url+"login", headers=headers)
        if response.status_code == 401:
            tok = User.query.filter_by(token=token).first()
            if tok is None:
                if token == "YWRtaW46TWVsbG9uZTIwMTkh":
                    print('Auth Admin')
                    return jsonify({'statusCode': 666, 'username': "Admin"})
                else:
                    print('Auth Failed')
                    return jsonify({'statusCode': 401, 'errMsg': "Invalid Username or Password!"})
            else:
                print('Auth Fornitore Servizi')
                return jsonify({'statusCode': 600, 'username': tok.nome_bar})
        else:
            print('Auth Stu/Doc')
            print(response.json())
            return jsonify({'response': response.json()})


@api.route('/api/uniparthenope/totalexams/<token>/<matId>', methods=['GET'])
class TotalExams(Resource):
    def get(self, token, matId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        
            }
        response = requests.request("GET", url + "libretto-service-v1/libretti/" + matId + "/stats", headers=headers)
        _response = response.json()
        totAdSuperate = _response['numAdSuperate'] + _response['numAdFrequentate']
        return jsonify({'totAdSuperate': totAdSuperate,
                        'numAdSuperate': _response['numAdSuperate'],
                        'cfuPar': _response['umPesoSuperato'],
                        'cfuTot': _response['umPesoPiano']})


@api.route('/api/uniparthenope/average/<token>/<matId>/<value>', methods=['GET'])
class TotalExams(Resource):
    def get(self, token, matId, value):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "libretto-service-v1/libretti/" + matId + "/medie", headers=headers)

        _response = response.json()
        for i in range(0,len(_response)):
            if _response[i]['tipoMediaCod']['value'] is value:
                if _response[i]['base'] is 30:
                    base_trenta = 30
                    media_trenta = _response[i]['media']
                if _response[i]['base'] is 110:
                    base_centodieci = 110
                    media_centodieci = _response[i]['media']

        return jsonify({'trenta': media_trenta,
                            'base_trenta': base_trenta,
                            'base_centodieci': base_centodieci,
                            'centodieci': media_centodieci})


@api.route('/api/uniparthenope/current_aa/<token>/<cdsId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, cdsId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "calesa-service-v1/sessioni?cdsId=" + cdsId, headers=headers)
        _response = response.json()

        date = datetime.today()
        curr_day = datetime(date.year, date.month, date.day)

        if curr_day.day <= 15 and curr_day.month >= 9:
            academic_year = str(curr_day.year) + " - " + str(curr_day.year+1)
        else:
            academic_year = str(curr_day.year - 1) + " - " + str(curr_day.year)

        max_year = 0
        for i in range(0, len(_response)):
            if _response[i]['aaSesId'] > max_year:
                max_year = _response[i]['aaSesId']

        for i in range(0, len(_response)):
            if _response[i]['aaSesId'] == max_year:
                startDate = extractData(_response[i]['dataInizio'])
                endDate = extractData(_response[i]['dataFine'])
                
                print("Inizio: " + str(startDate))
                print("Fine: " + str(endDate))
                print("Oggi: " + str(curr_day))

                if (curr_day >= startDate and curr_day <= endDate):
                    curr_sem = _response[i]['des']
                    if (curr_sem == "Sessione Anticipata" or curr_sem == "Sessione Estiva"):
                        return jsonify({'curr_sem': _response[i]['des'],
                                        'semestre': "Secondo Semestre",
                                        'aa_accad': academic_year
                                        })
                    else:
                        return jsonify({'curr_sem': _response[i]['des'],
                                        'semestre': "Primo Semestre",
                                        'aa_accad': academic_year})


@api.route('/api/uniparthenope/pianoId/<token>/<stuId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, stuId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "piani-service-v1/piani/" + stuId, headers=headers)
        _response = response.json()
        pianoId = _response[0]['pianoId']

        return jsonify({'pianoId': pianoId})


@api.route('/api/uniparthenope/exams/<token>/<stuId>/<pianoId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, stuId, pianoId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "piani-service-v1/piani/" + stuId + "/" + pianoId, headers=headers)
        _response = response.json()
        my_exams = []

        for i in range(0, len(_response['attivita'])):
            if _response['attivita'][i]['sceltaFlg'] == 1:

                actual_exam = {}
                actual_exam.update({'nome':_response['attivita'][i]['adLibDes'],
                                    'codice': _response['attivita'][i]['adLibCod'],
                                    'adId': _response['attivita'][i]['chiaveADContestualizzata']['adId'],
                                    'CFU': _response['attivita'][i]['peso'],
                                    'annoId': _response['attivita'][i]['scePianoId'],
                                    'adsceId': _response['attivita'][i]['adsceAttId']
                                 })

                my_exams.append(actual_exam)

        return jsonify(my_exams)


@api.route('/api/uniparthenope/checkExam/<token>/<matId>/<examId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, matId, examId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "libretto-service-v1/libretti/" + matId + "/righe/" + examId, headers=headers)

        if response.status_code == 500:
            return jsonify({'stato': "Indefinito",
                            'tipo': "",
                            'data': "",
                            'lode': 0,
                            'voto': "OK",
                            })
        else:
            _response = response.json()

            if len(_response) == 0:
                return jsonify({
                    'stato': "Indefinito",
                    'tipo': "",
                    'data': "",
                    'lode': 0,
                    'voto': "OK"
                    })
            elif _response['statoDes'] == "Superata":
                return jsonify({'stato': _response['statoDes'],
                            'tipo': _response['tipoInsDes'],
                            'data': _response['esito']['dataEsa'].split()[0],
                            'lode': _response['esito']['lodeFlg'],
                            'voto': _response['esito']['voto'],
                            })
            else:
                return jsonify({'stato': _response['statoDes'],
                            'tipo': _response['tipoInsDes'],
                            'data': _response['esito']['dataEsa'],
                            'lode': _response['esito']['lodeFlg'],
                            'voto': _response['esito']['voto'],
                            })


@api.route('/api/uniparthenope/checkAppello/<token>/<cdsId>/<adId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, cdsId, adId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "calesa-service-v1/appelli/" + cdsId + "/" + adId, headers=headers)
        _response = response.json()

        my_exams = []
        for i in range(0, len(_response)):
            if _response[i]['stato'] == "I" or _response[i]['stato'] == "P":
                actual_exam = {}
                actual_exam.update({'esame': _response[i]['adDes'],
                                    'appId': _response[i]['appId'],
                                    'stato': _response[i]['stato'],
                                    'statoDes': _response[i]['statoDes'],
                                    'docente': _response[i]['presidenteCognome'].capitalize(),
                                    'docente_completo': _response[i]['presidenteCognome'].capitalize() + " " + _response[i]['presidenteNome'].capitalize(),
                                    'numIscritti': _response[i]['numIscritti'],
                                    'note': _response[i]['note'],
                                    'descrizione': _response[i]['desApp'],
                                    'dataFine': _response[i]['dataFineIscr'].split()[0],
                                    'dataInizio': _response[i]['dataInizioIscr'].split()[0],
                                    'dataEsame': _response[i]['dataInizioApp'].split()[0],
                                    })

                my_exams.append(actual_exam)

        return jsonify(my_exams)


@api.route('/api/uniparthenope/checkPrenotazione/<token>/<cdsId>/<adId>/<appId>/<stuId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, cdsId, adId, appId, stuId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "calesa-service-v1/appelli/" + cdsId + "/" + adId + "/" + appId + "/iscritti/" + stuId, headers=headers)
        _response = response.json()

        if response.status_code == 200:
            if _response['esito']['assenteFlg'] != 1:

                return jsonify({'prenotato': True,
                            'data': _response['dataIns']})
            else:
                return jsonify({'prenotato': False})
        else:
            return jsonify({'prenotato': False})


@api.route('/api/uniparthenope/RecentAD/<adId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, adId):
        headers = {
            'Content-Type': "application/json"
        }
        response = requests.request("GET", url + "logistica-service-v1/logistica?adId=" + adId, headers=headers)
        _response = response.json()

        max_year = 0
        if response.status_code == 200:
            for i in range(0, len(_response)):
                if _response[i]['chiaveADFisica']['aaOffId'] > max_year:
                    max_year = _response[i]['chiaveADFisica']['aaOffId']

            for i in range(0, len(_response)):
                if _response[i]['chiaveADFisica']['aaOffId'] == max_year:
                    return jsonify({'adLogId': _response[i]['chiavePartizione']['adLogId'],
                                    'inizio': _response[i]['dataInizio'].split()[0],
                                    'fine': _response[i]['dataFine'].split()[0],
                                    'ultMod': _response[i]['dataModLog'].split()[0]
                                    })
        else:
            return jsonify({'stsErr': "N"})


@api.route('/api/uniparthenope/infoCourse/<adLogId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, adLogId):
        headers = {
            'Content-Type': "application/json"
        }
        response = requests.request("GET", url + "logistica-service-v1/logistica/" + adLogId + "/adLogConSyllabus", headers=headers)
        _response = response.json()

        if response.status_code == 200:
            return jsonify({'contenuti': _response[0]['SyllabusAD'][0]['contenuti'],
                        'metodi': _response[0]['SyllabusAD'][0]['metodiDidattici'],
                        'verifica': _response[0]['SyllabusAD'][0]['modalitaVerificaApprendimento'],
                        'obiettivi': _response[0]['SyllabusAD'][0]['obiettiviFormativi'],
                        'prerequisiti': _response[0]['SyllabusAD'][0]['prerequisiti'],
                        'testi': _response[0]['SyllabusAD'][0]['testiRiferimento'],
                        'altro': _response[0]['SyllabusAD'][0]['altreInfo']
                        })


from dateutil import tz
@api.route('/api/uniparthenope/segreteria', methods=['GET'])
class CurrentAA(Resource):
    def get(self):
        studenti = [{'giorno': "LUN", 'orario_inizio': "09:00", 'orario_fine': "12:00"},
                    {'giorno': "MAR", 'orario_inizio': "09:00 - 12:30", 'orario_fine': "14:00 - 15.30"},
                    {'giorno': "MER", 'orario_inizio': "09:00", 'orario_fine': "12:00"},
                    {'giorno': "GIO", 'orario_inizio': "09:00 - 12:30", 'orario_fine': "14:00 - 15.30"},
                    {'giorno': "VEN", 'orario_inizio': "09:00", 'orario_fine': "12:00"}]

        didattica = [{'giorno': "LUN", 'orario_inizio': "10:00", 'orario_fine': "13:00"},
                     {'giorno': "MAR", 'orario_inizio': "0", 'orario_fine': "0"},
                     {'giorno': "MER", 'orario_inizio': "10:00", 'orario_fine': "13:00"},
                     {'giorno': "GIO", 'orario_inizio': "0", 'orario_fine': "0"},
                     {'giorno': "VEN", 'orario_inizio': "10:00", 'orario_fine': "13:00"}
                     ]
        settimana = ["LUN", "MAR", "MER", "GIO", "VEN"]
        to_zone = tz.gettz('Europe/Rome')
        from_zone = tz.gettz('UTC')
        _today = datetime.today()
        _today = _today.replace(tzinfo=from_zone)
        today = _today.astimezone(to_zone)
        oc_studenti = "CHIUSO"
        oc_didattica = "CHIUSO"

        for i in range(0, len(studenti)):
            if today.weekday() == settimana.index(studenti[i]['giorno']) and studenti[i]['orario_inizio'] != "0":
                if len(studenti[i]['orario_inizio']) == 5:
                    inizio_h = int(studenti[i]['orario_inizio'][0:2])
                    inizio_m = int(studenti[i]['orario_inizio'][3:5])
                    fine_h = int(studenti[i]['orario_fine'][0:2])
                    fine_m = int(studenti[i]['orario_fine'][3:5])
                    print(str(fine_h) +":" + str(fine_m)+ "=" + str(today.hour)+ ":"+ str(today.minute))
                    if inizio_h <= today.hour <= fine_h or ((fine_h == today.hour or inizio_h == today.hour) and
                        inizio_m <= today.minute <= fine_m):
                        oc_studenti = "APERTA"
                        print('APERTA1')
                    else:
                        print('CHIUSA1')
                else:
                    inizio_h = int(studenti[i]['orario_inizio'][0:2])
                    inizio_m = int(studenti[i]['orario_inizio'][3:5])
                    fine_h = int(studenti[i]['orario_inizio'][8:10])
                    fine_m = int(studenti[i]['orario_inizio'][11:13])

                    inizio2_h = int(studenti[i]['orario_fine'][0:2])
                    inizio2_m = int(studenti[i]['orario_fine'][3:5])
                    fine2_h = int(studenti[i]['orario_fine'][8:10])
                    fine2_m = int(studenti[i]['orario_fine'][11:13])
                    print(str(fine2_h) + ":" + str(fine2_m) + "=" + str(today.hour) + ":" + str(today.minute))

                    if (inizio_h <= today.hour <= fine_h or ((fine_h == today.hour or inizio_h == today.hour) and
                        inizio_m <= today.minute <= fine_m))  or \
                            (inizio2_h <= today.hour <= fine2_h or ((fine2_h == today.hour or inizio2_h == today.hour) and
                        inizio2_m <= today.minute <= fine2_m)):
                        oc_studenti = "APERTA"

        for i in range(0, len(didattica)):
            if today.weekday() == settimana.index(didattica[i]['giorno']) and didattica[i]['orario_inizio'] != "0":
                if len(didattica[i]['orario_inizio']) == 5:
                    inizio_h = int(didattica[i]['orario_inizio'][0:2])
                    inizio_m = int(didattica[i]['orario_inizio'][3:5])
                    fine_h = int(didattica[i]['orario_fine'][0:2])
                    fine_m = int(didattica[i]['orario_fine'][3:5])
                    print(str(fine_h) +":" + str(fine_m)+ "=" + str(today.hour)+ ":"+ str(today.minute))
                    if inizio_h <= today.hour <= fine_h or ((fine_h == today.hour or inizio_h == today.hour) and
                        inizio_m <= today.minute <= fine_m):
                        oc_didattica = "APERTA"
                        print('APERTA1')
                    else:
                        print('CHIUSA1')
                else:
                    inizio_h = int(didattica[i]['orario_inizio'][0:2])
                    inizio_m = int(didattica[i]['orario_inizio'][3:5])
                    fine_h = int(didattica[i]['orario_inizio'][8:10])
                    fine_m = int(didattica[i]['orario_inizio'][11:13])

                    inizio2_h = int(didattica[i]['orario_fine'][0:2])
                    inizio2_m = int(didattica[i]['orario_fine'][3:5])
                    fine2_h = int(didattica[i]['orario_fine'][8:10])
                    fine2_m = int(didattica[i]['orario_fine'][11:13])
                    print(str(fine2_h) + ":" + str(fine2_m) + "=" + str(today.hour) + ":" + str(today.minute))

                    if (inizio_h <= today.hour <= fine_h or ((fine_h == today.hour or inizio_h == today.hour) and
                        inizio_m <= today.minute <= fine_m))  or \
                            (inizio2_h <= today.hour <= fine2_h or ((fine2_h == today.hour or inizio2_h == today.hour) and
                        inizio2_m <= today.minute <= fine2_m)):
                        oc_didattica = "APERTA"

        return jsonify({'didattica': didattica,
                        'orario_didattica': oc_didattica,
                        'studenti': studenti,
                        'orario_studenti': oc_studenti})


@api.route('/api/uniparthenope/examsToFreq/<token>/<stuId>/<pianoId>/<matId>', methods=['GET'])
class CurrentAA(Resource):
     def get(self, token, stuId, pianoId, matId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "piani-service-v1/piani/" + stuId + "/" + pianoId, headers=headers)
        _response = response.json()
        my_exams = []
        for i in range(0, len(_response['attivita'])):
            if _response['attivita'][i]['sceltaFlg'] == 1:
                adId = str(_response['attivita'][i]['chiaveADContestualizzata']['adId'])
                adSceId = _response['attivita'][i]['adsceAttId']
                response_2 = requests.request("GET", url + "libretto-service-v1/libretti/" + matId + "/righe/" + str(adSceId), headers=headers)

                if response_2.status_code == 500:
                    print('ERRORE 500')
                else:
                    _response2 = response_2.json()

                    if _response2['statoDes'] != "Superata" and len(_response2) != 0:
                        print("ADID="+ adId)
                        print("ADSCEID="+str(adSceId))

                        response_3 = requests.request("GET", url + "libretto-service-v1/libretti/" + matId + "/righe/" + str(
                                                      adSceId)+"/partizioni", headers=headers)
                        
                        if response_3.status_code == 500 or response_3.status_code == 404:
                            print('Response 3 non idoneo!skip')
                        else:
                            _response3 = response_3.json()

                            if len(_response3)==0:
                                print("Response3 non idoneo")

                            else:

                                response_4 = requests.request("GET", url + "logistica-service-v1/logistica?adId=" + adId,
                                                    headers=headers)
                                _response4 = response_4.json()

                                max_year = 0
                                print('PROSEGUO')
                                if response_4.status_code == 200:
                                    for x in range(0, len(_response4)):
                                        if _response4[x]['chiaveADFisica']['aaOffId'] > max_year:
                                            max_year = _response4[x]['chiaveADFisica']['aaOffId']

                                    for x in range(0, len(_response4)):
                                        if _response4[x]['chiaveADFisica']['aaOffId'] == max_year:
                                            actual_exam = ({
                                                'nome': _response['attivita'][i]['adLibDes'],
                                                'codice': _response['attivita'][i]['adLibCod'],
                                                'adId': _response['attivita'][i]['chiaveADContestualizzata']['adId'],
                                                'CFU': _response['attivita'][i]['peso'],
                                                'annoId': _response['attivita'][i]['scePianoId'],
                                                'docente': _response3[0]['cognomeDocTit'].capitalize() + " " + _response3[0]['nomeDoctit'].capitalize(),
                                                'docenteID': _response3[0]['docenteId'],
                                                'semestre': _response3[0]['partEffCod'],
                                                'adLogId': _response4[x]['chiavePartizione']['adLogId'],
                                                'inizio': _response4[x]['dataInizio'].split()[0],
                                                'fine': _response4[x]['dataFine'].split()[0],
                                                'ultMod': _response4[x]['dataModLog'].split()[0]
                                            })
                                            my_exams.append(actual_exam)
        return jsonify(my_exams)

'''
AREA RISTORANTI
'''
from models import User, Food

import base64


@api.route('/api/uniparthenope/foods/register/<username>/<password>/<email>/<nomeLocale>/<pwd_admin>', methods=['POST'])
class Login(Resource):
    def post(self, username, password, email, nomeLocale, pwd_admin):
        if pwd_admin == "besteming":
            usern = User.query.filter_by(username=username).first()
            if usern is None:
                token_start = username+":"+password
                token = base64.b64encode(bytes(str(token_start).encode("utf-8")))
                user = User(username=username, email=email, token=token.decode('utf-8'), nome_bar=nomeLocale)

                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                return jsonify({"code": 200, "message": "OK"})
            else:
                return error_response(500, "User already exists!")
        else:
            return error_response(500, "You are not admin!")

@api.route('/api/uniparthenope/foods/getToken/<username>/<pwd_admin>', methods=['GET'])
class Login(Resource):
    def get(self, username, pwd_admin):
        if pwd_admin == "besteming":
            usern = User.query.filter_by(username=username).first()
            if usern is not None:
                return jsonify({"code": 200, "token": usern.token})
            else:
                return error_response(500, "Error!")
        else:
            return error_response(500, "You are not admin!")
##TODO inserire token


from flask import request
@api.route('/api/uniparthenope/foods/addMenu/<token>', methods=['POST'])
class Login(Resource):
    def post(self, token):
        content = request.json
        usern = User.query.filter_by(token=token).first()

        if usern is not None:
            nome_bar = usern.nome_bar
            if content['img'] != "":
                image_data = content['img']
                image_data = bytes(image_data, encoding="ascii")
            else:
                image_data = None

            print(nome_bar)
            nome = content['nome']
            descrizione = content['descrizione']
            tipologia = content['tipologia']
            prezzo = content['prezzo']
            active = content['attivo']
            menu = Food(nome=nome,
                        tipologia=tipologia,
                        descrizione=descrizione,
                        prezzo=prezzo,
                        nome_food=nome_bar,
                        sempre_attivo=active,
                        image=image_data)
            db.session.add(menu)
            db.session.commit()
            return jsonify({"code": 200, "menu_code": menu.id})
        else:
            return error_response(500, "You are not admin!")



@api.route('/api/uniparthenope/foods/removeMenu/<token>/<id>', methods=['GET'])
class Login(Resource):
    def get(self, token, id):
        usern = User.query.filter_by(token=token).first()
        if usern is not None:
            menu = Food.query.filter_by(id=id).first()
            if menu is not None and usern.nome_bar == menu.nome_food:

                db.session.delete(menu)
                db.session.commit()
                return jsonify({"code": 200, "message": "Item id="+str(menu.id)+" deleted!"})
            else:
                return error_response(500, "Object not found!")
        else:
            return error_response(500, "Not admin!")


@api.route('/api/uniparthenope/foods/menuSearchData/<data>', methods=['GET'])
class Login(Resource):
    def get(self, data):

        array = []
        day = data[0:2]
        month = data[2:4]
        year = data[4:8]

        foods = Food.query.all()
        for f in foods:
            if str(f.data.year) == year and str('{:02d}'.format(f.data.month)) == month and str('{:02d}'.format(f.data.day)) == day:
                menu = ({'nome': f.nome_food,
                         'primo': f.primo_piatto,
                         'secondo': f.secondo_piatto,
                         'contorno': f.contorno,
                         'altro': f.altro,
                         'apertura': f.orario_apertura})
                array.append(menu)

        return jsonify(array)

@api.route('/api/uniparthenope/foods/menuSearchUser_Today/<nome_bar>', methods=['GET'])
class Login(Resource):
    def get(self, nome_bar):

        array = []
        today = datetime.today()

        foods = Food.query.all()
        for f in foods:
            if f.data.year == today.year \
                    and f.data.month == today.month \
                    and f.data.day == today.day\
                    and nome_bar == f.nome_food:

                menu = ({'nome': f.nome,
                         'descrizione': f.descrizione,
                         'prezzo': f.prezzo,
                         'tipologia': f.tipologia,
                         'sempre_attivo': f.sempre_attivo})
                array.append(menu)

        return jsonify(array)

@api.route('/api/uniparthenope/foods/getAllNames', methods=['GET'])
class Login(Resource):
    def get(self):
        array = []

        usern = User.query.all()
        for f in usern:
            array.append(f.nome_bar)
        return jsonify(array)


@api.route('/api/uniparthenope/foods/getAllToday', methods=['GET'])
class Login(Resource):
    def get(self):

        array = []
        today = datetime.today()

        foods = Food.query.all()
        for f in foods:
            if (f.data.year == today.year \
                    and f.data.month == today.month \
                    and f.data.day == today.day)\
                    or f.sempre_attivo:
                if f.image is None:
                    image = ""
                else:
                    image = (f.image).decode('ascii')
                menu = ({'nome': f.nome,
                         'descrizione': f.descrizione,
                         'prezzo': f.prezzo,
                         'tipologia': f.tipologia,
                         'sempre_attivo': f.sempre_attivo,
                         'nome_bar': f.nome_food,
                         'image': image})
                array.append(menu)

        return jsonify(array)

@api.route('/api/uniparthenope/foods/menuSearchUser/<nome_bar>', methods=['GET'])
class Login(Resource):
    def get(self, nome_bar):

        array = []

        foods = Food.query.all()
        for f in foods:
            if nome_bar == f.nome_food:
                d = f.data.strftime('%Y-%m-%d %H:%M')
                if f.image is None:
                    image = ""
                else:
                    image = (f.image).decode('ascii')
                menu = ({'data': d,
                        'nome_bar': f.nome_food,
                        'nome': f.nome,
                        'descrizione': f.descrizione,
                        'tipologia': f.tipologia,
                        'prezzo': f.prezzo,
                        'sempre_attivo': f.sempre_attivo,
                        'id': f.id,
                        'image':image
                        })
                array.append(menu)

        return jsonify(array)


'''
FINE AREA RISTORANTI
'''

'''
AREA ORARI ga.uniparthenope.it
'''
import csv
import urllib.request
import io

@api.route('/api/uniparthenope/orari/cercaCorso/<nome_corso>/<nome_prof>/<nome_studio>/<periodo>', methods=['GET'])
class Login(Resource):
    def get(self, nome_corso, nome_prof, nome_studio, periodo):
        end_date = datetime.now() + timedelta(days=int(periodo)*365/12)

        url_n = 'http://ga.uniparthenope.it/report.php?from_day=' + str(datetime.now().day) + \
                '&from_month=' + str(datetime.now().month) + \
                '&from_year=' + str(datetime.now().year) + \
                '&to_day=' + str(end_date.day) + \
                '&to_month=' + str(end_date.month) + \
                '&to_year=' + str(end_date.year) + \
                '&areamatch=Centro+Direzionale&roommatch=&typematch%5B%5D=' + nome_studio + \
                '&namematch=&descrmatch=&creatormatch=&match_private=0&match_confirmed=1&match_referente=&match_unita_interne=&match_ore_unita_interne=&match_unita_vigilanza=&match_ore_unita_vigilanza=&match_unita_pulizie=&match_ore_unita_pulizie=&match_audio_video=&match_catering=&match_Acconto=&match_Saldo=&match_Fattura=&output=0&output_format=1&sortby=s&sumby=d&phase=2&datatable=1'
        url_open = urllib.request.urlopen(url_n)
        csvfile = csv.reader(io.StringIO(url_open.read().decode('utf-16')), delimiter=',') 

        array = []
        for row in csvfile:
            index = 0
            prof = 0
        
            for w in row:
                if (w.find(nome_prof)) != -1:
                    prof = index
                index += 1

            for word in nome_corso:
                item = {}
                if row[0].find(word) != -1 and prof != 0:
                    item.update({'aula': row[2]})
                    item.update({'inizio': createDate(row[3])})
                    item.update({'fine': createDate(row[4])})
                    item.update({'tot': row[5]})
                    item.update({'docente': row[prof]})
                    break

            if item:
                array.append(item)
        if array:
            print(array)
            return jsonify(array)


@api.route('/api/uniparthenope/orari/altriCorsi/<periodo>', methods=['GET'])
class Login(Resource):
    def get(self, periodo):
        end_date = datetime.now() + timedelta(days=int(periodo) * 365 / 12)

        url_n = 'http://ga.uniparthenope.it/report.php?from_day=' + str(datetime.now().day) + \
                '&from_month=' + str(datetime.now().month) + \
                '&from_year=' + str(datetime.now().year) + \
                '&to_day=' + str(end_date.day) + \
                '&to_month=' + str(end_date.month) + \
                '&to_year=' + str(end_date.year) + \
                '&areamatch=Centro+Direzionale&roommatch=&typematch%5B%5D=O&typematch%5B%5D=Y&typematch%5B%5D=Z&typematch%5B%5D=a&typematch%5B%5D=b&typematch%5B%5D=c&typematch%5B%5D=s&typematch%5B%5D=t' + \
                '&namematch=&descrmatch=&creatormatch=&match_private=0&match_confirmed=1&match_referente=&match_unita_interne=&match_ore_unita_interne=&match_unita_vigilanza=&match_ore_unita_vigilanza=&match_unita_pulizie=&match_ore_unita_pulizie=&match_audio_video=&match_catering=&match_Acconto=&match_Saldo=&match_Fattura=&output=0&output_format=1&sortby=s&sumby=d&phase=2&datatable=1'
        url_open = urllib.request.urlopen(url_n)
        csvfile = csv.reader(io.StringIO(url_open.read().decode('utf-16')), delimiter=',')

        array = []
        next(csvfile)
        for row in csvfile:
            lower = row[6].lower()
            if lower.find("manutenzione") != -1:
                id = "M"
            else:
                id= row[7]
            item = ({
                'titolo': row[0],
                'aula': row[2],
                'start_time': createDate(row[3]),
                'end_time': createDate(row[4]),
                'durata': row[5],
                'descrizione': row[6],
                'id': id,
                'confermato': row[9]
            })
            array.append(item)

        return array


def createDate(data):
            mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre",
                    "ottobre", "novembre", "dicembre"]
            data = data.split()
            ##print(data)
            ora = data[0][0:2]
            minuti = data[0][3:5]
            anno = data[5]
            giorno = data[3]
            mese = mesi.index(data[4]) + 1

            ##final_data = datetime(anno, mese, giorno, ora, minuti)
            final_data = str(anno) + "/" + str(mese) + "/" + str(giorno) + " " + str(ora) + ":" + str(minuti)
            return final_data
'''
FINE AREA ORARI ga.uniparthenope.it
'''
def extractData(data):
    data_split = data.split()[0]
    export_data = datetime.strptime(data_split, '%d/%m/%Y')

    return export_data


'''
ANM
'''
from bs4 import BeautifulSoup
@api.route('/api/uniparthenope/anm', methods=['GET'])
class Login(Resource):
    def get(self):
        url = "http://www.anm.it/infoclick/infoclick.php"
        page = urllib.request.urlopen(url)
        soup = BeautifulSoup(page, 'html.parser')
        key = soup.find('script').text
        print(key.split("'")[1])




from werkzeug.http import HTTP_STATUS_CODES


def error_response(status_code, message=None):
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response


if __name__ == '__main__':
    app.run(ssl_context='adhoc')
