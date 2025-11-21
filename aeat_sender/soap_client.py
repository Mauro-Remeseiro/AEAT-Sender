"""Cliente SOAP para comunicación con los servicios web de la AEAT."""

import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend

from aeat_sender.config import Config, ConfigError


class AeatSenderError(Exception):
    """Excepción base para errores relacionados con el envío a AEAT."""
    pass


class AeatConfigError(AeatSenderError):
    """Errores relacionados con la configuración (URLs, sistema, entorno, etc.)."""
    pass


class AeatCommunicationError(AeatSenderError):
    """Errores de comunicación (timeout, TLS, HTTP != 200, conexión, etc.)."""
    pass


class AeatFunctionalError(AeatSenderError):
    """Errores funcionales devueltos por AEAT (Fault SOAP o códigos de error de negocio)."""
    pass


class AeatCertificateError(AeatSenderError):
    """Errores relacionados con el certificado cliente (.pfx/.p12)."""
    pass


def cargar_certificado_cliente(cert_path: Path, cert_password: str) -> Tuple[Path, Path]:
    """
    Carga un certificado cliente (.pfx/.p12) y lo convierte a formato PEM temporal.
    
    Args:
        cert_path: Ruta al fichero .pfx o .p12.
        cert_password: Contraseña del certificado.
    
    Returns:
        Tupla (cert_pem_path, key_pem_path) con las rutas a los ficheros PEM temporales.
        Estos ficheros deben eliminarse después de usarlos.
    
    Raises:
        AeatCertificateError: Si hay un error cargando o convirtiendo el certificado.
    """
    import logging
    
    logger = logging.getLogger("aeat_sender")
    
    if not cert_path.exists():
        raise AeatCertificateError(f"El fichero de certificado no existe: {cert_path}")
    
    try:
        # Leer el fichero .pfx/.p12
        with open(cert_path, "rb") as f:
            pfx_data = f.read()
        
        # Cargar el certificado usando cryptography
        try:
            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                pfx_data,
                cert_password.encode("utf-8") if cert_password else None,
                backend=default_backend(),
            )
        except ValueError as e:
            # ValueError se lanza cuando la contraseña es incorrecta o el formato es inválido
            raise AeatCertificateError(
                f"Error cargando certificado: contraseña incorrecta o formato inválido. {e}"
            )
        except Exception as e:
            raise AeatCertificateError(f"Error inesperado cargando certificado: {e}")
        
        if private_key is None or certificate is None:
            raise AeatCertificateError("El certificado no contiene clave privada o certificado válido")
        
        # Crear ficheros temporales PEM
        cert_pem_file = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False)
        key_pem_file = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False)
        
        cert_pem_path = Path(cert_pem_file.name)
        key_pem_path = Path(key_pem_file.name)
        
        try:
            # Escribir certificado en formato PEM
            from cryptography.hazmat.primitives.serialization import (
                Encoding,
                NoEncryption,
                PrivateFormat,
            )
            
            cert_pem = certificate.public_bytes(Encoding.PEM).decode("utf-8")
            cert_pem_file.write(cert_pem)
            cert_pem_file.close()
            
            # Escribir clave privada en formato PEM (sin contraseña)
            # Usar PrivateFormat.PKCS8 que es compatible con requests
            key_pem = private_key.private_bytes(
                Encoding.PEM,
                format=PrivateFormat.PKCS8,
                encryption_algorithm=NoEncryption(),
            ).decode("utf-8")
            key_pem_file.write(key_pem)
            key_pem_file.close()
            
            logger.debug(f"Certificado convertido a PEM: cert={cert_pem_path}, key={key_pem_path}")
            
            return (cert_pem_path, key_pem_path)
            
        except Exception as e:
            # Limpiar ficheros temporales en caso de error
            try:
                cert_pem_path.unlink(missing_ok=True)
                key_pem_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise AeatCertificateError(f"Error escribiendo ficheros PEM temporales: {e}")
    
    except AeatCertificateError:
        raise
    except Exception as e:
        raise AeatCertificateError(f"Error procesando certificado: {e}")


def limpiar_certificados_temporales(cert_pem_path: Path, key_pem_path: Path) -> None:
    """
    Elimina los ficheros PEM temporales después de usarlos.
    
    Args:
        cert_pem_path: Ruta al fichero PEM del certificado.
        key_pem_path: Ruta al fichero PEM de la clave privada.
    """
    import logging
    
    logger = logging.getLogger("aeat_sender")
    
    try:
        cert_pem_path.unlink(missing_ok=True)
        key_pem_path.unlink(missing_ok=True)
        logger.debug("Ficheros PEM temporales eliminados")
    except Exception as e:
        logger.warning(f"Error eliminando ficheros PEM temporales: {e}")


