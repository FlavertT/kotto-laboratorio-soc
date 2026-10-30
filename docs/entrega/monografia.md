# Detección y respuesta ante cambios no autorizados en un controlador de refrigeración
## Laboratorio simulado con Python, Django y análisis de tráfico
Trabajo de investigación final grupal · Diplomatura en Ciberseguridad Aplicada
UTN La Plata
Ignacio Echave · Amparo Rodriguez · Flavio Sistro
30 de octubre de 2026

Maqueta experimental KOTTO. El programa Python representa funciones básicas de un PLC; no constituye un controlador industrial ni una instalación frigorífica real.

<!-- PAGE -->
# Autores, resumen y organización
## Presentación de los autores
Ignacio Echave, Amparo Rodriguez y Flavio Sistro integran el grupo que presenta este trabajo final de la Diplomatura en Ciberseguridad Aplicada de UTN La Plata. El proyecto integra programación, redes, gestión de registros y respuesta a incidentes en una maqueta de refrigeración conectada. La documentación describe el alcance implementado, sus resultados y las limitaciones que deben considerarse al interpretar la experiencia.
## Resumen
Se desarrolló un laboratorio aislado para estudiar modificaciones de parámetros en un controlador de refrigeración simulado. Un SOC consulta registros, contrasta cada cambio con una autorización previa y comprueba rangos operativos. Ante una desviación, bloquea la cuenta de origen y recupera una configuración de referencia. Tres ensayos de red mostraron que un cambio sin aprobación puede detectarse incluso dentro del rango permitido. Los reintentos fueron rechazados con defensa y aceptados sin ella. Se preservaron doce evidencias con SHA-256. Los resultados se limitan a la maqueta y no estiman pérdidas económicas ni seguridad alimentaria.
## Palabras clave
Ciberseguridad OT; PLC simulado; autorización; SOC; respuesta a incidentes; PCAP; cadena de custodia.
## Organización del documento
Las páginas siguientes presentan el problema y el antecedente, la pregunta de investigación, la arquitectura, el modelo relacional y las decisiones de diseño. Luego se describen el procedimiento experimental, los resultados observados, la evidencia de red, las limitaciones y las conclusiones. Se incluyen instrucciones de reproducción y referencias bibliográficas. Las cifras provienen de los experimentos 5, 6 y 7 de la versión con autorizaciones, ejecutados el 29 de octubre de 2026; las pruebas de software se repitieron durante la preparación de la entrega.

<!-- PAGE -->
# 1. Contexto y espacio del problema
Un sistema de refrigeración conectado combina un proceso físico, una lógica de control y una vía de administración. La temperatura medida representa el estado observado, mientras que la consigna expresa el objetivo que debe seguir el controlador. Un usuario remoto puede necesitar modificar legítimamente esa consigna o la duración del descongelamiento. Por ello, impedir toda modificación haría imposible parte de la operación: el problema consiste en distinguir cambios esperados de acciones indebidas y responder sin perder trazabilidad.

En una organización, una cuenta de mantenimiento puede habilitar operaciones sobre varios equipos. Si esa cuenta es utilizada por una persona no autorizada, una autenticación correcta no garantiza una operación legítima. Tampoco una temperatura todavía normal descarta una manipulación: el efecto térmico puede aparecer después de la orden. Esta diferencia temporal motiva observar los cambios de configuración y sus autorizaciones, además de las mediciones.

El escenario ficticio KOTTO representa una única unidad de refrigeración. Participan una estación de administración, una estación que reproduce el uso indebido de una cuenta, un PLC simulado y un SOC de laboratorio. No se emplean equipos comerciales, datos de clientes ni conexiones hacia dispositivos de terceros. El entorno reproduce intercambios HTTP reales entre procesos; el comportamiento físico es una aproximación matemática.

La guía de seguridad OT del NIST sitúa estos sistemas en un contexto donde el control del entorno físico convive con requisitos particulares de rendimiento, fiabilidad y seguridad (Stouffer et al., 2023). En esta experiencia, esa distinción se refleja en conservar la simulación activa durante la contención: se restringen las órdenes remotas y se restaura la configuración, sin equiparar el bloqueo de acceso con apagar un equipo.
## Problema delimitado
¿Cómo detectar y contener modificaciones realizadas con credenciales válidas cuando el cambio carece de aprobación operativa, incluso si sus valores están dentro del rango habitual? El trabajo aborda esa pregunta con un registro de autorizaciones independiente del controlador y con una comparación entre respuesta habilitada y deshabilitada.

