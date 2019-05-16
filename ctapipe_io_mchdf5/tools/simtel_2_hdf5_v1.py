
# coding: utf-8

import tables
import numpy as np
from ctapipe.io import event_source
import argparse


def getNbTel(event):
	'''
	Get the number of telescopes in the run
	'''
	nbTel = event.inst.subarray.num_tels
	return nbTel


def getTelescopeInfoFromEvent(source, telescope_info, max_nb_tel): 
	source.back_seekable = True
	for evt in source:
		if max_nb_tel == 0:
			max_nb_tel = getNbTel(evt)
		
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


def createRunHeader(fileh, evt0):
	'''
	Create the run header as a group in hdf5
	------
	Parameter :
		fileh : hdf5 file to be used
		evt0 : first event of a simtel file
	'''
	runHeaderGroup = fileh.create_group("/", 'RunHeader', 'Header of the run')
	
	nbTel = getNbTel(evt0)
	
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
	

def createCosrika(fileh, event):
	'''
	Create the corsika data as a group in hdf5
	------
	Parameter :
		fileh : hdf5 file to be used
		event : first event of a simtel file
	'''
	corsikaGroup = fileh.create_group("/", 'Corsika', 'Simulated event properties')
	
	#Find the appropriate values in simtel
	targetName = "Name of the corresponding target"
	altitudeMin = np.float32(event.mcheader.min_alt)
	altitudeMax = np.float32(event.mcheader.max_alt)
	azimuthMin = np.float32(event.mcheader.min_az)
	azimuthMax = np.float32(event.mcheader.max_az)
	isDiffuseMode = np.bool(event.mcheader.diffuse)
	
	coreMinX = np.float32(0.0)
	coreMaxX = np.float32(0.0)
	coreMinY = np.float32(0.0)
	coreMaxY = np.float32(0.0)
	nbUseShower = np.uint64(event.mcheader.shower_reuse)
	nbShower = np.uint64(event.mcheader.num_showers)
	
	run_array_direction = np.float32(event.mcheader.run_array_direction)
	corsika_version = np.uint64(event.mcheader.corsika_version)
	simtel_version = np.uint64(event.mcheader.simtel_version)
	energy_range_min = np.float32(event.mcheader.energy_range_min)
	energy_range_max = np.float32(event.mcheader.energy_range_max)
	prod_site_B_total = np.float32(event.mcheader.prod_site_B_total)
	prod_site_B_declination = np.float32(event.mcheader.prod_site_B_declination)
	prod_site_B_inclination = np.float32(event.mcheader.prod_site_B_inclination)
	prod_site_alt = np.float32(event.mcheader.prod_site_alt)
	prod_site_array = np.array(list(event.mcheader.prod_site_array))
	prod_site_coord = np.array(list(event.mcheader.prod_site_coord))
	prod_site_subarray = np.array(list(event.mcheader.prod_site_subarray))
	spectral_index = np.float32(event.mcheader.spectral_index)
	shower_prog_start = np.float64(event.mcheader.shower_prog_start)
	shower_prog_id = np.uint64(event.mcheader.shower_prog_id)
	detector_prog_start = np.float64(event.mcheader.detector_prog_start)
	detector_prog_id = np.uint64(event.mcheader.detector_prog_id)
	max_viewcone_radius = np.float32(event.mcheader.max_viewcone_radius)
	min_viewcone_radius = np.float32(event.mcheader.min_viewcone_radius)
	max_scatter_range = np.float32(event.mcheader.max_scatter_range)
	min_scatter_range = np.float32(event.mcheader.min_scatter_range)
	core_pos_mode = event.mcheader.core_pos_mode
	injection_height = np.float32(event.mcheader.injection_height)
	atmosphere = np.uint64(event.mcheader.atmosphere)
	corsika_iact_options = event.mcheader.corsika_iact_options
	corsika_low_E_model = np.float32(event.mcheader.corsika_low_E_model)
	corsika_high_E_model = np.float32(event.mcheader.corsika_high_E_model)
	corsika_bunchsize = np.float64(event.mcheader.corsika_bunchsize)
	corsika_wlen_min = np.float64(event.mcheader.corsika_wlen_min)
	corsika_wlen_max = np.float64(event.mcheader.corsika_wlen_max)
	corsika_low_E_detail = np.float64(event.mcheader.corsika_low_E_detail)
	corsika_high_E_detail = np.float64(event.mcheader.corsika_high_E_detail)
	
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
	fileh.create_array(corsikaGroup, 'nbShower', nbShower, "Number of showers")
	
	fileh.create_array(corsikaGroup, 'run_array_direction', run_array_direction, "the tracking/pointing direction in [radians].\nDepending on 'tracking_mode' this either\ncontains: [0]=Azimuth, [1]=Altitude in mode 0,\nOR [0]=R.A., [1]=Declination in mode 1")
	fileh.create_array(corsikaGroup, 'corsika_version', corsika_version, "CORSIKA version * 1000")
	fileh.create_array(corsikaGroup, 'simtel_version', simtel_version, "sim_telarray version * 1000")
	fileh.create_array(corsikaGroup, 'energy_range_min', energy_range_min, "Lower limit of energy range of primary particle [TeV]")
	fileh.create_array(corsikaGroup, 'energy_range_max', energy_range_max, "Upper limit of energy range of primary particle [TeV]")
	fileh.create_array(corsikaGroup, 'prod_site_B_total', prod_site_B_total, "total geomagnetic field [uT]")
	fileh.create_array(corsikaGroup, 'prod_site_B_declination', prod_site_B_declination, "magnetic declination [rad]")
	fileh.create_array(corsikaGroup, 'prod_site_B_inclination', prod_site_B_inclination, "magnetic inclination [rad]")
	fileh.create_array(corsikaGroup, 'prod_site_alt', prod_site_alt, "height of observation level [m]")
	fileh.create_array(corsikaGroup, 'prod_site_array', prod_site_array, "site array")
	fileh.create_array(corsikaGroup, 'prod_site_coord', prod_site_coord, "site (long., lat.) coordinates")
	fileh.create_array(corsikaGroup, 'prod_site_subarray', prod_site_subarray, "site subarray")
	fileh.create_array(corsikaGroup, 'spectral_index', spectral_index, "Power-law spectral index of spectrum")
	fileh.create_array(corsikaGroup, 'shower_prog_start', shower_prog_start, "Time when shower simulation started, CORSIKA: only date")
	fileh.create_array(corsikaGroup, 'shower_prog_id', shower_prog_id, "CORSIKA=1, ALTAI=2, KASCADE=3, MOCCA=4")
	fileh.create_array(corsikaGroup, 'detector_prog_start', detector_prog_start, "Time when detector simulation started")
	fileh.create_array(corsikaGroup, 'detector_prog_id', detector_prog_id, "simtelarray=1")
	fileh.create_array(corsikaGroup, 'max_viewcone_radius', max_viewcone_radius, "Maximum viewcone radius [deg]")
	fileh.create_array(corsikaGroup, 'min_viewcone_radius', min_viewcone_radius, "Minimum viewcone radius [deg]")
	fileh.create_array(corsikaGroup, 'max_scatter_range', max_scatter_range, "Maximum scatter range [m]")
	fileh.create_array(corsikaGroup, 'min_scatter_range', min_scatter_range, "Maximum scatter range [m]")
	fileh.create_array(corsikaGroup, 'core_pos_mode', core_pos_mode, "Core Position Mode (fixed/circular/...)")
	fileh.create_array(corsikaGroup, 'injection_height', injection_height, "Height of particle injection [m]")
	fileh.create_array(corsikaGroup, 'atmosphere', atmosphere, "Atmospheric model number")
	fileh.create_array(corsikaGroup, 'corsika_iact_options', corsika_iact_options, "Detector MC information")
	fileh.create_array(corsikaGroup, 'corsika_low_E_model', corsika_low_E_model, "Detector MC information")
	fileh.create_array(corsikaGroup, 'corsika_high_E_model', corsika_high_E_model, "Detector MC information")
	fileh.create_array(corsikaGroup, 'corsika_bunchsize', corsika_bunchsize, "Number of photons per bunch")
	fileh.create_array(corsikaGroup, 'corsika_wlen_min', corsika_wlen_min, "Minimum wavelength of cherenkov light [nm]")
	fileh.create_array(corsikaGroup, 'corsika_wlen_max', corsika_wlen_max, "Maximum wavelength of cherenkov light [nm]")
	fileh.create_array(corsikaGroup, 'corsika_low_E_detail', corsika_low_E_detail, "Detector MC information")
	fileh.create_array(corsikaGroup, 'corsika_high_E_detail', corsika_high_E_detail, "Detector MC information")
	
	#Create the table of cosrika event(+shower)
	tableMcCorsikaEvent = fileh.create_table(corsikaGroup, 'tabCorsikaEvent', MCCorsikaEvent, "Table of all monte carlo event")
	#Do something with it
	return tableMcCorsikaEvent


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


