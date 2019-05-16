
import tables
import numpy as np
import argparse


def createTelescopeMinSelectionNode(outFile, telNode):
	'''
	Create the telescope group and table
	It is important not to add an other dataset with the type of the camera to simplify the serach of a telescope by telescope index in the file structure
	Parameters:
	-----------
		outFile : HDF5 file to be used
		telNode : telescope node to be copied
	'''
	telGroupName = telNode._v_name
	camTelGroup = hfile.create_group("/r1", telGroupName, 'Data of telescopes '+telGroupName)
	
	outFile.copy_node(telNode.nbPixel, newparent=camTelGroup, recursive=True)
	outFile.copy_node(telNode.nbSlice, newparent=camTelGroup, recursive=True)
	outFile.copy_node(telNode.nbGain, newparent=camTelGroup, recursive=True)
	outFile.copy_node(telNode.telIndex, newparent=camTelGroup, recursive=True)
	outFile.copy_node(telNode.telType, newparent=camTelGroup, recursive=True)
	outFile.copy_node(telNode.telId, newparent=camTelGroup, recursive=True)
	try:
		outFile.copy_node(telNode.tabRefShape, newparent=camTelGroup, recursive=True)
	except Exception as e:
		print(e)
	try:
		outFile.copy_node(telNode.tabGain, newparent=camTelGroup, recursive=True)
	except Exception as e:
		print(e)
		
	outFile.copy_node(telNode.trigger, newparent=camTelGroup, recursive=True)
	outFile.copy_node(telNode.pedestal, newparent=camTelGroup, recursive=True)
	outFile.copy_node(telNode.photo_electron_image, newparent=camTelGroup, recursive=True)
	
	#columns_dict_waveform  = {"waveformHi": tables.UInt16Col(shape=image_shape)}
	#description_waveform = type('description columns_dict_waveform', (tables.IsDescription,), columns_dict_waveform)
	#hfile.create_table(camTelGroup, 'waveformHi', description_waveform, "Table of waveform of the high gain signal", chunkshape=chunkshape)
	
	#if nbGain > 1:
		#columns_dict_waveformLo  = {"waveformLo": tables.UInt16Col(shape=image_shape)}
		#description_waveformLo = type('description columns_dict_waveformLo', (tables.IsDescription,), columns_dict_waveformLo)
		#hfile.create_table(camTelGroup, 'waveformLo', description_waveformLo, "Table of waveform of the low gain signal", chunkshape=chunkshape)


def createAllTelescopeMinSelected(outFile, inFile, nbEventPerMin):
	'''
	Create all the telescope with the minimum selection
	Parameters:
	-----------
		outFile : output file
		inFile : input file
		nbEventPerMin : number of events to be used to compute one minimum
	'''
	for telNode in inFile.walk_nodes("/r1", "Group"):
		createTelescopeMinSelectionNode(outFile, telNode)


def processMinSelection(inputFileName, outputFileName, nbEventPerMin):
	'''
	Process the minimum selection
	Parameters:
	-----------
		inputFileName : name of the input file
		outputFileName : name of the output file
		nbEventPerMin : number of events to be used to compute one minimum
	'''
	inFile = tables.open_file(inputFileName, "r")
	outFile = tables.open_file(outputFileName, "w", filters=inFile.filters)
	
	#Copy the instrument and simulation groups
	outFile.copy_node(inFile.root.instrument, newparent=outFile.root, recursive=True)
	outFile.copy_node(inFile.root.simulation, newparent=outFile.root, recursive=True)
	outFile.copy_node(inFile.root.r1, newparent=outFile.root, recursive=True)
	
	createAllTelescopeMinSelected(outFile, inFile, nbEventPerMin)
	
	inFile.close()
	outFile.close()


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help="hdf5 r1 v2 output file",
						required=True)
	parser.add_argument('-o', '--output', help="hdf5 r1 v2 output file",
						required=True)
	parser.add_argument('-n', '--nbeventpermin', help="Number of event to be used to compute the minimum",
						required=False, type=int)
	args = parser.parse_args()

	inputFileName = args.input
	outputFileName = args.output
	nbEventPerMin = args.nbeventpermin
	processMinSelection(inputFileName, outputFileName, nbEventPerMin)


if __name__ == '__main__':
	main()


