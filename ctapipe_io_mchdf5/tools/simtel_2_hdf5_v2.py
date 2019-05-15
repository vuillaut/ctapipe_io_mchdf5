
# coding: utf-8

import tables
import numpy as np
from tables import open_file
from ctapipe.io import event_source
import argparse

class RunConfigEvent(tables.IsDescription):
	'''
	Configuration of the simulated events
	'''
	atmosphere = tables.UInt64Col()
	core_pos_mode = tables.UInt64Col()
	corsika_bunchsize = tables.Float32Col()
	corsika_high_E_detail = tables.Int32Col()
	corsika_high_E_model = tables.Int32Col()
	corsika_iact_options = tables.Int32Col()
	corsika_low_E_detail = tables.Int32Col()
	corsika_low_E_model = tables.Int32Col()
	corsika_version = tables.Int32Col()
	corsika_wlen_max = tables.Float32Col()
	corsika_wlen_min = tables.Float32Col()
	detector_prog_id = tables.UInt64Col()
	detector_prog_start = tables.Int32Col()
	diffuse = tables.Int32Col()
	energy_range_max = tables.Float32Col()
	energy_range_min = tables.Float32Col()
	injection_height = tables.Float32Col()
	max_alt = tables.Float32Col()
	max_az = tables.Float32Col()
	max_scatter_range = tables.Float32Col()
	max_viewcone_radius = tables.Float32Col()
	min_alt = tables.Float32Col()
	min_az = tables.Float32Col()
	min_scatter_range = tables.Float32Col()
	min_viewcone_radius = tables.Float32Col()
	num_showers = tables.UInt64Col()
	obs_id = tables.UInt64Col()
	prod_site_B_declination = tables.Float32Col()
	prod_site_B_inclination = tables.Float32Col()
	prod_site_B_total = tables.Float32Col()
	prod_site_alt = tables.Float32Col()
	run_array_direction = tables.Float32Col()
	shower_prog_id = tables.UInt64Col()
	shower_prog_start = tables.Int32Col()
	shower_reuse = tables.UInt64Col()
	simtel_version = tables.Int32Col()
	spectral_index = tables.Float32Col()


class ThrowEventDistribution(tables.IsDescription):
	'''
	Distribution of the simulated events
	'''
	bins_core_dist = tables.Float32Col(shape=(201,))
	bins_energy = tables.Float32Col(shape=(121,))
	hist_id = tables.UInt64Col()
	histogram = tables.Float32Col(shape=(120, 200))
	num_entries = tables.UInt64Col()
	obs_id = tables.UInt64Col()


class MCEvent(tables.IsDescription):
	'''
	Simulated corsika event
	Attributes
	----------
	event_id : tables.UInt64Col
		Shower event id.
	mc_alt : tables.Float32Col
		Shower altitude (zenith) angle. From Monte Carlo simulation parameters.
	mc_az : tables.Float32Col
		Shower azimuth angle. From Monte Carlo simulation parameters.
	mc_core_x : tables.Float32Col
		Shower core position x coordinate. From Monte Carlo simulation
		parameters.
	mc_core_y : tables.Float32Col
		Shower core position y coordinate. From Monte Carlo simulation
		parameters.
	mc_energy : tables.Float32Col
		Energy of the shower primary particle. From Monte Carlo simulation
		parameters.
	mc_h_first_int : tables.Float32Col
		Height of shower primary particle first interaction. From Monte Carlo
		simulation parameters.
	mc_shower_primary_id : tables.UInt8Col
		Particle type id for the shower primary particle. From Monte Carlo
		simulation parameters.
	mc_x_max : tables.Float32Col
		Atmospheric depth of shower maximum [g/cm^2], derived from all charged particles
	obs_id : tables.UInt64Col
		Shower observation (run) id. Replaces old "run_id" in ctapipe r0
		container.
	'''
	event_id = tables.UInt64Col()
	mc_alt = tables.Float32Col()
	mc_az = tables.Float32Col()
	mc_core_x = tables.Float32Col()
	mc_core_y = tables.Float32Col()
	mc_energy = tables.Float32Col()
	mc_h_first_int = tables.Float32Col()
	mc_shower_primary_id = tables.UInt64Col()
	mc_x_max = tables.Float32Col()
	obs_id = tables.UInt64Col()
	


