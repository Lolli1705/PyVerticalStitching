import numpy as np
import matplotlib.pyplot as plt
from skimage import io
from skimage import data
from skimage.registration import phase_cross_correlation
from skimage.transform import warp_polar, rotate, rescale, SimilarityTransform, warp
from skimage.util import img_as_float
import warnings
warnings.filterwarnings('ignore')
import os
from PyQt6.QtCore import QThread
import time

### Functions

# central cropping
def cropped(I1,cropped_rows_and_cols):
    rpos = np.max([0,int((I1.shape[0]-cropped_rows_and_cols)/2)])
    cpos = np.max([0,int((I1.shape[1]-cropped_rows_and_cols)/2)])
    I1=I1[rpos:rpos+cropped_rows_and_cols+1,cpos:cpos+cropped_rows_and_cols+1]
    return I1

# this calculated the image correlation coefficient as optimization criteria
def corr(I1,I2):
    mean1=np.average(I1)
    mean2=np.average(I2)
    I1=I1-mean1
    I2=I2-mean2
    _corr = np.sum(I1*I2)/np.sqrt(np.sum(I1*I1)*np.sum(I2*I2))
    print('correlation = ',mean1,' ',mean2,' ',_corr)
    return _corr

# list all filenames in a directory including the provided path
# results may not be sorted
def getListOfFiles(dirName):
    # create a list of file and sub directories 
    # names in the given directory 
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory 
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)
                
    return allFiles

# copies all images and applies rotation and cropping
# a global filenumber is used as counter


def export_files(filenames,start_slice,end_slice,num,export_dir,export_data_type,min_gval,max_gval):
    for i in range(start_slice,end_slice+1):
        
        I1 = np.array(io.imread(filenames[i]),dtype='float')
        
        if export_data_type==0:
            I1 = np.asarray((I1-min_gval)/(max_gval-min_gval)*255,dtype='uchar')
        if export_data_type==1:
            I1 = np.asarray((I1-min_gval)/(max_gval-min_gval)*65535,dtype='ushort')
        if export_data_type==2:
            I1 = np.asarray((I1-min_gval)/(max_gval-min_gval),dtype='single')*(max_gval-min_gval)+min_gval
        
        print('save ',filenames[i],' -> ',export_dir+'/slice_%04d' % num+'.tif')
        output = f'save: {filenames[i]} --> {export_dir}slice_%04d.tif'%num
        #output_list.append(output)
        io.imsave(export_dir+'/slice_%04d' % num+'.tif',I1)
        num+=1
    return num


# detects the rotation and correlation coefficient comparing one fixed image with a range of moving images
# the image number with the highest correlation coefficient and the resulting angle is reported
def detect_corr(I1,filenames_moving,overlap_range,cropped_rows_and_cols):
    res=np.zeros((overlap_range[1]-overlap_range[0]+1, 2))
    for i in range(overlap_range[0],overlap_range[1]+1):
        #print('analysing ',filenames_moving[i])
        I2 = cropped(np.array(io.imread(filenames_moving[i]),dtype='float'),cropped_rows_and_cols)
        #print('mean I2 ',np.average(I2))
        res[i-overlap_range[0],:]=corr(I1,I2)
    pos = np.argmax(res[:,0])
    slice_num = pos+overlap_range[0]    
    print('best guess ',slice_num,' corr = ',res[pos])   
    
    #validate
    I2 = cropped(np.array(io.imread(filenames_moving[pos]),dtype='float'),cropped_rows_and_cols)
   
    
    return [slice_num,res[pos]]


class MyThread(QThread):

    def __init__(self,start_slice,end_slice,input_path,output_path,dirnames, overlap_range,filenames,exported_data_type,filenames_fixed,max_gval, min_gval):

        QThread.__init__(self)

        self.start_slice=start_slice
        self.end_slice = end_slice
        self.input_path = input_path
        self.output_path = output_path
        self.dirnames=dirnames
        self.overlap_range=overlap_range
        self.filenames=filenames
        self.exported_data_type = exported_data_type
        self.filenames_fixed = filenames_fixed
        self.max_gval = max_gval
        self.min_gval = min_gval



        def export_files(filenames,start_slice,end_slice,num,output_path,export_data_type,output_list, max_gval, min_gval,):
            for i in range(start_slice,end_slice+1):
                
            
                
                if export_data_type==0:
                    I1 = np.asarray((I1-min_gval)/(max_gval-min_gval)*255,dtype='uchar')
                if export_data_type==1:
                    I1 = np.asarray((I1-min_gval)/(max_gval-min_gval)*65535,dtype='ushort')
                if export_data_type==2:
                    I1 = np.asarray((I1-min_gval)/(max_gval-min_gval),dtype='single')*(max_gval-min_gval)+min_gval
                
                #print('save ',filenames[i],' -> ',export_dir+'/slice_%04d' % num+'.tif')
                output = f'save: {filenames[i]} --> {output_path}slice_%04d.tif'%num
                output_list.append(output)
                #print(output)
                io.imsave(output_path+'/slice_%04d' % num+'.tif',I1)
                num+=1
                self.sleep(1)
            return num
                
                

        def run(self):

            num = 0
            total_list = []
            num = self.export_files(filenames_fixed,start_slice,end_slice,num,output_path,total_list)

            for i in range(1,len(dirnames)):
                #print(dirnames[i-1],'->',dirnames[i])
                
                
                filenames_moving=np.sort(getListOfFiles(input_path+dirnames[i]))
                I1 = np.array(io.imread(filenames_fixed[end_slice]),dtype='float')
                cropped_rows_and_cols = I1.shape[0]
                #detect overlap and rotation
                res = detect_corr(I1,filenames_moving,overlap_range,cropped_rows_and_cols)
                start_slice = res[0]+1;
                angle = res[1]+angle;
                print('resulting angle =',angle)
                if (i==len(dirnames)-1):
                    end_slice = len(filenames_moving)-1
                total_list.append('---------------------------------------------------------------------------------\n')
                num = self.export_files(filenames_moving,start_slice,end_slice,angle,0,0,num,output_path,total_list)
                
                
                #prepare for next round
                filenames_fixed = filenames_moving  

                        
                        