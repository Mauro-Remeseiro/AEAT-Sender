# AEAT-Sender · Project Portfolio

## Mini presentación

AEAT-Sender es una utilidad de línea de comandos escrita en Python 3.11 que automatiza el envío de XML ya generados a los servicios SOAP 1.1 de la Agencia Tributaria Española (SII y VeriFactu). Nació como herramienta interna para integrar ERPs con la AEAT sin depender de componentes propietarios y evolucionó hasta convertirse en un ejecutable listo para operaciones 24/7 con monitoreo, logging y códigos de salida claros.

## Resumen técnico

- **Stack:** Python 3.11, requests, cryptography, logging rotativo, PyInstaller, pytest.
- **Protocolos:** SOAP 1.1 document/literal sobre HTTPS con autenticación por certificado digital cualificado (.pfx/.p12).
- **Arquitectura:** CLI empaquetable (`aeat-sender.exe`) + paquete instalable (`pip install .`), configuración declarativa, comunicación segregada por entorno (pruebas / producción).
- **Testing:** Pytest con mocks de `requests.Session` para no depender de la AEAT; cobertura de casos de éxito, faults, errores HTTP y timeouts.

## Problema que resuelve

- Automatiza el **envío seguro de información fiscal** (SII / VeriFactu) desde sistemas de facturación internos.
- Reduce el riesgo operativo al manejar certificados, SOAP envelopes y errores funcionales de la AEAT de manera uniforme.
- Simplifica la integración para equipos DevOps/FinOps que necesitan ejecutar envíos programados o manuales desde Windows.

## Competencias demostradas

- Diseño de CLI profesional con argparse, `--version`, `--debug` y códigos de salida estándares.
- Manejo avanzado de certificados: carga de `.pfx/.p12`, conversión a PEM, gestión de temporales y validación TLS.
- Construcción y análisis de envelopes SOAP manuales, detección de `Fault` y mapping a excepciones de negocio.
- Logging observability-ready (rotativo, estructura, diferenciación de errores técnicos y funcionales).
- Testing aislado mediante mocks detallados de `requests.Session` y `cryptography`.

## Snippets destacados

### Conversión de certificado `.pfx/.p12` a PEM temporales

```python
cert_pem_file = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False)
key_pem_file = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False)

private_key, certificate, _ = pkcs12.load_key_and_certificates(
    pfx_data,
    cert_password.encode("utf-8"),
    backend=default_backend(),
)

cert_pem_file.write(certificate.public_bytes(Encoding.PEM).decode("utf-8"))
key_pem_file.write(
    private_key.private_bytes(
        Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    ).decode("utf-8")
)
```

### Detección de Fault SOAP y propagación como error funcional

```python
fault = root.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Fault")
if fault is None:
    fault = root.find(".//Fault")

if fault is not None:
    faultcode = fault.find(".//faultcode")
    faultstring = fault.find(".//faultstring")
    mensaje = ""
    if faultcode is not None:
        mensaje += f"Código: {faultcode.text or ''} "
    if faultstring is not None:
        mensaje += f"Mensaje: {faultstring.text or ''}"
    raise AeatFunctionalError(f"Error funcional de AEAT: {mensaje.strip()}")
```

### Mock de `requests.Session.post` en los tests

```python
@patch("aeat_sender.soap_client.requests.Session")
def test_enviar_xml_timeout(mock_session_class):
    mock_session = MagicMock()
    mock_session.post.side_effect = requests.exceptions.Timeout("Connection timeout")
    mock_session_class.return_value = mock_session

    with pytest.raises(AeatCommunicationError):
        enviar_xml("SII", "pruebas", "<xml />", config_test)
```

> El código completo y los tests están disponibles en `aeat_sender/soap_client.py` y `tests/test_soap_client.py`.