class SubarrayLayout(tables.IsDescription):
	'''
	Layout of the subaray
	'''
	tel_id = tables.UInt64Col()
	pos_x = tables.Float32Col()
	pos_y = tables.Float32Col()
	pos_z = tables.Float32Col()
	name = tables.StringCol(5, dflt=b'')
	type = tables.StringCol(3, dflt=b'')
	num_mirrors = tables.UInt64Col()
	camera_type = tables.StringCol(9, dflt=b'')
	tel_description = tables.StringCol(14, dflt=b'')


class CameraPixel(tables.IsDescription):
	'''
	Desctibes the pixels of a camera
	'''
	pix_id = tables.UInt64Col()
	pix_x = tables.Float32Col()
	pix_y = tables.Float32Col()
	pix_area = tables.Float32Col()


def createCameraTable(fileh, parentGroup, tableName):
	'''
	Create a table to describe a camera
	Parameters:
	-----------
		fileh : HDF5 file to be used
		parentGroup : parent group of the table to be created
		tableName : name of the table to be created
	Return:
	-------
		created table
	'''
	table = fileh.create_table(parentGroup, tableName, ThrowEventDistribution, "Distribution of the "+tableName+" camera")
	return table


class OpticDescription(tables.IsDescription):
	'''
	Describe the optic of the all the telescopes
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
	'''
	event_id = tables.UInt64Col()
	time_s = tables.UInt32Col()
	time_qns = tables.UInt32Col()
	obs_id = tables.UInt64Col()


def createTelGroupAndTable(fileh, telIndex, telId, telInfo):
	'''
	Create the telescope group and table
	It is important not to add an other dataset with the type of the camera to simplify the serach of a telescope by telescope index in the file structure
	Parameters:
	-----------
		fileh : HDF5 file to be used
		telIndex : index of the group to be created for the given telescope type
		telId : id of the telescope
		telInfo : table of some informations related to the telescope
	'''
	camTelGroup = fileh.create_group("/r1", "Tel_"+telIndex, 'Data of telescopes '+telIndex)
	
	fileh.create_table(camTelGroup, 'trigger', TriggerInfo, "Trigger of the telescope events")
	
	telType = telInfo[4]
	tabRefShape = np.asarray(telInfo[0], dtype=np.float32)
	nbSample = tabRefShape.shape[1]
	nbGain = np.uint64(tabRefShape.shape[0])
	nbSlice = telInfo[1]
	
	tabGain = np.asarray(telInfo[3])
	tabPed = np.asarray(telInfo[2])
	
	nbPixel = tabPed.shape[-1]
	
	fileh.create_array(telGroup, 'nbPixel', nbPixel, "Number of pixels of the telescope")
	fileh.create_array(telGroup, 'nbSlice', nbSlice, "Number of slices of the telescope")
	fileh.create_array(telGroup, 'nbGain', nbGain, "Number of gain (channels) of the telescope")

	fileh.create_array(telGroup, 'telIndex', telIndex, "Index of the telescope")
	fileh.create_array(telGroup, 'telType', telType, "Type of the telescope (0 : LST, 1 : NECTAR, 2 : FLASH, 3 : SCT, 4 : ASTRI, 5 : DC, 6 : GCT)")
	fileh.create_array(telGroup, 'telId', telId, "Id of the telescope")
	
	fileh.create_array(telGroup, 'tabRefShape', tabRefShape, "Reference pulse shape of the pixel of the telescope (channel, pixel, sample)")
	fileh.create_array(telGroup, 'tabGain', tabGain, "Table of the gain of the telescope (channel, pixel)")
	
	image_shape = (nbSlice, nbPixel)
	
	columns_dict_waveform  = {"waveformHi": tables.UInt16Col(shape=image_shape)}
	description_waveform = type('description columns_dict_waveform', (tables.IsDescription,), columns_dict_waveform)
	fileh.create_table(camTelGroup, 'waveformHi', description_waveform, "Table of waveform of the high gain signal")
	
	if nbGain > 1:
		columns_dict_waveformLo  = {"waveformLo": tables.UInt16Col(shape=image_shape)}
		description_waveformLo = type('description columns_dict_waveformLo', (tables.IsDescription,), columns_dict_waveformLo)
		fileh.create_table(camTelGroup, 'waveformLo', description_waveformLo, "Table of waveform of the low gain signal")
	
	
	ped_shape = (nbGain, nbPixel)
	columns_dict_pedestal = {
		"first_event_id" :  tables.UInt64Col(),
		"last_event_id" :  tables.UInt64Col(),
		"pedestal" :  tables.Float32Col(shape=ped_shape)
	}
	description_pedestal = type('description columns_dict_pedestal', (tables.IsDescription,), columns_dict_pedestal)
	tablePedestal = fileh.create_table(camTelGroup, 'pedestal', description_pedestal, "Table of waveform of the pedestal for high and low gain")
	
	tabPedForEntry = tablePedestal.row
	tabPedForEntry["first_event_id"] = np.uint64(0)
	tabPedForEntry["last_event_id"] = np.uint64(-1)
	tabPedForEntry["pedestal"] = tabPed
	tabPedForEntry.append()
	


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


