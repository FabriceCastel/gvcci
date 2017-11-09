from config import get_args

logs_enabled = not get_args()['print_output']

def log(str):
	if (logs_enabled):
		print(str)