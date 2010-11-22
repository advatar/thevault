"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""
import sys
from multiprocessing import freeze_support

if sys.platform == "win32":
    from launcherwindows import main
elif sys.platform == "linux2":
    from launcherubuntu import main
elif sys.platform == "darwin":
    import launcherosx

if __name__ == "__main__":
    freeze_support()
    main()