def createFileStructure(fileh, telInfo_from_evt):
	'''
	Create the structure of the HDF5 file
	Parameters:
	-----------
		fileh : HDF5 file to be used
		telInfo_from_evt : information of telescopes
	Return:
	-------
		table of mc_event
	'''
	#Group : r1
	r1Group = fileh.create_group("/", 'r1', 'Raw data waveform informations of the run')
	eventR1Group = fileh.create_group("/r1", 'event', 'Raw data waveform events')
	
	#The group in the r1 group will be completed on the fly with the informations collected in telInfo_from_evt
	for telIndex, (telId, telInfo) in enumerate(telInfo_from_evt.items()):
		createTelGroupAndTable(fileh, telIndex, telId, telInfo)
	
	#Group : instrument
	instrumentGroup = fileh.create_group("/", 'instrument', 'Instrument informations of the run')
	#	Group : instrument/subaray
	subarrayGroup = fileh.create_group("/instrument", 'subarray', 'Subarray of the run')
	tableSubarrayLayout = fileh.create_table(subarrayGroup, 'layout', SubarrayLayout, "Layout of the subaray")
	#		Group : instrument/subaray/telescope
	subarrayTelescopeGroup = fileh.create_group("/instrument/subarray", 'telescope', 'Telescope of the subarray')
	
	#			Group : instrument/subaray/telescope/camera
	camTelSubInstGroup = fileh.create_group("/instrument/subarray/telescope", 'camera', 'Camera in the run')
	tableLstCam = createCameraTable(fileh, camTelSubInstGroup, "LSTCam")
	tableNectarCam = createCameraTable(fileh, camTelSubInstGroup, "NectarCam")
	tableFlashCam = createCameraTable(fileh, camTelSubInstGroup, "FlashCam")
	tableSCTCam = createCameraTable(fileh, camTelSubInstGroup, "SCTCam")
	tableAstriCam = createCameraTable(fileh, camTelSubInstGroup, "AstriCam")
	tableDcCam = createCameraTable(fileh, camTelSubInstGroup, "DCCam")
	tableGctCam = createCameraTable(fileh, camTelSubInstGroup, "GCTCam")
	
	tableRunConfig = fileh.create_table(subarrayTelescopeGroup, 'optics', OpticDescription, "Describe the optic of the all the telescopes")
	
	simulationGroup = fileh.create_group("/", 'simulation', 'Simulation informations of the run')
	
	tableRunConfig = fileh.create_table(simulationGroup, 'run_config', RunConfigEvent, "Configuration of the simulated events")
	tableThrowEventDistribution = fileh.create_table(simulationGroup, 'thrown_event_distribution', ThrowEventDistribution, "Distribution of the simulated events")
	tableMcEvent = fileh.create_table(simulationGroup, 'mc_event', MCEvent, "All simulated Corsika events")
	return tableMcEvent







