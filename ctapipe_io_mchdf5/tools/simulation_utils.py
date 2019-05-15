
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



