"""Tests para el módulo xml_handler.py."""

import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
import xml.etree.ElementTree as ET

from aeat_sender.xml_handler import leer_xml, validar_xml


def test_leer_xml():
    """Test de lectura de fichero XML."""
    # Crear fichero temporal con contenido XML válido
    with NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?><root><test>contenido</test></root>')
        temp_path = Path(f.name)
    
    try:
        contenido = leer_xml(temp_path)
        assert "<root>" in contenido
        assert "contenido" in contenido
    finally:
        temp_path.unlink()


def test_leer_xml_inexistente():
    """Test que lanza excepción si el fichero no existe."""
    with pytest.raises(FileNotFoundError):
        leer_xml(Path("fichero_que_no_existe.xml"))


def test_validar_xml_bien_formado():
    """Test de validación de XML bien formado."""
    xml_valido = '<?xml version="1.0" encoding="UTF-8"?><root><test>contenido</test></root>'
    
    assert validar_xml(xml_valido) is True


def test_validar_xml_mal_formado():
    """Test de validación de XML mal formado."""
    xml_invalido = '<root><test>contenido</test>'  # Falta cierre de root
    
    assert validar_xml(xml_invalido) is False


# TODO: Añadir tests de validación contra XSD cuando se implemente
# def test_validar_xml_con_xsd():
#     """Test de validación contra XSD."""
#     xml_contenido = '<?xml version="1.0"?><root><test>contenido</test></root>'
#     xsd_path = Path("esquema.xsd")
#     
#     # Mock o fichero XSD real para test
#     resultado = validar_xml(xml_contenido, xsd_path)
#     assert resultado is True or False según el caso

