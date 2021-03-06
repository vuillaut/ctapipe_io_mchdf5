"""
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
"""

import tables
from .get_telescope_info import *


class SubarrayLayout(tables.IsDescription):
	"""
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
	"""
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


class OpticDescription(tables.IsDescription):
	"""
	Describe the optic of the all the telescopes
	Attributes:
	-----------
		description : description of the telescope optic (one mirror, two, etc)
		name : name of the optic
		type : type of the optic
		mirror_area : area of the mirror in meters square
		num_mirror_tiles : number of mirrors tiles
		equivalent_focal_length : equivalent focal lenght of the mirror in meters
		camera_rotation : rotation [rad] of the camera
		pixel_rotation : rotation [rad] of the angel
	"""
	description = tables.StringCol(14, dflt=b'')
	name = tables.StringCol(5, dflt=b'')
	type = tables.StringCol(3, dflt=b'')
	mirror_area = tables.Float32Col()
	num_mirrors = tables.UInt64Col()
	num_mirror_tiles = tables.UInt64Col()
	equivalent_focal_length = tables.Float32Col(shape=(), dflt=0.0, pos=6)
	cam_rotation = tables.Float32Col()
	pix_rotation = tables.Float32Col()


class CameraGeometry(tables.IsDescription):
	"""
	Camera geometry
	"""
	pix_id = tables.UInt64Col()
	pix_x = tables.Float32Col()
	pix_y = tables.Float32Col()
	pix_area = tables.Float32Col()


class CameraReadOut(tables.IsDescription):
	"""
	Pulse reference shape
	"""
	reference_pulse_shape_channel0 = tables.Float32Col()
	reference_pulse_shape_channel1 = tables.Float32Col()
	reference_pulse_sample_time = tables.Float32Col()


def fill_subarray_layout(hfile, telInfo_from_evt, nbTel):
	"""
	Fill the subarray informations
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
		nbTel : number of telescope in the run
	"""
	tableSubarrayLayout = hfile.root.configuration.instrument.subarray.layout
	tabSubLayout = tableSubarrayLayout.row
	
	for telIndexIter in range(0, nbTel):
		telId = telIndexIter + 1
		if telId in telInfo_from_evt:
			telInfo = telInfo_from_evt[telId]
			telType = telInfo[TELINFO_TELTYPE]
			camera_name = get_camera_name_from_type(telType)
			telTypeStr = get_telescope_type_str_from_camera_type(telType)
			
			tabSubLayout["tel_id"] = np.uint64(telId)
			tabSubLayout["pos_x"] = np.float32(telInfo[TELINFO_TELPOSX])
			tabSubLayout["pos_y"] = np.float32(telInfo[TELINFO_TELPOSY])
			tabSubLayout["pos_z"] = np.float32(telInfo[TELINFO_TELPOSZ])
			tabSubLayout["name"] = telInfo[TELINFO_TEL_NAME]
			tabSubLayout["type"] = telTypeStr
			tabSubLayout["type_id"] = np.uint64(telType)
			
			tabSubLayout["num_mirrors"] = np.uint64(telInfo[TELINFO_NBMIRROR])
			tabSubLayout["camera_type"] = camera_name
			tabSubLayout["tel_description"] = telTypeStr + '_' + telInfo[TELINFO_TEL_NAME] + '_' + camera_name
			tabSubLayout.append()
		else:
			tabSubLayout["tel_id"] = np.uint64(telId)
			tabSubLayout["pos_x"] = np.float32(0.0)
			tabSubLayout["pos_y"] = np.float32(0.0)
			tabSubLayout["pos_z"] = np.float32(0.0)
			tabSubLayout["name"] = ""
			tabSubLayout["type"] = ""
			tabSubLayout["type_id"] = np.uint64(7)
			
			tabSubLayout["num_mirrors"] = np.uint64(0)
			tabSubLayout["camera_type"] = ""
			tabSubLayout["tel_description"] = ""
			tabSubLayout.append()
	tableSubarrayLayout.flush()


