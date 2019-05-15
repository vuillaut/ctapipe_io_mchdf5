
# coding: utf-8

import tables
import numbers
import numpy as np
from tables import open_file
from ctapipe.io import event_source
import argparse

from .camera_tel_type import getCameraTypeFromName, getCameraNameFromType, getTelescopeTypeStrFromCameraType
from .get_telescope_info import *
from .simulation_utils import *
from .get_nb_tel import getNbTel

class SubarrayLayout(tables.IsDescription):
	'''
	Layout of the subarray
	Attributes:
		tel_id : id of the telescope
		pos_x : position of the telescope on the X axix (in meters to the north)
		pos_y : position of the telescope on the Y axix (in meters to the west)
		pos_z : high of the telescope in meters
		name : name of the telescope
		type : type of the telescope
		type_id : type of the telscope in unsigned long (to speed up the access for specific analysis)
		num_mirrors : number of mirror of the telescope
		camera_type : type of the telescope camera
		tel_description : description of the telescope
	'''
	tel_id = tables.UInt64Col()
	pos_x = tables.Float32Col()
	pos_y = tables.Float32Col()
	pos_z = tables.Float32Col()
	name = tables.StringCol(5, dflt=b'')
	type = tables.StringCol(3, dflt=b'')
	type_id = tables.UInt64Col()
	num_mirrors = tables.UInt64Col()
	camera_type = tables.StringCol(9, dflt=b'')
	tel_description = tables.StringCol(14, dflt=b'')


def fillSubarrayLayout(hfile, telInfo_from_evt):
	'''
	Fill the subarray informations
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
	'''
	tableSubarrayLayout = hfile.root.instrument.subarray.layout
	tabSubLayout = tableSubarrayLayout.row
	for telIndex, (telId, telInfo) in enumerate(telInfo_from_evt.items()):
		telType = telInfo[TELINFO_TELTYPE]
		camName = getCameraNameFromType(telType)
		telTypeStr = getTelescopeTypeStrFromCameraType(telType)
		
		tabSubLayout["tel_id"] = np.uint64(telId)
		tabSubLayout["pos_x"] = np.float32(telInfo[TELINFO_TELPOSX])
		tabSubLayout["pos_y"] = np.float32(telInfo[TELINFO_TELPOSY])
		tabSubLayout["pos_z"] = np.float32(telInfo[TELINFO_TELPOSZ])
		tabSubLayout["name"] = camName
		tabSubLayout["type"] = telTypeStr
		tabSubLayout["type_id"] = np.uint64(telType)
		
		tabSubLayout["num_mirrors"] = np.uint64(telInfo[TELINFO_NBMIRROR])
		tabSubLayout["camera_type"] = camName + "Cam"
		tabSubLayout["tel_description"] = "Description"
		


class CameraPixel(tables.IsDescription):
	'''
	Desctibes the pixels of a camera
	Attributes:
		pix_id : id of the pixel
		pix_x : position of the pixel on x
		pix_y : position of the pixel on y
		pix_area : area of the pixel (in meter square)
	'''
	pix_id = tables.UInt64Col()
	pix_x = tables.Float32Col()
	pix_y = tables.Float32Col()
	pix_area = tables.Float32Col()


def createCameraTable(hfile, parentGroup, tableName):
	'''
	Create a table to describe a camera
	Parameters:
	-----------
		hfile : HDF5 file to be used
		parentGroup : parent group of the table to be created
		tableName : name of the table to be created
	Return:
	-------
		created table
	'''
	table = hfile.create_table(parentGroup, tableName, ThrowEventDistribution, "Distribution of the "+tableName+" camera")
	return table


