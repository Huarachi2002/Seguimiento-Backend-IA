"""
Tests Package
=============

Estructura de tests siguiendo la arquitectura del proyecto.
"""

import pytest
import sys
from pathlib import Path

# Añadir el directorio raíz al path para imports
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
