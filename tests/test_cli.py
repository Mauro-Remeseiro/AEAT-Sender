"""Tests para el módulo cli.py."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from aeat_sender.cli import parse_args, main, EXIT_SUCCESS, EXIT_ARGUMENT_ERROR


def test_parse_args_minimal():
    """Test del parseo de argumentos mínimos."""
    args = parse_args([
        "--sistema", "SII",
        "--entorno", "pruebas",
        "--input", "entrada.xml",
        "--output", "salida.xml",
    ])
    
    assert args.sistema.upper() == "SII"
    assert args.entorno == "pruebas"
    assert args.input == Path("entrada.xml")
    assert args.output == Path("salida.xml")
    assert args.config is None
    assert args.debug is False


def test_parse_args_completo():
    """Test del parseo de argumentos completos."""
    args = parse_args([
        "--sistema", "VERIFACTU",
        "--entorno", "produccion",
        "--input", "C:/ruta/entrada.xml",
        "--output", "C:/ruta/salida.xml",
        "--config", "mi_config.json",
        "--debug",
    ])
    
    assert args.sistema.upper() == "VERIFACTU"
    assert args.entorno == "produccion"
    assert args.config == Path("mi_config.json")
    assert args.debug is True


def test_parse_args_case_insensitive():
    """Test que el sistema acepta mayúsculas y minúsculas."""
    args = parse_args([
        "--sistema", "sii",
        "--entorno", "pruebas",
        "--input", "entrada.xml",
        "--output", "salida.xml",
    ])
    
    assert args.sistema.upper() == "SII"


# TODO: Añadir más tests para main() cuando se complete la implementación
# - Test con configuración válida
# - Test con fichero de entrada inexistente
# - Test con error de comunicación
# - Test con éxito completo