class OpticDescription(tables.IsDescription):
	'''
	Describe the optic of the all the telescopes
	Attributes:
	-----------
		description : description of the telescope optic (one mirror, two, etc)
		name : name of the optic
		type : type of the optic
		mirror_area : area of the mirror in meters square
		num_mirror_tiles : number of mirrors tiles
		equivalent_focal_length : equivalent focal lenght of the mirror in meters
	'''
	description = tables.StringCol(14, dflt=b'')
	name = tables.StringCol(5, dflt=b'')
	type = tables.StringCol(3, dflt=b'')
	mirror_area = tables.Float32Col()
	num_mirrors = tables.UInt64Col()
	num_mirror_tiles = tables.UInt64Col()
	equivalent_focal_length = tables.Float32Col(shape=(), dflt=0.0, pos=6)


class TriggerInfo(tables.IsDescription):
	'''
	Describe the trigger informations of the telescopes events
	Attributes:
	-----------
		event_id : id of the corresponding event
		time_s : time of the event in second since 1st january 1970
		time_qns : time in nanosecond (or picosecond) to complete the time in second
		obs_id : id of the observation
	'''
	event_id = tables.UInt64Col()
	time_s = tables.UInt32Col()
	time_qns = tables.UInt32Col()
	obs_id = tables.UInt64Col()


