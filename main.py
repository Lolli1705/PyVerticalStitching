import numpy as np
import matplotlib.pyplot as plt
from skimage import io
from skimage import data
from skimage.registration import phase_cross_correlation
from skimage.transform import warp_polar, rotate, rescale, SimilarityTransform, warp
from skimage.util import img_as_float
from worker import Worker
import warnings
warnings.filterwarnings('ignore')
import os
import time




from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QApplication, QFileDialog, QWidget, QMessageBox

from PyQt6.QtGui import QPixmap, QImage

from PyQt6.QtCore import QObject, QThread, pyqtSignal

import pyqtgraph as pg
from qimage2ndarray import gray2qimage


from Widget import Ui_PyVerticalStitching

from tool import getListOfFiles, cropped, corr, detect_corr, export_files




class MainWidget(QWidget, Ui_PyVerticalStitching):

    def __init__(self, parent=None):
        super(MainWidget, self).__init__(parent)
        self.setupUi(self)


        ## Parameters for the import

        #Input path

        self.input_path = ""
        self.output_path = ""
        self.end_slice = 0
        self.start_over = 0
        self.end_over = 0
        self.con_8 = False
        self.con_16 = True
        self.con_32 = False
        self.log = []
        self.save_log = False
        self.ready = False
        self.exported_data_type = 1
        self.num = 0
        self.max_gval = 0
        self.min_gval=0


        self.pbinput.clicked.connect(self.get_input)
        self.pboutput.clicked.connect(self.get_output)

        self.SBendslice.valueChanged.connect(self.get_value)
        self.SBoverstart.valueChanged.connect(self.get_value_start)
        self.SBoverend.valueChanged.connect(self.get_value_end)

        self.CB8.toggled.connect(self.con_type)
        self.CB16.toggled.connect(self.con_type)
        self.CB32.toggled.connect(self.con_type)

        self.CB16.setChecked(True)

        self.CBlogsave.toggled.connect(self.log_save)

        self.PBSet.clicked.connect(self.dis)
        self.PBCancel.clicked.connect(self.en)
        self.PBShow.clicked.connect(self.show_)
        self.PBRun.clicked.connect(self.run)


