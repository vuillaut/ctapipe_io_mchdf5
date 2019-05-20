

def copyTelescopeWithoutWaveform(outFile, telNode, chunkshape=1):
	'''
	Copy the telescope node but not the waveform ones
	Parameters:
	-----------
		outFile : HDF5 file to be used
		telNode : telescope node to be copied
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	Return:
	-------
		created camera node
	'''
	telGroupName = telNode._v_name
	camTelGroup = outFile.create_group("/r1", telGroupName, 'Data of telescopes '+telGroupName)
	
	outFile.copy_node(telNode.nbPixel, newparent=camTelGroup, recursive=True)
	outFile.copy_node(telNode.nbSlice, newparent=camTelGroup, recursive=True)
	outFile.copy_node(telNode.nbGain, newparent=camTelGroup, recursive=True)
	outFile.copy_node(telNode.telIndex, newparent=camTelGroup, recursive=True)
	outFile.copy_node(telNode.telType, newparent=camTelGroup, recursive=True)
	outFile.copy_node(telNode.telId, newparent=camTelGroup, recursive=True)
	try:
		outFile.copy_node(telNode.tabRefShape, newparent=camTelGroup, recursive=True)
	except Exception as e:
		pass
	try:
		outFile.copy_node(telNode.tabGain, newparent=camTelGroup, recursive=True)
	except Exception as e:
		pass
		
	outFile.copy_node(telNode.trigger, newparent=camTelGroup, recursive=True)
	outFile.copy_node(telNode.pedestal, newparent=camTelGroup, recursive=True)
	try:
		outFile.copy_node(telNode.photo_electron_image, newparent=camTelGroup, recursive=True)
	except Exception as e:
		pass
	return camTelGroup
	



