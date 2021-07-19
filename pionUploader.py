#!/usr/bin/env python
import re
import sys
from time import sleep

import serial

import pionUploader_esptool as esptool
import json

from datetime import datetime

from PyQt5.QtCore import QUrl, Qt, QThread, QObject, pyqtSignal, pyqtSlot, QSettings, QTimer, QSize, QIODevice
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPort
from PyQt5.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QComboBox, QWidget, QCheckBox, QRadioButton, \
    QButtonGroup, QFileDialog, QProgressBar, QLabel, QMessageBox, QDialogButtonBox, QGroupBox, QFormLayout, QStatusBar

import banner
import firmwareURL

from gui import HLayout, VLayout, GroupBoxH, GroupBoxV, SpinBox, dark_palette
from utils import NoBinFile, NetworkError

__version__ = '1.0.0'

class ESPWorker(QObject):
    error = pyqtSignal(Exception)
    waiting = pyqtSignal()
    done = pyqtSignal()

    def __init__(self, port, actions, **params):
        super().__init__()
        self.command = [
                      '--chip', 'esp32',
                      '--port', port,
                      '--baud', '921600'
            ]

        self._actions = actions
        self._params = params
        self._continue = False

    @pyqtSlot()
    def run(self):
        esptool.sw.setContinueFlag(True)

        try:
            if esptool.sw.continueFlag() and 'write' in self._actions:
                file_path = self._params['file_path']
                file_pathBoot = self._params['file_pathBoot']
                file_pathBootloader = self._params['file_pathBootloader']
                file_pathPart = self._params['file_pathPart']
                command_write = ['--before','default_reset','--after','hard_reset','write_flash','-z','--flash_mode','dio','--flash_freq','40m','--flash_size','detect','0xe000',file_pathBoot,'0x1000',file_pathBootloader,'0x10000',file_path ,'0x8000', file_pathPart]
                if 'erase' in self._actions:
                    command_write.append('--erase-all')
                esptool.main(self.command + command_write)

        except (esptool.FatalError) as e:
            self.error.emit(e)
        self.done.emit()

    def wait_for_user(self):
        self._continue = False
        self.waiting.emit()
        while not self._continue:
            sleep(.1)

    def continue_ok(self):
        self._continue = True

    def abort(self):
        esptool.sw.setContinueFlag(False)