<!-- PAGE -->
# 2. Antecedente y justificación
En octubre de 2026, el CERT-FR publicó la alerta CERTFR-2026-ALE-012 sobre compromisos de controladores remotos de refrigeración. La versión consultada, actualizada el 16 de octubre, identifica las familias Danfoss AK-SM y AK-SC, Copeland XWEB y Dixell XWEB. Entre sus recomendaciones figuran retirar la exposición directa a Internet, verificar la configuración y restablecer accesos mediante una red protegida o VPN (CERT-FR, 2026).

Este antecedente justifica estudiar la relación entre administración remota y control de parámetros. No permite afirmar que nuestra maqueta reproduce el acceso inicial, la vulnerabilidad o las técnicas exactas empleadas en aquellos incidentes. Tampoco se atribuye una pérdida económica específica a Carrefour: ese dato no es necesario para evaluar el prototipo y no se dispone de una cuantificación propia verificable para esa empresa.

En el laboratorio se adopta una precondición explícita: el atacante posee la contraseña de una cuenta de mantenimiento. El ejecutor entrega una credencial efímera a la estación de prueba. No se desarrolla una técnica para obtenerla y no se explotan productos reales. Esta elección concentra el experimento en lo que ocurre después de un acceso autenticado: modificación, registro, detección, respuesta y verificación posterior.

La utilidad educativa consiste en poder mostrar el mismo hecho desde distintas fuentes. El tráfico revela el intercambio entre direcciones; el controlador informa qué parámetros cambió; Django conserva la autorización esperada, la alerta y las actuaciones. La correlación evita que una dirección IP o una lectura aislada se presente como prueba suficiente de identidad o intención.
## Aporte de la experiencia
El aporte es una implementación reproducible que vincula cambios con aprobaciones de un solo uso y permite observar una defensa efectiva sobre sesiones. Su evaluación es funcional: verifica comportamientos concretos dentro de condiciones conocidas. No propone un algoritmo novedoso ni certifica seguridad industrial. La relación entre autorización, evidencia y respuesta ofrece una forma accesible de integrar contenidos de la diplomatura en un caso aplicado.

<!-- PAGE -->
# 3. Objetivos, pregunta y alcance
## Objetivo general
Implementar y evaluar un laboratorio de refrigeración simulada que detecte cambios de parámetros sin autorización previa, contenga el acceso utilizado y documente la recuperación y las evidencias del experimento.
## Objetivos específicos
Relacionar en SQL equipos, mediciones, cambios, aprobaciones, eventos y casos. Separar las funciones de operación y respuesta en el controlador. Implementar una regla que contraste la cuenta, los valores y el horario de un cambio con una aprobación de un solo uso. Preservar registros y tráfico con metadatos y hashes. Comparar reintentos y evolución térmica con y sin respuesta. Documentar los límites para evitar extrapolar la maqueta a instalaciones reales.
## Pregunta de investigación
¿Puede un SOC de laboratorio detectar una modificación sin aprobación aunque sus valores estén dentro de los rangos operativos, y contener los siguientes intentos de la cuenta utilizada?
## Criterios de cumplimiento
Un cambio aprobado debe consumirse una sola vez y no producir una alerta de autorización. Un cambio sin aprobación debe generar una alerta aunque su consigna sea admisible. Con defensa activa, la siguiente orden de la sesión y un nuevo inicio de sesión de la cuenta deben ser rechazados. La recuperación debe restablecer los parámetros de referencia manteniendo la restricción remota. Los archivos preservados deben conservar sus hashes al verificarlos.
## Alcance y exclusiones
Se utiliza un controlador Python, una unidad térmica simplificada, cuentas efímeras y estaciones lógicas. La comunicación usa HTTP en una red temporal sin salida a Internet. Se excluyen hardware industrial, protocolos de fabricante, explotación de vulnerabilidades, captura de tráfico ajeno, valoración económica, análisis de conservación de alimentos y atribución personal. TLS, persistencia de bloqueos, segmentación entre estaciones y alta disponibilidad quedan como mejoras futuras.

