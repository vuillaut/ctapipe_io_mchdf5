
# coding: utf-8

import tables
import numbers
import numpy as np
from tables import open_file
from ctapipe.io import event_source
import argparse


def getCameraTypeFromName(camName):
	'''
	Get the type of the given camera by its name
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


def getCameraNameFromType(camType):
	'''
	Get the name of the given camera by its type
	------------------
	Parameters :
		camType : type of the given camera
	------------------
	Return :
		Corresponding name of the camera
	'''
	if camType == 0:
		return "LSTCam"
	elif camType == 1:
		return "NectarCam"
	elif camType == 2:
		return "FlashCam"
	elif camType == 3:
		return "SCTCam"
	elif camType == 4:
		return "ASTRICam"
	elif camType == 5:
		return "DigiCam"
	elif camType == 6:
		return "CHEC"
	else:
		return "UNKNOWN_cameraType"


def getTelescopeTypeStrFromCameraType(camType):
	'''
	Get the type of the given telescope by its camera type
	------------------
	Parameters :
		camType : type of the given camera
	------------------
	Return :
		Corresponding type of the telescope
	'''
	if camType == 0:
		return "LST"
	elif camType in [1, 2, 3]:
		return "MST"
	elif camType in [4, 5, 6]:
		return "SST"
	else:
		return "UNKNOWN_telescopeType"
	

TELINFO_REFSHAPE = 0
TELINFO_NBSLICE = 1
TELINFO_PEDESTAL = 2
TELINFO_GAIN = 3
TELINFO_TELTYPE = 4
TELINFO_FOCLEN = 5
TELINFO_TABPIXELX = 6
TELINFO_TABPIXELY = 7
TELINFO_NBMIRROR = 8
TELINFO_TELPOSX = 9
TELINFO_TELPOSY = 10
TELINFO_TELPOSZ = 11
TELINFO_NBMIRRORTILES = 12
TELINFO_MIRRORAREA = 13
TELINFO_NBGAIN = 14
TELINFO_NBPIXEL = 15

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
	telescope_info = dict() # Key is tel id, value (ref_shape, slice, ped, gain, telType, focalLen, tabPixelX, tabPixelY, nbMirror)
	source = event_source(inputFileName)
	
	dicoTelInfo = None
	posTelX = None
	posTelY = None
	posTelZ = None
	for evt in source:
		if dicoTelInfo is None:
			dicoTelInfo = evt.inst.subarray.tel
			posTelX = np.asarray(evt.inst.subarray.tel_coords.x, dtype=np.float32)
			posTelY = np.asarray(evt.inst.subarray.tel_coords.y, dtype=np.float32)
			posTelZ = np.asarray(evt.inst.subarray.tel_coords.z, dtype=np.float32)
		for tel_id in evt.r0.tels_with_data:
			if not tel_id in telescope_info:
				ref_shape = evt.mc.tel[tel_id].reference_pulse_shape
				nb_slice = evt.r0.tel[tel_id].waveform.shape[2]
				nbGain = evt.r0.tel[tel_id].waveform.shape[0]
				nbPixel = evt.r0.tel[tel_id].waveform.shape[1]
				ped = evt.mc.tel[tel_id].pedestal
				gain =  evt.mc.tel[tel_id].dc_to_pe
				
				telInfo = dicoTelInfo[tel_id]
				telType = np.uint64(getCameraTypeFromName(telInfo.camera.cam_id))
				focalLen = np.float32(telInfo.optics.equivalent_focal_length.value)
				
				tabPixelX = np.asarray(telInfo.camera.pix_x, dtype=np.float32)
				tabPixelY = np.asarray(telInfo.camera.pix_y, dtype=np.float32)
				
				nbMirror = np.uint64(telInfo.optics.num_mirrors)
				nbMirrorTiles = np.uint64(telInfo.optics.num_mirror_tiles)
				mirrorArea = np.uint64(telInfo.optics.mirror_area.value)
				
				telX = posTelX[tel_id - 1]
				telY = posTelY[tel_id - 1]
				telZ = posTelZ[tel_id - 1]
				
				telescope_info[tel_id] = (ref_shape, nb_slice, ped, gain, telType, focalLen, tabPixelX, tabPixelY, nbMirror,
								telX, telY, telZ, nbMirrorTiles, mirrorArea, nbGain, nbPixel)
		if len(telescope_info) >= max_nb_tel:
			return telescope_info
	return telescope_info


class RunConfigEvent(tables.IsDescription):
	'''
	Configuration of the simulated events
	Attributes:
		atmosphere : Atmospheric model number
		core_pos_mode : Core Position Mode (fixed/circular/...)
		corsika_bunchsize : Number of photons per bunch
		corsika_high_E_detail : Detector MC information
		corsika_high_E_model : Detector MC information
		corsika_iact_options : Detector MC information
		corsika_low_E_detail : Detector MC information
		corsika_low_E_model : Detector MC information
		corsika_version : CORSIKA version * 1000
		corsika_wlen_max : Maximum wavelength of cherenkov light [nm]
		corsika_wlen_min : Minimum wavelength of cherenkov light [nm]
		detector_prog_id : simtelarray=1
		detector_prog_start : Time when detector simulation started
		diffuse : True if the events are diffuse, False is they are point like
		energy_range_max : Upper limit of energy range of primary particle [TeV]
		energy_range_min : Lower limit of energy range of primary particle [TeV]
		injection_height : Height of particle injection [m]
		max_alt : Maximum altitude of the simulated showers in radian
		max_az : Maximum azimuth of the simulated showers in radian
		max_scatter_range : Maximum scatter range [m]
		max_viewcone_radius : Maximum viewcone radius [deg]
		min_alt : Minimum altitude of the simulated showers in radian
		min_az : Minimum azimuth of the simulated showers in radian
		min_scatter_range : Maximum scatter range [m]
		min_viewcone_radius : Minimum viewcone radius [deg]
		num_showers : total number of shower
		obs_id : id of the observation
		prod_site_B_declination : magnetic declination [rad]
		prod_site_B_inclination : magnetic inclination [rad]
		prod_site_B_total : total geomagnetic field [uT]
		prod_site_alt : height of observation level [m]
		run_array_direction : direction of the run (in azimuth and altitude in radian)
		shower_prog_id : CORSIKA=1, ALTAI=2, KASCADE=3, MOCCA=4
		shower_prog_start : Time when shower simulation started, CORSIKA: only date
		shower_reuse : Number of used shower per event
		simtel_version : sim_telarray version * 1000
		spectral_index : Power-law spectral index of spectrum
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
	run_array_direction = tables.Float32Col(shape=2)
	shower_prog_id = tables.UInt64Col()
	shower_prog_start = tables.Int32Col()
	shower_reuse = tables.UInt64Col()
	simtel_version = tables.Int32Col()
	spectral_index = tables.Float32Col()


