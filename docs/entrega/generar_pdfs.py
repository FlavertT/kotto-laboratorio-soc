from pathlib import Path
import json,re,html
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,Flowable
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_JUSTIFY
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/pdf';OUT.mkdir(parents=True,exist_ok=True)
for name,file in [('DV','DejaVuSans.ttf'),('DVB','DejaVuSans-Bold.ttf')]:
 pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/dejavu/'+file))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DVB',italic='DV',boldItalic='DVB')
navy=colors.HexColor('#102b46');teal=colors.HexColor('#007d83');red=colors.HexColor('#b24535');gray=colors.HexColor('#53616c')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyX',fontName='DV',fontSize=10.2,leading=15.2,spaceAfter=10,alignment=TA_JUSTIFY,textColor=navy))
styles.add(ParagraphStyle(name='HeadX',fontName='DVB',fontSize=19,leading=24,spaceAfter=18,textColor=navy))
styles.add(ParagraphStyle(name='SubX',fontName='DVB',fontSize=11.4,leading=16,spaceBefore=10,spaceAfter=8,textColor=teal))
styles.add(ParagraphStyle(name='CellX',fontName='DV',fontSize=8.5,leading=12,textColor=navy))
P=lambda text,style='BodyX':Paragraph(html.escape(text),styles[style])
data=json.loads((ROOT/'docs/entrega/resultados.json').read_text())