Las mediciones permiten comparar respuestas del modelo, no determinar cuánto tardaría una cámara real en recuperarse. Del mismo modo, el tiempo entre registro y alerta describe esta ejecución local y no un acuerdo de nivel de servicio.

<!-- PAGE -->
# 4. Arquitectura y comunicación
El laboratorio se ejecuta en Linux mediante un namespace de usuario y de red. El namespace de red contiene solamente la interfaz loopback y no tiene ruta predeterminada. El ejecutor comprueba esas condiciones antes de iniciar el experimento. Las direcciones 127.0.0.x son válidas dentro de esa red temporal; no corresponden a equipos externos ni a la LAN doméstica.

La administración, el atacante, el PLC y el monitor son procesos diferentes. El servidor del PLC escucha en 127.0.0.20:8001. Cada cliente establece explícitamente su dirección de origen. Django registra los resultados en la base local compartida por el usuario; la interfaz administrativa web se ejecuta fuera del namespace y se consulta en 127.0.0.1:8000. El aislamiento es de red, no de almacenamiento ni de usuarios del sistema operativo.

[[ARCHITECTURE]]

El tráfico transporta solicitudes JSON mediante HTTP. La captura se inicia antes de la actividad de las estaciones y utiliza un filtro exclusivo del PLC. La elección de texto claro permite inspeccionar el intercambio en un entorno didáctico, pero implica que la captura contiene credenciales efímeras y tokens. Por ese motivo, los PCAP completos se conservan localmente y no forman parte del repositorio público ni del paquete público de código.

Separar procesos hace posible observar paquetes reales; asignar direcciones diferentes facilita la lectura del experimento. Sin embargo, no constituye segmentación mediante firewall entre estaciones. Un despliegue más amplio debería separar zonas, restringir flujos y proteger el canal. La arquitectura actual pretende que el ejercicio sea repetible en un equipo Linux, con pocos componentes y sin depender de infraestructura de producción.

<!-- PAGE -->
# 5. PLC simulado y modelo de comportamiento
El servidor Python mantiene la temperatura, la consigna, la duración de descongelamiento, las sesiones y el estado de bloqueo. El valor inicial es 3 °C y la duración de referencia es 20 minutos. Cada solicitud actualiza la temperatura según el tiempo transcurrido, por lo que no existe un sensor físico ni un proceso termodinámico validado.

El modelo utiliza la relación T_nueva = T_anterior + (T_objetivo - T_anterior) × (1 - exp(-Δt/10)). El objetivo se calcula como consigna + max(0, minutos_descongelamiento - 20) × 0,05. El factor de diez segundos y el incremento asociado al parámetro de descongelamiento son elecciones de la maqueta. No representan capacidades reales de refrigeración, cargas térmicas ni tiempos sanitarios.

El servidor admite consignas entre -30 y 30 °C y duraciones enteras entre 0 y 120 minutos; rechaza valores no finitos, booleanos usados como números y parámetros desconocidos. Estos límites amplios permiten realizar el incidente. La política del SOC es más estrecha: consigna de 2 a 5 °C y duración de 0 a 30 minutos. Por tanto, una solicitud puede ser técnicamente válida para el servidor y, a la vez, quedar fuera de política.

Las rutas de lectura devuelven estado o eventos. La ruta de parámetros registra cuenta, sesión, dirección de origen, hora UTC y valores anteriores y posteriores. Las rutas de contención y recuperación requieren rol SOC. La recuperación vuelve a 3 °C y 20 minutos, sin quitar el bloqueo remoto.
## Distinción necesaria
La temperatura calculada evoluciona gradualmente; restaurar la consigna no devuelve instantáneamente la temperatura a 3 °C. Además, el campo de descongelamiento activo de las mediciones se mantiene en falso: no se implementan ciclos de activación. El parámetro de duración influye de manera agregada en el objetivo matemático. Esta simplificación se declara para que los resultados no se confundan con pruebas de un PLC o de una heladera comercial.

<!-- PAGE -->
# 6. Modelo relacional y trazabilidad
El esquema separa datos operativos de datos de investigación. Una heladera tiene muchas mediciones y cambios de parámetros. Un caso agrupa alertas, evidencias y una línea temporal. Un experimento relaciona un caso con una heladera, una semilla, el estado de la ejecución y la configuración de defensa. Cada ensayo crea su propia heladera lógica, evitando mezclar sus series temporales.

