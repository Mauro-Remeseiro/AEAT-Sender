# Guía Rápida de Uso - aeat-sender

## Instalación Rápida

```bash
# 1. Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar
# Copiar config.json.example a config.json y completar con tus datos
copy config.json.example config.json
# Editar config.json con tus datos reales
```

## Configuración Inicial

1. **Copiar archivo de configuración:**
   ```bash
   copy config.json.example config.json
   ```

2. **Editar `config.json` con tus datos:**
   - Ruta al certificado `.pfx` o `.p12`
   - Contraseña del certificado
   - URLs de los servicios AEAT (consultar documentación oficial)

3. **Obtener certificado digital:**
   - El certificado debe ser un certificado digital cualificado de la AEAT
   - Formato: `.pfx` o `.p12`
   - Debe estar instalado o disponible como fichero

## Uso Básico

### Envío a SII (entorno de pruebas)

```bash
aeat-sender ^
  --sistema SII ^
  --entorno pruebas ^
  --input "C:\ruta\factura.xml" ^
  --output "C:\ruta\respuesta.xml"
```

### Envío a VeriFactu (producción)

```bash
aeat-sender ^
  --sistema VERIFACTU ^
  --entorno produccion ^
  --input "C:\ruta\verifactu.xml" ^
  --output "C:\ruta\resultado.xml"
```

### Modo Debug

```bash
aeat-sender ^
  --sistema SII ^
  --entorno pruebas ^
  --input entrada.xml ^
  --output salida.xml ^
  --debug
```

## Verificación

### Verificar que funciona

1. **Probar con entorno de pruebas primero**
2. **Revisar logs** en `logs/aeat_sender.log`
3. **Verificar código de salida:**
   - `0` = Éxito
   - Otros = Error (ver códigos en README.md)

### Ejemplo de verificación

```bash
aeat-sender --sistema SII --entorno pruebas --input test.xml --output respuesta.xml
echo %ERRORLEVEL%
# Si es 0, todo OK
# Si es otro valor, revisar logs/aeat_sender.log
```

## Solución de Problemas Comunes

### Error: "El fichero de certificado no existe"
- Verificar que la ruta en `config.json` es correcta
- Usar rutas absolutas (ej: `C:/certs/certificado.pfx`)
- Verificar que el fichero existe

### Error: "contraseña incorrecta o formato inválido"
- Verificar la contraseña del certificado en `config.json`
- Asegurarse de que el certificado no está corrupto

### Error: "Error de comunicación con AEAT"
- Verificar conexión a Internet
- Verificar que las URLs en `config.json` son correctas
- Revisar logs para más detalles

### Error: "Error funcional de AEAT"
- AEAT ha rechazado el XML
- Revisar el mensaje de error en los logs
- Verificar que el XML cumple con la especificación de AEAT

## Logs

Los logs se guardan en: `logs/aeat_sender.log`

Para ver los últimos errores:
```bash
type logs\aeat_sender.log | findstr ERROR
```

## Próximos Pasos

1. **Configurar URLs reales** de los servicios AEAT
2. **Configurar operaciones SOAP** según el tipo de XML
3. **Probar con entorno de pruebas** antes de producción
4. **Revisar ROADMAP.md** para detalles completos

## Soporte

Para más información:
- Ver `README.md` para documentación completa
- Ver `ROADMAP.md` para estado del proyecto y pendientes
- Consultar documentación oficial de la AEAT

