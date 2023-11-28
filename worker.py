import os 
import numpy as np
from skimage import io
import time

from PyQt6.QtCore import QThread, pyqtSignal
from tool import getListOfFiles, export_files, cropped, detect_corr

class Worker(QThread):

    def __init__(self,input_path,output_path,
                 end_slice,
                 start_over,
                 end_over,
                 exported_data_type,
                 save_log,
                 parent=None):
        super(QThread, self).__init__()
        # Input needed
        self.input_path = input_path
        self.output_path = output_path
        self.end_slice = end_slice
        self.start_over = start_over
        self.end_over = end_over
        self.exported_data_type = exported_data_type
        self.save_log = save_log


    # Signals

    max_val = pyqtSignal(float)
    min_val = pyqtSignal(float)
    updates = pyqtSignal(str)
    log_files = pyqtSignal(str)


    def run(self):
 
        log_file_list = []
        max_gval=-1000000
        min_gval=1000000

        dirnames = np.sort(os.listdir(self.input_path))

        for i in range(0,len(dirnames)):

            if '' in dirnames[i]:

                message = f"Start: {dirnames[i]}"
                self.updates.emit(message) # To have the dir name

                filenames = np.sort(getListOfFiles(self.input_path+dirnames[i]))

                for j in range(0,len(filenames),1):

                    I = np.array(io.imread(filenames[j]),dtype='float')

                    max_gval = np.max([max_gval, np.max(I)])
                    min_gval = np.min([min_gval,np.min(I)])
                #self.updates.emit(f"End: {dirnames[i]}\n")
        
        
        # To catch the max and min values
        #self.updates.emit("\n")
        self.updates.emit("*"*50)
        self.updates.emit("Max and Min calculation finished\n")
        self.max_val.emit(max_gval)
        self.min_val.emit(min_gval)
        self.updates.emit("*"*50)
        #self.updates.emit(f"Save log {self.save_log}")
        # Starting the stitching

        start_slice = 0
        num = 0

        dirnames_ = np.sort(os.listdir(self.input_path))[::-1]
        filenames_fixed = np.sort(getListOfFiles(self.input_path+dirnames_[0]))

        I = np.array(io.imread(filenames_fixed[self.end_slice]),dtype='float')

        cropped_row_and_cols = I.shape[0]-120

        self.updates.emit(f"Cropping to {cropped_row_and_cols}")

        # Start copying the first step

        

        for i in range(start_slice,self.end_slice+1):

            I1 = cropped(np.array(io.imread(filenames_fixed[i]),dtype='float'),cropped_rows_and_cols=cropped_row_and_cols)

            if self.exported_data_type==0:
                I1 = np.asarray((I1-min_gval)/(max_gval-min_gval)*255,dtype=np.uint8)
            if self.exported_data_type==1:
                I1 = np.asarray((I1-min_gval)/(max_gval-min_gval)*65535,dtype='ushort')
            if self.exported_data_type==2:
                I1 = np.asarray((I1-min_gval)/(max_gval-min_gval),dtype='single')*(max_gval-min_gval)+min_gval

            output = f"save: {filenames_fixed[i]} --> {self.output_path}slice_%04d.tif"%num
            log_file_list.append(output)
            self.log_files.emit(output)
            self.updates.emit(output)
            io.imsave(self.output_path+'/slice_%04d' %num +'.tif', I1)
            num = num + 1
        overlap_range = [self.start_over, self.end_over]
        for i in range(1, len(dirnames_)):

            filenames_moving = np.sort(getListOfFiles(self.input_path+dirnames_[i]))
            #time.sleep(2)
            #self.updates.emit(f"{filenames_fixed[self.end_slice]}")

            I2 = cropped(np.array(io.imread(filenames_fixed[self.end_slice]),dtype='float'),cropped_rows_and_cols=cropped_row_and_cols)
            self.updates.emit("-"*50)
            self.updates.emit("Start calculating correlation...")
            res = detect_corr(I2, filenames_moving,overlap_range, cropped_row_and_cols)
            self.updates.emit(f"Best guest slice: {res[0]} correlation: {res[1]}")
            self.updates.emit("-"*50)
            start_slice = res[0]+1

            if(i==len(dirnames_)-1):

                self.end_slice = len(filenames_moving)-1

            for j in range(start_slice,self.end_slice+1):

                I1 = cropped(np.array(io.imread(filenames_moving[j]),dtype='float'),cropped_rows_and_cols=cropped_row_and_cols)

                if self.exported_data_type==0:
                    I1 = np.asarray((I1-min_gval)/(max_gval-min_gval)*255,dtype=np.uint8)
                if self.exported_data_type==1:
                    I1 = np.asarray((I1-min_gval)/(max_gval-min_gval)*65535,dtype='ushort')
                if self.exported_data_type==2:
                    I1 = np.asarray((I1-min_gval)/(max_gval-min_gval),dtype='single')*(max_gval-min_gval)+min_gval

                output = f"save: {filenames_moving[j]} --> {self.output_path}slice_%04d.tif"%num
                log_file_list.append(output)
                self.log_files.emit(output)
                self.updates.emit(output)
                io.imsave(self.output_path+'/slice_%04d' %num +'.tif', I1)
                num = num + 1
            #self.updates.emit("I am here")
            #time.sleep(2)
            filenames_fixed = filenames_moving
        self.updates.emit("-"*50)
        if self.save_log:
            output_txt_path = self.output_path+'output.txt'
            f=open(f'{output_txt_path}', 'a')

            for item in log_file_list:

                f.writelines(item+"\n")
            f.close()
            self.updates.emit("\nLog file saved...\n")
        self.updates.emit("Stitching Done !")



        







        


        

        
        

        