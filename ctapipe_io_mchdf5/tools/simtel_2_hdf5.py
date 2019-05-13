
# coding: utf-8

import tables
import numpy as np
from tables import open_file
from ctapipe.io import event_source
import argparse


	
def getTelescopeInfoFromEvent(source, telescope_info, max_nb_tel): 
	for evt in source: 
		for tel_id in evt.r0.tels_with_data:
			if not tel_id in telescope_info:
				ref_shape = evt.mc.tel[tel_id].reference_pulse_shape
				nb_slice = evt.r0.tel[tel_id].waveform.shape[2]
				ped = evt.mc.tel[tel_id].pedestal
				gain =  evt.mc.tel[tel_id].dc_to_pe
				telescope_info[tel_id] = (ref_shape, nb_slice, ped, gain)
		if len(telescope_info) >= max_nb_tel:
			return
	

def getCameraTypeFromName(camName):
	'''
	Get the type of teh given camera by its name
	------------------
	Parameters :
		camName : name of the given camera
	------------------
	Return :
		Corresponding type of the camera
	'''
	#print("getCameraTypeFromName : camName = '"+str(camName)+"'")
	if camName == "LSTCam":
		return 0
	elif camName == "NectarCam":
		return 1
	elif camName == "FlashCam":
		return 2
	elif camName == "SCTCam":
		return 3
	elif camName == "ASTRICam":
		return 4
	elif camName == "DigiCam":
		return 5
	elif camName == "CHEC":
		return 6
	else:
		return 7


def getNbTel(source):
	itSource = iter(source)
	evt0 = next(itSource)
	nbTel = evt0.inst.subarray.num_tels
	return nbTel


def createRunHeader(fileh, source):
	'''
	Create the run header as a group in hdf5
	------
	Parameter :
		fileh : hdf5 file to be used
		source : source of a simtel file
	'''
	runHeaderGroup = fileh.create_group("/", 'RunHeader', 'Header of the run')
	
	nbTel = getNbTel(source)
	#I take the first event, it may be useful
	itSource = iter(source)
	evt0 = next(itSource)
	
	#Find the appropriate values in simtel
	posTelX = np.asarray(evt0.inst.subarray.tel_coords.x, dtype=np.float32)
	posTelY = np.asarray(evt0.inst.subarray.tel_coords.y, dtype=np.float32)
	posTelZ = np.asarray(evt0.inst.subarray.tel_coords.z, dtype=np.float32)

	fileh.create_array(runHeaderGroup, 'tabPosTelX', posTelX, "Position of the telescope on the X axis in meters")
	fileh.create_array(runHeaderGroup, 'tabPosTelY', posTelY, "Position of the telescope on the Y axis in meters")
	fileh.create_array(runHeaderGroup, 'tabPosTelZ', posTelZ, "Position of the telescope on the Z axis in meters")

	tabFocalTel = np.zeros(nbTel, dtype=np.float32)
	dicoTelInfo = evt0.inst.subarray.tel
	for telIndex in range(0, nbTel):
		telInfo = dicoTelInfo[telIndex + 1]
		tabFocalTel[telIndex] = np.float32(telInfo.optics.equivalent_focal_length.value)

	fileh.create_array(runHeaderGroup, 'tabFocalTel', tabFocalTel, "Focal lenght of the telescope in meters")

	
	altitude = np.float32(evt0.mcheader.run_array_direction[1])
	azimuth = np.float32(evt0.mcheader.run_array_direction[0])

	fileh.create_array(runHeaderGroup, 'altitude', altitude, "Altitude angle observation of the telescope in radian")
	fileh.create_array(runHeaderGroup, 'azimuth', azimuth, "Azimuth angle observation of the telescope in radian")


