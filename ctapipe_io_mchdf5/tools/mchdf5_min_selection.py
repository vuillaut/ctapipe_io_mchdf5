
import tables
import numpy as np
import argparse

if __name__ == '__main__':
	from min_selection_utils import createAllTelescopeMinSelected
else:
	from .min_selection_utils import createAllTelescopeMinSelected


def processMinSelectionTelescope(telNodeOut, telNodeIn, nbEventPerMin):
	'''
	Split the signal in minimum values and signal without minimum values
	Parameters:
	-----------
		telNodeOut : telescope from output file
		telNodeIn : telescope from input file
		nbEventPerMin : number of events to be used to compute one minimum
	'''
	
	


def processMinSelectionAllTelescope(outFile, inFile, nbEventPerMin):
	'''
	Split the signal in minimum values and signal without minimum values for all telescopes
	Parameters:
	-----------
		outFile : output file
		inFile : input file
		nbEventPerMin : number of events to be used to compute one minimum
	'''
	for telNodeIn, telNodeOut in zip(inFile.walk_nodes("/r1", "Group"), outFile.walk_nodes("/r1", "Group")):
		try:
			processMinSelectionTelescope(telNodeOut, telNodeIn, nbEventPerMin)
		except Exception as e:
			print(e)


def processMinSelection(inputFileName, outputFileName, nbEventPerMin, chunkshape=1):
	'''
	Process the minimum selection
	Parameters:
	-----------
		inputFileName : name of the input file
		outputFileName : name of the output file
		nbEventPerMin : number of events to be used to compute one minimum
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	inFile = tables.open_file(inputFileName, "r")
	outFile = tables.open_file(outputFileName, "w", filters=inFile.filters)
	
	#Copy the instrument and simulation groups
	outFile.copy_node(inFile.root.instrument, newparent=outFile.root, recursive=True)
	outFile.copy_node(inFile.root.simulation, newparent=outFile.root, recursive=True)
	
	createAllTelescopeMinSelected(outFile, inFile, nbEventPerMin, chunkshape=chunkshape)
	processMinSelectionAllTelescope(outFile, inFile, nbEventPerMin)
	
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


