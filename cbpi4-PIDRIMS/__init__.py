from cbpi.api import *
from cbpi.api.base import CBPiBase
from cbpi.api.property import Property
from cbpi.api.decorator import parameters
import asyncio
from asyncio import tasks
import logging
import time
import datetime

@parameters([Property.Number(label = "P", configurable = True, description="P Value of PID"),
             Property.Number(label = "I", configurable = True, description="I Value of PID"),
             Property.Number(label = "D", configurable = True, description="D Value of PID"),
             Property.Number(label = "Delta", configurable = True, description="Maximum allowed temperature difference between RIMS and MLT"),
             Property.Select(label="SampleTime", options=[2,5], description="PID Sample time in seconds. Default: 5 (How often is the output calculation done)"),
             Property.Sensor(label="RIMS Sensor", description="Sensor de temperatura da resistência RIMS")])

class PIDRIMS(CBPiKettleLogic):

    async def on_start(self):
        self.heat_percent_old = 0
        self.running = True
        logging.info("PIDRIMS Liga")

    async def on_stop(self):
        await self.actor_off(self.heater)
        pass

    async def run(self):
        try:
            self.TEMP_UNIT = self.get_config_value("TEMP_UNIT", "C")
            wait_time = sampleTime = int(self.props.get("SampleTime",5))
            delta = float(self.props.get("Delta", 2.0))

            p = float(self.props.get("P", 117.0795))
            i = float(self.props.get("I", 0.2747))
            d = float(self.props.get("D", 41.58))
            self.kettle = self.get_kettle(self.id)
            self.heater = self.kettle.heater
            self.heater_actor = self.cbpi.actor.find_by_id(self.heater)
            self.rims_sensor = self.props.get("RIMS Sensor", None)
                       
            pid = PIDArduino(sampleTime, p, i, d, 0, 100)
            heat_percent_old = 0

            while self.running == True:
                current_kettle_power = self.heater_actor.power
                
                # Leitura dos sensores
                mlt_temp = self.get_sensor_value(self.kettle.sensor).get("value")
                rims_temp = self.get_sensor_value(self.rims_sensor).get("value") if self.rims_sensor else mlt_temp
                target_temp = self.get_kettle_target_temp(self.id)
                
                # Cálculo do PID baseado na temperatura da MLT
                heat_percent = pid.calc(mlt_temp, target_temp)

                # Verifica se a temperatura do RIMS está dentro do limite
                if rims_temp > (target_temp + delta):
                    heat_percent = 0
                    logging.warning(f"Temperatura RIMS ({rims_temp}°{self.TEMP_UNIT}) acima do limite. Desligando aquecimento.")
                
                if (heat_percent_old != heat_percent) or (heat_percent != current_kettle_power):
                    await self.actor_set_power(self.heater, heat_percent)
                    heat_percent_old = heat_percent
                
                await asyncio.sleep(sampleTime)

        except asyncio.CancelledError as e:
            pass
        except Exception as e:
            logging.error("BM_PIDRIMS Error {}".format(e))
        finally:
            self.running = False
            await self.actor_off(self.heater)

# Based on Arduino PID Library
# See https://github.com/br3ttb/Arduino-PID-Library
class PIDArduino(object):

    def __init__(self, sampleTimeSec, kp, ki, kd, outputMin=float('-inf'),
                 outputMax=float('inf'), getTimeMs=None):
        if kp is None:
            raise ValueError('kp must be specified')
        if ki is None:
            raise ValueError('ki must be specified')
        if kd is None:
            raise ValueError('kd must be specified')
        if float(sampleTimeSec) <= float(0):
            raise ValueError('sampleTimeSec must be greater than 0')
        if outputMin >= outputMax:
            raise ValueError('outputMin must be less than outputMax')

        self._logger = logging.getLogger(type(self).__name__)
        self._Kp = kp
        self._Ki = ki * sampleTimeSec
        self._Kd = kd / sampleTimeSec
        self._sampleTime = sampleTimeSec * 1000
        self._outputMin = outputMin
        self._outputMax = outputMax
        self._iTerm = 0
        self._lastInput = 0
        self._lastOutput = 0
        self._lastCalc = 0

        if getTimeMs is None:
            self._getTimeMs = self._currentTimeMs
        else:
            self._getTimeMs = getTimeMs

    def calc(self, inputValue, setpoint):
        now = self._getTimeMs()

        if (now - self._lastCalc) < self._sampleTime:
            return self._lastOutput

        # Compute all the working error variables
        error = setpoint - inputValue
        dInput = inputValue - self._lastInput

        # In order to prevent windup, only integrate if the process is not saturated
        if self._lastOutput < self._outputMax and self._lastOutput > self._outputMin:
            self._iTerm += self._Ki * error
            self._iTerm = min(self._iTerm, self._outputMax)
            self._iTerm = max(self._iTerm, self._outputMin)

        p = self._Kp * error
        i = self._iTerm
        d = -(self._Kd * dInput)

        # Compute PID Output
        self._lastOutput = p + i + d
        self._lastOutput = min(self._lastOutput, self._outputMax)
        self._lastOutput = max(self._lastOutput, self._outputMin)

        # Log some debug info
        self._logger.debug('P: {0}'.format(p))
        self._logger.debug('I: {0}'.format(i))
        self._logger.debug('D: {0}'.format(d))
        self._logger.debug('output: {0}'.format(self._lastOutput))

        # Remember some variables for next time
        self._lastInput = inputValue
        self._lastCalc = now
        return self._lastOutput

    def _currentTimeMs(self):
        return time.time() * 1000

def setup(cbpi):

    '''
    This method is called by the server during startup 
    Here you need to register your plugins at the server
    
    :param cbpi: the cbpi core 
    :return: 
    '''

    cbpi.plugin.register("PIDRIMS", PIDRIMS)