class MCCorsikaEvent(tables.IsDescription):
	"""Describe row format for event table.

	Contains event-level information, mostly from Monte Carlo simulation
	parameters. NOTE: Additional columns are added dynamically to some tables,
	see the github wiki page for the full table/data format descriptions.

	Attributes
	----------
	eventId : tables.UInt64Col
		Shower event id.
	obsId : tables.UInt64Col
		Shower observation (run) id. Replaces old "run_id" in ctapipe r0
		container.
	showerPrimaryId : tables.UInt8Col
		Particle type id for the shower primary particle. From Monte Carlo
		simulation parameters.
	coreX : tables.Float32Col
		Shower core position x coordinate. From Monte Carlo simulation
		parameters.
	coreY : tables.Float32Col
		Shower core position y coordinate. From Monte Carlo simulation
		parameters.
	h_first_int : tables.Float32Col
		Height of shower primary particle first interaction. From Monte Carlo
		simulation parameters.
	energy : tables.Float32Col
		Energy of the shower primary particle. From Monte Carlo simulation
		parameters.
	az : tables.Float32Col
		Shower azimuth angle. From Monte Carlo simulation parameters.
	alt : tables.Float32Col
		Shower altitude (zenith) angle. From Monte Carlo simulation parameters.
	depthStart : tables.Float32Col
		height of first interaction a.s.l. [m]
	xmax : tables.Float32Col
		Atmospheric depth of shower maximum [g/cm^2], derived from all charged particles
	hmax : tables.Float32Col
		Height of shower maximum [m] in xmax
	emax : tables.Float32Col
		Atm. depth of maximum in electron number [electron number]
	cmax : tables.Float32Col
		Atm. depth of max. in Cherenkov photon emission [m]
	"""

	eventId = tables.UInt64Col()
	obsId = tables.UInt64Col()
	showerPrimaryId = tables.UInt8Col()
	coreX = tables.Float32Col()
	coreY = tables.Float32Col()
	h_first_int = tables.Float32Col()
	energy = tables.Float32Col()
	az = tables.Float32Col()
	alt = tables.Float32Col()
	depthStart = tables.Float32Col()
	xmax = tables.Float32Col()
	hmax = tables.Float32Col()
	emax = tables.Float32Col()
	cmax = tables.Float32Col()
	

def createCosrika(fileh, source):
	'''
	Create the corsika data as a group in hdf5
	------
	Parameter :
		fileh : hdf5 file to be used
		source : source of a simtel file
	'''
	corsikaGroup = fileh.create_group("/", 'Corsika', 'Simulated event properties')
	
	#Find the appropriate values in simtel
	targetName = "Name of the corresponding target"
	altitudeMin = np.float32(0.0)
	altitudeMax = np.float32(0.0)
	azimuthMin = np.float32(0.0)
	azimuthMax = np.float32(0.0)
	isDiffuseMode = np.bool(False)
	coreMinX = np.float32(0.0)
	coreMaxX = np.float32(0.0)
	coreMinY = np.float32(0.0)
	coreMaxY = np.float32(0.0)
	nbUseShower = np.uint64(0)
	
	#Put the values in the hdf5 file
	fileh.create_array(corsikaGroup, 'targetName', np.array(targetName), "Name of the corresponding target")
	fileh.create_array(corsikaGroup, 'altitudeMin', altitudeMin, "Minimum altitude of the simulated showers in radian")
	fileh.create_array(corsikaGroup, 'altitudeMax', altitudeMax, "Maximum altitude of the simulated showers in radian")
	fileh.create_array(corsikaGroup, 'azimuthMin', azimuthMin, "Minimum azimuth of the simulated showers in radian")
	fileh.create_array(corsikaGroup, 'azimuthMax', azimuthMax, "Maximum azimuth of the simulated showers in radian")
	fileh.create_array(corsikaGroup, 'isDiffuseMode', isDiffuseMode, "True is the events are diffuse, False is they are point like")
	fileh.create_array(corsikaGroup, 'coreMinX', coreMinX, "Minimum value of the simulated impact parameters on the X axis in meters")
	fileh.create_array(corsikaGroup, 'coreMaxX', coreMaxX, "Maximum value of the simulated impact parameters on the X axis in meters")
	fileh.create_array(corsikaGroup, 'coreMinY', coreMinY, "Minimum value of the simulated impact parameters on the Y axis in meters")
	fileh.create_array(corsikaGroup, 'coreMaxY', coreMaxY, "Maximum value of the simulated impact parameters on the Y axis in meters")
	fileh.create_array(corsikaGroup, 'nbUseShower', nbUseShower, "Number of used shower per event")
	
	#Create the table of cosrika event(+shower)
	tableMcCorsikaEvent = fileh.create_table(corsikaGroup, 'tabCorsikaEvent', MCCorsikaEvent, "Table of all monte carlo event")
	#Do something with it
	return tableMcCorsikaEvent.row