def createGroupOfAllTelescope(fileh, nbTel, evt0, telInfo_from_evt, listTelescopeLayout):
	'''
	Create the group of all the telescope data
	------------------
	Parameters :
		fileh : HDF5 file to be completed
		nbTel : number of telescopes
		evt0 : first event of simtel data
		listTelescopeLayout : layout to be used to select the telescopes
	'''
	dicoTelInfo = evt0.inst.subarray.tel
	
	for telIndexIter in range(0, nbTel):
		telIndex = np.uint64(telIndexIter)
		telId = np.uint64(telIndex + 1)
		if len(listTelescopeLayout) != 0:
			if not telId in listTelescopeLayout:
				continue
		
		telInfo = dicoTelInfo[telIndexIter + 1]
		#Maybe, we have to do some thing with this to avoid trouble due to this stupid thing
		cameraRotation = telInfo.camera.cam_rotation.value
		
		telGroup = fileh.create_group("/Tel", 'Tel_' + str(telIndexIter), 'Telescopes ' + str(telIndexIter))

		telType = np.uint64(getCameraTypeFromName(telInfo.camera.cam_id))
		
		
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
			
			columns_dict_event_id  = {"eventId": tables.UInt64Col()}
			columns_dict_timestamp = {"timestamp": tables.Float64Col()}
			columns_dict_waveform  = {"waveform": tables.UInt16Col(shape=image_shape)}
			columns_dict_photo_electron_image  = {"photo_electron_image": tables.Int32Col(shape=nbPixel)}
			
			description_event_id = type('description event_id', (tables.IsDescription,), columns_dict_event_id)
			description_timestamp = type('description timestamp', (tables.IsDescription,), columns_dict_timestamp)
			description_waveform = type('description columns_dict_waveform', (tables.IsDescription,), columns_dict_waveform)
			description_dict_photo_electron_image = type('description columns_dict_photo_electron_image', (tables.IsDescription,), columns_dict_photo_electron_image)
			
			fileh.create_table(telGroup, 'eventId', description_event_id, "Table of event id")
			fileh.create_table(telGroup, 'timestamp', description_timestamp, "Table of timestamp")
			fileh.create_table(telGroup, 'waveform', description_waveform, "Table of waveform")
			fileh.create_table(telGroup, 'photo_electron_image', description_dict_photo_electron_image, "Table of pure signal recorded by the camera")


