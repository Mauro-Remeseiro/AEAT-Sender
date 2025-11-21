"""Tests para el módulo soap_client.py."""

import pytest
import requests
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

from aeat_sender.soap_client import (
    AeatSenderError,
    AeatConfigError,
    AeatCertificateError,
    AeatCommunicationError,
    AeatFunctionalError,
    cargar_certificado_cliente,
    construir_envelope_soap,
    extraer_body_soap,
    detectar_fault_soap,
    enviar_xml,
)
from aeat_sender.config import Config, Entornos, Timeouts


def test_construir_envelope_soap():
    """Test de construcción básica del envelope SOAP."""
    xml_contenido = "<factura>test</factura>"
    operacion = "TestOperation"
    namespace = "http://test.namespace.com"
    
    envelope = construir_envelope_soap(xml_contenido, operacion, namespace)
    
    assert "soapenv:Envelope" in envelope
    assert "soapenv:Body" in envelope
    assert operacion in envelope
    assert namespace in envelope
    assert xml_contenido in envelope


def test_extraer_body_soap():
    """Test de extracción del body SOAP."""
    xml_respuesta = """<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
    <soapenv:Body>
        <respuesta>OK</respuesta>
    </soapenv:Body>
</soapenv:Envelope>"""
    
    body = extraer_body_soap(xml_respuesta)
    assert "<respuesta>OK</respuesta>" in body
    assert "soapenv:Envelope" not in body


def test_extraer_body_soap_sin_body():
    """Test de extracción cuando no hay body SOAP."""
    xml_sin_body = "<respuesta>OK</respuesta>"
    
    body = extraer_body_soap(xml_sin_body)
    assert body == xml_sin_body


def test_detectar_fault_soap():
    """Test de detección de Fault SOAP."""
    xml_con_fault = """<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
    <soapenv:Body>
        <soapenv:Fault>
            <faultcode>SOAP-ENV:Server</faultcode>
            <faultstring>Error de procesamiento</faultstring>
        </soapenv:Fault>
    </soapenv:Body>
</soapenv:Envelope>"""
    
    fault = detectar_fault_soap(xml_con_fault)
    assert fault is not None
    assert "Error de procesamiento" in fault
    assert "SOAP-ENV:Server" in fault
    
    xml_sin_fault = """<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
    <soapenv:Body>
        <respuesta>OK</respuesta>
    </soapenv:Body>
</soapenv:Envelope>"""
    
    fault = detectar_fault_soap(xml_sin_fault)
    assert fault is None


def test_detectar_fault_soap_diferentes_namespaces():
    """Test de detección de Fault con diferentes namespaces."""
    # Fault con namespace soap (sin env)
    xml_fault_soap = """<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <soap:Fault>
            <faultcode>Server</faultcode>
            <faultstring>Error</faultstring>
        </soap:Fault>
    </soap:Body>
</soap:Envelope>"""
    
    fault = detectar_fault_soap(xml_fault_soap)
    assert fault is not None


def test_detectar_fault_soap_xml_invalido():
    """Test de detección de Fault con XML inválido."""
    xml_invalido = "<esto no es XML válido"
    
    fault = detectar_fault_soap(xml_invalido)
    assert fault is None


# Helper para crear configuración de test
def crear_config_test():
    """Crea una configuración de test."""
    return Config(
        cert_path=Path("test_cert.pfx"),
        cert_password="test_password",
        entornos={
            "SII": Entornos(
                pruebas="https://test-sii-pruebas.aeat.es/ws",
                produccion="https://test-sii-prod.aeat.es/ws",
            ),
            "VERIFACTU": Entornos(
                pruebas="https://test-verifactu-pruebas.aeat.es/ws",
                produccion="https://test-verifactu-prod.aeat.es/ws",
            ),
        },
        timeouts=Timeouts(connect=10, read=60),
    )


@patch("aeat_sender.soap_client.requests.Session")
@patch("aeat_sender.soap_client.limpiar_certificados_temporales")
@patch("aeat_sender.soap_client.cargar_certificado_cliente")
def test_enviar_xml_exito(mock_cargar_cert, mock_limpiar, mock_session_class):
    """Test de envío exitoso sin Fault SOAP."""
    # Configurar mocks
    cert_pem_path = Path("/tmp/cert.pem")
    key_pem_path = Path("/tmp/key.pem")
    mock_cargar_cert.return_value = (cert_pem_path, key_pem_path)
    
    # Mock de la respuesta HTTP exitosa
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
    <soapenv:Body>
        <respuesta xmlns="http://test.aeat.es">
            <codigo>0</codigo>
            <mensaje>OK</mensaje>
        </respuesta>
    </soapenv:Body>
