
import numbers
import tables
import numpy as np
from .get_telescope_info import *


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
	camTelGroup = hfile.create_group("/r1", "Tel_"+str(telId), 'Data of telescopes '+str(telId))
	
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
		tablePedestal.flush()


def createR1Dataset(hfile, telInfo_from_evt):
	'''
	Create the r1 dataset
	Parameters:
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
	'''
	#Group : r1
	hfile.create_group("/", 'r1', 'Raw data waveform informations of the run')
	
	#The group in the r1 group will be completed on the fly with the informations collected in telInfo_from_evt
	for telId, telInfo in telInfo_from_evt.items():
		createTelGroupAndTable(hfile, telId, telInfo)



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
	
	#If the bug is still there I can try without np.asarray function
	tabWaveformHi = telNode.waveformHi.row
	tabWaveformHi['waveformHi'] = np.asarray(np.swapaxes(waveform[0], 0, 1), dtype=np.uint16)
	tabWaveformHi.append()
	
	if waveform.shape[0] > 1:
		tabWaveformLo = telNode.waveformLo.row
		tabWaveformLo['waveformLo'] = np.asarray(np.swapaxes(waveform[1], 0, 1), dtype=np.uint16)
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
		telNode = hfile.get_node("/r1", 'Tel_' + str(telId))
		photo_electron_image = event.mc.tel[telId].photo_electron_image
		appendWaveformInTelescope(telNode, waveform, photo_electron_image, event.r0.event_id, event.trig.gps_time.value)


