
from ctapipe.io import event_source

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