def extraer_body_soap(xml_respuesta: str) -> str:
    """
    Extrae el contenido del body SOAP de la respuesta.
    
    Args:
        xml_respuesta: Contenido XML completo de la respuesta SOAP.
    
    Returns:
        Contenido del body SOAP como string XML.
        Si no se puede extraer, devuelve el XML completo.
    
    Nota:
        Busca el elemento <soap:Body> o <soapenv:Body> y devuelve su contenido.
    """
    try:
        root = ET.fromstring(xml_respuesta)
        
        # Buscar Body en diferentes namespaces posibles
        namespaces = {
            "soap": "http://schemas.xmlsoap.org/soap/envelope/",
            "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
        }
        
        # Intentar encontrar Body con diferentes prefijos
        body = None
        for prefix, namespace in namespaces.items():
            body = root.find(f".//{{{namespace}}}Body")
            if body is not None:
                break
        
        # Si no se encuentra con namespace, buscar sin namespace
        if body is None:
            body = root.find(".//Body")
        
        if body is not None and len(body) > 0:
            # Devolver el contenido del body (el primer hijo)
            contenido = ET.tostring(body[0], encoding="unicode")
            return contenido
        
        # Si no hay body o está vacío, devolver el XML completo
        return xml_respuesta
        
    except ET.ParseError:
        # Si no es XML válido, devolver el contenido completo
        return xml_respuesta
    except Exception:
        # En caso de cualquier otro error, devolver el contenido completo
        return xml_respuesta


def detectar_fault_soap(xml_respuesta: str) -> Optional[str]:
    """
    Detecta si la respuesta SOAP contiene un Fault y extrae el mensaje de error.
    
    Args:
        xml_respuesta: Contenido XML de la respuesta SOAP.
    
    Returns:
        Mensaje de error del Fault si existe, None si no hay Fault.
    
    Nota:
        Busca el elemento <soap:Fault> o <soapenv:Fault> en la respuesta.
        Extrae el <faultstring> o <faultstring> para obtener el mensaje.
    """
    try:
        root = ET.fromstring(xml_respuesta)
        
        # Buscar Fault en diferentes namespaces posibles
        namespaces = {
            "soap": "http://schemas.xmlsoap.org/soap/envelope/",
            "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
        }
        
        # Intentar encontrar Fault con diferentes prefijos
        fault = None
        for prefix, namespace in namespaces.items():
            fault = root.find(f".//{{{namespace}}}Fault")
            if fault is not None:
                break
        
        # Si no se encuentra con namespace, buscar sin namespace
        if fault is None:
            fault = root.find(".//Fault")
        
        if fault is not None:
            # Buscar faultstring o faultcode
            faultstring = fault.find(".//faultstring")
            if faultstring is None:
                faultstring = fault.find(".//{http://schemas.xmlsoap.org/soap/envelope/}faultstring")
            
            faultcode = fault.find(".//faultcode")
            if faultcode is None:
                faultcode = fault.find(".//{http://schemas.xmlsoap.org/soap/envelope/}faultcode")
            
            mensaje = ""
            if faultcode is not None:
                mensaje += f"Código: {faultcode.text or ''} "
            if faultstring is not None:
                mensaje += f"Mensaje: {faultstring.text or ''}"
            
            # Si no hay mensaje específico, devolver el XML del Fault
            if not mensaje.strip():
                mensaje = ET.tostring(fault, encoding="unicode")
            
            return mensaje.strip() if mensaje else "Fault SOAP detectado en la respuesta"
        
        return None
        
    except ET.ParseError:
        # Si no es XML válido, no podemos detectar Fault
        return None
    except Exception:
        # En caso de cualquier otro error, no podemos determinar si hay Fault
        return None


def construir_envelope_soap(xml_contenido: str, operacion: str, namespace: Optional[str] = None) -> str:
    """
    Construye el envelope SOAP 1.1 en modo document/literal.
    
    Args:
        xml_contenido: Contenido XML del mensaje a enviar.
        operacion: Nombre de la operación SOAP (por ejemplo, "SuministroLRFacturasEmitidas").
        namespace: Namespace XML para la operación. Si es None, se usa un placeholder.
    
    Returns:
        Envelope SOAP completo como string XML.
    
    Nota:
        El formato es SOAP 1.1 document/literal como exige la AEAT.
        El namespace debe ser proporcionado según la especificación de cada servicio.
    
    TODO:
        - Definir los namespaces exactos según la especificación de AEAT para SII y VeriFactu.
        - Validar que el xml_contenido es XML válido antes de insertarlo.
    """
    # Namespace por defecto si no se proporciona
    if namespace is None:
        namespace = "TODO: namespace de AEAT - consultar documentación oficial"
    
    # Construir el envelope SOAP 1.1
    envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
    <soapenv:Body>
        <{operacion} xmlns="{namespace}">
            {xml_contenido}
        </{operacion}>
    </soapenv:Body>
