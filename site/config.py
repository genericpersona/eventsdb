# -*- coding: utf-8 -*-

import multiprocessing as mp
import os

# Statement for enabling the development environment
DEBUG = True

# Define the application directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define the mongodb database
MONGO_DBNAME = "eventsdb"

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other
THREADS_PER_PAGE = 2 * mp.cpu_count()

# Default maximum number of events per page
LIMIT_PER_PAGE = 25

# Enable protection against CSRF
CSRF_ENABLED = True

# CSRF signing key
CSRF_SESSION_KEY = "3d\xec|\x12\x95\xff\xb9\x03N9$v+\xa3\t\xdc\xd5]\xfb7(\xd6y"

# Cookie signing key
SECRET_KEY = "\xf3R\xd8\x1e5\xbc\x12\to\xc6f\xd33\x1f>D\xd4\xda\xbb\xa1\x02\x9f\xb1\xf7"