[[SCHEMA]]

La entidad ControllerEvent conserva el contenido recibido del PLC y su secuencia. Una restricción única sobre experimento y secuencia evita duplicar un evento cuando el monitor vuelve a consultar el registro completo. ChangeAuthorization contiene la cuenta autorizada, los valores exactos, una ventana temporal, el aprobador y, cuando corresponde, el evento que consumió la aprobación. ResponseAction documenta la acción enviada, el actor, su hora y la respuesta recibida.

La evidencia se guarda como archivo separado de SQLite. La base mantiene su nombre original, origen, tamaño, responsable, fecha de recolección, fecha de incorporación y hash SHA-256. CustodyEvent registra la incorporación y permite documentar actuaciones posteriores. Los eventos temporales de cambios se vinculan con el archivo del controlador; la captura PCAP recibe una entrada propia de evidencia dentro del caso.

Las claves foráneas utilizan protección frente a borrados de registros referenciados. Las migraciones versionan el esquema y permiten crear una base vacía. Los archivos SQL exportados facilitan inspeccionarlo, pero la instalación usa las migraciones de Django. Los permisos de la aplicación y las restricciones del administrador reducen modificaciones accidentales; no impiden que quien controle el disco altere la base o los archivos.

<!-- PAGE -->
# 7. Autenticación, roles y autorizaciones
La autenticación del PLC crea un token aleatorio con vigencia de quince minutos. El servidor conserva su hash en memoria y lo asocia con una cuenta, un rol y un identificador de sesión. Los operadores pueden modificar parámetros; el rol SOC puede consultar eventos y ejecutar respuesta. Bloquear una cuenta hace que sus tokens dejen de ser aceptados y que nuevos intentos de autenticación sean rechazados.

Django gestiona por separado los usuarios que consultan y documentan el laboratorio. Se configuraron grupos de Consulta, Respuesta y Aprobación. El administrador asigna permisos por modelo y comprueba permisos antes de entregar informes. Este uso de usuarios, grupos y permisos corresponde a las capacidades documentadas del framework (Django Software Foundation, s. f.). El permiso para aprobar cambios no se concede automáticamente al grupo de respuesta.

Una autorización establece experimento, nombre de cuenta del PLC, consigna y duración finales exactas, inicio y vencimiento. El sistema registra al aprobador y el momento de creación. Al observar un cambio, el SOC exige que la aprobación ya existiera a la hora del evento y que este se encuentre dentro de la ventana. Luego la consume mediante una actualización condicional; una aprobación ya consumida no puede justificar un evento posterior.

[[AUTHORIZATION]]

En el ejecutor, la cuenta técnica lab-approver registra explícitamente el cambio legítimo a 4 °C y 20 minutos antes de iniciarlo. La estación atacante no recibe una aprobación. El detector no recibe una etiqueta de ataque ni depende de conocer la dirección del atacante. Evalúa la relación entre lo observado y lo previamente permitido.

Esta comprobación es posterior al cambio. Una cuenta comprometida podría consumir una autorización válida si realiza exactamente la operación aprobada en su ventana; no se identifica a la persona detrás de la cuenta. La integridad del reloj y de los registros del PLC se presupone en la maqueta. La aprobación tampoco invalida los límites operativos: un valor aprobado fuera de política sigue generando una alerta.

<!-- PAGE -->
# 8. Detección, contención y recuperación
El monitor consulta los eventos aproximadamente cada segundo. Para cada cambio nuevo evalúa dos condiciones: existencia de una aprobación válida y cumplimiento de rangos. Si falta aprobación o se excede la política, crea una alerta vinculada al caso y conserva el evento observado. El cambio se clasifica como autorizado o no autorizado según la aprobación, mientras que la desviación de rango queda registrada por separado.

Con defensa habilitada, el SOC solicita primero la contención de la sesión de origen. El PLC bloquea la cuenta asociada y deshabilita las modificaciones remotas de los operadores. Después, el SOC solicita restaurar la configuración de referencia. Cada solicitud produce un registro ResponseAction con código HTTP, resultado y responsable. Si la contención falla, el monitor no continúa automáticamente con la recuperación. Un caso solo pasa a contenido después de recibir confirmación de contención.

