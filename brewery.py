'''Brewery'''
from datetime import datetime
import sales_predictor

# Brew Stages
BREW_STAGE_NONE = 0
BREW_STAGE_HOT_BREW = 1
BREW_STAGE_FERMENTATION = 2
BREW_STAGE_CONDITIONING = 3
BREW_STAGE_BOTTLING = 4
BREW_STAGE_STORAGE = 5
BREW_STAGE_DISPACTH = 6

brew_stage = ['None',
              'Hot Brew',
              'Fermentation',
              'Conditioning',
              'Bottling',
              'Storage',
              'Dispatch'
             ]

recipe = ['None',
          'Pilsner',
          'Dunkel',
          'Red Helles'
         ]

class Gyle:
    def __init__(self, id):
        self.id = id
        return

class Product:
    def __init__(self, recipe, hot_brew_time=0, fermentation_time=0, conditioning_time=0):
        self.recipe = recipe
        self.hot_brew_duration = hot_brew_time
        self.fermentation_duration = fermentation_time
        self.conditioning_duration = conditioning_time

class Brew_tank:
    def __init__(self, name, volume, fermenter, conditioner):
        self.name = name
        self.volume = volume
        self.fermenter = fermenter
        self.conditioner = conditioner
        return

class Brewery_tank_pool:
    def __init__(self, name):
        self.tank_pool_name = name
        self.tank_pool = []
        return

    def get_free_tank(self, name=None, volume=0, fermenter=True):
        '''
        Gets a tank from tank_pool if it is available of the given name

        name: name of tank to get from the pool
        volume: the minimum tank volume
        fermenter: allows you to choose a tank with that ability
        '''
        for tank in self.tank_pool:
            if name is not None:
                if name == tank.name:
                    self.tank_pool.remove(tank)
                    return tank

            if (tank.volume >= volume and volume != 0):
                if fermenter:
                    if tank.fermenter:
                        self.tank_pool.remove(tank)
                        return tank
                else:
                    if tank.conditioner:
                        self.tank_pool.remove(tank)
                        return tank
        return None

    def add(self, tank):
        '''
        Add a new tank to the pool
        '''
        self.tank_pool.append(tank)
        return

class Brew_stage:
    def __init__(self, stage, gyle, start=0, duration=0):
        self.stage = stage
        self.gyle = gyle
        self.duration = duration
        self.start_time = start
        self.end_time = 0

class Bottling:
    def __init__(self, stage, gyle, start=0, duration=0):
        self.stage = stage
        self.gyle = gyle
        self.duration = duration
        self.start_time = start
        self.end_time = 0
        self.bottles = 0

class Storage:
    def __init__(self, stage, gyle, start=0, duration=0):
        self.stage = stage
        self.gyle = gyle
        self.duration = duration
        self.start_time = start
        self.end_time = 0

class Dispatch:
    def __init__(self, stage, gyle, start=0, duration=0):
        self.stage = stage
        self.gyle = gyle
        self.duration = duration
        self.start_time = start
        self.end_time = 0

class Batch:
    '''
    Used to record the current state of the batch
    '''
    def __init__(self, gyle, product):
        self.gyle = gyle
        self.product = product
        self.volume = 0
        self.brew_tanks = []
        self.current_brew_stage = BREW_STAGE_NONE
        # Array of stages
        self.brew_stage_log = [BREW_STAGE_NONE,]
        self.brew_stage = {BREW_STAGE_HOT_BREW     : Brew_stage(BREW_STAGE_HOT_BREW, gyle),
                           BREW_STAGE_FERMENTATION : Brew_stage(BREW_STAGE_FERMENTATION, gyle),
                           BREW_STAGE_CONDITIONING : Brew_stage(BREW_STAGE_CONDITIONING, gyle),
                           BREW_STAGE_BOTTLING     : Bottling(BREW_STAGE_BOTTLING, gyle),
                           BREW_STAGE_STORAGE      : Storage(BREW_STAGE_STORAGE, gyle),
                           BREW_STAGE_DISPACTH     : Dispatch(BREW_STAGE_DISPACTH, gyle)
                          }
        return

    def start_brew_stage(self, stage, gyle, start, duration, tank=None):
        '''
        Used to record the start of stage infomation

        stage: The process the batch is currently in
        gyle: The unique batch number
        start: The start date of the current process
        duration: How long each process will last
        '''
        if self.gyle == gyle:
            self.current_brew_stage = stage
            stage = self.brew_stage[stage]
            stage.gyle = gyle
            stage.start_time = start
            stage.duration = duration
            if tank is not None:
                self.brew_tanks.append(tank)

            # schedule brew! add event to scheduler queue

        return

    def end_brew_stage(self, stage, gyle, tank_pool=None):
        '''
        Used to record the end of stage infomation

        stage: The process the batch is currently in
        gyle: The unique batch number
        '''
        if self.gyle == gyle:
            stage = self.brew_stage[stage]
            stage.end_time = datetime.now()
            if tank_pool is not None:
                for tank in self.brew_tanks:
                    tank_pool.add(tank)
                self.brew_tanks = []
        return


def init_brew_tank_pool(pool_name):
    '''
    Called at start-of-day to create the brewing tank pool
    '''
    tank_pool = Brewery_tank_pool(pool_name)
    tank_pool.add(Brew_tank('Albert', 1000, True, True))
    tank_pool.add(Brew_tank('Brigadier', 800, True, True))
    tank_pool.add(Brew_tank('Camilla', 1000, True, True))
    tank_pool.add(Brew_tank('Dylon', 800, True, True))
    tank_pool.add(Brew_tank('Emily', 1000, True, True))
    tank_pool.add(Brew_tank('Florence', 800, True, True))
    tank_pool.add(Brew_tank('Gertrude', 680, False, True))
    tank_pool.add(Brew_tank('Harry', 680, False, True))
    tank_pool.add(Brew_tank('R2D2', 800, True, False))
    return tank_pool

def brew_new_batch(gyle, volume, product, start, tank_pool):
    '''
    Helper function for the testing, it records all the infomation for the
    specific batch
    '''
    tank = tank_pool.get_free_tank(volume)
    b = Batch(gyle, product)
    b.current_brew_stage = BREW_STAGE_HOT_BREW
    b.start_brew_stage(BREW_STAGE_HOT_BREW, gyle, start, product.hot_brew_time, product, tank)
    print(b)
    print(tank)

def test_fncs():
    '''
    Testing function, used to execute unit test functions
    '''
    brewery_tank_pool = init_brew_tank_pool('barnabys')
    print(brewery_tank_pool)
    #test_tank()
    #test_gyle()
    #test_batch()
    return


if __name__ == "__main__":
    # unit tests
    test_fncs()