def createTelGroupAndTable(hfile, telId, telInfo):
	'''
	Create the telescope group and table
	It is important not to add an other dataset with the type of the camera to simplify the serach of a telescope by telescope index in the file structure
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telId : id of the telescope
		telInfo : table of some informations related to the telescope
	'''
	telIndex = telId - 1
	if telIndex < 0:
		telIndex = 0
	camTelGroup = hfile.create_group("/r1", "Tel_"+str(telIndex), 'Data of telescopes '+str(telIndex))
	
	hfile.create_table(camTelGroup, 'trigger', TriggerInfo, "Trigger of the telescope events")
	
	telType = np.uint64(telInfo[TELINFO_TELTYPE])
	
	nbGain = np.uint64(telInfo[TELINFO_NBGAIN])
	nbSlice = np.uint64(telInfo[TELINFO_NBSLICE])
	
	infoTabGain = telInfo[TELINFO_GAIN]
	tabGain = np.asarray(infoTabGain, dtype=np.float32)
	
	infoTabPed = telInfo[TELINFO_PEDESTAL]
	tabPed = np.asarray(infoTabPed, dtype=np.float32)
	
	nbPixel = np.uint64(telInfo[TELINFO_NBPIXEL])
	
	hfile.create_array(camTelGroup, 'nbPixel', nbPixel, "Number of pixels of the telescope")
	hfile.create_array(camTelGroup, 'nbSlice', nbSlice, "Number of slices of the telescope")
	hfile.create_array(camTelGroup, 'nbGain', nbGain, "Number of gain (channels) of the telescope")

	hfile.create_array(camTelGroup, 'telIndex', telIndex, "Index of the telescope")
	hfile.create_array(camTelGroup, 'telType', telType, "Type of the telescope (0 : LST, 1 : NECTAR, 2 : FLASH, 3 : SCT, 4 : ASTRI, 5 : DC, 6 : GCT)")
	hfile.create_array(camTelGroup, 'telId', telId, "Id of the telescope")
	
	infoRefShape = telInfo[TELINFO_REFSHAPE]
	tabRefShape = np.asarray(infoRefShape, dtype=np.float32)
	if infoRefShape is not None:
		nbSample = np.uint64(tabRefShape.shape[1])
		hfile.create_array(camTelGroup, 'tabRefShape', tabRefShape, "Reference pulse shape of the pixel of the telescope (channel, pixel, sample)")
	
	if infoTabGain is not None:
		hfile.create_array(camTelGroup, 'tabGain', tabGain, "Table of the gain of the telescope (channel, pixel)")
	
	image_shape = (nbSlice, nbPixel)
	
	columns_dict_waveform  = {"waveformHi": tables.UInt16Col(shape=image_shape)}
	description_waveform = type('description columns_dict_waveform', (tables.IsDescription,), columns_dict_waveform)
	hfile.create_table(camTelGroup, 'waveformHi', description_waveform, "Table of waveform of the high gain signal")
	
	if nbGain > 1:
		columns_dict_waveformLo  = {"waveformLo": tables.UInt16Col(shape=image_shape)}
		description_waveformLo = type('description columns_dict_waveformLo', (tables.IsDescription,), columns_dict_waveformLo)
		hfile.create_table(camTelGroup, 'waveformLo', description_waveformLo, "Table of waveform of the low gain signal")
	
	
	columns_dict_photo_electron_image  = {"photo_electron_image": tables.Float32Col(shape=nbPixel)}
	description_photo_electron_image = type('description columns_dict_photo_electron_image', (tables.IsDescription,), columns_dict_photo_electron_image)
	hfile.create_table(camTelGroup, 'photo_electron_image', description_photo_electron_image, "Table of real signal in the camera (for simulation only)")
	
	ped_shape = (nbGain, nbPixel)
	columns_dict_pedestal = {
		"first_event_id" :  tables.UInt64Col(),
		"last_event_id" :  tables.UInt64Col(),
		"pedestal" :  tables.Float32Col(shape=ped_shape)
	}
	description_pedestal = type('description columns_dict_pedestal', (tables.IsDescription,), columns_dict_pedestal)
	tablePedestal = hfile.create_table(camTelGroup, 'pedestal', description_pedestal, "Table of the pedestal for high and low gain")
	
	if infoTabPed is not None:
		tabPedForEntry = tablePedestal.row
		tabPedForEntry["first_event_id"] = np.uint64(0)
		tabPedForEntry["last_event_id"] = np.uint64(-1)
		tabPedForEntry["pedestal"] = tabPed
		tabPedForEntry.append()


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
	#Group : r1
	r1Group = hfile.create_group("/", 'r1', 'Raw data waveform informations of the run')
	eventR1Group = hfile.create_group("/r1", 'event', 'Raw data waveform events')
	
	#The group in the r1 group will be completed on the fly with the informations collected in telInfo_from_evt
	for telId, telInfo in telInfo_from_evt.items():
		createTelGroupAndTable(hfile, telId, telInfo)
	
	#Group : instrument
	instrumentGroup = hfile.create_group("/", 'instrument', 'Instrument informations of the run')
	#	Group : instrument/subarray
	subarrayGroup = hfile.create_group("/instrument", 'subarray', 'Subarray of the run')
	tableSubarrayLayout = hfile.create_table(subarrayGroup, 'layout', SubarrayLayout, "Layout of the subarray")
	#		Group : instrument/subarray/telescope
	subarrayTelescopeGroup = hfile.create_group("/instrument/subarray", 'telescope', 'Telescope of the subarray')
	
	#			Group : instrument/subarray/telescope/camera
	camTelSubInstGroup = hfile.create_group("/instrument/subarray/telescope", 'camera', 'Camera in the run')
	tableLstCam = createCameraTable(hfile, camTelSubInstGroup, "LSTCam")
	tableNectarCam = createCameraTable(hfile, camTelSubInstGroup, "NectarCam")
	tableFlashCam = createCameraTable(hfile, camTelSubInstGroup, "FlashCam")
	tableSCTCam = createCameraTable(hfile, camTelSubInstGroup, "SCTCam")
	tableAstriCam = createCameraTable(hfile, camTelSubInstGroup, "AstriCam")
	tableDcCam = createCameraTable(hfile, camTelSubInstGroup, "DCCam")
	tableGctCam = createCameraTable(hfile, camTelSubInstGroup, "GCTCam")
	
	tableOptic = hfile.create_table(subarrayTelescopeGroup, 'optics', OpticDescription, "Describe the optic of the all the telescopes")
	
	tableMcEvent = createSimiulationDataset(hfile)
	return tableMcEvent