El bloqueo global de cambios remotos es una decisión conservadora de la maqueta. Mantiene funcionando el cálculo de temperatura, pero también impide modificaciones legítimas posteriores durante ese ensayo. Por ello, no puede trasladarse sin evaluación a una instalación real: deben considerarse necesidades de mantenimiento y mecanismos de recuperación de acceso. En esta versión, un nuevo ensayo inicia un estado limpio.

La respuesta a incidentes requiere conectar detección, actuación y recuperación con la gestión del riesgo; esa relación orienta el uso de casos y evidencias de este trabajo (Nelson et al., 2025). No se afirma cumplimiento integral de la publicación ni de una norma de certificación.
## Límites de continuidad
El monitor es un comando ejecutado durante el ensayo, no un servicio de alta disponibilidad. Si pierde conexión, termina. No renueva automáticamente su sesión de quince minutos ni reintenta una respuesta interrumpida entre etapas. La memoria del PLC no conserva sesiones ni bloqueos tras reiniciarse. Estas limitaciones explican por qué se evalúan ejecuciones cortas y controladas, y constituyen trabajos futuros.

<!-- PAGE -->
# 9. Captura de tráfico y preservación
La adquisición utiliza tcpdump sobre loopback dentro de la red temporal. El filtro de captura es «host 127.0.0.20 and tcp port 8001». Se guardan únicamente paquetes relacionados con el servicio del PLC, incluyendo administración, monitoreo y estación atacante. La captura tiene una duración aproximada de quince segundos; la telemetría continúa hasta los dieciocho segundos. Por tanto, no se afirma que el PCAP contenga todos los últimos instantes de recuperación.

La estación atacante utiliza 127.0.0.30. En Wireshark, el filtro de visualización «ip.addr == 127.0.0.30» permite concentrarse en su intercambio sin modificar el archivo original. Se distinguen el filtro aplicado al guardar tráfico y el filtro aplicado al leerlo. Los paquetes permiten observar origen, destino, tiempos y respuestas, mientras que los registros del PLC aportan el significado operativo del cambio.

Al finalizar una ejecución completa se incorporan cuatro archivos: controller.jsonl, traffic.pcap, results.json y tcpdump.log. La función de incorporación copia el archivo al almacenamiento de evidencias, calcula SHA-256 sobre esa copia y registra custodia inicial. El verificador recalcula el hash y falla ante cambios o archivos ausentes. El hash detecta diferencias respecto del valor conservado; no demuestra por sí mismo autenticidad si un administrador puede alterar ambos.

Los informes muestran hashes y metadatos, pero no exponen contraseñas ni tokens. Los PCAP originales quedan fuera del repositorio público porque HTTP transporta credenciales efímeras del ensayo. Para una presentación se utilizan tablas y gráficos derivados, no volcados completos del contenido de las solicitudes.
## Criterio de atribución
La dirección del cliente identifica una estación lógica configurada por el experimento. No prueba identidad personal ni basta para determinar intención. La conclusión de cambio sin autorización se fundamenta en la cuenta registrada, los valores, el momento y la ausencia de una aprobación coincidente. Las fuentes se correlacionan por hora UTC y por contexto del evento; no se realizó un peritaje judicial.

<!-- PAGE -->
# 10. Metodología experimental
Se realizó una evaluación funcional de tres escenarios en la versión con autorizaciones. Cada ejecución crea un namespace independiente, cuentas efímeras, un caso y una heladera lógica. Se inicia la captura, se arranca el PLC y se activa el monitor. La estación de administración ejecuta primero el cambio aprobado a 4 °C y 20 minutos. Después actúa la estación que representa la cuenta de mantenimiento comprometida.

El experimento 5 utiliza una consigna de 5 °C y 25 minutos, ambos dentro de política, sin aprobación y con defensa activa. El experimento 6 utiliza 15 °C y 45 minutos, fuera de política, con defensa activa. El experimento 7 repite el cambio dentro de rango del experimento 5, pero sin ejecutar respuesta. Esta pareja permite comparar el efecto de la defensa sobre los reintentos y la evolución térmica bajo una misma configuración maliciosa.

