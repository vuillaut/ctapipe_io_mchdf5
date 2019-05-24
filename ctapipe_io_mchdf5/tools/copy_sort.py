'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import tables
import numpy as np

from .telescope_copy import copyTelescopeWithoutWaveform


def createSortedWaveformTable(hfile, camTelGroup, nameWaveformHi, nbSlice, nbPixel, isStoreSlicePixel, chunkshape=1):
	'''
	Create the table to store the signal
	Parameters:
		hfile : HDF5 file to be used
		camTelGroup : telescope group in which to put the tables
		nameWaveformHi : name of the table to store the waveform
		nbSlice : number of slices of the signal
		nbPixel : number of pixels of the camera
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	image_shape = (nbPixel, nbSlice)
	if isStoreSlicePixel:
		image_shape = (nbSlice, nbPixel)
	columns_dict_waveformHi  = {nameWaveformHi: tables.UInt16Col(shape=image_shape)}
	description_waveformHi = type('description columns_dict_waveformHi', (tables.IsDescription,), columns_dict_waveformHi)
	hfile.create_table(camTelGroup, nameWaveformHi, description_waveformHi, "Table of waveform of the signal", chunkshape=chunkshape)


def createTelescopeSorted(outFile, telNode, isStoreSlicePixel, chunkshape=1):
	'''
	Create the telescope group and table
	Parameters:
	-----------
		outFile : HDF5 file to be used
		telNode : telescope node to be copied
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	camTelGroup = copyTelescopeWithoutWaveform(outFile, telNode, chunkshape)
	
	nbPixel = np.uint64(telNode.nbPixel.read())
	nbSlice = np.uint64(telNode.nbSlice.read())
	
	createSortedWaveformTable(outFile, camTelGroup, "waveformHi", nbSlice, nbPixel, isStoreSlicePixel, chunkshape=chunkshape)
	nbGain = np.uint64(telNode.nbGain.read())
	if nbGain > 1:
		createSortedWaveformTable(outFile, camTelGroup, "waveformLo", nbSlice, nbPixel, isStoreSlicePixel, chunkshape=chunkshape)


def createAllTelescopeSorted(outFile, inFile, isStoreSlicePixel, chunkshape=1):
	'''
	Create all the telescope ready for pixels sorting
	Parameters:
	-----------
		outFile : output file
		inFile : input file
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	outFile.create_group("/", 'r1', 'Raw data waveform informations of the run')
	for telNode in inFile.walk_nodes("/r1", "Group"):
		try:
			createTelescopeSorted(outFile, telNode, isStoreSlicePixel, chunkshape=chunkshape)
		except tables.exceptions.NoSuchNodeError as e:
			pass