def table(rows,widths=None):
 t=Table([[P(str(x),'CellX') for x in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dcebf0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),.5,teal),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f6f8')])]))
 return t

class Chart(Flowable):
 def __init__(self,w=480,h=225):self.width=w;self.height=h
 def draw(self):
  c=self.canv;w=self.width;h=self.height;l=38;b=35;pw=w-55;ph=h-65
  c.setFont('DV',8)
  for temp in [3,3.5,4,4.5,5]:
   y=b+(temp-3)/2*ph;c.setStrokeColor(colors.HexColor('#dde3e7'));c.line(l,y,l+pw,y);c.setFillColor(gray);c.drawRightString(l-6,y-3,str(temp))
  for secs in [0,5,10,15,20]:
   x=l+secs/20*pw;c.setFillColor(gray);c.drawCentredString(x,b-15,str(secs))
  for exp,col in [(data[0],teal),(data[2],red)]:
   c.setStrokeColor(col);c.setLineWidth(2);path=c.beginPath();start=datetime.fromisoformat(exp['measurements'][0]['timestamp'])
   for i,m in enumerate(exp['measurements']):
    t=(datetime.fromisoformat(m['timestamp'])-start).total_seconds();x=l+t/20*pw;y=b+(m['temperature']-3)/2*ph
    (path.moveTo if i==0 else path.lineTo)(x,y)
   c.drawPath(path)
  c.setFillColor(navy);c.drawString(0,h-10,'Temperatura (°C)');c.drawCentredString(l+pw/2,1,'Segundos desde la primera medición')
  c.setFillColor(teal);c.drawString(l+105,h-10,'Con defensa · E5');c.setFillColor(red);c.drawString(l+260,h-10,'Sin defensa · E7')

class Architecture(Flowable):
 def __init__(self): self.width=480; self.height=155
 def draw(self):
  c=self.canv
  boxes=[(0,95,140,45,'Administración','127.0.0.11'),(0,15,140,45,'Atacante simulado','127.0.0.30'),(195,55,120,55,'PLC Python','127.0.0.20:8001'),(355,55,125,55,'SOC / monitor','127.0.0.10')]
  for x,y,w,h,a,b in boxes:
   c.setFillColor(colors.HexColor('#e9f1f4'));c.setStrokeColor(teal);c.roundRect(x,y,w,h,5,fill=1,stroke=1)
   c.setFillColor(navy);c.setFont('DVB',9);c.drawCentredString(x+w/2,y+h-17,a);c.setFont('DV',8);c.drawCentredString(x+w/2,y+12,b)
  c.setStrokeColor(teal);c.setLineWidth(1.3)
  for sy in (117,37):
   c.line(140,sy,166,sy);c.line(166,sy,166,82);c.line(166,82,193,82)
  c.line(315,82,353,82)
  c.setFillColor(teal);c.setFont('DV',9);c.drawCentredString(335,95,'HTTP')
  c.setFillColor(gray);c.setFont('DV',8);c.drawString(195,20,'Red temporal: solo loopback, sin Internet')

def insert(tag):
 if tag=='ARCHITECTURE':return Architecture()
 if tag=='SCHEMA':return table([['Relación','Cardinalidad / propósito'],['Heladera → Medición / Cambio','Una a muchas; historial operativo'],['Caso → Experimento','Uno a uno; identifica el ensayo'],['Experimento → Evento / Autorización','Uno a muchos; secuencias y permisos'],['Autorización → Evento consumido','Como máximo uno; evita reutilización'],['Evento → Acción de respuesta','Uno a muchas; resultados de actuación'],['Caso → Evidencia → Custodia','Archivos, hashes y actuaciones']], [210,270])
 if tag=='AUTHORIZATION':return table([['Condición','Comprobación'],['Identidad y alcance','Mismo experimento y cuenta del PLC'],['Valores','Coincidencia exacta de ambos valores finales'],['Tiempo','Creada antes del evento y dentro de vigencia'],['Uso','Sin evento consumidor previo'],['Política adicional','Rangos seguros de la maqueta']], [150,330])
 if tag=='MATRIX':return table([['Ensayo','Solicitud sin aprobación','Defensa'],['E5','5 °C / 25 minutos','Activa'],['E6','15 °C / 45 minutos','Activa'],['E7','5 °C / 25 minutos','Desactivada']], [70,280,130])
 if tag=='RESULTS':return table([['Ensayo','Primera alerta','Reintento / login','T final'],['E5','0,272 s','401 / 403','3,058 °C'],['E6','0,291 s','401 / 403','3,136 °C'],['E7','0,302 s','200 / 200','4,775 °C']], [65,125,180,110])
 if tag=='CHART':return Chart()
 if tag=='TESTS':return table([['Área','Verificación'],['Evidencias','Copia independiente y detección de alteración'],['Autenticación','Sesión, expiración y separación de roles'],['Respuesta','Revocación y recuperación sin desbloquear'],['Autorizaciones','Uso único, valores, identidad y fechas'],['Monitoreo','Cambio legítimo y cambio indebido dentro de rango'],['Acceso al informe','Permisos de consulta exigidos']], [130,350])
 if tag=='COMMANDS':return table([['Paso','Comando desde la raíz'],['Entorno','python3 -m venv .venv'],['Dependencias','.venv/bin/python -m pip install -r requirements.txt'],['Base y usuarios','.venv/bin/python manage.py migrate\n.venv/bin/python manage.py createsuperuser'],['Comprobación','.venv/bin/python manage.py test soc lab'],['Con defensa','./lab/run-isolated.sh --output runs/demo-con --seed 42 --within-range'],['Sin defensa','./lab/run-isolated.sh --output runs/demo-sin --seed 42 --within-range --no-defense'],['Interfaz','.venv/bin/python manage.py runserver 127.0.0.1:8000']], [95,385])

source=(ROOT/'docs/entrega/monografia.md').read_text();story=[]
for index,section in enumerate(source.split('<!-- PAGE -->')):
 if index:story.append(PageBreak())
 for block in section.strip().split('\n\n'):
  for part in re.split(r'(\[\[[A-Z]+\]\])',block):
   if not part.strip():continue
   if part.startswith('[['):story.extend([insert(part[2:-2]),Spacer(1,14)]);continue
   if part.startswith('#'):
    for line in part.splitlines():
     if line.startswith('# '):story.append(P(line[2:],'HeadX'))
     elif line.startswith('## '):story.append(P(line[3:],'SubX'))
     else:story.append(P(line))
   else:story.append(P(part.replace('\n',' ')))
 defnoop=None

def footer(c,doc):
 c.setFont('DV',8);c.setFillColor(gray);c.drawString(54,28,'UTN La Plata · KOTTO · Trabajo final grupal');c.drawRightString(541,28,str(doc.page))
name='SISTRO_FLAVIO_KOTTO_Monografia.pdf'
doc=SimpleDocTemplate(str(OUT/name),pagesize=(595.28,841.89),leftMargin=54,rightMargin=54,topMargin=48,bottomMargin=48,title='KOTTO: detección y respuesta ante cambios no autorizados',author='Ignacio Echave; Amparo Rodriguez; Flavio Sistro')
doc.build(story,onFirstPage=footer,onLaterPages=footer)

slides=[
('KOTTO','Detección y respuesta ante cambios no autorizados en refrigeración','PLC simulado con Python y Django\nIgnacio Echave · Amparo Rodriguez · Flavio Sistro\nDiplomatura en Ciberseguridad Aplicada · UTN La Plata\n30 de octubre de 2026'),
('El problema','Una cuenta válida puede realizar un cambio indebido','Temperatura medida ≠ consigna configurada.\nUn valor dentro de rango tampoco demuestra autorización.\nAntecedente: alerta oficial CERTFR-2026-ALE-012.\nLa maqueta estudia el acceso posterior a una credencial comprometida.'),
('La pregunta','¿Detectamos un cambio sin aprobación dentro de rango?','Evaluamos detección, bloqueo de reintentos y recuperación.\nComparamos defensa activa y desactivada.\nEl PLC y el proceso térmico son simulados; los paquetes de red son reales.'),
('Arquitectura','Cuatro procesos en una red temporal sin Internet','Administración 127.0.0.11 → PLC 127.0.0.20:8001\nAtacante 127.0.0.30 → PLC\nSOC 127.0.0.10 ↔ PLC\nDjango conserva registros en SQLite. Captura limitada al servicio del PLC.'),
('Autorizaciones','Una aprobación previa, exacta y de un solo uso','Cuenta + experimento + valores finales + ventana temporal.\nLa aprobación debe existir antes del evento.\nEl evento consume la aprobación; no se puede reutilizar.\nEl detector consulta registros, sin recibir una etiqueta de ataque.'),
('Defensa','Detectar → contener → recuperar → verificar','Alerta por falta de aprobación o exceso de rango.\nBloqueo de la cuenta y de cambios remotos.\nRestauración a 3 °C y 20 minutos sin quitar el bloqueo.\nCada acción conserva responsable, hora y resultado.'),
('Experimentos','Tres ensayos con semilla 42','E5: 5 °C / 25 min sin aprobación; con defensa.\nE6: 15 °C / 45 min sin aprobación; con defensa.\nE7: mismo cambio que E5; sin defensa.\nTodos comienzan con un cambio legítimo aprobado a 4 °C.'),
('Resultados','El cambio dentro de rango también fue detectado','E5: alerta en 0,272 s; reintento 401; nuevo acceso 403.\nE6: alerta en 0,291 s; reintento 401; nuevo acceso 403.\nE7: alerta en 0,302 s; reintento y acceso permitidos (200).\nCero alertas en los tres cambios legítimos observados.'),
('Evolución','La recuperación cambia el objetivo térmico','CHART'),
('Evidencias','La secuencia queda documentada','12 pruebas automatizadas aprobadas.\n12 evidencias de los ensayos finales con hashes verificados.\nPCAP + registros del PLC + resultados + diagnóstico de captura.\nLos PCAP originales contienen credenciales efímeras: no se publican.'),
('Limitaciones','Resultados funcionales de una maqueta','Una ejecución por escenario; sin inferencia estadística.\nDetección posterior: el primer cambio llega a aplicarse.\nSin TLS, persistencia de bloqueos ni alta disponibilidad.\nLa IP no identifica a una persona y el modelo no evalúa alimentos.'),
('Conclusión','Autorizar el cambio aporta más que vigilar el rango','El SOC detectó la falta de aprobación dentro del rango.\nCon defensa, se rechazaron nuevos intentos y se restauró la consigna.\nPróximo paso: autorización preventiva, TLS y reintentos confiables.\nDemostración: experimentos 5, 6 y 7 en Django.'),
('Fuentes','Antecedente oficial y marco técnico','CERT-FR (2026). CERTFR-2026-ALE-012.\nStouffer et al. (2023). NIST SP 800-82 Rev. 3.\nNelson et al. (2025). NIST SP 800-61 Rev. 3.\nDjango Software Foundation. Documentación 5.2.\nReferencias completas y enlaces en la monografía.'),
]
c=canvas.Canvas(str(OUT/'SISTRO_FLAVIO_KOTTO_Presentacion.pdf'),pagesize=(960,540));c.setTitle('KOTTO · Presentación del trabajo final');c.setAuthor('Ignacio Echave; Amparo Rodriguez; Flavio Sistro')
for i,(kicker,title,body) in enumerate(slides):
 c.setFillColor(colors.HexColor('#f6f8fa'));c.rect(0,0,960,540,fill=1,stroke=0)
 c.setFillColor(teal);c.setFont('DVB',15);c.drawString(48,490,kicker.upper())
 style=ParagraphStyle('title',fontName='DVB',fontSize=30,leading=37,textColor=navy)
 p=Paragraph(html.escape(title),style);w,h=p.wrap(860,110);p.drawOn(c,48,455-h)
 if body=='CHART':
  ch=Chart(800,270);ch.wrap(800,270);ch.drawOn(c,70,95)
  c.setFont('DV',12);c.setFillColor(gray);c.drawString(48,60,'Mediciones propias E5/E7; tiempos relativos. Modelo térmico simplificado.')
 else:
  y=340
  for line in body.split('\n'):
   p=Paragraph(html.escape(line),ParagraphStyle('slidebody',fontName='DV',fontSize=19,leading=27,textColor=navy));w,h=p.wrap(855,100);p.drawOn(c,48,y-h);y-=h+17
  assert y>30,(i,y)
 c.setFont('DV',10);c.setFillColor(gray);c.drawString(48,20,'UTN La Plata · KOTTO');c.drawRightString(910,20,f'{i+1:02d} / {len(slides):02d}')
 c.showPage()
c.save()
print('PDFs creados')
