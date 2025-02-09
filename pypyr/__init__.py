"""Initialize the pypyr package.

The most notable side-effect of importing this is package is that it adds a
NOTIFY (25) log level and notify() method to the global logger object.
"""
import pypyr.log.logger

__version__ = "5.8.0"

pypyr.log.logger.set_up_notify_log_level()
