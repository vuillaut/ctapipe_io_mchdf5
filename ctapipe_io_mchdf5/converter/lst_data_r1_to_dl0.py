# coding: utf-8

'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import tables
from ctapipe.io import event_source
import argparse

from ctapipe_io_mchdf5.tools.get_nb_tel import getNbTel
from ctapipe_io_mchdf5.tools.r1_file import *
from ctapipe_io_mchdf5.tools.r1_utils import *
# from ctapipe_io_mchdf5.tools.get_telescope_info import *
from ctapipe_io_mchdf5.tools.simulation_utils import *
from ctapipe_io_mchdf5.tools.instrument_utils import *
from ctapipe.calib import CameraCalibrator
from lstchain.calib.camera.calibrator import LSTCameraCalibrator
from lstchain.calib.camera.r0 import LSTR0Corrections
from lstchain.io import read_configuration_file, standard_config, replace_config
from traitlets.config.loader import Config
from lstchain.reco.volume_reducer import check_and_apply_volume_reduction
from lstchain.calib import load_gain_selector_from_config
from lstchain.calib.camera.calib import gain_selection


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
    parser.add_argument('-i', '--input', help="simtel input file",
                        required=True)
    parser.add_argument('-o', '--output', help="hdf5 r1 output file",
                        required=True)
    parser.add_argument('-m', '--max_event', help="maximum event to reconstruct",
                        required=False, type=int)
    parser.add_argument('-c', '--compression',
                        help="compression level for the output file [0 (No compression), 1 - 9]. Default = 6",
                        required=False, type=int, default='6')

    parser.add_argument('--config_file', '-conf', action='store', type=str,
                        dest='config_file',
                        help='Path to a configuration file. If none is given, a standard configuration is applied',
                        default=None
                        )

    parser.add_argument('--pedestal_path', '-pedestal', action='store', type=str,
                        dest='pedestal_path',
                        help='Path to a pedestal file',
                        default=None
                        )

    parser.add_argument('--calibration_path', '-calib', action='store', type=str,
                        dest='calibration_path',
                        help='Path to a calibration file',
                        default=None
                        )

    parser.add_argument('--time_calibration_path', '-time_calib', action='store', type=str,
                        dest='time_calibration_path',
                        help='Path to a calibration file for pulse time correction',
                        default=None
                        )

    args = parser.parse_args()

    inputFileName = args.input
    nbTel = getNbTel(inputFileName)
    print("Number of telescope : ", nbTel)

    # Increase the number of nodes in cache if necessary (avoid warning about nodes reopening)
    tables.parameters.NODE_CACHE_SLOTS = max(tables.parameters.NODE_CACHE_SLOTS, 3 * nbTel + 20)

    telInfo_from_evt, nbEvent = getTelescopeInfoFromEvent(inputFileName, nbTel)
    # For LST1, the first two and last two slices are removed during calibration
    telInfo_from_evt[1][1] = 36

    print("Found", nbEvent, "events")

    hfile = openOutputFile(args.output, compressionLevel=args.compression)

    print('Create file structure')
    tableMcCorsikaEvent = createFileStructure(hfile, telInfo_from_evt)

    print('Fill the subarray layout information')
    fillSubarrayLayout(hfile, telInfo_from_evt, nbTel)

    isSimulationMode = checkIsSimulationFile(telInfo_from_evt)

    if isSimulationMode:
        print('Fill the optic description of the telescopes')
        fillOpticDescription(hfile, telInfo_from_evt, nbTel)

        print('Fill the simulation header information')
        fillSimulationHeaderInfo(hfile, inputFileName)

    source = event_source(inputFileName, max_events=None)

    nb_event = 0
    # max_event = args.max_event
    if args.max_event != None:
        max_event = int(args.max_event)
    else:
        max_event = nbEvent

    if isSimulationMode:
        cal = CameraCalibrator()
    else:
        if args.config_file is not None:
                try:
                    custom_config = read_configuration_file(args.config_file)
                except("Custom configuration could not be loaded !!!"):
                    pass
                config = replace_config(standard_config, custom_config)
        else:
            config = standard_config

        r0_r1_calibrator = LSTR0Corrections(pedestal_path=args.pedestal_path,
                                            tel_id=1)

        r1_dl1_calibrator = LSTCameraCalibrator(calibration_path=args.calibration_path,
                                                time_calibration_path=args.time_calibration_path,
                                                extractor_product=config['image_extractor'],
                                                gain_threshold=Config(config).gain_selector_config['threshold'],
                                                config=Config(config),
                                                allowed_tels=[1],
                                                )

        gain_selector = load_gain_selector_from_config(config)

    print("\n")
    for event in source:
        if isSimulationMode:
            cal(event)
            appendCorsikaEvent(tableMcCorsikaEvent, event)

        else:
            r0_r1_calibrator.calibrate(event)
            r1_dl1_calibrator(event)
            # event.dl0.tel[1].waveform = event.dl0.tel[1].waveform[0]
            event.dl0.tel[1].waveform, gain_mask = gain_selector(event.dl0.tel[1].waveform)
            check_and_apply_volume_reduction(event, config)
            # for tel_id in event.r0.tels_with_data:
            #     event.dl0.tel[tel_id].waveform *= 100


        write_dl0(hfile, event)
        nb_event += 1
        print("\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r{} / {}".format(nb_event, max_event), end="")
        if nb_event >= max_event:
            break
    print("\nFlushing tables")
    if isSimulationMode:
        tableMcCorsikaEvent.flush()

    flushR1Tables(hfile)
    # move R1 to DL0 ;-)
    hfile.root.r1._f_move(newname='dl0')
    hfile.close()
    print('\nDone')



if __name__ == '__main__':
    main()
