"""Script to start the application"""

import sys
import pyvcsshark.main

if __name__ == "__main__":
    try:
        pyvcsshark.start()
    except KeyboardInterrupt:
        print ("\n\nReceived Ctrl-C or other break signal. Exiting.")
        sys.exit(0)
