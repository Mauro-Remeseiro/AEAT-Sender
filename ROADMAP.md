# Roadmap - AEAT-Sender

Este roadmap resume qué está listo, qué falta para llegar a producción y qué mejoras opcionales pueden añadirse para reforzar el valor del proyecto en un contexto profesional / portfolio.

## ✅ Completed

- **CLI profesional:** argparse con `--version`, `--debug`, formateo del help con logo ASCII y códigos de salida (0-5) para integración con orquestadores.
- **Manejo de certificados:** carga de `.pfx/.p12`, conversión a PEM temporal, limpieza segura y reporting de errores específicos (`AeatCertificateError`).
- **SOAP client:** construcción de envelope SOAP 1.1, sesión HTTPS con reintentos, detección de `SOAP Fault`, extracción del body y diferenciación entre errores de comunicación / funcionales.
- **Configuración:** loader JSON tipado con validación de campos obligatorios, tiempos de espera configurables y estructura por sistemas (`SII`, `VERIFACTU`).
- **Observabilidad y testing:** logging rotativo (`logs/aeat_sender.log`), respuesta persistida en disco, pruebas unitarias con mocks de `requests.Session`.

## ▶️ Next Steps (producción)

1. **URLs oficiales de AEAT**
   - Sustituir placeholders por las URLs reales de SII y VeriFactu (pruebas / producción) en `config.json`.
2. **Operaciones SOAP + namespaces**
   - Mapear cada tipo de XML a la operación real (`SuministroLRFacturasEmitidas`, etc.), definir `SOAPAction` y namespaces. Archivo: `aeat_sender/soap_client.py`.
3. **Validación funcional**
   - Ejecutar pruebas end-to-end contra el entorno de pruebas de AEAT con certificados reales; documentar resultados en `PORTFOLIO.md` o en la wiki del repo.
4. **Packaging**
   - Generar `aeat-sender.exe` con PyInstaller, adjuntar instrucciones de despliegue y comprobar que `config.json` se resuelve correctamente en modo frozen.

## 💡 Optional Extensions

- **Detección automática del tipo de XML** para seleccionar operación/namespace sin intervención manual.
- **Validación contra XSD oficiales** usando `lxml` o `xmlschema` antes de enviar a la AEAT.
- **Extracción de códigos de error específicos** (detalle en `<detail>` del Fault) para enriquecer los logs y los mensajes al usuario.
- **Soporte multi-certificado o multi-cliente** leyendo una lista de certificados y permitiendo seleccionar uno vía CLI.
- **Modo “dry-run”** que valide configuración/certificado sin enviar el XML real.

## Checklist rápido

- [ ] URLs oficiales configuradas (`config.json`)
- [ ] Operaciones SOAP, namespaces y SOAPAction definidos
- [ ] Tests end-to-end con certificados reales
- [ ] Binario `.exe` generado y documentado
- [ ] Capturas reales añadidas a `docs/media`

## Notas de seguridad

- Nunca versionar `config.json` ni certificados.
- Guardar certificados `.pfx/.p12` en almacenes seguros (BitLocker, Azure KeyVault, etc.).
- Rotar contraseñas periódicamente y limitar permisos del fichero.

## Comandos útiles

```bash
# Instalar dependencias principales
pip install -r requirements.txt

# Instalar en modo desarrollo (incluye pytest, black, ruff)
pip install -r requirements-dev.txt

# Ejecutar tests
pytest

# Compilar a .exe
pyinstaller --onefile --name aeat-sender --console aeat_sender/cli.py
```

---

**Última actualización:** 2024  
**Versión del proyecto:** 0.1.0