def appendCorsikaEvent(tableMcCorsikaEvent, event):
	'''
	Append the Monte Carlo informations in the table of Corsika events
	------
	Parameter :
		tableMcCorsikaEvent : table of Corsika events to be completed
		event : Monte Carlo event to be used
	'''
	tableMcCorsikaEvent['eventId'] = np.uint64(event.r0.event_id)
	tableMcCorsikaEvent['obsId'] = np.uint64(event.r0.obs_id)
	tableMcCorsikaEvent['showerPrimaryId'] = np.uint8(event.mc.shower_primary_id)
	tableMcCorsikaEvent['coreX'] = np.float32(event.mc.core_x)
	tableMcCorsikaEvent['coreY'] = np.float32(event.mc.core_y)
	tableMcCorsikaEvent['h_first_int'] = np.float32(event.mc.h_first_int)
	tableMcCorsikaEvent['xmax'] = np.float32(event.mc.x_max)
	tableMcCorsikaEvent['energy'] = np.float32(event.mc.energy)
	tableMcCorsikaEvent['az'] = np.float32(event.mc.az)
	tableMcCorsikaEvent['alt'] = np.float32(event.mc.alt)
	#I don't know where to find the following informations but they exist in C version
	tableMcCorsikaEvent['depthStart'] = np.float32(0.0)
	tableMcCorsikaEvent['hmax'] = np.float32(0.0)
	tableMcCorsikaEvent['emax'] = np.float32(0.0)
	tableMcCorsikaEvent['cmax'] = np.float32(0.0)
	
	tableMcCorsikaEvent.append()


def createGroupOfAllTelescope(fileh, nbTel, source):
	'''
	Create the group of all the telescope data
	------------------
	Parameters :
		fileh : HDF5 file to be completed
		nbTel : number of telescopes
		source : simtel data
	'''
	itSource = iter(source)
	evt0 = next(itSource)
	dicoTelInfo = evt0.inst.subarray.tel
	
	telInfo_from_evt = dict() # Key is tel id, value (ref_shape, slice, ped, gain)
	getTelescopeInfoFromEvent(source, telInfo_from_evt, nbTel)
	
	for telIndexIter in range(0, nbTel):
		telInfo = dicoTelInfo[telIndexIter + 1]
		#Maybe, we have to do some thing with this to avoid trouble due to this stupid thing
		cameraRotation = telInfo.camera.cam_rotation.value
		
		telGroup = fileh.create_group("/Tel", 'Tel_' + str(telIndexIter), 'Telescopes ' + str(telIndexIter))

		telIndex = np.uint64(telIndexIter)
		telType = np.uint64(getCameraTypeFromName(telInfo.camera.cam_id))
		telId = np.uint64(telIndex + 1)
		
		nbPixel = telInfo.camera.n_pixels
		tabPixelX = np.asarray(telInfo.camera.pix_x, dtype=np.float32)
		tabPixelY = np.asarray(telInfo.camera.pix_y, dtype=np.float32)
		
		
		   
		if telId in telInfo_from_evt:
			tabRefShape = np.asarray(telInfo_from_evt[telId][0], dtype=np.float32)
			nbSample = tabRefShape.shape[1]
			nbGain = np.uint64(tabRefShape.shape[0])
			nbSlice = telInfo_from_evt[telId][1]
			
			tabPed = np.asarray(telInfo_from_evt[telId][2])
			tabGain = np.asarray(telInfo_from_evt[telId][3])
  
			fileh.create_array(telGroup, 'nbPixel', nbPixel, "Number of pixels of the telescope")
			fileh.create_array(telGroup, 'nbSlice', nbSlice, "Number of slices of the telescope")
			fileh.create_array(telGroup, 'nbGain', nbGain, "Number of gain (channels) of the telescope")

			fileh.create_array(telGroup, 'telIndex', telIndex, "Index of the telescope")
			fileh.create_array(telGroup, 'telType', telType, "Type of the telescope (0 : LST, 1 : NECTAR, 2 : FLASH, 3 : SCT, 4 : ASTRI, 5 : DC, 6 : GCT)")
			fileh.create_array(telGroup, 'telId', telId, "Id of the telescope")
			fileh.create_array(telGroup, 'tabPixelX', tabPixelX, "Position of the pixels on the X axis in the camera in meters")
			fileh.create_array(telGroup, 'tabPixelY', tabPixelY, "Position of the pixels on the Y axis in the camera in meters")
			fileh.create_array(telGroup, 'tabRefShape', tabRefShape, "Reference pulse shape of the pixel of the telescope (channel, pixel, sample)")
			fileh.create_array(telGroup, 'tabGain', tabGain, "Table of the gain of the telescope (channel, pixel)")
			fileh.create_array(telGroup, 'tabPed', tabPed, "Table of the pedestal of the telescope (channel, pixel)")

			#Create the table of images/waveform of the telescope
			image_shape = (nbGain, nbSlice, nbPixel)
			'''
			columns_dict = {
				"eventId": tables.UInt64Col(),
				"timeStamp": tables.Float64Col(),
				"waveform": tables.Float32Col(shape=image_shape)
			}

			description = type('description', (tables.IsDescription,), columns_dict)

			table = fileh.create_table(telGroup, "tabEvent", description, "Table of the telescopes data (video)")
			'''
			columns_dict_event_id  = {"eventId": tables.UInt64Col()}
			columns_dict_timestamp = {"timestamp": tables.Float64Col()}
			columns_dict_waveform  = {"waveform": tables.UInt16Col(shape=image_shape)}
			
			description_event_id = type('description event_id', (tables.IsDescription,), columns_dict_event_id)
			description_timestamp = type('description timestamp', (tables.IsDescription,), columns_dict_timestamp)
			description_waveform = type('description columns_dict_waveform', (tables.IsDescription,), columns_dict_waveform)
			
			fileh.create_table(telGroup, 'eventId', description_event_id, "Table of event id")
			fileh.create_table(telGroup, 'timestamp', description_timestamp, "Table of timestamp")
			fileh.create_table(telGroup, 'waveform', description_waveform, "Table of waveform")
			

