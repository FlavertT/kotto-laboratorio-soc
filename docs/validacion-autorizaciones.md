# Validación de autorizaciones — 29 de octubre de 2026

12 pruebas automatizadas aprobadas. Tres ensayos de red aislada con semilla 42; no constituyen una evaluación estadística.

| Experimento | Defensa | Consigna atacante | Alertas | Latencia primera alerta | Reintento | Temperatura final |
|---|---|---|---|---|---|---|
| 5 | True | 5 °C | 1 | 0.272 s | HTTP 401 | 3.058 °C |
| 6 | True | 15 °C | 1 | 0.291 s | HTTP 401 | 3.136 °C |
| 7 | False | 5 °C | 2 | 0.302 s | HTTP 200 | 4.775 °C |

Todos los cambios legítimos tuvieron aprobación consumida y cero alertas. Se verificaron las 12 evidencias de los tres ensayos. Sin defensa, cada nueva orden sin autorización genera su alerta; no se debe confundir ese recuento con varios incidentes independientes.

La regla usa cuenta, valores finales exactos, experimento, ventana temporal y aprobación previa de un solo uso. El control es posterior a la aplicación del cambio, no preventivo. Una cuenta comprometida puede consumir una autorización válida coincidente. El reloj y los registros del PLC son fuentes confiadas en esta maqueta.