</soapenv:Envelope>"""
    mock_response.headers = {"Content-Type": "text/xml"}
    
    # Mock de Session
    mock_session = MagicMock()
    mock_session.post.return_value = mock_response
    mock_session_class.return_value = mock_session
    
    # Ejecutar
    config = crear_config_test()
    xml_contenido = "<factura>test</factura>"
    
    resultado = enviar_xml("SII", "pruebas", xml_contenido, config)
    
    # Verificaciones
    assert resultado is not None
    assert "<respuesta>" in resultado
    assert "<codigo>0</codigo>" in resultado
    
    # Verificar que se llamó a post con los parámetros correctos
    mock_session.post.assert_called_once()
    call_args = mock_session.post.call_args
    assert call_args[0][0] == "https://test-sii-pruebas.aeat.es/ws"
    assert "text/xml" in call_args[1]["headers"]["Content-Type"]
    assert call_args[1]["cert"] == (str(cert_pem_path), str(key_pem_path))
    assert call_args[1]["verify"] is True
    
    # Verificar que se limpiaron los certificados temporales
    mock_limpiar.assert_called_once_with(cert_pem_path, key_pem_path)


@patch("aeat_sender.soap_client.requests.Session")
@patch("aeat_sender.soap_client.limpiar_certificados_temporales")
@patch("aeat_sender.soap_client.cargar_certificado_cliente")
def test_enviar_xml_fault_soap(mock_cargar_cert, mock_limpiar, mock_session_class):
    """Test de envío que devuelve Fault SOAP."""
    # Configurar mocks
    cert_pem_path = Path("/tmp/cert.pem")
    key_pem_path = Path("/tmp/key.pem")
    mock_cargar_cert.return_value = (cert_pem_path, key_pem_path)
    
    # Mock de la respuesta HTTP con Fault SOAP
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
    <soapenv:Body>
        <soapenv:Fault>
            <faultcode>SOAP-ENV:Server</faultcode>
            <faultstring>Error funcional de AEAT: XML inválido</faultstring>
            <detail>
                <codigo>1001</codigo>
                <descripcion>El XML no cumple con el esquema XSD</descripcion>
            </detail>
        </soapenv:Fault>
    </soapenv:Body>
</soapenv:Envelope>"""
    mock_response.headers = {"Content-Type": "text/xml"}
    
    # Mock de Session
    mock_session = MagicMock()
    mock_session.post.return_value = mock_response
    mock_session_class.return_value = mock_session
    
    # Ejecutar y verificar que lanza AeatFunctionalError
    config = crear_config_test()
    xml_contenido = "<factura>test</factura>"
    
    with pytest.raises(AeatFunctionalError) as exc_info:
        enviar_xml("SII", "pruebas", xml_contenido, config)
    
    # Verificar el mensaje de error
    assert "Error funcional de AEAT" in str(exc_info.value)
    assert "XML inválido" in str(exc_info.value)
    
    # Verificar que se limpiaron los certificados temporales incluso con error
    mock_limpiar.assert_called_once_with(cert_pem_path, key_pem_path)


@patch("aeat_sender.soap_client.requests.Session")
@patch("aeat_sender.soap_client.limpiar_certificados_temporales")
@patch("aeat_sender.soap_client.cargar_certificado_cliente")
def test_enviar_xml_error_http(mock_cargar_cert, mock_limpiar, mock_session_class):
    """Test de envío que devuelve error HTTP (status != 200)."""
    # Configurar mocks
    cert_pem_path = Path("/tmp/cert.pem")
    key_pem_path = Path("/tmp/key.pem")
    mock_cargar_cert.return_value = (cert_pem_path, key_pem_path)
    
    # Mock de la respuesta HTTP con error 500
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.headers = {"Content-Type": "text/html"}
    
    # Mock de Session
    mock_session = MagicMock()
    mock_session.post.return_value = mock_response
    mock_session_class.return_value = mock_session
    
    # Ejecutar y verificar que lanza AeatCommunicationError
    config = crear_config_test()
    xml_contenido = "<factura>test</factura>"
    
    with pytest.raises(AeatCommunicationError) as exc_info:
        enviar_xml("SII", "pruebas", xml_contenido, config)
    
    # Verificar el mensaje de error
    assert "Error HTTP 500" in str(exc_info.value)
    
    # Verificar que se limpiaron los certificados temporales
    mock_limpiar.assert_called_once_with(cert_pem_path, key_pem_path)


