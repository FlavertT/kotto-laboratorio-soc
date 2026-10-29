# KOTTO · Laboratorio SOC y análisis forense

Prototipo académico en desarrollo para el trabajo final grupal de la Diplomatura en Ciberseguridad Aplicada. Autores: Ignacio Echave, Amparo Rodriguez y Flavio Sistro.

Python representa un PLC simulado dentro de una maqueta; no reproduce íntegramente un equipo industrial. Actualmente incluye Django, SQL (SQLite), gestión de registros y simulación local. La comunicación de red, captura PCAP y defensa activa están pendientes.

El repositorio no incluye la base local, usuarios, contraseñas, evidencias ni capturas de tráfico.
El SOC participa mediante alertas, casos, línea temporal y registro de actuaciones de custodia.

## Iniciar en este equipo

En el equipo de desarrollo, el entorno `.venv` y la base local ya están preparados. Si clonaste el repositorio, seguí primero «Instalación nueva».

```bash
source .venv/bin/activate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Abrir http://127.0.0.1:8000/admin/ e ingresar con el usuario creado.
Crear un caso desde «Cases»; anotar su ID. No se incluyen contraseñas predeterminadas.
Las evidencias se incorporan por comando; desde el administrador se consultan y se agregan actuaciones de custodia.

## Experimento inicial

```bash
python simulator/controller.py --output runs/baseline
python simulator/controller.py --output runs/incident --incident
python manage.py detect_incident runs/incident/controller.jsonl --case 1
python manage.py ingest_evidence runs/incident/controller.jsonl --case 1 --user TU_USUARIO --source controlador-kotto --collected-at 2026-10-28T16:00:00Z
python manage.py verify_evidence
```

Reemplazar el ID, usuario y fecha de recolección por los reales. Incorporar también telemetry.jsonl y manifest.json si forman parte del análisis.
Cada ejecución necesita una carpeta de salida nueva para evitar sobrescribir registros.

La simulación genera 30 muestras con intervalos sintéticos de 10 segundos a partir de la hora UTC inicial, sin esperar cinco minutos reales. En la muestra 10 cambia la consigna de 3 a 12 °C y el parámetro de descongelamiento de 20 a 60 minutos. El descongelamiento es un parámetro registrado; todavía no modela un ciclo térmico. Los archivos están identificados como simulados.
La detección lee la marca `authorized=false` del escenario y crea una alerta y un evento temporal. Es una regla de demostración, no una validación independiente de autenticación. Repetir la importación secuencial no duplica la alerta.

## SQL y datos

- `soc/models.py`: entidades y relaciones.
- `soc/migrations/0001_initial.py`: esquema reproducible gestionado por Django.
- `sql/001_soc_sqlite.sql`: SQL equivalente de las tablas del laboratorio, para estudiar o revisar. Las tablas de usuarios y sesiones se crean con las migraciones de Django.
- `db.sqlite3`: base local, excluida de Git.
- `media/evidence/`: copias preservadas, excluidas de Git. No se publican por URL.

El comando de incorporación calcula SHA-256 sobre la copia almacenada y registra actor, origen, fecha de recolección y custodia inicial. La verificación vuelve a calcularlo y falla si falta o cambia un archivo. Respaldar juntos la base y `media/`.
Las restricciones del administrador evitan editar evidencias o alterar actuaciones existentes desde esa interfaz. No constituyen almacenamiento inmutable: quien controle el disco o la base puede modificarlos. No hay certificación judicial ni firma criptográfica de la custodia.

## Comprobar

```bash
python manage.py check
python manage.py test
```

Las pruebas cubren preservación independiente del original, detección de alteraciones y detección del incidente sin alertas en la operación normal.

## Instalación nueva

Requiere Python 3.12 con soporte venv/pip.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

Esta configuración es de desarrollo local (DEBUG habilitado y clave local). No desplegarla públicamente.

## Próxima etapa del laboratorio

Pendientes: controlador con acceso autenticado y sesiones; estaciones de administración y atacante en red aislada; adquisición PCAP real del experimento; monitoreo continuo; contención y recuperación documentadas; permisos por rol SOC; vincular evidencias con los eventos y generar informe. Esta primera base no ejecuta ataques ni controla dispositivos reales.