def getTelescopeInfoFromEvent(inputFileName, max_nb_tel):
	'''
	Get the telescope information from the event
	Parameters:
	-----------
		inputFileName : name of the input file to be used
		max_nb_tel : maximum number of telescope in the simulation
	Return:
	-------
		dictionnnary which contains the telescope informations (ref_shape, nb_slice, ped, gain) with telescope id as key
	'''
	telescope_info = dict() # Key is tel id, value (ref_shape, slice, ped, gain, telType, focalLen, tabPixelX, tabPixelY)
	source = event_source(inputFileName)
	
	dicoTelInfo = None
	for evt in source:
		if dicoTelInfo is None:
			dicoTelInfo = evt.inst.subarray.tel
		for tel_id in evt.r0.tels_with_data:
			if not tel_id in telescope_info:
				ref_shape = evt.mc.tel[tel_id].reference_pulse_shape
				nb_slice = evt.r0.tel[tel_id].waveform.shape[2]
				ped = evt.mc.tel[tel_id].pedestal
				gain =  evt.mc.tel[tel_id].dc_to_pe
				
				telInfo = dicoTelInfo[tel_id]
				telType = np.uint64(getCameraTypeFromName(telInfo.camera.cam_id))
				focalLen = np.float32(telInfo.optics.equivalent_focal_length.value)
				
				tabPixelX = np.asarray(telInfo.camera.pix_x, dtype=np.float32)
				tabPixelY = np.asarray(telInfo.camera.pix_y, dtype=np.float32)
				
				telescope_info[tel_id] = (ref_shape, nb_slice, ped, gain, telType, focalLen, tabPixelX, tabPixelY)
		if len(telescope_info) >= max_nb_tel:
			return telescope_info
	return telescope_info


def fillSimulationHeaderInfo(hfile, inputFileName):
	'''
	Fill the simulation informations in the simulation header (/simulation/run_config)
	Parameters:
	-----------
		hfile : HDF5 file to be used
		inputFileName : name of the input file to be used
	'''
	source = event_source(inputFileName)
	evt0 = next(iter(source))
	
	tableSimulationConfig = hfile.root.simulation.run_config
	tabSimConf = tableSimulationConfig.row
	
	#TODO : fill the simulation header informations with the proper values
	
	tabSimConf["atmosphere"] = np.uint64(0)
	tabSimConf["core_pos_mode"] = np.uint64(0)
	tabSimConf["corsika_bunchsize"] = np.float32(0.0)
	tabSimConf["corsika_high_E_detail"] = np.int32(0)
	tabSimConf["corsika_high_E_model"] = np.int32(0)
	tabSimConf["corsika_iact_options"] = np.int32(0)
	tabSimConf["corsika_low_E_detail"] = np.int32(0)
	tabSimConf["corsika_low_E_model"] = np.int32(0)
	tabSimConf["corsika_version"] = np.int32(0)
	tabSimConf["corsika_wlen_max"] = np.float32(0.0)
	tabSimConf["corsika_wlen_min"] = np.float32(0.0)
	tabSimConf["detector_prog_id"] = np.uint64(0)
	tabSimConf["detector_prog_start"] = np.int32(0)
	tabSimConf["diffuse"] = np.int32(0)
	tabSimConf["energy_range_max"] = np.float32(0.0)
	tabSimConf["energy_range_min"] = np.float32(0.0)
	tabSimConf["injection_height"] = np.float32(0.0)
	tabSimConf["max_alt"] = np.float32(0.0)
	tabSimConf["max_az"] = np.float32(0.0)
	tabSimConf["max_scatter_range"] = np.float32(0.0)
	tabSimConf["max_viewcone_radius"] = np.float32(0.0)
	tabSimConf["min_alt"] = np.float32(0.0)
	tabSimConf["min_az"] = np.float32(0.0)
	tabSimConf["min_scatter_range"] = np.float32(0.0)
	tabSimConf["min_viewcone_radius"] = np.float32(0.0)
	tabSimConf["num_showers"] = np.uint64(0)
	tabSimConf["obs_id"] = np.uint64(0)
	tabSimConf["prod_site_B_declination"] = np.float32(0.0)
	tabSimConf["prod_site_B_inclination"] = np.float32(0.0)
	tabSimConf["prod_site_B_total"] = np.float32(0.0)
	tabSimConf["prod_site_alt"] = np.float32(0.0)
	tabSimConf["run_array_direction"] = np.float32(0.0)
	tabSimConf["shower_prog_id"] = np.uint64(0)
	tabSimConf["shower_prog_start"] = np.int32(0)
	tabSimConf["shower_reuse"] = np.uint64(0)
	tabSimConf["simtel_version"] = np.int32(0)
	tabSimConf["spectral_index"] = np.float32(0.0)
	
	tabSimConf.append()
	