## FUNCTION

    def get_input(self):

        dialog = QFileDialog(self, caption="Select Input directory")
        dialog.setFileMode(QFileDialog.FileMode.Directory)

        dialog.exec()

        self.input_path = os.path.normpath(dialog.selectedFiles()[0])
        self.leinput.setText(self.input_path)
        self.input_path = self.input_path + "\\"
    
    
    def get_output(self):


        dialog = QFileDialog(self, caption="Select Output directory")
        dialog.setFileMode(QFileDialog.FileMode.Directory)

        dialog.exec()

        self.output_path = os.path.normpath(dialog.selectedFiles()[0])
        self.leoutput.setText(self.output_path)
        self.output_path = self.output_path + "\\"
    
    def get_value(self):

        self.end_slice = self.SBendslice.value()

    def get_value_start(self):

        self.start_over = self.SBoverstart.value()

    def get_value_end(self):

        self.end_over = self.SBoverend.value()

    def con_type(self):

        if self.CB16.isChecked():

            self.CB8.setDisabled(True)
            self.CB32.setDisabled(True)

            self.exported_data_type = 1
        
        elif self.CB8.isChecked():
    
            self.CB16.setDisabled(True)
            self.CB32.setDisabled(True)

            self.exported_data_type = 0

        elif self.CB32.isChecked():

            self.CB16.setDisabled(True)
            self.CB8.setDisabled(True)

            self.exported_data_type = 2
        
        else:
            self.CB8.setDisabled(False)
            self.CB32.setDisabled(False)
            self.CB16.setDisabled(False)
        

    def log_save(self):

        if self.CBlogsave.isChecked():

            self.save_log = True

        else:

            self.save_log = False

        
        
    
    def dis(self):
        
        self.SBendslice.setDisabled(True)
        self.SBoverstart.setDisabled(True)
        self.SBoverend.setDisabled(True)
        self.CB8.setDisabled(True)
        self.CB32.setDisabled(True)
        self.CB16.setDisabled(True)
        self.CBlogsave.setDisabled(True)

        self.ready=True

    def en(self):

        self.SBendslice.setDisabled(False)
        self.SBoverstart.setDisabled(False)
        self.SBoverend.setDisabled(False)
        if self.CB16.isChecked():

            self.CB8.setDisabled(True)
            self.CB32.setDisabled(True)
            self.CB16.setDisabled(False)
            self.con_16 = True
            #self.exported_data_type = 1
            
        elif self.CB8.isChecked():
    
            self.CB16.setDisabled(True)
            self.CB32.setDisabled(True)
            self.CB8.setDisabled(False)
            #self.exported_data_type = 0
            #print(self.exported_data_type)

            

        elif self.CB32.isChecked():

            self.CB16.setDisabled(True)
            self.CB8.setDisabled(True)
            self.CB32.setDisabled(False)
            #self.exported_data_type = 2
            #print(self.exported_data_type)

            #self.con_32 = True
        
        else:
            self.CB8.setDisabled(False)
            self.CB32.setDisabled(False)
            self.CB16.setDisabled(False)
            #print(self.exported_data_type)
        self.CBlogsave.setDisabled(False)
        self.ready=False

    def show_(self):
        
        dirnames=np.sort(os.listdir(self.input_path))[::-1]
        filenames_fixed=np.sort(getListOfFiles(self.input_path+dirnames[0]))
        filenames_float=np.sort(getListOfFiles(self.input_path+dirnames[1]))
        overlap_range = [self.start_over,self.end_over]

        I1 = np.array(io.imread(filenames_fixed[self.end_slice]))
        I2 = np.array(io.imread(filenames_float[overlap_range[0]]))
        I3 = np.array(io.imread(filenames_float[overlap_range[1]]))

        self.TElog.append(f"Reference slice:{self.end_slice}, Check range {self.start_over}-{self.end_over}\n")

        qI1 = QImage(gray2qimage(I1, normalize=True))
        qI2 = QImage(gray2qimage(I2, normalize=True))
        qI3 = QImage(gray2qimage(I3, normalize=True))


        self.QLRef.setScaledContents(True)
        self.QLRef.setPixmap(QPixmap.fromImage(qI1))

        self.QLStart.setScaledContents(True)
        self.QLStart.setPixmap(QPixmap.fromImage(qI2))

        self.QLEnd.setScaledContents(True)
        self.QLEnd.setPixmap(QPixmap.fromImage(qI3))


    def run(self):
            
            if self.ready:
            

                self.TElog.append("Stitching procedure started...\n")
                self.TElog.append("*"*50)
                self.TElog.append("Starting calculation of max_gval and min_gval..\n")
                if self.exported_data_type == 0:
                    self.TElog.append(f"Conversion set to 8-bit\n")
                elif self.exported_data_type==1:
                    self.TElog.append(f"Conversion set to 16-bit\n")
                else:
                    self.TElog.append(f"Conversion set to 32-bit\n")
                
                if self.save_log:
                    self.TElog.append(f"Saving log file --> {self.output_path}output.txt\n")
                
                ## Calculation of Max and Min

                self.worker = Worker(self.input_path,self.output_path,self.end_slice,
                                     self.start_over,
                                     self.end_over,
                                     self.exported_data_type,
                                     self.save_log)
                self.worker.start()
            
                self.worker.max_val.connect(self.max_value)
                self.worker.min_val.connect(self.min_value)
                self.worker.updates.connect(self.update_msg)
                self.worker.log_files.connect(self.log_)

                
                
                
            
            else:

                QMessageBox.warning(self,"Not ready to start", "Please select the set button")

              

    
    def max_value(self,val):
            
            self.max_gval = val
            #print(f'Max val is {val}')
            self.TElog.append(f'max_gval = {self.max_gval}') 

    
    def min_value(self,val):
            
            self.min_gval = val
            #print(f'Min val is {val}')
            self.TElog.append(f'min_gval = {self.min_gval}')
    
    def counter_dir(self,val):

        self.TElog.append(f"{val}")

    def update_msg(self,value):

        self.TElog.append(value)
    
    def log_(self,val):

        self.TElog.append(val)
        self.log.append(val)



       
app = QApplication([])
window = MainWidget()
window.show()
app.exec()