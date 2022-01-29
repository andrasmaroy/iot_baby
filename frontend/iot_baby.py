#! /usr/bin/env python3
import logging

from collections import deque
from pyqtgraph import plot, ViewBox
from pyqtgraph.Qt import QtCore, QtGui
from serial import Serial
from serial.serialutil import SerialException
from sys import argv, exit
from threading import Thread
from time import sleep


class App(QtGui.QMainWindow):
    def __init__(self, parent=None, max_length=200, data_sources=5):
        super(App, self).__init__(parent)

        self._data_sources = data_sources

        self._serial = Serial("/dev/ttyUSB0", 9600)
        while self._serial.in_waiting == 0:
            sleep(0.1)

        self._data_queues = []
        for _ in range(data_sources):
            self._data_queues.append(deque([0.0] * max_length, max_length))

        self._reader_thread = Thread(target=self._read)
        self._reader_thread.start()

        self._plot_widget = plot()
        self._plot_widget.setRange(
            xRange=(0, max_length), yRange=(0, 175), disableAutoRange=False
        )
        self._plot_widget.setLimits(yMin=0, yMax=175)
        self._plot_widget.enableAutoRange(axis=ViewBox.YAxis, enable=True)
        self._plot_widget.resize(720, 450)

        self._plots = []
        for color in ["b", "r", "g", "m", "y"]:
            self._plots.append(self._plot_widget.plot(pen=color))

        self._update()
        self._plot_widget.showFullScreen()

    def _add_data(self, data):
        for i, queue in enumerate(self._data_queues):
            queue.append(data[i])

    def _read(self):
        while True:
            try:
                line = self._serial.readline().decode("ascii").strip()
                data = [float(val.split(":")[1]) for val in line.split()]
                # print data
                if len(data) == self._data_sources:
                    self._add_data(data)
            except SerialException:
                logging.exception("SerialException trying to set different usb port...")
                if self._serial.port == "/dev/ttyUSB0":
                    self._serial.port = "/dev/ttyUSB1"
                else:
                    self._serial.port = "/dev/ttyUSB0"
            except UnicodeDecodeError:
                logging.exception(
                    "UnicodeDecodeError while reading from serial, continuing..."
                )
            except Exception:
                logging.exception("Exception while reading from serial, continuing...")

    def _update(self):
        for pair in zip(self._plots, self._data_queues):
            pair[0].setData(pair[1])
        QtCore.QTimer.singleShot(1, self._update)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        handlers=[logging.handlers.SysLogHandler("/dev/log")]
    )
    try:
        app = QtGui.QApplication(argv)
        App()
        exit(app.exec_())
    except Exception as e:
        logging.exception(e)
