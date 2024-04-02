'''
Raspberry Pi Pico W
pico-munin-node for CircuitPython

'''
import os
import io
import microcontroller
import time

from errno import EAGAIN, ECONNRESET, ETIMEDOUT
import socketpool
import wifi
import ipaddress
import mdns

import digitalio
import board
import busio

# pico-munin-node version
version = '0.0.1'

# plugins
from bme280_plugin import Plguin as bme280_plugin

# i2c = busio.I2C(sda=board.GP0, scl=board.GP1, frequency=400000)
i2c = busio.I2C(sda=board.GP14, scl=board.GP15, frequency=400000)
plugin = bme280_plugin(i2c, addr=0x76)
plugins = {
    'bme280_humidityrelative': plugin.humidityrelative(),
    'bme280_pressure': plugin.pressure(),
    'bme280_temp': plugin.temp(),
}

# LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT


class ReadWriter:
    def __init__(self, sock):
        self.sock = sock
        self.buffer = b''
        self.rbuffer = bytearray(256)

    def ReadLine(self):
        while b'\n' not in self.buffer:
            try:
                length = self.sock.recv_into(self.rbuffer, len(self.rbuffer))
                if length == 0:
                    return None
                self.buffer += self.rbuffer[:length]
            except OSError as ex:
                if ex.errno == ECONNRESET:
                    return None
                if ex.errno == ETIMEDOUT:
                    return None
                raise
            except Exception as ex:
                raise ex

        line, _, self.buffer = self.buffer.partition(b'\n')
        return line.decode()

    def Write(self, str):
        buffer = str.encode('utf-8')
        bytes_sent: int = 0
        bytes_to_send = len(buffer)
        view = memoryview(buffer)
        while bytes_sent < bytes_to_send:
            try:
                bytes_sent += self.sock.send(view[bytes_sent:])
            except OSError as ex:
                if ex.errno == EAGAIN:
                    continue
                if ex.errno == ECONNRESET:
                    return
                raise


# Wi-Fi接続を実行
ssid = os.getenv('CIRCUITPY_WIFI_SSID')
password = os.getenv('CIRCUITPY_WIFI_PASSWORD')
hostname = os.getenv('HOSTNAME')

print(f'Hostname: {hostname}')

while True:
    try:
        print('Connecting Wi-Fi...')
        wifi.radio.connect(ssid, password)
        break
    except Exception as e:
        print('Failed to connect.')
        print('Error:\n', str(e))
        time.sleep(5)
        microcontroller.reset()

print('Connected to', ssid)

HOST = str(wifi.radio.ipv4_address)
PORT = 4949
TIMEOUT = 10
MAXBUF = 256

mdns_server = mdns.Server(wifi.radio)
mdns_server.hostname = hostname
mdns_server.advertise_service(service_type='_munin', protocol='_tcp', port=PORT)

pool = socketpool.SocketPool(wifi.radio)

print("Create TCP Server socket", (HOST, PORT))
s = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
s.settimeout(None)

s.bind((HOST, PORT))
s.listen(2)
print('Listening')

cap = {
    'multigraph': False,
    'dirtyconfig': True,
}

while True:
    print('Accepting connections\n')
    conn, addr = s.accept()

    conn.settimeout(TIMEOUT)
    print('Accepted from', addr)
    led.value = True
    rw = ReadWriter(conn)

    rw.Write(f'# munin node at {hostname}\n')

    ena = {
        'multigraph': False,
        'dirtyconfig': False,
    }

    while True:
        line = rw.ReadLine()
        if line is None:
            break

        print('Received', line)

        args = line.split()
        cmd = arg = ''
        if len(args) >= 1:
            cmd = args[0]
        if len(args) >= 2:
            arg = args[1]

        if cmd == '.':
            break
        elif cmd == 'quit':
            break
        elif cmd == 'version':
            rw.Write(f'pico-munin node on {hostname} version: {version}\n')
        elif cmd == 'nodes':
            rw.Write(hostname + '\n')
            rw.Write('.\n')
        elif cmd == 'cap':
            for c in args[1:]:
                if c in cap:
                    ena[c] = True
                    print('Enable', c)
            rw.Write('cap dirtyconfig\n')
        elif cmd == 'list':
            if arg == '' or arg == hostname:
                rw.Write(' '.join(plugins.keys()))
            rw.Write('\n')
        elif cmd == 'config':
            if arg in plugins:
                with io.StringIO() as out:
                    plugins[arg].config(out)
                    plugins[arg].fetch(out) if ena['dirtyconfig'] else None
                    rw.Write(out.getvalue())
            else:
                rw.Write('# Unknown service\n')
            rw.Write('.\n')

        elif cmd == 'fetch':
            if arg in plugins:
                with io.StringIO() as out:
                    plugins[arg].fetch(out)
                    rw.Write(out.getvalue())
            else:
                rw.Write('# Unknown service\n')
            rw.Write('.\n')
        else:
            rw.Write('# Unknown command. Try cap, list, nodes, config, fetch, version or quit\n')

    led.value = False
    conn.close()
    print('Disconnected:', addr)
