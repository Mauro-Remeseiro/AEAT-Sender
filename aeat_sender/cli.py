"""Interfaz de línea de comandos para aeat-sender."""

import argparse
import sys
from pathlib import Path

from aeat_sender import __version__
from aeat_sender.config import Config, ConfigError
from aeat_sender.logging_config import setup_logging
from aeat_sender.xml_handler import leer_xml
from aeat_sender.soap_client import (
    enviar_xml,
    AeatConfigError,
    AeatCertificateError,
    AeatCommunicationError,
    AeatFunctionalError,
)


# Códigos de salida
EXIT_SUCCESS = 0
EXIT_ARGUMENT_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_FILE_ERROR = 3
EXIT_COMMUNICATION_ERROR = 4
EXIT_AEAT_ERROR = 5


ASCII_LOGO = """
===============================================================
                                                              
                    AEAT - SENDER                             
                                                              
    CLI para envio de XML a servicios SOAP de la AEAT        
    (SII y VeriFactu)                                         
                                                              
===============================================================
"""


def parse_args() -> argparse.Namespace:
    """Parsea los argumentos de la línea de comandos."""
    parser = argparse.ArgumentParser(
        description=f"{ASCII_LOGO}\nEnvía XML a los servicios web SOAP de la AEAT (SII o VeriFactu)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--sistema",
        required=True,
        choices=["SII", "VERIFACTU", "sii", "verifactu"],
        help="Sistema a utilizar: SII o VERIFACTU (case-insensitive)",
    )
    
    parser.add_argument(
        "--entorno",
        required=True,
        choices=["pruebas", "produccion"],
        help="Entorno a utilizar: pruebas o produccion",
    )
    
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Ruta al fichero XML de entrada",
    )
    
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Ruta al fichero XML de salida",
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Ruta al fichero de configuración (por defecto: config.json en el directorio del ejecutable)",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Activa el nivel de logging DEBUG",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Muestra la versión de aeat-sender y termina",
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Función principal de la CLI.
    
    Returns:
        Código de salida (0 = éxito, otros = error)
    """
    try:
        args = parse_args()
    except SystemExit:
        return EXIT_ARGUMENT_ERROR
    
    # Configurar logging
    log_level = "DEBUG" if args.debug else "INFO"
    logger = setup_logging(log_level)
    
    logger.info("=" * 60)
    logger.info("Iniciando aeat-sender")
    logger.info(f"Sistema: {args.sistema.upper()}")
    logger.info(f"Entorno: {args.entorno}")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    
    # Cargar configuración
    try:
        config_path = args.config
        if config_path is None:
            # Por defecto, buscar config.json junto al ejecutable o en el directorio actual
            if getattr(sys, 'frozen', False):
                # Ejecutable compilado con PyInstaller
                config_path = Path(sys.executable).parent / "config.json"
            else:
                # Ejecución desde código fuente
                config_path = Path(__file__).parent.parent / "config.json"
        
        config = Config.cargar(config_path)
        logger.info(f"Configuración cargada desde: {config_path}")
    except ConfigError as e:
        logger.error(f"Error cargando configuración: {e}", exc_info=True)
        print(f"Error: No se pudo cargar la configuración: {e}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    except Exception as e:
        logger.error(f"Error inesperado cargando configuración: {e}", exc_info=True)
        print(f"Error inesperado: {e}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    
    # Validar y leer XML de entrada
    try:
        if not args.input.exists():
            raise FileNotFoundError(f"El fichero de entrada no existe: {args.input}")
        
        xml_contenido = leer_xml(args.input)
        logger.info(f"XML de entrada leído correctamente ({len(xml_contenido)} caracteres)")
    except FileNotFoundError as e:
        logger.error(f"Error accediendo al fichero de entrada: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_FILE_ERROR
    except Exception as e:
        logger.error(f"Error leyendo XML de entrada: {e}", exc_info=True)
        print(f"Error leyendo XML: {e}", file=sys.stderr)
        return EXIT_FILE_ERROR
    
    # Enviar XML a AEAT
    try:
        sistema = args.sistema.upper()
        logger.info(f"Enviando XML a AEAT (sistema={sistema}, entorno={args.entorno})")
        
        xml_respuesta = enviar_xml(sistema, args.entorno, xml_contenido, config)
        
        logger.info(f"Respuesta recibida de AEAT ({len(xml_respuesta)} caracteres)")
    except AeatConfigError as e:
        logger.error(f"Error de configuración: {e}", exc_info=True)
        print(f"Error de configuración: {e}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    except AeatCertificateError as e:
        logger.error(f"Error con el certificado: {e}", exc_info=True)
        print(f"Error con el certificado: {e}", file=sys.stderr)
        return EXIT_COMMUNICATION_ERROR
    except AeatCommunicationError as e:
        logger.error(f"Error de comunicación con AEAT: {e}", exc_info=True)
        print(f"Error de comunicación con AEAT: {e}", file=sys.stderr)
        return EXIT_COMMUNICATION_ERROR
    except AeatFunctionalError as e:
        logger.error(f"Error funcional de AEAT: {e}", exc_info=True)
        print(f"Error funcional de AEAT: {e}", file=sys.stderr)
        return EXIT_AEAT_ERROR
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
        print(f"Error inesperado: {e}", file=sys.stderr)
        return EXIT_COMMUNICATION_ERROR
    
    # Guardar respuesta
    try:
        # Crear directorio de salida si no existe
        args.output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(xml_respuesta)
        
        logger.info(f"Respuesta guardada en: {args.output}")
    except Exception as e:
        logger.error(f"Error guardando fichero de salida: {e}", exc_info=True)
        print(f"Error guardando respuesta: {e}", file=sys.stderr)
        return EXIT_FILE_ERROR
    
    logger.info("Proceso completado con éxito")
    logger.info("=" * 60)
    
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())