def create_camera_table(hfile, telInfo):
	"""
	Create a table to describe a camera
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telInfo : table of some informations related to the telescope
	"""
	camera_name = get_camera_name_from_type(telInfo[TELINFO_TELTYPE])
	geometry_camera_name = 'geometry_' + camera_name
	readout_camera_name = 'readout_' + camera_name

	pix_x = np.asarray(telInfo[TELINFO_TABPIXELX], dtype=np.float32)
	pix_y = np.asarray(telInfo[TELINFO_TABPIXELY], dtype=np.float32)
	pix_area = np.asanyarray(telInfo[TELINFO_PIX_AREA], dtype=np.float32)

	# You can get it directly from telInfo if you complete the field from `get_telescope_info`
	pix_id = np.arange(0, pix_y.size, dtype=np.uint64)

	try:
		camera_telescope_table = hfile.create_table("/configuration/instrument/telescope/camera", geometry_camera_name,
													CameraGeometry, "Geometry of " + camera_name)

		camera_tel_row = camera_telescope_table.row
		for item in zip(pix_x, pix_y, pix_id, pix_area):
			camera_tel_row["pix_x"] = item[0]
			camera_tel_row["pix_y"] = item[1]
			camera_tel_row["pix_id"] = item[2]
			camera_tel_row["pix_area"] = item[3]

			camera_tel_row.append()

		info_ref_shape = telInfo[TELINFO_REFSHAPE]
		info_ref_pulse_time = telInfo[TELINFO_REF_PULSE_TIME]
		if info_ref_shape is not None:
			camera_readout_table = hfile.create_table("/configuration/instrument/telescope/camera", readout_camera_name,
													  CameraReadOut, "Reference shape of " + camera_name)
			camera_readout_table_row = camera_readout_table.row

			tab_ref_shape = np.asarray(info_ref_shape, dtype=np.float32)
			nb_sample = np.uint64(tab_ref_shape.shape[1])  # in cols

			tab_ref_pulse_time = np.asarray(info_ref_pulse_time, dtype=np.float32)
			for i in range(nb_sample):
				camera_readout_table_row['reference_pulse_shape_channel0'] = np.float32(tab_ref_shape[0, i])
				camera_readout_table_row['reference_pulse_sample_time'] = tab_ref_pulse_time[i]
				if telInfo[TELINFO_NBGAIN] == 2:
					camera_readout_table_row['reference_pulse_shape_channel1'] = np.float32(tab_ref_shape[1, i])

				camera_readout_table_row.append()

	except tables.exceptions.NodeError:
		pass


def create_instrument_dataset(hfile, telInfo_from_evt):
	"""
	Create the instrument dataset
	Parameters:
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
	"""
	# Group: configuration
	hfile.create_group('/', 'configuration', 'Simulation, telescope and subarray configuration.')
	# Group : configuration/instrument
	hfile.create_group('/configuration', 'instrument', 'Instrument information of the run')
	# Group : configuration/instrument/subarray
	subarray_group = hfile.create_group('/configuration/instrument', 'subarray', 'Subarray of the run')
	# Group : configuration/instrument/subarray/telescope
	telescope_group = hfile.create_group('/configuration/instrument', 'telescope', 'Telescope of the subarray')
	hfile.create_table(subarray_group, 'layout', SubarrayLayout, "Layout of the subarray")
	# Group : configuration/instrument/telescope/camera
	hfile.create_group("/configuration/instrument/telescope", 'camera', 'Cameras in the run')
	
	for telId, telInfo in telInfo_from_evt.items():
		create_camera_table(hfile, telInfo)
	
	hfile.create_table(telescope_group, 'optics', OpticDescription, "Describe the optic of the all the telescopes")


def fill_optic_description(hfile, telInfo_from_evt, nbTel):
	"""
	Fill the optic description table
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
		nbTel : number of telescope in the run
	"""
	
	tableOptic = hfile.root.configuration.instrument.telescope.optics
	tabOp = tableOptic.row
	for telIndexIter in range(0, nbTel):
		telId = telIndexIter + 1
		if telId in telInfo_from_evt:
			telInfo = telInfo_from_evt[telId]
			telType = telInfo[TELINFO_TELTYPE]
			
			camera_name = get_camera_name_from_type(telType)
			telTypeStr = get_telescope_type_str_from_camera_type(telType)
			
			tabOp["description"] = telTypeStr + '_' + telInfo[TELINFO_TEL_NAME] + '_' + camera_name
			tabOp["name"] = telInfo[TELINFO_TEL_NAME]
			tabOp["type"] = telTypeStr
			tabOp["mirror_area"] = np.float32(telInfo[TELINFO_MIRRORAREA])
			tabOp["num_mirrors"] = np.float32(telInfo[TELINFO_NBMIRROR])
			tabOp["num_mirror_tiles"] = np.float32(telInfo[TELINFO_NBMIRRORTILES])
			tabOp["equivalent_focal_length"] = np.float32(telInfo[TELINFO_FOCLEN])
			tabOp["cam_rotation"] = np.float32(telInfo[TEL_INFOR_CAMERA_ROTATION])
			tabOp["pix_rotation"] = np.float32(telInfo[TEL_INFOR_PIX_ROTATION])
			tabOp.append()
		else:
			tabOp["description"] = ""
			tabOp["name"] = ""
			tabOp["type"] = ""
			tabOp["mirror_area"] = np.float32(0.0)
			tabOp["num_mirrors"] = np.float32(0.0)
			tabOp["num_mirror_tiles"] = np.float32(0.0)
			tabOp["equivalent_focal_length"] = np.float32(1.0)
			tabOp["cam_rotation"] = np.float32(0.0)
			tabOp["pix_rotation"] = np.float32(0.0)
			tabOp.append()