class ProcessDialog(QDialog):
    def __init__(self, port, **kwargs):
        super().__init__()

        self.setWindowTitle('Preparando seu Satélite Educacional...')
        self.setFixedWidth(600)

        self.exception = None

        esptool.sw.progress.connect(self.update_progress)

        self.nam = QNetworkAccessManager()
        
        self.nrDownloads = 0

        self.nrBinFile1 = QNetworkRequest()
        self.bin_data1 = b''
        
        self.nrBinFile2 = QNetworkRequest()
        self.bin_data2 = b''

        self.nrBinFile3 = QNetworkRequest()
        self.bin_data3 = b''

        self.nrBinFile4 = QNetworkRequest()
        self.bin_data4 = b''

        self.setLayout(VLayout(5, 5))
        self.actions_layout = QFormLayout()
        self.actions_layout.setSpacing(5)

        self.layout().addLayout(self.actions_layout)

        self._actions = []
        self._action_widgets = {}

        self.port = port

        self.file_path = kwargs.get('file_url')
        self.file_pathBoot = kwargs.get('file_urlBoot')
        self.file_pathBootloader = kwargs.get('file_urlBootloader')
        self.file_pathPart = kwargs.get('file_urlPart')
        
        self._actions.append('download')
        
        self.erase = kwargs.get('erase')
        if self.erase:
            self._actions.append('erase')

        if self.file_path:
            self._actions.append('write')

        self.create_ui()
        self.start_process()

    def create_ui(self):
        for action in self._actions:
            pb = QProgressBar()
            pb.setFixedHeight(35)
            self._action_widgets[action] = pb
            self.actions_layout.addRow(action.capitalize(), pb)

        self.btns = QDialogButtonBox(QDialogButtonBox.Abort)
        self.btns.rejected.connect(self.abort)
        self.layout().addWidget(self.btns)

        self.sb = QStatusBar()
        self.layout().addWidget(self.sb)

    def appendBinFile1(self):
        self.bin_data1 += self.bin_reply1.readAll()
    
    def appendBinFile2(self):
        self.bin_data2 += self.bin_reply2.readAll()
    
    def appendBinFile3(self):
        self.bin_data3 += self.bin_reply3.readAll()
    
    def appendBinFile4(self):
        self.bin_data4 += self.bin_reply4.readAll()
    
    def downloadsFinished(self):
        if self.nrDownloads == 4:
            self.run_esp()

    def saveBinFile1(self):
        if self.bin_reply1.error() == QNetworkReply.NoError:
            self.file_path = self.file_path.split('/')[-1]
            with open(self.file_path, 'wb') as f:
                f.write(self.bin_data1)
            self.nrDownloads += 1
            self.downloadsFinished()
        else:
            raise NetworkError

    def saveBinFile2(self):
        if self.bin_reply2.error() == QNetworkReply.NoError:
            self.file_pathBoot = self.file_pathBoot.split('/')[-1]
            with open(self.file_pathBoot, 'wb') as f:
                f.write(self.bin_data2)
            self.nrDownloads += 1
            self.downloadsFinished()
        else:
            raise NetworkError

    def saveBinFile3(self):
        if self.bin_reply3.error() == QNetworkReply.NoError:
            self.file_pathBootloader = self.file_pathBootloader.split('/')[-1]
            with open(self.file_pathBootloader, 'wb') as f:
                f.write(self.bin_data3)
            self.nrDownloads += 1
            self.downloadsFinished()
        else:
            raise NetworkError

    def saveBinFile4(self):
        if self.bin_reply4.error() == QNetworkReply.NoError:
            self.file_pathPart = self.file_pathPart.split('/')[-1]
            with open(self.file_pathPart, 'wb') as f:
                f.write(self.bin_data4)
            self.nrDownloads += 1
            self.downloadsFinished()
        else:
            raise NetworkError

    def updateBinProgress(self, recv, total):
        self._action_widgets['download'].setValue(recv//total*100)

    def download_bin(self):
        self.nrBinFile1.setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)
        self.nrBinFile1.setUrl(QUrl(self.file_path))
        self.bin_reply1 = self.nam.get(self.nrBinFile1)
        self.bin_reply1.readyRead.connect(self.appendBinFile1)
        self.bin_reply1.downloadProgress.connect(self.updateBinProgress)
        self.bin_reply1.finished.connect(self.saveBinFile1)

        self.nrBinFile2.setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)
        self.nrBinFile2.setUrl(QUrl(self.file_pathBoot))
        self.bin_reply2 = self.nam.get(self.nrBinFile2)
        self.bin_reply2.readyRead.connect(self.appendBinFile2)
        self.bin_reply2.finished.connect(self.saveBinFile2)
        
        self.nrBinFile3.setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)
        self.nrBinFile3.setUrl(QUrl(self.file_pathBootloader))
        self.bin_reply3 = self.nam.get(self.nrBinFile3)
        self.bin_reply3.readyRead.connect(self.appendBinFile3)
        self.bin_reply3.finished.connect(self.saveBinFile3)

        self.nrBinFile4.setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)
        self.nrBinFile4.setUrl(QUrl(self.file_pathPart))
        self.bin_reply4 = self.nam.get(self.nrBinFile4)
        self.bin_reply4.readyRead.connect(self.appendBinFile4)
        self.bin_reply4.finished.connect(self.saveBinFile4)

    def show_connection_state(self, state):
        self.sb.showMessage(state, 0)

    def run_esp(self):
        params = {
            'file_path': self.file_path,
            'file_pathBoot': self.file_pathBoot,
            'file_pathBootloader': self.file_pathBootloader,
            'file_pathPart': self.file_pathPart,
            'erase': self.erase
        }

        self.esp_thread = QThread()
        self.esp = ESPWorker(
            self.port,
            self._actions,
            **params
        )
        esptool.sw.connection_state.connect(self.show_connection_state)
        self.esp.done.connect(self.accept)
        self.esp.error.connect(self.error)
        self.esp.moveToThread(self.esp_thread)
        self.esp_thread.started.connect(self.esp.run)
        self.esp_thread.start()

    def start_process(self):
        if 'download' in self._actions:
            self.download_bin()
            self._actions = self._actions[1:]
        else:
            self.run_esp()

    def update_progress(self, action, value):
        self._action_widgets[action].setValue(value)

    @pyqtSlot()

    def stop_thread(self):
        self.esp_thread.wait(2000)
        self.esp_thread.exit()

    def accept(self):
        self.stop_thread()
        self.done(QDialog.Accepted)

    def abort(self):
        self.sb.showMessage('Aborting...', 0)
        QApplication.processEvents()
        self.esp.abort()
        self.stop_thread()
        self.reject()

    def error(self, e):
        self.exception = e
        self.abort()

    def closeEvent(self, e):
        self.stop_thread()

