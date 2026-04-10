from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("steamlayer")
except PackageNotFoundError:
    __version__ = "dev"
