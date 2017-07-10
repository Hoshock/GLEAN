import os
from .lib import *

if not os.path.exists(glean.Glean.OUT_DIR):
	os.mkdir(glean.Glean.OUT_DIR)