def appendWaveformInTelescope(telNode, waveform, eventId, timeStamp):
	'''
	Append a waveform signal (to be transposed) into a telescope node
	-------------------
	Parameters :
		telNode : telescope node to be used
		waveform : waveform signal to be used
		eventId : id of the corresponding event
		timeStamp : time of the event in UTC
	'''
	#We transpose the waveform :
	tabEventId = telNode.eventId.row
	tabEventId['eventId'] = eventId
		
	tabTimestamp = telNode.timestamp.row
	tabTimestamp['timestamp'] = timeStamp
	   
	tabWaveform = telNode.waveform.row
	tabWaveform['waveform'] = np.swapaxes(waveform,1 , 2)
	
   
	tabEventId.append()
	tabTimestamp.append()
	tabWaveform.append()


def appendEventTelescopeData(fileh, event):
	'''
	Append data from event in telescopes
	--------------
	Parameters :
		fileh : HDF5 file to be used
		event : current event
	'''
	tabTelWithData = event.r0.tels_with_data
	dicoTel = event.r0.tel
	for telId in tabTelWithData:
		waveform = dicoTel[telId].waveform
		#print('waveform.shape:', waveform.shape)
		telNode = fileh.get_node("/Tel", 'Tel_' + str(telId - 1))
		appendWaveformInTelescope(telNode, waveform, event.r0.event_id, event.trig.gps_time.value)
		

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help="simtel r1 input file",
						required=True)
	parser.add_argument('-o', '--output', help="hdf5 r1 output file",
						required=True)
	parser.add_argument('-m', '--max_event', help="maximum event to reconstuct",
						required=False, type=int)
	args = parser.parse_args()

	source = event_source(args.input)
	nbTel = getNbTel(source)
	print("Number of telescope : ",nbTel)
	fileh = tables.open_file(args.output, mode = "w")

	createRunHeader(fileh, source)
	#We can set the Monte Carlo values durring the iteration on source
	print('createCosrika')
	tableMcCorsikaEvent = createCosrika(fileh, source)

	#Create the group of all telescopes
	allTelGroup = fileh.create_group("/", 'Tel', 'Telescopes data')
	#Create all the telescopes in the /Tel group
	print('createGroupOfAllTelescope start')
	createGroupOfAllTelescope(fileh, nbTel, source)
	print('createGroupOfAllTelescope done')


	nb_event = 0
	max_event = 0
	if args.max_event != None:
		max_event = int(args.max_event)

	for event in source:
		#I found the timestamp
		eventTimeStamp = np.float64(event.trig.gps_time.value)
		obsId = event.r0.obs_id
		eventId = event.r0.event_id
		appendCorsikaEvent(tableMcCorsikaEvent, event)
		appendEventTelescopeData(fileh, event)
		nb_event+=1
		print("{} / {}".format(nb_event, max_event), end="\r")
		if nb_event >= max_event:
			break
	print('Done')


if __name__ == '__main__':
	main()

