'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import numbers
import tables
import numpy as np
from .get_telescope_info import *
from .r1_utils import createBaseTelescopeGroupTable


def createDL0TableTel(hfile, telNode, nbGain, nbPixel, nbSlice, chunkshape=1):
	'''
	Create the waveform tables into the given telescope node
	Parameters:
		hfile : HDF5 file to be used
		telNode : telescope to be completed
		nbGain : number of gains of the camera
		nbPixel : number of pixels
		nbSlice : number of slices
		chunkshape : shape of the chunk to be used to store the data
	'''
	pixelLo = create_vlarray(camTelGroup, "pixelLo", tables.UInt16Atom(shape=()), "table of the index of the pixels which are in low gain mode",)
	pixelWaveform = create_vlarray(camTelGroup, "pixelWaveform", tables.UInt16Atom(shape=(nbSlice)), "table of the index of the pixels recorded with the waveform",)
	
	#TODO finish the work
	
	#columns_dict_waveform  = {"waveformHi": tables.UInt16Col(shape=image_shape)}
	#description_waveform = type('description columns_dict_waveform', (tables.IsDescription,), columns_dict_waveform)
	#hfile.create_table(telNode, 'waveformHi', description_waveform, "Table of waveform of the high gain signal", chunkshape=chunkshape)
	
	#if nbGain > 1:
		#columns_dict_waveformLo  = {"waveformLo": tables.UInt16Col(shape=image_shape)}
		#description_waveformLo = type('description columns_dict_waveformLo', (tables.IsDescription,), columns_dict_waveformLo)
		#hfile.create_table(telNode, 'waveformLo', description_waveformLo, "Table of waveform of the low gain signal", chunkshape=chunkshape)


def createDL0TelGroupAndTable(hfile, telId, telInfo, chunkshape=1):
	'''
	Create the telescope group and table
	It is important not to add an other dataset with the type of the camera to simplify the serach of a telescope by telescope index in the file structure
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telId : id of the telescope
		telInfo : table of some informations related to the telescope
		chunkshape : shape of the chunk to be used to store the data
	'''
	camTelGroup = createBaseTelescopeGroupTable(hfile, telId, telInfo, chunkshape=chunkshape)
	
	nbGain = np.uint64(telInfo[TELINFO_NBGAIN])
	nbPixel = np.uint64(telInfo[TELINFO_NBPIXEL])
	nbSlice = np.uint64(telInfo[TELINFO_NBSLICE])
	
	createDL0TableTel(hfile, camTelGroup, nbGain, nbPixel, nbSlice, chunkshape=chunkshape)




def createDL0Dataset(hfile, telInfo_from_evt):
	'''
	Create the dl0 dataset
	Parameters:
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
	'''
	#Group : dl0
	hfile.create_group("/", 'dl0', 'Raw data DL0 waveform and integrated signal informations of the run')
	
	#The group in the dl0 group will be completed on the fly with the informations collected in telInfo_from_evt
	for telId, telInfo in telInfo_from_evt.items():
		createDL0TelGroupAndTable(hfile, telId, telInfo)

