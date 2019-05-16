
# coding: utf-8

import tables
import numpy as np
from tables import open_file
from ctapipe.io import event_source
import argparse

from .camera_tel_type import getCameraTypeFromName, getCameraNameFromType, getTelescopeTypeStrFromCameraType
from .get_telescope_info import *
from .simulation_utils import *
from .get_nb_tel import getNbTel
from .instrument_utils import *
from .r1_utils import *


def createFileStructure(hfile, telInfo_from_evt):
	'''
	Create the structure of the HDF5 file
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
	Return:
	-------
		table of mc_event
	'''
	createR1Dataset(hfile, telInfo_from_evt)
	createInstrumentDataset(hfile, telInfo_from_evt)
	tableMcEvent = createSimiulationDataset(hfile)
	return tableMcEvent


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help="simtel r1 input file",
						required=True)
	parser.add_argument('-o', '--output', help="hdf5 r1 output file",
						required=True)
	parser.add_argument('-m', '--max_event', help="maximum event to reconstuct",
						required=False, type=int)
	args = parser.parse_args()

	inputFileName = args.input
	nbTel = getNbTel(inputFileName)
	print("Number of telescope : ",nbTel)
	
	#Increase the number of nodes in cache if necessary (avoid warning about nodes reopening)
	tables.parameters.NODE_CACHE_SLOTS = max(tables.parameters.NODE_CACHE_SLOTS, 3*nbTel + 20)
	
	telInfo_from_evt = getTelescopeInfoFromEvent(inputFileName, nbTel)
	
	#zstdFilter = tables.Filters(complevel=6, complib='blosc:zstd', shuffle=False, bitshuffle=False, fletcher32=False)
	hfile = tables.open_file(args.output, mode = "w"
			  #, filters=zstdFilter
			  )
	hfile.title = "R1-V2"
	
	print('Create file structure')
	tableMcCorsikaEvent = createFileStructure(hfile, telInfo_from_evt)
	
	print('Fill the subarray layout informations')
	fillSubarrayLayout(hfile, telInfo_from_evt)
	
	isSimulationMode = checkIsSimulationFile(telInfo_from_evt)
	
	if isSimulationMode:
		print('Fill the optic description of the telescopes')
		fillOpticDescription(hfile, telInfo_from_evt)
		
		print('Fill the simulation header informations')
		fillSimulationHeaderInfo(hfile, inputFileName)
	
	source = event_source(inputFileName)
	
	nb_event = 0
	max_event = 10000000
	if args.max_event != None:
		max_event = int(args.max_event)
	print("\n")
	for event in source:
		if isSimulationMode:
			appendCorsikaEvent(tableMcCorsikaEvent, event)
		appendEventTelescopeData(hfile, event)
		nb_event+=1
		print("\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r{} / {}".format(nb_event, max_event), end="")
		if nb_event >= max_event:
			break
	if isSimulationMode:
		tableMcCorsikaEvent.flush()
		
	hfile.close()
	print('\nDone')


if __name__ == '__main__':
	main()