</soapenv:Envelope>"""
    
    return envelope


def enviar_xml(sistema: str, entorno: str, xml_contenido: str, config: Config) -> str:
    """
    Envía el XML a los servicios web de la AEAT usando SOAP 1.1 sobre HTTPS.
    
    Args:
        sistema: "SII" o "VERIFACTU".
        entorno: "pruebas" o "produccion".
        xml_contenido: Contenido XML a enviar.
        config: Configuración de la aplicación.
    
    Returns:
        XML de respuesta de la AEAT como string.
    
    Raises:
        AeatConfigError: Si hay un error en la configuración (URLs, sistema, entorno).
        AeatCertificateError: Si hay un error con el certificado cliente.
        AeatCommunicationError: Si hay un error de comunicación (timeout, TLS, HTTP, conexión).
        AeatFunctionalError: Si AEAT devuelve un error funcional (Fault SOAP).
    
    TODO:
        - Determinar la operación SOAP correcta según el sistema (SII vs VeriFactu).
        - Usar WSDL de AEAT si está disponible (con zeep) o construir envelope manualmente.
        - Añadir headers SOAP correctos (Content-Type: text/xml; charset=utf-8, SOAPAction).
        - Validar certificado del servidor (verify=True) y permitir CA custom si es necesario.
    """
    import logging
    
    logger = logging.getLogger("aeat_sender")
    
    # Obtener URL del servicio
    try:
        url = config.obtener_url(sistema, entorno)
        logger.info(f"URL del servicio: {url}")
    except ConfigError as e:
        logger.error(f"Error obteniendo URL: {e}")
        raise AeatConfigError(f"Error en configuración: {e}") from e
    
    # Cargar certificado cliente y convertirlo a PEM
    cert_pem_path = None
    key_pem_path = None
    
    try:
        cert_pem_path, key_pem_path = cargar_certificado_cliente(config.cert_path, config.cert_password)
        logger.debug("Certificado cliente cargado y convertido a PEM")
    except AeatCertificateError:
        raise
    except Exception as e:
        logger.error(f"Error inesperado cargando certificado: {e}", exc_info=True)
        raise AeatCertificateError(f"Error inesperado cargando certificado: {e}") from e
    
    try:
        # Construir envelope SOAP
        # TODO: Determinar operación y namespace según sistema y tipo de XML
        # Por ahora, usar valores genéricos que deben ser configurados según la documentación de AEAT
        operacion = "TODO: operacion_soap"  # Por ejemplo: "SuministroLRFacturasEmitidas" para SII
        namespace = None  # TODO: Definir namespace según operación y sistema
        envelope = construir_envelope_soap(xml_contenido, operacion, namespace)
        
        # Configurar sesión HTTP con reintentos
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        
        # Headers SOAP
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "",  # TODO: Definir SOAPAction según operación
        }
        
        # Realizar petición
        try:
            logger.info("Enviando petición SOAP a AEAT...")
            response = session.post(
                url,
                data=envelope.encode("utf-8"),
                headers=headers,
                cert=(str(cert_pem_path), str(key_pem_path)),
                verify=True,  # Validar certificado del servidor
                timeout=(config.timeouts.connect, config.timeouts.read),
            )
            
            logger.info(f"Respuesta recibida: {response.status_code}")
            logger.debug(f"Headers de respuesta: {response.headers}")
            
            # Verificar código HTTP
            if response.status_code != 200:
                raise AeatCommunicationError(
                    f"Error HTTP {response.status_code} en respuesta de AEAT: {response.text[:500]}"
                )
            
            xml_respuesta_completa = response.text
            
            # Detectar Fault SOAP en la respuesta
            fault_mensaje = detectar_fault_soap(xml_respuesta_completa)
            if fault_mensaje:
                logger.error(f"Fault SOAP detectado en respuesta: {fault_mensaje}")
                raise AeatFunctionalError(f"Error funcional de AEAT: {fault_mensaje}")
            
            # Extraer el contenido del body SOAP
            xml_respuesta = extraer_body_soap(xml_respuesta_completa)
            
            logger.info("Respuesta SOAP procesada correctamente (sin Fault)")
            logger.debug(f"Contenido del body SOAP extraído ({len(xml_respuesta)} caracteres)")
            
            return xml_respuesta
            
        except AeatCommunicationError:
            raise
        except AeatFunctionalError:
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout en la comunicación con AEAT: {e}")
            raise AeatCommunicationError(f"Timeout comunicando con AEAT: {e}") from e
        except requests.exceptions.SSLError as e:
            logger.error(f"Error SSL/TLS: {e}")
            raise AeatCommunicationError(f"Error de certificado SSL/TLS: {e}") from e
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Error de conexión: {e}")
            raise AeatCommunicationError(f"Error de conexión con AEAT: {e}") from e
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP: {e}")
            raise AeatCommunicationError(f"Error HTTP en respuesta de AEAT: {e}") from e
        except Exception as e:
            logger.error(f"Error inesperado en comunicación SOAP: {e}", exc_info=True)
            raise AeatCommunicationError(f"Error inesperado comunicando con AEAT: {e}") from e
        
    finally:
        # Limpiar ficheros PEM temporales
        if cert_pem_path and key_pem_path:
            limpiar_certificados_temporales(cert_pem_path, key_pem_path)