Tres segundos después de su primera solicitud, el atacante repite la orden e intenta iniciar una nueva sesión. El ejecutor conserva los códigos de estado y consulta el estado final. La semilla 42 fija la selección aleatoria cuando corresponde; la opción dentro de rango define explícitamente 5 °C y 25 minutos. No reproduce tiempos idénticos del planificador ni del tráfico.

[[MATRIX]]

Se miden la demora desde la hora del evento hasta crear la primera alerta, los resultados de reintento y nueva autenticación, la consigna final y la temperatura simulada final. Se comprueba además que el cambio legítimo tenga autorización consumida y no genere alerta. Los archivos de cada ensayo se preservan y verifican antes de elaborar los informes.

El tamaño de muestra es una ejecución por escenario. No se calculan intervalos de confianza ni tasas generales de detección. Las pruebas automatizadas cubren casos de borde del software, pero no sustituyen repeticiones experimentales ni pruebas con hardware. Los ensayos anteriores sin autorizaciones se excluyen de la tabla principal para no mezclar versiones del detector.

<!-- PAGE -->
# 11. Resultados observados
[[RESULTS]]

Los tres cambios legítimos iniciales consumieron su aprobación y no produjeron alertas. El experimento 5 mostró que una consigna admisible no basta para legitimar una operación: el SOC detectó la falta de aprobación, pese a que ambos valores estaban dentro de política. La primera alerta se creó 0,272 segundos después del evento registrado. Con defensa, el siguiente uso del token recibió HTTP 401 y el nuevo inicio de sesión de la cuenta recibió HTTP 403.

En el experimento 6 se observó la misma contención para un cambio fuera de rango. La demora de la primera alerta fue 0,291 segundos. La recuperación restableció 3 °C y 20 minutos y mantuvo el bloqueo de cambios remotos. La temperatura final observada en la respuesta de estado fue 3,136 °C. No equivale a una validación térmica industrial.

En el experimento 7, el monitor continuó detectando cambios, pero la respuesta estaba deshabilitada. El reintento y el nuevo acceso recibieron HTTP 200. Se produjeron dos alertas porque hubo dos órdenes sin aprobación, no porque se modelaran dos atacantes o dos incidentes independientes. La consigna final permaneció en 5 °C y la temperatura simulada llegó a 4,775 °C.

Las latencias inferiores a un segundo son observaciones de estas ejecuciones y dependen de la fase de consulta. No prueban una latencia máxima, una media estable ni un comportamiento bajo carga. Tampoco se deriva una tasa universal de falsas alarmas: se comprobó únicamente la ausencia de alertas en los tres cambios aprobados observados.

Fuente de las tablas y cifras: resultados.json y registros de Django de los experimentos 5, 6 y 7, ejecutados el 29 de octubre de 2026; exportación y verificación del 30 de octubre. Los hashes de las doce evidencias fueron recalculados satisfactoriamente durante el cierre.

<!-- PAGE -->
# 12. Evolución térmica y comparación
[[CHART]]

La figura compara las mediciones almacenadas de los experimentos 5 y 7, alineadas por segundos desde la primera muestra de cada uno. Ambos incluyen un cambio legítimo previo y una modificación posterior a 5 °C y 25 minutos sin aprobación. La serie con defensa retorna hacia la configuración de referencia; la serie sin defensa continúa acercándose al objetivo alterado. La alineación es relativa y no implica que las solicitudes ocurrieran en el mismo milisegundo.

Las muestras en SQL se conservan con dos decimales, mientras que la respuesta final del PLC entrega tres decimales. Por eso la tabla final y el último punto del gráfico pueden mostrar redondeos o instantes ligeramente diferentes. El gráfico no interpola supuestas lecturas de un sensor: une las observaciones disponibles para facilitar su lectura.

La diferencia observada es consistente con el diseño: la contención impide repetir órdenes y la recuperación cambia el objetivo del modelo. No permite cuantificar ahorro económico, calidad de alimentos o tiempo real de reparación. Tampoco separa el efecto individual del cambio de consigna y del parámetro de descongelamiento, ya que ambos se modifican juntos en el escenario.
## Interpretación de utilidad
La principal evidencia de defensa no es que la curva baje, sino que el servidor rechaza nuevas acciones de la cuenta comprometida y deja constancia de la recuperación. La curva complementa esa verificación mostrando una consecuencia dentro de la simulación. La combinación de códigos de respuesta, eventos y mediciones permite evaluar la secuencia con mayor claridad que cualquiera de esas fuentes por separado.