@patch("aeat_sender.soap_client.requests.Session")
@patch("aeat_sender.soap_client.limpiar_certificados_temporales")
@patch("aeat_sender.soap_client.cargar_certificado_cliente")
def test_enviar_xml_timeout(mock_cargar_cert, mock_limpiar, mock_session_class):
    """Test de envío que lanza timeout."""
    # Configurar mocks
    cert_pem_path = Path("/tmp/cert.pem")
    key_pem_path = Path("/tmp/key.pem")
    mock_cargar_cert.return_value = (cert_pem_path, key_pem_path)
    
    # Mock de Session que lanza Timeout
    mock_session = MagicMock()
    mock_session.post.side_effect = requests.exceptions.Timeout("Connection timeout")
    mock_session_class.return_value = mock_session
    
    # Ejecutar y verificar que lanza AeatCommunicationError
    config = crear_config_test()
    xml_contenido = "<factura>test</factura>"
    
    with pytest.raises(AeatCommunicationError) as exc_info:
        enviar_xml("SII", "pruebas", xml_contenido, config)
    
    # Verificar el mensaje de error
    assert "Timeout" in str(exc_info.value) or "timeout" in str(exc_info.value).lower()
    
    # Verificar que se limpiaron los certificados temporales
    mock_limpiar.assert_called_once_with(cert_pem_path, key_pem_path)


@patch("aeat_sender.soap_client.requests.Session")
@patch("aeat_sender.soap_client.limpiar_certificados_temporales")
@patch("aeat_sender.soap_client.cargar_certificado_cliente")
def test_enviar_xml_ssl_error(mock_cargar_cert, mock_limpiar, mock_session_class):
    """Test de envío que lanza error SSL/TLS."""
    # Configurar mocks
    cert_pem_path = Path("/tmp/cert.pem")
    key_pem_path = Path("/tmp/key.pem")
    mock_cargar_cert.return_value = (cert_pem_path, key_pem_path)
    
    # Mock de Session que lanza SSLError
    mock_session = MagicMock()
    mock_session.post.side_effect = requests.exceptions.SSLError("SSL certificate verification failed")
    mock_session_class.return_value = mock_session
    
    # Ejecutar y verificar que lanza AeatCommunicationError
    config = crear_config_test()
    xml_contenido = "<factura>test</factura>"
    
    with pytest.raises(AeatCommunicationError) as exc_info:
        enviar_xml("SII", "pruebas", xml_contenido, config)
    
    # Verificar el mensaje de error
    assert "SSL" in str(exc_info.value) or "TLS" in str(exc_info.value)
    
    # Verificar que se limpiaron los certificados temporales
    mock_limpiar.assert_called_once_with(cert_pem_path, key_pem_path)


@patch("aeat_sender.soap_client.requests.Session")
@patch("aeat_sender.soap_client.limpiar_certificados_temporales")
@patch("aeat_sender.soap_client.cargar_certificado_cliente")
def test_enviar_xml_connection_error(mock_cargar_cert, mock_limpiar, mock_session_class):
    """Test de envío que lanza error de conexión."""
    # Configurar mocks
    cert_pem_path = Path("/tmp/cert.pem")
    key_pem_path = Path("/tmp/key.pem")
    mock_cargar_cert.return_value = (cert_pem_path, key_pem_path)
    
    # Mock de Session que lanza ConnectionError
    mock_session = MagicMock()
    mock_session.post.side_effect = requests.exceptions.ConnectionError("Connection refused")
    mock_session_class.return_value = mock_session
    
    # Ejecutar y verificar que lanza AeatCommunicationError
    config = crear_config_test()
    xml_contenido = "<factura>test</factura>"
    
    with pytest.raises(AeatCommunicationError) as exc_info:
        enviar_xml("SII", "pruebas", xml_contenido, config)
    
    # Verificar el mensaje de error
    assert "conexión" in str(exc_info.value).lower() or "connection" in str(exc_info.value).lower()
    
    # Verificar que se limpiaron los certificados temporales
    mock_limpiar.assert_called_once_with(cert_pem_path, key_pem_path)


@patch("aeat_sender.soap_client.cargar_certificado_cliente")
def test_enviar_xml_error_certificado(mock_cargar_cert):
    """Test de envío con error al cargar certificado."""
    # Mock que lanza error al cargar certificado
    mock_cargar_cert.side_effect = AeatCertificateError("Contraseña incorrecta")
    
    # Ejecutar y verificar que lanza AeatCertificateError
    config = crear_config_test()
    xml_contenido = "<factura>test</factura>"
    
    with pytest.raises(AeatCertificateError) as exc_info:
        enviar_xml("SII", "pruebas", xml_contenido, config)
    
    # Verificar el mensaje de error
    assert "certificado" in str(exc_info.value).lower()


def test_enviar_xml_error_config():
    """Test de envío con error de configuración (sistema/entorno no válido)."""
    config = crear_config_test()
    xml_contenido = "<factura>test</factura>"
    
    # Intentar con sistema no válido
    with pytest.raises(AeatConfigError):
        enviar_xml("SISTEMA_INVALIDO", "pruebas", xml_contenido, config)
    
    # Intentar con entorno no válido
    with pytest.raises(AeatConfigError):
        enviar_xml("SII", "entorno_invalido", xml_contenido, config)