class ThrowEventDistribution(tables.IsDescription):
	'''
	Distribution of the simulated events
	Attributes:
		bins_core_dist : distribution of the impact parameters by respect to the dstance by the center of the site
		bins_energy : distribution of the energy of the simulated events
		hist_id : id of the histogram
		num_entries : number of entries of the histogram
		obs_id : observation id
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
	
	tableRunConfig = hfile.create_table(subarrayTelescopeGroup, 'optics', OpticDescription, "Describe the optic of the all the telescopes")
	
	simulationGroup = hfile.create_group("/", 'simulation', 'Simulation informations of the run')
	
	tableRunConfig = hfile.create_table(simulationGroup, 'run_config', RunConfigEvent, "Configuration of the simulated events")
	tableThrowEventDistribution = hfile.create_table(simulationGroup, 'thrown_event_distribution', ThrowEventDistribution, "Distribution of the simulated events")
	tableMcEvent = hfile.create_table(simulationGroup, 'mc_event', MCEvent, "All simulated Corsika events")
	return tableMcEvent


def fillSimulationHeaderInfo(hfile, inputFileName):
	'''
	Fill the simulation informations in the simulation header (/simulation/run_config)
	Parameters:
	-----------
		hfile : HDF5 file to be used
		inputFileName : name of the input file to be used
	'''
	source = event_source(inputFileName)
	evt = next(iter(source))
	
	tableSimulationConfig = hfile.root.simulation.run_config
	tabSimConf = tableSimulationConfig.row
	
	mcHeader = evt.mcheader
	tabSimConf["atmosphere"] = np.uint64(mcHeader.atmosphere)
	tabSimConf["core_pos_mode"] = np.uint64(mcHeader.core_pos_mode)
	tabSimConf["corsika_bunchsize"] = np.float32(mcHeader.corsika_bunchsize)
	tabSimConf["corsika_high_E_detail"] = np.int32(mcHeader.corsika_high_E_detail)
	tabSimConf["corsika_high_E_model"] = np.int32(mcHeader.corsika_high_E_model)
	tabSimConf["corsika_iact_options"] = np.int32(mcHeader.corsika_iact_options)
	tabSimConf["corsika_low_E_detail"] = np.int32(mcHeader.corsika_low_E_detail)
	tabSimConf["corsika_low_E_model"] = np.int32(mcHeader.corsika_low_E_model)
	tabSimConf["corsika_version"] = np.int32(mcHeader.corsika_version)
	tabSimConf["corsika_wlen_max"] = np.float32(mcHeader.corsika_wlen_max)
	tabSimConf["corsika_wlen_min"] = np.float32(mcHeader.corsika_wlen_min)
	tabSimConf["detector_prog_id"] = np.uint64(mcHeader.detector_prog_id)
	tabSimConf["detector_prog_start"] = np.int32(mcHeader.detector_prog_start)
	tabSimConf["diffuse"] = np.int32(mcHeader.diffuse)
	tabSimConf["energy_range_max"] = np.float32(mcHeader.energy_range_max)
	tabSimConf["energy_range_min"] = np.float32(mcHeader.energy_range_min)
	tabSimConf["injection_height"] = np.float32(mcHeader.injection_height)
	tabSimConf["max_alt"] = np.float32(mcHeader.max_alt)
	tabSimConf["max_az"] = np.float32(mcHeader.max_az)
	tabSimConf["max_scatter_range"] = np.float32(mcHeader.max_scatter_range)
	tabSimConf["max_viewcone_radius"] = np.float32(mcHeader.max_viewcone_radius)
	tabSimConf["min_alt"] = np.float32(mcHeader.min_alt)
	tabSimConf["min_az"] = np.float32(mcHeader.min_az)
	tabSimConf["min_scatter_range"] = np.float32(mcHeader.min_scatter_range)
	tabSimConf["min_viewcone_radius"] = np.float32(mcHeader.min_viewcone_radius)
	tabSimConf["num_showers"] = np.uint64(mcHeader.num_showers)
	tabSimConf["obs_id"] = np.uint64(evt.r0.obs_id)
	tabSimConf["prod_site_B_declination"] = np.float32(mcHeader.prod_site_B_declination)
	tabSimConf["prod_site_B_inclination"] = np.float32(mcHeader.prod_site_B_inclination)
	tabSimConf["prod_site_B_total"] = np.float32(mcHeader.prod_site_B_total)
	tabSimConf["prod_site_alt"] = np.float32(mcHeader.prod_site_alt)
	tabSimConf["run_array_direction"] = np.float32(mcHeader.run_array_direction)
	tabSimConf["shower_prog_id"] = np.uint64(mcHeader.shower_prog_id)
	tabSimConf["shower_prog_start"] = np.int32(mcHeader.shower_prog_start)
	tabSimConf["shower_reuse"] = np.uint64(mcHeader.shower_reuse)
	tabSimConf["simtel_version"] = np.int32(mcHeader.simtel_version)
	tabSimConf["spectral_index"] = np.float32(mcHeader.spectral_index)
	
	tabSimConf.append()


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


def appendCorsikaEvent(tableMcCorsikaEvent, event):
	'''
	Append the Monte Carlo informations in the table of Corsika events
	------
	Parameter :
		tableMcCorsikaEvent : table of Corsika events to be completed
		event : Monte Carlo event to be used
	'''
	tabMcEvent = tableMcCorsikaEvent.row
	tabMcEvent['event_id'] = np.uint64(event.r0.event_id)
	tabMcEvent['mc_az'] = np.float32(event.mc.az)
	tabMcEvent['mc_alt'] = np.float32(event.mc.alt)
	
	tabMcEvent['mc_core_x'] = np.float32(event.mc.core_x)
	tabMcEvent['mc_core_y'] = np.float32(event.mc.core_y)
	
	tabMcEvent['mc_energy'] = np.float32(event.mc.energy)
	tabMcEvent['mc_h_first_int'] = np.float32(event.mc.h_first_int)
	tabMcEvent['mc_shower_primary_id'] = np.uint8(event.mc.shower_primary_id)
	
	tabMcEvent['mc_x_max'] = np.float32(event.mc.x_max)
	
	tabMcEvent['obs_id'] = np.uint64(event.r0.obs_id)
	
	#I don't know where to find the following informations but they exist in C version
	#tabMcEvent['depthStart'] = np.float32(0.0)
	#tabMcEvent['hmax'] = np.float32(0.0)
	#tabMcEvent['emax'] = np.float32(0.0)
	#tabMcEvent['cmax'] = np.float32(0.0)
	
	tabMcEvent.append()


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
	tabWaveformHi['waveformHi'] = np.swapaxes(waveform[0], 0, 1)
	tabWaveformHi.append()
	
	if waveform.shape[0] > 1:
		tabWaveformLo = telNode.waveformLo.row
		tabWaveformLo['waveformLo'] = np.swapaxes(waveform[1], 0, 1)
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
		#print('waveform.shape:', waveform.shape)
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

