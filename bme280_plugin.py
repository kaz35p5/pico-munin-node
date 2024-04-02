'''
pico-munin-node plugin for CircuitPython

Typical usage:

import board
import busio
from bme280_plugin import Plguin as bme280_plugin

i2c = busio.I2C(sda=board.GP0, scl=board.GP1, frequency=400000)
plugin = bme280_plugin(i2c, addr=0x76)
plugins = {
    'bme280_humidityrelative': plugin.humidityrelative(),
    'bme280_pressure': plugin.pressure(),
    'bme280_temp': plugin.temp(),
}
'''
from adafruit_bme280 import basic as adafruit_bme280


class Plugin:
    def __init__(self, i2c=None, bus=0, addr=0x76, category='weather', label='bme280'):
        self._i2c = i2c
        self._bus = bus
        self._addr = addr
        self._name = f'i2c_{bus}_{addr:02x}'
        self._category = category
        self._label = label
        self._bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=addr)

    def humidityrelative(self, label=None):
        label = self._label if not label else label
        return self.Humidity(self, label)

    def pressure(self, label=None):
        label = self._label if not label else label
        return self.Pressure(self, label)

    def temp(self, label=None):
        label = self._label if not label else label
        return self.Temp(self, label)

    class Humidity:
        def __init__(self, parent, label):
            self._parent = parent
            self._label = label

        def config(self, w):
            w.write(f'''\
graph_title Humidity
graph_args --lower-limit 0 --upper-limit 100
graph_vlabel %RH
graph_scale no
graph_category {self._parent._category}
{self._parent._name}.label {self._label}
''')

        def fetch(self, w):
            val = self._parent._bme280.relative_humidity
            w.write(f'{self._parent._name}.value {val}\n')

    class Pressure:
        def __init__(self, parent, label):
            self._parent = parent
            self._label = label

        def config(self, w):
            w.write(f'''\
graph_title Pressure
graph_args --lower-limit 900 --upper-limit 1050
graph_args_after --y-grid 10:5
graph_vlabel hPa
graph_scale no
graph_category {self._parent._category}
{self._parent._name}.label {self._label}
''')

        def fetch(self, w):
            val = self._parent._bme280.pressure
            w.write(f'{self._parent._name}.value {val}\n')

    class Temp:
        def __init__(self, parent, label):
            self._parent = parent
            self._label = label

        def config(self, w):
            w.write(f'''\
graph_title Temperature
graph_vlabel Celsius
graph_scale no
graph_category {self._parent._category}
{self._parent._name}.label {self._label}
''')

        def fetch(self, w):
            val = self._parent._bme280.temperature
            w.write(f'{self._parent._name}.value {val}\n')