def appendWaveformInTelescope(telNode, waveform, eventId, timeStamp, photo_electron_image):
	'''
	Append a waveform signal (to be transposed) into a telescope node
	-------------------
	Parameters :
		telNode : telescope node to be used
		waveform : waveform signal to be used
		eventId : id of the corresponding event
		timeStamp : time of the event in UTC
		photo_electron_image : image of pure signal recorded by the camera
	'''
	#We transpose the waveform :
	tabEventId = telNode.eventId.row
	tabEventId['eventId'] = eventId
		
	tabTimestamp = telNode.timestamp.row
	tabTimestamp['timestamp'] = timeStamp
	   
	tabWaveform = telNode.waveform.row
	tabWaveform['waveform'] = np.swapaxes(waveform, 1, 2)
	
	tabPhotoElectronImage = telNode.photo_electron_image.row
	tabPhotoElectronImage['photo_electron_image'] = photo_electron_image
	
	tabEventId.append()
	tabTimestamp.append()
	tabWaveform.append()
	tabPhotoElectronImage.append()


def appendEventTelescopeData(fileh, event, listTelescopeLayout):
	'''
	Append data from event in telescopes
	--------------
	Parameters :
		fileh : HDF5 file to be used
		event : current event
		listTelescopeLayout : layout to be used to select the telescopes
	'''
	tabTelWithData = event.r0.tels_with_data
	dicoTel = event.r0.tel
	for telId in tabTelWithData:
		if len(listTelescopeLayout) != 0:
			if not telId in listTelescopeLayout:
				continue
		
		waveform = dicoTel[telId].waveform
		photo_electron_image = event.mc.tel[telId].photo_electron_image
		#print('waveform.shape:', waveform.shape)
		telNode = fileh.get_node("/Tel", 'Tel_' + str(telId - 1))
		appendWaveformInTelescope(telNode, waveform, event.r0.event_id, event.trig.gps_time.value, photo_electron_image)


