"""Configuración del sistema de logging."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(level: str = "INFO", log_file: Optional[Path] = None) -> logging.Logger:
    """
    Configura el sistema de logging de la aplicación.
    
    Args:
        level: Nivel de logging ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
        log_file: Ruta al fichero de log. Si es None, usa logs/aeat_sender.log
                  en el directorio del ejecutable o del proyecto.
    
    Returns:
        Logger configurado.
    """
    # Determinar ruta del log si no se especifica
    if log_file is None:
        if getattr(sys, 'frozen', False):
            # Ejecutable compilado con PyInstaller
            base_dir = Path(sys.executable).parent
        else:
            # Ejecución desde código fuente
            base_dir = Path(__file__).parent.parent
        
        log_dir = base_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "aeat_sender.log"
    
    # Crear logger principal
    logger = logging.getLogger("aeat_sender")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Evitar duplicar handlers si se llama varias veces
    if logger.handlers:
        return logger
    
    # Formato de los mensajes de log
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Handler para fichero (rotativo, máximo 10MB, 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)  # En fichero siempre DEBUG para tener todo
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para consola (solo INFO y superiores)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

