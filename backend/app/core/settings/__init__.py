import os
from typing import Type, Union

from .base import BaseAppSettings
from .development import DevelopmentSettings

# For now, we'll just use development settings
settings = DevelopmentSettings() 