def getNbTel(inputFileName):
	'''
	Get the number of telescope in the simulation file
	Parameters:
	-----------
		inputFileName : name of the input file to be used
	Return:
	-------
		number of telescopes in the simulation file
	'''
	source = event_source(inputFileName)
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


def appendCorsikaEvent(tableMcCorsikaEvent, event):
	'''
	Append the Monte Carlo informations in the table of Corsika events
	------
	Parameter :
		tableMcCorsikaEvent : table of Corsika events to be completed
		event : Monte Carlo event to be used
	'''
	tableMcCorsikaEvent['event_id'] = np.uint64(event.r0.event_id)
	tableMcCorsikaEvent['mc_az'] = np.float32(event.mc.az)
	tableMcCorsikaEvent['mc_alt'] = np.float32(event.mc.alt)
	
	tableMcCorsikaEvent['mc_core_x'] = np.float32(event.mc.core_x)
	tableMcCorsikaEvent['mc_core_y'] = np.float32(event.mc.core_y)
	
	tableMcCorsikaEvent['mc_energy'] = np.float32(event.mc.energy)
	tableMcCorsikaEvent['mc_h_first_int'] = np.float32(event.mc.h_first_int)
	tableMcCorsikaEvent['mc_shower_primary_id'] = np.uint8(event.mc.shower_primary_id)
	
	tableMcCorsikaEvent['mc_x_max'] = np.float32(event.mc.x_max)
	
	tableMcCorsikaEvent['obs_id'] = np.uint64(event.r0.obs_id)
	
	#I don't know where to find the following informations but they exist in C version
	#tableMcCorsikaEvent['depthStart'] = np.float32(0.0)
	#tableMcCorsikaEvent['hmax'] = np.float32(0.0)
	#tableMcCorsikaEvent['emax'] = np.float32(0.0)
	#tableMcCorsikaEvent['cmax'] = np.float32(0.0)
	
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
	
	
	tabtrigger = telNode.trigger.row
	tabtrigger['event_id'] = eventId
	
	tabtrigger = telNode.timestamp.row
	#TODO : use the proper convertion from timeStamp to the time in second and nanosecond
	tabtrigger['time_s'] = timeStamp
	tabtrigger['time_qns'] = timeStamp
	
	
	tabWaveformHi = telNode.waveformHi.row
	tabWaveformHi['waveformHi'] = np.swapaxes(waveform[0], 0, 1)
	
	if waveform.shape[0] > 1:
		tabWaveformLo = telNode.waveformLo.row
		tabWaveformLo['waveformLo'] = np.swapaxes(waveform[1], 0, 1)
		tabWaveformLo.append()
   
	tabEventId.append()
	tabTimestamp.append()
	tabWaveformHi.append()


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
		telNode = fileh.get_node("/r1", 'Tel_' + str(telId - 1))
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

	inputFileName = args.input
	nbTel = getNbTel(inputFileName)
	print("Number of telescope : ",nbTel)
	telInfo_from_evt = getTelescopeInfoFromEvent(inputFileName, nbTel)
	
	fileh = tables.open_file(args.output, mode = "w")
	
	print('Create file structure')
	tableMcCorsikaEvent = createFileStructure(fileh, telInfo_from_evt)
	
	fillSimulationHeaderInfo(fileh, inputFileName)
	
	source = event_source(inputFileName)
	
	nb_event = 0
	max_event = 10000000
	if args.max_event != None:
		max_event = int(args.max_event)

	for event in source:
		appendCorsikaEvent(tableMcCorsikaEvent, event)
		appendEventTelescopeData(fileh, event)
		nb_event+=1
		print("{} / {}".format(nb_event, max_event), end="\r")
		if nb_event >= max_event:
			break
	print('Done')


if __name__ == '__main__':
	main()

