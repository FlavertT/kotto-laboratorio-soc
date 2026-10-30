# Laboratorio conectado

## Ejecutar

Linux con Python 3.12, `ip`, `unshare`, `tcpdump` y namespaces de usuario habilitados. No requiere Docker ni modificar la red del equipo. Desde la raíz del proyecto:

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py setup_soc_roles
./lab/run-isolated.sh --output runs/ensayo-con-defensa --seed 42
./lab/run-isolated.sh --output runs/ensayo-sin-defensa --seed 42 --no-defense
```

Usar una carpeta nueva para cada ejecución. Cada ensayo dura unos 20 segundos. En entornos restringidos se debe autorizar la creación del namespace. El script rechaza ejecutar el experimento si hay interfaces adicionales a loopback o una ruta predeterminada.

## Arquitectura y alcance

Procesos independientes en un único namespace de red sin Internet, con direcciones loopback distintas:

- PLC: 127.0.0.20:8001.
- Administración: 127.0.0.11.
- Atacante simulado: 127.0.0.30.
- SOC: 127.0.0.10.

Son estaciones lógicas, no máquinas virtuales ni segmentos de firewall separados. Comparten el filesystem del usuario. Django escribe los resultados en la base local; su administrador web permanece fuera del namespace. Ninguna captura escucha en la red doméstica. `tcpdump` captura en loopback y filtra `host 127.0.0.20 and tcp port 8001`, durante unos 15 segundos. No se capturan todos los últimos segundos de recuperación; la telemetría continúa hasta los 18 segundos. El proceso de captura usa root únicamente dentro del namespace, mapeado al usuario del host.

## Incidente y política

Se asume comprometida una cuenta de mantenimiento. La estación atacante recibe su contraseña efímera para representar esa precondición; no se implementa robo de contraseñas ni explotación. La administración aplica primero un cambio legítimo a 4 °C. El atacante modifica consigna y duración con un generador aleatorio de semilla registrada. El PLC acepta rangos amplios para demostrar la detección posterior.

El SOC consulta eventos cada segundo. La regla compara los valores con la política de la maqueta: consigna de 2 a 5 °C y duración de 0 a 30 minutos. No utiliza la IP del atacante ni una marca de ataque. Además exige una autorización previa de un solo uso para la cuenta, experimento y valores exactos, válida a la hora del evento. Detecta cambios dentro de rango sin autorización. No prueba identidad: alguien con la cuenta comprometida que ejecuta exactamente un cambio ya aprobado puede consumir su autorización. Un cambio autorizado fuera de rango sigue generando una alerta de política.

Con defensa activa: bloquea la cuenta de origen, invalida su acceso y bloquea modificaciones remotas de todos los operadores; luego restaura 3 °C y 20 minutos sin desbloquear. Un nuevo ensayo comienza con estado nuevo. El SOC posee un rol separado; un operador no puede ejecutar contención o recuperación. Sesiones de 15 minutos, tokens aleatorios guardados como hash en memoria. No hay persistencia de bloqueos tras reiniciar el PLC: es una limitación de esta maqueta.

El modelo térmico es exponencial simplificado, con un efecto agregado de duración de descongelamiento; no simula ciclos físicos reales. La semilla reproduce las consignas elegidas, no los tiempos de red ni temperaturas idénticas. Las temperaturas no sustentan conclusiones sobre seguridad alimentaria real.

## Evidencias y reportes

Cada ejecución completa crea caso, heladera, experimento, mediciones, cambios, alertas y acciones de respuesta. Incorpora cuatro evidencias con SHA-256 y custodia inicial: registros del PLC, PCAP, resultados y diagnóstico de captura. Los cambios en la línea temporal quedan vinculados al registro del PLC; la captura tiene su entrada propia de evidencia.

En Django: **Experimentos → Descargar informe**. El informe Markdown contiene alertas y latencia, acciones, temperaturas, hashes y línea temporal. Puede regenerarse:

```bash
.venv/bin/python manage.py experiment_report --experiment 3 --output runs/informe.md
.venv/bin/python manage.py verify_evidence
```

Los ensayos incompletos se conservan con estado Fallido para no confundirlos con resultados válidos. Los informes completos iniciales corresponden a experimentos 3 y 4 en el equipo de desarrollo.

El PCAP usa HTTP dentro del namespace y contiene contraseñas y tokens efímeros de ese ensayo. `runs/`, `media/`, PCAP y la base están excluidos de Git. No publicar capturas sin anonimización. TLS queda pendiente.

## Roles SOC

`setup_soc_roles` crea grupos **SOC · Consulta** y **SOC · Respuesta**. Asignar usuarios y habilitar acceso staff si usarán el administrador. Consulta puede consultar registros e informes; Respuesta además puede documentar casos y custodia y ejecutar el comando de monitoreo con ese actor. El informe comprueba permisos. La cuenta técnica `soc-monitor` tiene contraseña inutilizable y permisos de respuesta. No habilita inicio de sesión web.

El monitor puede ejecutarse continuamente (`--seconds 0`, valor por defecto) dentro de la misma red que el PLC:

```bash
.venv/bin/python manage.py monitor_plc --experiment ID --credentials runs/ENSAYO/credentials.json --actor soc-monitor
```

El ejecutor automatizado lo inicia y termina por ensayo. No es todavía un servicio supervisado: ante error de conexión termina; una interrupción entre ingestión y respuesta no se reintenta automáticamente. Los usuarios de sistema con acceso a disco pueden manipular registros; no hay custodia inmutable.

## Validación

```bash
.venv/bin/python manage.py test soc lab
```

Pruebas de autenticación, expiración, separación de roles, revocación, recuperación manteniendo bloqueo, valores inválidos, detección independiente de marcas de ataque, deduplicación, autorización del informe e integridad de evidencia.

## Autorización de cambios

En Django, «Autorizaciones de cambios → Añadir»: seleccionar experimento, cuenta del PLC, valores exactos y ventana UTC. El aprobador y la fecha se registran automáticamente; no se permite editar ni borrar desde el administrador. El grupo **SOC · Aprobación** puede crear autorizaciones; Consulta y Respuesta no reciben ese permiso. Las aprobaciones son registros de control, no secretos.

El ejecutor crea explícitamente la aprobación del cambio legítimo (cuenta admin, 4 °C, 20 minutos) con el actor técnico `lab-approver`, sin contraseña utilizable. Se registra aparte del PLC; este no marca eventos como autorizados. El SOC consume la aprobación al leer un evento coincidente. No se admiten aprobaciones retroactivas. El alcance de una aprobación es un cambio completo con ambos valores finales, no una sesión específica.

```bash
./lab/run-isolated.sh --output runs/prueba-interna --seed 42 --within-range
./lab/run-isolated.sh --output runs/prueba-interna-sin-defensa --seed 42 --within-range --no-defense
```

La autorización se evalúa después de aplicar el cambio para estudiar detección y contención. No es aún un bloqueo preventivo del PLC. Los usuarios con acceso directo a la base pueden modificar aprobaciones; no se implementa separación administrativa a nivel del sistema operativo.
