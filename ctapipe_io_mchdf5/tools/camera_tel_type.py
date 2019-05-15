
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

