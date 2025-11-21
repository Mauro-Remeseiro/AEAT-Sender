"""Utilidades para manejo de archivos XML."""

from pathlib import Path
from typing import Optional


def leer_xml(ruta: Path) -> str:
    """
    Lee el contenido de un fichero XML desde disco.
    
    Args:
        ruta: Ruta al fichero XML.
    
    Returns:
        Contenido del XML como string.
    
    Raises:
        FileNotFoundError: Si el fichero no existe.
        UnicodeDecodeError: Si hay problemas de codificación.
        IOError: Si hay otros errores de lectura.
    """
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def validar_xml(xml_contenido: str, xsd_path: Optional[Path] = None) -> bool:
    """
    Valida un XML contra un esquema XSD (opcional).
    
    Args:
        xml_contenido: Contenido del XML a validar.
        xsd_path: Ruta al fichero XSD. Si es None, solo valida que sea XML bien formado.
    
    Returns:
        True si el XML es válido, False en caso contrario.
    
    Raises:
        TODO: Implementar validación contra XSD de AEAT.
        Por ahora, solo valida que sea XML bien formado usando xml.etree.ElementTree.
    """
    import xml.etree.ElementTree as ET
    
    try:
        # Validar que es XML bien formado
        ET.fromstring(xml_contenido)
        
        # TODO: Si se proporciona xsd_path, validar contra el esquema XSD
        # Opciones:
        # 1. Usar lxml con XMLSchema
        # 2. Usar xmlschema (librería Python pura)
        # 3. Usar validación manual contra los XSDs de AEAT
        # 
        # Ejemplo con lxml:
        # from lxml import etree
        # schema = etree.XMLSchema(file=xsd_path)
        # doc = etree.parse(StringIO(xml_contenido))
        # return schema.validate(doc)
        
        if xsd_path is not None:
            # Por ahora, solo avisar que la validación XSD no está implementada
            pass
        
        return True
    except ET.ParseError as e:
        # XML mal formado
        return False

