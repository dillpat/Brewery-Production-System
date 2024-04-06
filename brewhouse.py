'''Barnaby's Brewhouse'''
from datetime import datetime
from time import strftime
import json
import logging
from logging.handlers import RotatingFileHandler
import traceback
from flask import Flask, render_template, request, redirect
import brewery as bh
import sales_predictor as sp


config_file: str = "config.json"
config_dict: dict = {}

batches = {}
brewery_tank_pool = bh.Brewery_tank_pool('')


# Display user error message
def user_error(error_msg):
    msg = '<form action="/">' \
           +  error_msg \
           +  '<br>' \
           +  '<input type="submit" value="Back">' \
           + '</form>'
    return msg

# Initialise flask framework
app = Flask(__name__)


# Functions to integrate with flask logging.
@app.after_request
def after_request(response):
    '''
    This logs the web page after every request. This avoids duplication
    of every registry in the log since 500 is already logged via
    @app.errorhandler
    '''
    if response.status_code != 500:
        time_stamp = strftime('[%Y-%b-%d %H:%M]')
        logger.info('%s %s %s %s %s %s',
                    time_stamp,
                    request.remote_addr,
                    request.method,
                    request.scheme,
                    request.full_path,
                    response.status)
    return response


@app.errorhandler(404)
def not_found(e) ->str:
    '''
    Handle URL not found exceptions
    '''
    return 'Not Found: The requested URL was not found on the server', 404


@app.errorhandler(Exception)
def exceptions(e) -> [str, int]:
    '''
    Logging after every expection.
    Handle program crash exception. Logs stack back trace
    '''
    time_stamp = strftime('[%Y-%b-%d %H:%M]')
    trace_back = traceback.format_exc()
    logger.info('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s',
                time_stamp,
                request.remote_addr,
                request.method,
                request.scheme,
                request.full_path,
                trace_back)
    return "Internal Server Error", 500


def brew_status(beer=None):
    '''
    Allows the user to view the brewing status of the currently brewing recipes
    '''
    view_brewing = []
    for b in batches.values():
        recipe = b.product.recipe
        if beer is None or beer == recipe:
            batch_number = b.gyle
            stage = bh.brew_stage[b.current_brew_stage]
            time = b.brew_stage[b.current_brew_stage].start_time.strftime("%Y-%m-%dT%H:%M")
            if len(b.brew_tanks) > 0:
                name = b.brew_tanks[0].name
            else:
                name = ''
            row = '{} {} {} {} {}'.format(batch_number, stage, recipe, time, name)
            view_brewing.append(row)
    return view_brewing


@app.route('/', methods=['POST', 'GET'])
def main_page():
    return render_template('home.html')


@app.route('/salesprediction', methods=['POST', 'GET'])
def sales_predicition():
    sp.get_predicted_sales('Barnabys_sales_fabricated_data.csv', 'html')
    return render_template('predicted_sales.html')


@app.route('/viewbrewing', methods=['POST', 'GET'])
def view_brewing():
    brewing_list = brew_status()
    if brewing_list is not None:
        return render_template('brew_status.html', brew_status=brewing_list)
    return render_template('viewbrewing.html')


@app.route('/hotbrew', methods=['POST', 'GET'])
def hot_brew():
    ''''
    Allows the user to input a new recipe into the hot brew stage
    '''
    global batches

    query = request.args.get("home")
    if query is not None and query == 'hot_brew':
        return render_template('hotbrew.html')

    beer = request.args.get("beer")
    if beer is not None:
        return render_template('hotbrew.html', sel=beer)

    recipe = request.args.get("Recipe")
    gyle = request.args.get("BatchNumber")
    duration = request.args.get("Duration")
    # makes sure user inputs a valid gyle number
    if gyle is not None and \
       gyle != '' and \
       gyle not in batches:
        p = bh.Product(recipe, hot_brew_time=duration)
        b = bh.Batch(gyle, p)
        b.start_brew_stage(bh.BREW_STAGE_HOT_BREW, gyle, datetime.now(), duration)
        batches[gyle] = b
        return render_template('home.html')
    return user_error('Gyle Number Already in Use, Please Try Again')


@app.route('/fermentation', methods=['POST', 'GET'])
def fermentation():
    ''''
    Allows the user to input a new recipe into the fermentation stage
    '''
    global batches
    # import pdb;pdb.set_trace()
    query = request.args.get("home")
    if query is not None and query == 'fermentation':
        # makes a list of all the namesof the fermenting tanks
        tank_pool = [x.name for x in brewery_tank_pool.tank_pool if x.fermenter == True]
        datetime_now = datetime.now().strftime("%Y-%m-%dT%H:%M")
        return render_template('fermentation.html', tankpool=tank_pool, datetime_now=datetime_now)

    tank = request.args.get('tank')
    gyle = request.args.get('BatchNumber')
    start_time = request.args.get('StartTime')
    duration = request.args.get("Duration")

    # makes sure user inputs a valid gyle number
    if gyle is not None and \
       gyle != '' and \
       gyle in batches:
        b = batches[gyle]

        if b.current_brew_stage != bh.BREW_STAGE_HOT_BREW:
            return user_error('Batch first requires Hot Brew')

        tank = brewery_tank_pool.get_free_tank(name=tank)
        if tank is None:
            return user_error('No free available fermentation tanks')

        b.end_brew_stage(bh.BREW_STAGE_HOT_BREW, gyle, tank_pool=brewery_tank_pool)
        b.product.fermentation_duration = duration
        b.start_brew_stage(bh.BREW_STAGE_FERMENTATION, gyle, datetime.now(), duration, tank)
        return render_template('home.html')

    return user_error('Batch not found')


