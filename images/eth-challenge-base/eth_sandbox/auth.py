import os
import random

def get_shared_secret():
    return os.getenv("SHARED_SECRET", random.randbytes(32))
