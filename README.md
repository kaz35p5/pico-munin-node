# Pico Munin-node

## 目次


- [Pico Munin-node](#pico-munin-node)
  - [目次](#目次)
  - [概要](#概要)
  - [準備するもの](#準備するもの)
  - [Circuit Python の 書き込み](#circuit-python-の-書き込み)
  - [Pico Munin-node のインストール](#pico-munin-node-のインストール)
  - [Pico Munin-node の設定](#pico-munin-node-の設定)
  - [Plugin の登録](#plugin-の登録)
  - [Wish List](#wish-list)

## 概要

Pico W を Munin-node として動作させる Circuit Python 用スクリプトです。  
BME280を接続し、Muninで計測することを目的として作成しました。  

* mdnsサーバーを動作させているので、ホスト名.local でアクセス出来ます。
* Munin master が接続中は LED が点灯します。
* プラグイン方式（今のところ手動で追加/削除）

## 準備するもの

* Raspberry Pi Pico W
* [Circuit Python](https://circuitpython.org/) (Pico W 用 uf2ファイル)
* Circuit Python Bundles
* I2Cセンサー (BME280)

## Circuit Python の 書き込み

省略

## Pico Munin-node のインストール

1. Circuit Python Bundle から、lib/adafruit_bme280 ディレクトリを Pico W にコピーします。  
（使用するセンサーに対応するライブラリを入れます。）
2. bme280_plugin.py と code.py、 settings.toml の3ファイルを Pico W にコピーします。

ディレクトリ構成が以下のようになります。

    /
    ├─ lib/
    │  └─ adafruit_bme280/ 
    ├─ bme280_plugin.py
    ├─ code.py
    └─ settings.toml


## Pico Munin-node の設定

settings.toml にWi-Fiの SSID と パスワード、ホスト名を記載します。  

I2Cとして使うピンを code.py 内の I2Cインスタンス生成時に指定します。  
例えば、GPIO0とGPIO1を使う場合は、下記の様にします。
```
i2c = busio.I2C(sda=board.GP0, scl=board.GP1, frequency=400000)
```  


## Plugin の登録

有効にしたいプラグインのインスタンスを生成し、plugins に列挙します。

```
from bme280_plugin import Plguin as bme280_plugin

plugin = bme280_plugin(i2c, addr=0x76)
plugins = {
    'bme280_humidityrelative': plugin.humidityrelative(),
    'bme280_pressure': plugin.pressure(),
    'bme280_temp': plugin.temp(),
}
```

## Wish List

* plugins ディレクトリに入っている pluginスクリプトを自動で検出する。