@app.route('/conditioning', methods=['POST', 'GET'])
def conditioning():
    ''''
    Allows the user to input a new recipe into the conditioning stage
    '''
    global batches

    query = request.args.get("home")
    if query is not None and query == 'conditioning':
        # composed list of conditoner tank pool names
        tank_pool = [x.name for x in brewery_tank_pool.tank_pool if x.conditioner == True]
        datetime_now = datetime.now().strftime("%Y-%m-%dT%H:%M")
        return render_template('conditioning.html', tankpool=tank_pool, datetime_now=datetime_now)

    tank = request.args.get('tank')
    gyle = request.args.get('BatchNumber')
    start_time = request.args.get('StartTime')
    duration = request.args.get("Duration")


    # makes sure user inputs a valid gyle number
    if gyle is not None and \
       gyle != '' and \
       gyle in batches:
        b = batches[gyle]

        if b.current_brew_stage != bh.BREW_STAGE_FERMENTATION:
            return user_error('Batch requires fermentation')

        tank = brewery_tank_pool.get_free_tank(name=tank)
        if tank is None:
            return user_error('No free available conditoning tanks')

        b.end_brew_stage(bh.BREW_STAGE_FERMENTATION, gyle, tank_pool=brewery_tank_pool)
        b.product.conditioning_duration = duration
        b.start_brew_stage(bh.BREW_STAGE_CONDITIONING, gyle, datetime.now(), duration, tank)
        return render_template('home.html')

    return user_error('Batch not found')


@app.route('/bottling', methods=['POST', 'GET'])
def bottling():
    ''''
    Allows the user to input a new recipe into the bottling stage
    '''
    global batches

    query = request.args.get("home")
    if query is not None and query == 'bottling':
        datetime_now = datetime.now().strftime("%Y-%m-%dT%H:%M")
        return render_template('bottling.html', datetime_now=datetime_now)

    recipe = request.args.get('Recipe')
    gyle = request.args.get('BatchNumber')
    start_time = request.args.get('StartTime')
    duration = request.args.get("Duration")

    # makes sure user inputs a valid gyle number
    if gyle is not None and \
       gyle != '' and \
       gyle in batches:
        b = batches[gyle]

        if b.current_brew_stage != bh.BREW_STAGE_CONDITIONING:
            return user_error('Batch requires conditioning')

        b.end_brew_stage(bh.BREW_STAGE_CONDITIONING, gyle, brewery_tank_pool)
        b.product.bottling_duration = duration
        b.start_brew_stage(bh.BREW_STAGE_BOTTLING, gyle, datetime.now(), duration)
        return render_template('home.html')

    return user_error('Batch not found')


@app.route('/recommendation', methods=['POST', 'GET'])
def beer_recommendation():
    '''
    User can see the algorithms recommended beer brewing suggestion based on
    sales prediciton for the month. It also displays which current other brewings
    are being produced so the user can decide if brewing another batch is
    necessary
    '''
    global batches
    sales_data, df, _ = sp.get_predicted_sales('Barnabys_sales_fabricated_data.csv', 'html')
    months = [d.date().strftime("%Y-%b") for d in df['Month']]

    query = request.args.get("home")
    if query is not None and query == 'beer_recommendation':
        brewing_list = brew_status()
        return render_template('recommendation_month.html',
                               months=months,
                               brew_status=brewing_list
                               )

    month = request.args.get('month')

    # makes sure user inputs a valid month
    if month is not None and \
       month != '' and \
       month in months:
        m = months.index(month)

        # get recommend beer quantities for the given month
        pilsner = df['Pilsner'][m]
        dunkel = df['Dunkel'][m]
        red_helles = df['Red Helles'][m]
        total_quant = df['Total'][m]

        # recommend beer recipe to brew
        recommend = pilsner
        recipe = 'Pilsner'
        if dunkel > recommend:
            recommend = dunkel
            recipe = 'Dunkel'
        if red_helles > recommend:
            recommend = red_helles
            recipe = 'Red Helles'

        brewing_list = brew_status(recipe)
        return render_template('recommendation_beer.html',
                               months=months,
                               recommend=recipe,
                               brew_status=brewing_list
                               )

    return redirect('/')


def init_brewery():
    global brewery_tank_pool
    brewery_tank_pool = bh.init_brew_tank_pool('barnabys')


def load_config(filename):
    '''
    Loads a json format configuration file.

    filename - configuration file name
    '''
    config = {}
    # load json config file
    with open(filename, 'r') as file:
        config = json.load(file)
        print(config)
    return config


if __name__ == '__main__':
    # Load config
    config_dict = load_config(config_file)

    # Initialize logger
    log_file = config_dict['logging']['log_file']
    log_level = int(config_dict['logging']['log_level'])
    handler = RotatingFileHandler(log_file,
                                  maxBytes=100000,
                                  backupCount=3)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    logger.addHandler(handler)

    # start brewery
    init_brewery()

    # Start up flask framework
    app.run(debug=True, threaded=True)