<!-- PAGE -->
# 13. Pruebas de software y control de calidad
El cierre del prototipo incluyó doce pruebas automatizadas. Se verificó que la copia preservada siga íntegra aunque cambie el archivo original y que una alteración de la copia sea detectada. Se comprobó la deduplicación de eventos, la necesidad de permisos para acceder al informe y la diferencia entre una operación legítima y una modificación sin aprobación dentro del rango.

Las pruebas de autenticación incluyen ausencia de sesión, expiración y separación entre roles de operación y SOC. Las de contención comprueban revocación efectiva, rechazo de nueva autenticación y restauración de parámetros manteniendo el bloqueo. Las de entradas comprueban que valores inválidos no produzcan escrituras parciales. Las de autorización incluyen cuenta y valor incorrectos, vencimiento, uso anterior al inicio, aprobación retroactiva y reutilización.

[[TESTS]]

Las doce pruebas pasaron en la revisión final. También se comprobó que el modelo no tenga migraciones pendientes. La verificación de las evidencias de los tres ensayos finales confirmó doce archivos íntegros. Estos controles justifican afirmar que los recorridos ensayados funcionan; no constituyen cobertura exhaustiva de seguridad ni pruebas de rendimiento.

Los ensayos fallidos de preparación se mantienen identificados como tales y no forman parte de la muestra principal. Durante el desarrollo se encontró una dificultad al cerrar una captura dentro del namespace; la versión utilizada en los ensayos completos incorpora una duración acotada. La terminación excepcional de procesos y los permisos de captura requieren validación específica en cada sistema Linux.

La aplicación tiene configuración de desarrollo local y no debe exponerse como servicio público. El código fuente puede compartirse sin la base de datos ni las evidencias originales. La instalación nueva requiere crear sus propios usuarios; las credenciales del equipo de desarrollo no se distribuyen.

<!-- PAGE -->
# 14. Discusión, limitaciones y conclusiones
La experiencia respondió a la pregunta planteada dentro del alcance de la maqueta. El SOC detectó una modificación sin aprobación aunque sus valores fueran admisibles, y el PLC rechazó los siguientes intentos cuando la defensa estuvo activa. El contraste sin respuesta conservó el cambio y permitió continuar a la cuenta comprometida. La autorización previa aporta información que una regla de temperatura o rango por sí sola no contiene.

El registro de aprobaciones introduce nuevas dependencias: debe estar protegido, sus fechas deben ser confiables y la identidad de la cuenta debe registrarse correctamente. Una cuenta comprometida que ejecute exactamente una operación aprobada puede consumirla. El modelo tampoco demuestra quién operó la cuenta. La autorización de un cambio debe interpretarse como correspondencia con un permiso registrado, no como prueba absoluta de legitimidad humana.

La contención es amplia: deshabilita cambios remotos de todos los operadores. Aunque mantiene activo el modelo térmico, puede impedir mantenimiento legítimo. La recuperación utiliza valores predefinidos de la maqueta y no una configuración validada por un especialista industrial. El monitor y el controlador no son tolerantes a fallos; una interrupción entre la ingestión y la respuesta puede dejar una actuación pendiente sin reintento automático.

No se implementaron TLS, persistencia de sesiones o bloqueos, firewall entre estaciones, almacenamiento inmutable ni detección de manipulación del propio registro. La evaluación consta de tres ensayos cortos y no incluye carga, latencia de redes remotas, múltiples adversarios o sensores físicos. Estos límites deben mantenerse en cualquier presentación de los resultados.
## Propuestas futuras
Priorizar autenticación del canal y TLS; preservar el estado de contención al reiniciar; renovar las sesiones del monitor; implementar una cola transaccional de acciones pendientes y reintentos idempotentes; separar estaciones mediante reglas de red; proteger aprobaciones y custodia; ampliar ensayos con variaciones de carga y fallos. Una fase posterior podría exigir autorización antes de aplicar la orden, comparando prevención con detección posterior.
## Conclusión
El prototipo ofrece una demostración verificable de autorización, detección, contención y recuperación con evidencias correlacionadas. Su valor reside en hacer observable y reproducible ese recorrido, manteniendo explícita la distancia entre una maqueta educativa y una solución industrial.

