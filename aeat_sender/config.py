"""Gestión de configuración del proyecto."""

import json
from pathlib import Path
from typing import Dict, Optional

from dataclasses import dataclass


class ConfigError(Exception):
    """Excepción lanzada cuando hay un error en la configuración."""
    pass


@dataclass
class Timeouts:
    """Configuración de timeouts para las conexiones."""
    connect: int = 10
    read: int = 60


@dataclass
class Entornos:
    """URLs de los entornos para cada sistema."""
    pruebas: str
    produccion: str


@dataclass
class Config:
    """Configuración principal de la aplicación."""
    cert_path: Path
    cert_password: str
    entornos: Dict[str, Entornos]  # Clave: "SII" o "VERIFACTU"
    timeouts: Timeouts
    
    @classmethod
    def cargar(cls, config_path: Path) -> "Config":
        """
        Carga la configuración desde un fichero JSON.
        
        Args:
            config_path: Ruta al fichero de configuración JSON.
            
        Returns:
            Instancia de Config con los valores cargados.
            
        Raises:
            ConfigError: Si el fichero no existe, no es válido JSON, o faltan campos obligatorios.
        """
        if not config_path.exists():
            raise ConfigError(f"El fichero de configuración no existe: {config_path}")
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Error parseando JSON: {e}")
        except Exception as e:
            raise ConfigError(f"Error leyendo fichero de configuración: {e}")
        
        # Validar campos obligatorios
        campos_obligatorios = ["cert_path", "cert_password", "entornos"]
        for campo in campos_obligatorios:
            if campo not in data:
                raise ConfigError(f"Falta el campo obligatorio en la configuración: {campo}")
        
        # Validar estructura de entornos
        if not isinstance(data["entornos"], dict):
            raise ConfigError("El campo 'entornos' debe ser un objeto JSON")
        
        entornos_dict = {}
        sistemas_esperados = ["SII", "VERIFACTU"]
        
        for sistema in sistemas_esperados:
            if sistema not in data["entornos"]:
                raise ConfigError(f"Falta la configuración del sistema '{sistema}' en 'entornos'")
            
            sistema_data = data["entornos"][sistema]
            if not isinstance(sistema_data, dict):
                raise ConfigError(f"La configuración de '{sistema}' debe ser un objeto JSON")
            
            if "pruebas" not in sistema_data or "produccion" not in sistema_data:
                raise ConfigError(
                    f"La configuración de '{sistema}' debe incluir 'pruebas' y 'produccion'"
                )
            
            entornos_dict[sistema] = Entornos(
                pruebas=sistema_data["pruebas"],
                produccion=sistema_data["produccion"],
            )
        
        # Validar y cargar timeouts (opcional, con valores por defecto)
        timeouts_data = data.get("timeouts", {})
        timeouts = Timeouts(
            connect=timeouts_data.get("connect", 10),
            read=timeouts_data.get("read", 60),
        )
        
        # Validar que el certificado existe (advertencia, no error fatal)
        cert_path = Path(data["cert_path"])
        if not cert_path.exists():
            # No lanzamos excepción aquí, pero lo registraremos en el log más adelante
            pass
        
        return cls(
            cert_path=cert_path,
            cert_password=data["cert_password"],
            entornos=entornos_dict,
            timeouts=timeouts,
        )
    
    def obtener_url(self, sistema: str, entorno: str) -> str:
        """
        Obtiene la URL del servicio para un sistema y entorno dados.
        
        Args:
            sistema: "SII" o "VERIFACTU"
            entorno: "pruebas" o "produccion"
            
        Returns:
            URL del servicio.
            
        Raises:
            ConfigError: Si el sistema o entorno no están configurados.
        """
        sistema_upper = sistema.upper()
        if sistema_upper not in self.entornos:
            raise ConfigError(f"Sistema no configurado: {sistema}")
        
        entornos_obj = self.entornos[sistema_upper]
        
        if entorno == "pruebas":
            return entornos_obj.pruebas
        elif entorno == "produccion":
            return entornos_obj.produccion
        else:
            raise ConfigError(f"Entorno no válido: {entorno}")

