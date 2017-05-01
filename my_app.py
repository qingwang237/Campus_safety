# -*- coding: utf-8 -*-
from __future__ import print_function
import decimal, time
import json
from flask import Flask, request, Response, render_template
import boto3
from boto3.dynamodb.conditions import Key

app = Flask(__name__)

predefined_crime_labels = {'ROBBE': '抢劫', 'BURGLA': '入室盗窃', 'AGG_A': '攻击',
                           'VEHIC': '车辆犯罪', 'MURD': '谋杀', 'ARSON': '纵火',
                           'RAPE': '强奸', 'FORCIB': '强迫性侵害', 'NONFOR': '非强迫性侵害',
                           'NEG_M': '过失杀人', 'FONDL': '猥亵', 'STATR': '未成年性犯罪'}


def get_crime_at_year(year, data):
    """get the crime data for the specified year and return a dict"""
    return {i: data[i] for i in data if str(year) in i}


def get_crime_for_kind(crime, data, start_year=9, end_year=14):
    """get the crime data for one kind and return a dict"""
    year_range = range(start_year, end_year + 1)
    return {year: data[crime + str(year)] for year in year_range
            if crime + str(year) in data}


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert a DynamoDB item to JSON"""

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def get_dyno_data(name, branch_name=''):
    """get on campus crime data from the dynamodb"""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('OnCampusCrimeNew')
    response = table.query(
        KeyConditionExpression=Key('schoolName').eq(name))
    item = response['Items']
    # results = []
    # for i in item:
    #     results.append(json.dumps(i, cls=DecimalEncoder))
    if not branch_name:
        return item
    else:
        return [data for data in item if data['BRANCH'] == branch_name]


def save_user_info(email, query=''):
    """save user email to the dynamodb table"""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('UserEmail')
    table.put_item(
       Item={
            'email': email,
            'timestamp': int(time.time()),
            'query': query,
            'time': time.ctime(),
            'from_app': 'CampusCrime'
        }
    )


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/usersubmit/', methods=['POST'])
def usersubmit():
    fullname = request.form['schoolname']
    branch_name = fullname.split('-')[-1]
    campus_name = fullname.replace('-' + branch_name, '')
    email = request.form['youremail']
    save_user_info(email, campus_name + '-' + branch_name)
    data = get_dyno_data(campus_name)
    if not data:
        return render_template('errors.html',
                               message=u'未找到此学校的相关数据，请确认学校名字是否正确')
    # filter by branch name if provided otherwise use the first branch
    if branch_name:
        try:
            main_campus = [item for item in data if item[
                'BRANCH'] == branch_name][0]
        except IndexError:
            return render_template('errors.html',
                                   message=u"未找到此分校的相关数据，请确认输入是否正确")
    else:
        main_campus = data[0]
    labels = ["女", "男"]
    values = [main_campus['women_total'], main_campus['men_total']]
    colors = ["rgba(255, 64, 0, 0.8)", "rgba(0, 191, 255, 0.8)"]
    year_label = ['2009', '2010', '2011', '2012', '2013', '2014']
    crimes_per_year = [sum(d.itervalues()) for d in [
        get_crime_at_year(year, main_campus) for year in range(9, 15)]]
    latest_year_crime = get_crime_at_year(14, main_campus)
    year13_crime = get_crime_at_year(13, main_campus)
    year12_crime = get_crime_at_year(12, main_campus)
    majorcrimes14 = [latest_year_crime[crime] for crime in [
        'ARSON14', 'ROBBE14', 'BURGLA14', 'AGG_A14',  'VEHIC14']]
    majorcrimes13 = [year13_crime[crime] for crime in [
        'ARSON13', 'ROBBE13', 'BURGLA13', 'AGG_A13',  'VEHIC13']]
    majorcrimes12 = [year12_crime[crime] for crime in [
        'ARSON12', 'ROBBE12', 'BURGLA12', 'AGG_A12', 'VEHIC12']]
    crime_labels = []
    crime_type_values = []
    for key, value in latest_year_crime.iteritems():
        if int(value) != 0 and 'FILTER' not in key:
            crime_labels.append(predefined_crime_labels[str(key[:-2])])
            crime_type_values.append(value)
    return render_template('report.html',
                           labels=json.dumps(labels),
                           values=json.dumps(values, cls=DecimalEncoder),
                           colors=json.dumps(colors),
                           school_name=campus_name,
                           branch_name=main_campus['BRANCH'],
                           address=main_campus['Address'],
                           city=main_campus['City'],
                           state=main_campus['State'],
                           zipcode=main_campus['ZIP'],
                           sector=main_campus['Sector_desc'],
                           total_student=sum(values),
                           year_label=year_label,
                           crimes_per_year=json.dumps(
                               crimes_per_year, cls=DecimalEncoder),
                           crime_labels=json.dumps(crime_labels),
                           crime_type_values=json.dumps(crime_type_values,
                                                        cls=DecimalEncoder),
                           majorcrimes14=json.dumps(majorcrimes14,
                                                    cls=DecimalEncoder),
                           majorcrimes13=json.dumps(majorcrimes13,
                                                    cls=DecimalEncoder),
                           majorcrimes12=json.dumps(majorcrimes12,
                                                    cls=DecimalEncoder)
                           )
    # return render_template('generated.html', name=fullname, email=email)


@app.route('/oncampuscrime/')
def get_on_campus_crime():
    campus_name = request.args.get('name')
    branch_name = request.args.get('branch')
    if not campus_name:
        return "No campus name is provided.", 200
    else:
        if not branch_name:
            return Response(json.dumps(get_dyno_data(campus_name),
                                       cls=DecimalEncoder),
                            mimetype='application/json')
        else:
            return Response(json.dumps(get_dyno_data(campus_name, branch_name),
                                       cls=DecimalEncoder),
                            mimetype='application/json')


@app.route('/report/')
def get_report():
    campus_name = request.args.get('name')
    branch_name = request.args.get('branch')
    if not campus_name:
        return "No campus name is provided.", 200
    else:
        data = get_dyno_data(campus_name)
        if not data:
            return "No data found.", 200
        # filter by branch name if provided otherwise use the first branch
        if branch_name:
            try:
                main_campus = [item for item in data if item[
                    'BRANCH'] == branch_name][0]
            except IndexError:
                return "No branch for this name is found.", 200
        else:
            main_campus = data[0]
        labels = ["女", "男"]
        values = [main_campus['women_total'], main_campus['men_total']]
        colors = ["rgba(255, 64, 0, 0.8)", "rgba(0, 191, 255, 0.8)"]
        year_label = ['2009', '2010', '2011', '2012', '2013', '2014']
        crimes_per_year = [sum(d.itervalues()) for d in [
            get_crime_at_year(year, main_campus) for year in range(9, 15)]]
        latest_year_crime = get_crime_at_year(14, main_campus)
        year13_crime = get_crime_at_year(13, main_campus)
        year12_crime = get_crime_at_year(12, main_campus)
        majorcrimes14 = [latest_year_crime[crime] for crime in [
            'ARSON14', 'ROBBE14', 'BURGLA14', 'AGG_A14',  'VEHIC14']]
        majorcrimes13 = [year13_crime[crime] for crime in [
            'ARSON13', 'ROBBE13', 'BURGLA13', 'AGG_A13',  'VEHIC13']]
        majorcrimes12 = [year12_crime[crime] for crime in [
            'ARSON12', 'ROBBE12', 'BURGLA12', 'AGG_A12', 'VEHIC12']]
        crime_labels = []
        crime_type_values = []
        for key, value in latest_year_crime.iteritems():
            if int(value) != 0 and 'FILTER' not in key:
                crime_labels.append(predefined_crime_labels[str(key[:-2])])
                crime_type_values.append(value)
        return render_template('report.html',
                               labels=json.dumps(labels),
                               values=json.dumps(values, cls=DecimalEncoder),
                               colors=json.dumps(colors),
                               school_name=campus_name,
                               branch_name=main_campus['BRANCH'],
                               address=main_campus['Address'],
                               city=main_campus['City'],
                               state=main_campus['State'],
                               zipcode=main_campus['ZIP'],
                               sector=main_campus['Sector_desc'],
                               total_student=sum(values),
                               year_label=year_label,
                               crimes_per_year=json.dumps(
                                   crimes_per_year, cls=DecimalEncoder),
                               crime_labels=json.dumps(crime_labels),
                               crime_type_values=json.dumps(crime_type_values,
                                                            cls=DecimalEncoder),
                               majorcrimes14=json.dumps(majorcrimes14,
                                                        cls=DecimalEncoder),
                               majorcrimes13=json.dumps(majorcrimes13,
                                                        cls=DecimalEncoder),
                               majorcrimes12=json.dumps(majorcrimes12,
                                                        cls=DecimalEncoder)
                               )


# We only need this for local development.
if __name__ == '__main__':
    app.run()