class Tasmotizer(QDialog):

    def __init__(self):
        super().__init__()
        self.settings = QSettings('tasmotizer.cfg', QSettings.IniFormat)

        self.port = ''

        self.nam = QNetworkAccessManager()

        self.esp_thread = None

        self.setWindowTitle(f'PION Kits Educacionais {__version__}')
        self.setMinimumWidth(480)

        self.mode = 0  # BIN file
        self.file_path = ''

        self.create_ui()

        self.refreshPorts()

    def create_ui(self):
        vl = VLayout(3)
        self.setLayout(vl)

        # Banner
        banner = QLabel()
        banner.setPixmap(QPixmap(':/banner.png'))
        vl.addWidget(banner)

        # Port groupbox
        gbPort = GroupBoxH('Selecionar porta', 3)
        self.cbxPort = QComboBox()
        pbRefreshPorts = QPushButton('Atualizar')
        gbPort.addWidget(self.cbxPort)
        gbPort.addWidget(pbRefreshPorts)
        gbPort.layout().setStretch(0, 4)
        gbPort.layout().setStretch(1, 1)

        # Buttons
        self.flash = QPushButton('Gravar firmware!')
        self.flash.setFixedHeight(60)
        self.flash.setStyleSheet('background-color: #0D2556;')

        hl_btns = HLayout([50, 3, 50, 3])
        hl_btns.addWidgets([self.flash])

        vl.addWidgets([gbPort])
        vl.addLayout(hl_btns)

        pbRefreshPorts.clicked.connect(self.refreshPorts)
        self.flash.clicked.connect(self.start_process)

    def refreshPorts(self):
        self.cbxPort.clear()
        ports = reversed(sorted(port.portName() for port in QSerialPortInfo.availablePorts()))
        for p in ports:
            port = QSerialPortInfo(p)
            self.cbxPort.addItem(port.portName(), port.systemLocation())

    def start_process(self):
        try:
            if self.mode == 0:
                self.file_url = firmwareURL.URL+firmwareURL.FIRMWARE
                self.file_urlBoot = firmwareURL.URL+firmwareURL.BOOT
                self.file_urlBootloader = firmwareURL.URL+firmwareURL.BOOTLOADER
                self.file_urlPart = firmwareURL.URL+firmwareURL.PARTITIONS

            process_dlg = ProcessDialog(
                self.cbxPort.currentData(),
                file_url=self.file_url,
                file_urlBoot=self.file_urlBoot,
                file_urlBootloader=self.file_urlBootloader,
                file_urlPart=self.file_urlPart,
                backup=False,
                backup_size=0,
                erase=True,
                auto_reset=True
            )
            result = process_dlg.exec_()
            if result == QDialog.Accepted:
                message = 'Programado com Sucesso! \n\nSeu kit está sendo reiniciado, isso pode levar algum tempo.'
                QMessageBox.information(self, 'OK', message)
            elif result == QDialog.Rejected:
                if process_dlg.exception:
                    QMessageBox.critical(self, 'Error', str(process_dlg.exception))
                else:
                    QMessageBox.critical(self, 'Processo Cancelado', 'O processo foi cancelado pelo usuário')
            
        except NetworkError as e:
            QMessageBox.critical(self, 'Erro de rede', e.message)


def main():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    app.setQuitOnLastWindowClosed(True)
    app.setStyle('Fusion')
    app.setPalette(dark_palette)
    app.setStyleSheet('QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }')

    mw = Tasmotizer()
    mw.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