def fillOpticDescription(hfile, telInfo_from_evt):
	'''
	Fill the optic description table
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
	'''
	
	tableOptic = hfile.root.instrument.subarray.telescope.optics
	tabOp = tableOptic.row
	for telIndex, (telId, telInfo) in enumerate(telInfo_from_evt.items()):
		telType = telInfo[TELINFO_TELTYPE]
		
		camName = getCameraNameFromType(telType)
		telTypeStr = getTelescopeTypeStrFromCameraType(telType)
		
		tabOp["description"] = "Description"
		tabOp["name"] = camName
		tabOp["type"] = telTypeStr
		tabOp["mirror_area"] = np.float32(telInfo[TELINFO_MIRRORAREA])
		tabOp["num_mirrors"] = np.float32(telInfo[TELINFO_NBMIRROR])
		tabOp["num_mirror_tiles"] = np.float32(telInfo[TELINFO_NBMIRRORTILES])
		tabOp["equivalent_focal_length"] = np.float32(telInfo[TELINFO_FOCLEN])
		tabOp.append()


def appendWaveformInTelescope(telNode, waveform, photo_electron_image, eventId, timeStamp):
	'''
	Append a waveform signal (to be transposed) into a telescope node
	-------------------
	Parameters :
		telNode : telescope node to be used
		waveform : waveform signal to be used
		photo_electron_image : image of the pixel with signal (without noise)
		eventId : id of the corresponding event
		timeStamp : time of the event in UTC
	'''
	tabtrigger = telNode.trigger.row
	tabtrigger['event_id'] = eventId
	
	#TODO : use the proper convertion from timeStamp to the time in second and nanosecond
	if isinstance(timeStamp, numbers.Number):
		timeSecond = int(timeStamp)
		timeMicroSec = timeStamp - timeSecond
		tabtrigger['time_s'] = timeSecond
		tabtrigger['time_qns'] = timeMicroSec
	tabtrigger.append()
	
	tabWaveformHi = telNode.waveformHi.row
	tabWaveformHi['waveformHi'] = np.asarray(np.swapaxes(waveform[0], 0, 1), dtype=np.float32)
	tabWaveformHi.append()
	
	if waveform.shape[0] > 1:
		tabWaveformLo = telNode.waveformLo.row
		tabWaveformLo['waveformLo'] = np.asarray(np.swapaxes(waveform[1], 0, 1), dtype=np.float32)
		tabWaveformLo.append()
	
	if photo_electron_image is not None and isinstance(photo_electron_image, list):
		tabPhotoElectronImage = telNode.photo_electron_image.row
		tabPhotoElectronImage["photo_electron_image"] = np.asarray(photo_electron_image, dtype=np.float32)
		tabPhotoElectronImage.append()
	
	


def appendEventTelescopeData(hfile, event):
	'''
	Append data from event in telescopes
	--------------
	Parameters :
		hfile : HDF5 file to be used
		event : current event
	'''
	tabTelWithData = event.r0.tels_with_data
	dicoTel = event.r0.tel
	for telId in tabTelWithData:
		waveform = dicoTel[telId].waveform
		telIndex = telId - 1
		if telIndex < 0:
			telIndex = 0
		telNode = hfile.get_node("/r1", 'Tel_' + str(telIndex))
		photo_electron_image = event.mc.tel[telId].photo_electron_image
		appendWaveformInTelescope(telNode, waveform, photo_electron_image, event.r0.event_id, event.trig.gps_time.value)
		


def checkIsSimulationFile(telInfo_from_evt):
	'''
	Function which check if the file is a simulation one or not
	For now there is no origin in the ctapipe_io_lst plugin so I use this function to get the origin of the file
	Parameters:
	-----------
		telInfo_from_evt : information of the different telescopes
	Return:
	-------
		True if the data seems to provide of a simulation, False if not
	'''
	for key, value in telInfo_from_evt.items():
		if value[TELINFO_REFSHAPE] is None:
			return False
		else:
			return True


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

