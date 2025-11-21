# aeat-sender

![Status](https://img.shields.io/badge/status-active--development-blue?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey?style=flat-square&logo=windows)

CLI profesional en Python 3.11 que envía XML ya generados a los servicios SOAP 1.1 de la AEAT (SII y VeriFactu) con certificados cualificados. Automatiza la llamada HTTP(S), gestiona errores técnicos y funcionales y persiste los logs de cada transacción para auditoría. Diseñado para integrarse como micro-servicio o ejecutable standalone en flujos de facturación electrónica.

## Tecnologías aplicadas

- Python 3.11 + requests/httpx-style session handling
- SOAP 1.1 document/literal sobre HTTPS
- `cryptography` para convertir certificados `.pfx/.p12` a PEM temporales
- Logging rotativo con el módulo estándar (`RotatingFileHandler`)
- PyInstaller para distribución `aeat-sender.exe`
- Pytest + unittest.mock para tests sin dependencias externas

## Características principales

- CLI robusta (`aeat-sender`) con `--version`, `--debug` y códigos de salida diferenciados
- Configuración declarativa (`config.json`) separando certificados, entornos y timeouts
- Manejo completo de certificados cliente y validación TLS del servidor
- Detección de `SOAP Fault` y propagación como `AeatFunctionalError`
- Logs rotativos sin datos sensibles + respuesta persistida en disco

## Por qué es interesante técnicamente

- Implementa **SOAP 1.1 document/literal** manualmente, permitiendo desacoplar del WSDL oficial
- Convierte certificados **.pfx/.p12 → PEM** en tiempo de ejecución usando `cryptography`, limpiando los temporales
- Analiza el envelope y detecta **SOAP Fault** para mapear errores funcionales vs técnicos
- Expone **códigos de salida** estandarizados para integración con otros procesos (RPA, ETL, schedulers)
- Diseñado para **Windows** pero con código portable; preparado para empaquetarse en un `.exe` sin dependencias externas

## Capturas de uso (placeholders)

![CLI DEMO](https://github.com/Mauro-Remeseiro/AEAT-Sender/blob/7394e88afec0084b305e632d1c32b91036018456/docs/media/img/cli_help_version.jpg)

## Requisitos

- Python 3.11 o superior
- Windows (sistema operativo objetivo)
- Certificado digital cualificado (.pfx o .p12) de la AEAT

## Instalación rápida

```bash
# Clonar o descargar el proyecto
cd ProyectoXMLS

# Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate

# Instalar dependencias
pip install -e .

# O instalar con dependencias de desarrollo
pip install -e ".[dev]"
```

## Configuración

1. Copia `config.json.example` a `config.json`.
2. Completa la ruta a tu certificado `.pfx/.p12`, contraseña y URLs reales de los servicios.
3. Mantén `config.json` fuera del control de versiones.

Ejemplo:

```json
{
  "cert_path": "C:/ruta/a/tu/certificado.pfx",
  "cert_password": "TU_CONTRASEÑA",
  "entornos": {
    "SII": {
      "pruebas": "https://www7.aeat.es/wlpl/SSII-FACT/ws/fe/SiiFactFEV1SOAP",
      "produccion": "https://www2.aeat.es/wlpl/SSII-FACT/ws/fe/SiiFactFEV1SOAP"
    },
    "VERIFACTU": {
      "pruebas": "https://www7.aeat.es/wlpl/VERIFACTU/ws/VeriFactuSOAP",
      "produccion": "https://www2.aeat.es/wlpl/VERIFACTU/ws/VeriFactuSOAP"
    }
  },
  "timeouts": {
    "connect": 10,
    "read": 60
  }
}
```

> **Nota:** Las URLs incluidas son placeholders. Reemplázalas por las oficiales publicadas por AEAT.

## Uso

```
aeat-sender \
  --sistema SII \
  --entorno pruebas \
  --input "C:\ruta\entrada.xml" \
  --output "C:\ruta\respuesta.xml"
```

Parámetros importantes:

- `--sistema`: `SII` | `VERIFACTU` (case-insensitive)
- `--entorno`: `pruebas` | `produccion`
- `--input` / `--output`: rutas al XML de entrada/respuesta
- `--config`: ruta opcional al JSON de configuración
- `--debug`: activa logs detallados
- `--version`: muestra la versión del CLI y termina

### Ejemplos

```bash
# Envío a SII en entorno de pruebas
aeat-sender --sistema SII --entorno pruebas --input factura.xml --output respuesta.xml

# Envío a VeriFactu en producción
aeat-sender --sistema VERIFACTU --entorno produccion --input verifactu.xml --output resultado.xml --debug

# Especificar configuración personalizada
aeat-sender --sistema SII --entorno pruebas --input entrada.xml --output salida.xml --config mi_config.json
```

## Códigos de salida

- `0`: Éxito
- `1`: Error de argumentos/uso (por ejemplo, falta `--input`)
- `2`: Error cargando configuración (fichero inexistente, campos obligatorios faltantes)
- `3`: Error de acceso al fichero de entrada/salida
- `4`: Error de comunicación con AEAT (timeout, TLS, etc.)
- `5`: Error funcional devuelto por AEAT (por ejemplo, respuesta con código de error en el XML)

## Logs

Los logs se guardan en el directorio `logs/` con el nombre `aeat_sender.log`. El fichero es rotativo (máximo 10MB, 5 backups).

## Estructura del proyecto (compacta)

```
aeat_sender/
├─ aeat_sender/        # Código fuente del paquete
│  ├─ cli.py           # CLI + argparse + logging
│  ├─ config.py        # Loader/validador de config JSON
│  ├─ soap_client.py   # Certificados, SOAP y errores
│  ├─ xml_handler.py   # Utilidades XML
│  ├─ logging_config.py
│  └─ __init__.py
├─ tests/              # Pytest con mocks de requests.Session
├─ docs/ (opcional)    # Capturas y material de portfolio
├─ README.md / PORTFOLIO.md / ROADMAP.md
├─ config.json.example
├─ pyproject.toml
└─ requirements*.txt
```

## Desarrollo

### Ejecutar tests

```bash
pytest
```

### Formatear código

```bash
black aeat_sender tests
```

### Linting

```bash
ruff check aeat_sender tests
```

## Compilación a .exe

Para generar un ejecutable con PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --name aeat-sender --console aeat_sender/cli.py
```

El ejecutable se generará en `dist/aeat-sender.exe`.

## Estado del proyecto

✅ **Funcionalidades principales implementadas**: El proyecto tiene todas las funcionalidades core implementadas y listas para usar.

⚠️ **Configuración pendiente**: Antes de usar en producción, es necesario:

1. **Configurar URLs reales** de los servicios AEAT en `config.json`
2. **Definir operaciones SOAP** y namespaces según la documentación oficial de AEAT
3. **Probar con entorno de pruebas** de la AEAT

📋 **Para más detalles**, consulta `ROADMAP.md` que incluye:
- Lista completa de funcionalidades implementadas
- Checklist de configuración pendiente
- Pasos detallados para completar la configuración
- Guía de testing y validación

📖 **Guía rápida**: Consulta `GUIA_RAPIDA.md` para empezar rápidamente.

## Licencia

MIT

## Autor

Mauro Remeseiro Estrade