<!-- PAGE -->
# 15. Reproducción y guía de demostración
La ejecución requiere Linux, Python 3.12, soporte de entornos virtuales, iproute2, unshare y tcpdump. Deben estar permitidos los namespaces de usuario. Se instala Django mediante requirements.txt y se aplican las migraciones. El ejecutor no necesita salida a Internet durante el ensayo; la descarga inicial de dependencias sí puede necesitarla.

[[COMMANDS]]

Para demostrar el trabajo, abrir el administrador de Django y seleccionar el experimento 5. Mostrar su aprobación consumida, el cambio legítimo, la alerta del cambio sin aprobación y las dos acciones de respuesta. Luego abrir el experimento 7 y contrastar los códigos de reintento y el estado final. El informe descargable reúne la línea temporal y hashes. No es necesario ejecutar de nuevo el incidente durante la exposición si se dispone de las evidencias preservadas.

Cada ejecución requiere una carpeta nueva para no sobrescribir resultados. La semilla y las opciones deben anotarse junto con versiones y fecha. El comando de verificación debe ejecutarse después de copiar o trasladar evidencia. Si se desea observar tráfico, abrir localmente el PCAP en Wireshark, sin compartir sus cargas HTTP; mostrar solamente los campos necesarios o extractos anonimizados.

El repositorio de referencia es https://github.com/FlavertT/kotto-laboratorio-soc. Para asegurar la disponibilidad de la versión evaluada, la entrega incluye además un paquete de código sin credenciales, base local, capturas ni archivos de entorno virtual. Las instrucciones y migraciones permiten reconstruir el esquema; los ensayos generan datos nuevos, no duplican exactamente los tiempos de los resultados aquí presentados.

La monografía y la presentación identifican a los tres integrantes. La entrega académica debe realizarla una sola persona del grupo, conforme a la consigna. La publicación del repositorio no sustituye la carga de los dos PDF en la plataforma institucional.

<!-- PAGE -->
# Referencias bibliográficas
CERT-FR. (2026, 16 de octubre). Incident de sécurité ciblant les contrôleurs à distance des installations de réfrigération (CERTFR-2026-ALE-012). Agence nationale de la sécurité des systèmes d’information. https://cert.cyber.gouv.fr/alerte/CERTFR-2026-ALE-012/

Django Software Foundation. (s. f.). Using the Django authentication system. Django documentation, versión 5.2. Recuperado el 30 de octubre de 2026, de https://docs.djangoproject.com/en/5.2/topics/auth/default/

Nelson, A., Rekhi, S., Souppaya, M., & Scarfone, K. (2025). Incident response recommendations and considerations for cybersecurity risk management: A CSF 2.0 community profile (NIST Special Publication 800-61 Rev. 3). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-61r3

Stouffer, K., Pease, M., Tang, C., Zimmerman, T., Pillitteri, V., Lightman, S., Hahn, A., Saravia, S., Sherule, A., & Thompson, M. (2023). Guide to operational technology (OT) security (NIST Special Publication 800-82 Rev. 3). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-82r3

## Material propio y disponibilidad
Echave, I., Rodriguez, A., & Sistro, F. (2026). KOTTO: Laboratorio SOC y análisis forense [Código de maqueta y documentación del trabajo grupal]. https://github.com/FlavertT/kotto-laboratorio-soc

Los resultados proceden de los ensayos 5, 6 y 7 del proyecto. Los archivos derivados de entrega contienen series de mediciones, resultados y hashes; las capturas originales y credenciales efímeras permanecen en almacenamiento local. El material propio no constituye una fuente independiente para validar hechos del incidente francés.

## Nota sobre las fuentes
El antecedente se sustenta en la alerta oficial del CERT-FR. Las publicaciones del NIST aportan contexto conceptual; no se presenta el prototipo como una implementación certificada de esas guías. La documentación de Django sustenta el uso de grupos y permisos. Las decisiones de rangos, tiempos y respuesta pertenecen al diseño de la maqueta y no se atribuyen a recomendaciones industriales universales.