def initialisationGeneric(fileh, event, telInfo_from_evt, listTelescopeLayout):
	nbTel = getNbTel(event)
	print("Number of telescope : ",nbTel)
	createRunHeader(fileh, event)
	#We can set the Monte Carlo values durring the iteration on source
	print('createCosrika')
	nodeMcCorsikaEvent = createCosrika(fileh, event)
	tableMcCorsikaEvent = nodeMcCorsikaEvent.row
	
	#Create the group of all telescopes
	allTelGroup = fileh.create_group("/", 'Tel', 'Telescopes data')
	#Create all the telescopes in the /Tel group
	print('createGroupOfAllTelescope start')
	createGroupOfAllTelescope(fileh, nbTel, event, telInfo_from_evt, listTelescopeLayout)
	print('createGroupOfAllTelescope done')
	return nodeMcCorsikaEvent, tableMcCorsikaEvent, allTelGroup


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help="simtel r1 input file",
						required=True)
	parser.add_argument('-o', '--output', help="hdf5 r1 output file",
						required=True)
	
	parser.add_argument('-l', '--layout', help="hdf5 r1 layout file to select telescope to be converted",
						required=False)
	
	parser.add_argument('-m', '--max_event', help="maximum event to reconstuct",
						required=False, type=int)
	args = parser.parse_args()
	
	nb_event = 0
	max_event = 10000000
	listTelescopeLayout = []
	if args.max_event != None:
		max_event = int(args.max_event)
	
	if args.layout != None:
		with open(args.layout, 'r') as filehandle:  
			for line in filehandle:
				# remove linebreak which is the last character of the string
				currentPlace = line[:-1]
				listTelescopeLayout.append(int(currentPlace))
		
		print("Use layout file : '"+args.layout+"'", "which select telescopes :")
		print("Use layout of ",len(listTelescopeLayout), "telescopes :",listTelescopeLayout)
		if len(listTelescopeLayout) == 0:
			print("The layout cannot be empty!!!")
			sys.exit(-1) 
	else:
		print("No layout used")
	
	zstdFilter = tables.Filters(complevel=6, complib='blosc:zstd', shuffle=False, bitshuffle=False, fletcher32=False)
	fileh = tables.open_file(args.output, mode = "w", filters=zstdFilter)
	
	source = event_source(args.input)
	telInfo_from_evt = dict() # Key is tel id, value (ref_shape, slice, ped, gain)
	nbTel = 0
	getTelescopeInfoFromEvent(source, telInfo_from_evt, nbTel)
	source = event_source(args.input)
	
	for i,event in enumerate(source):
		source.back_seekable = True
		if i == 0:
			#We do all the stuff for one event
			nodeMcCorsikaEvent, tableMcCorsikaEvent, allTelGroup = initialisationGeneric(fileh, event, telInfo_from_evt, listTelescopeLayout)
		
		#I found the timestamp
		eventTimeStamp = np.float64(event.trig.gps_time.value)
		obsId = event.r0.obs_id
		eventId = event.r0.event_id
		appendCorsikaEvent(tableMcCorsikaEvent, event)
		appendEventTelescopeData(fileh, event, listTelescopeLayout)
		nb_event+=1
		print("{} / {}".format(nb_event, max_event), end="\r")
		if nb_event >= max_event:
			break
	
	nodeMcCorsikaEvent.flush()
	fileh.close()
	print("Processing of",nb_event,"events => Done")


if __name__ == '__main__':
	main()

