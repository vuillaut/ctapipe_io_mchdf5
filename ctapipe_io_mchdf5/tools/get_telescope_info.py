
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


