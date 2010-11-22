import sys

if sys.platform == 'darwin':
    __import__('pkg_resources').declare_namespace(__name__)
