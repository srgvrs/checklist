import os
import json
import sqlite3
import time
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, send_from_directory

# Cargar variables desde el archivo .env
load_dotenv()

# Configuración desde variables de entorno (con valores por defecto)
DB_PATH = os.getenv('DB_PATH', 'roadmap.db')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))

app = Flask(__name__)

# Crear carpeta de uploads si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Datos de fases (contenido mejorado) ---
PHASES = {
    1: {
        "title": "Fundamentos — meses 1 a 3",
        "sub": "Linux · redes · Python · Git · bash",
        "weeks": [
            {"title": "Semana 1-3: Linux profundo",
             "desc": "Sistema de archivos, permisos, procesos, logs del sistema (journalctl), systemd, bash scripting. Lectura obligatoria: The Linux Command Line (completo). Práctica: instala Ubuntu Server en VM y realiza todas las tareas del libro. Refuerza el uso de scripts de bash para automatizar tareas de administración y parseo de logs."},
            {"title": "Semana 4-5: Redes",
             "desc": "Modelo TCP/IP, DNS, HTTP/HTTPS, handshake TLS, firewalls (iptables/nftables). Usa tcpdump y Wireshark para capturar tráfico. Lectura: Computer Networking: A Top-Down Approach (capítulos 1-4). Practica siempre en entornos controlados (VMs, red local)."},
            {"title": "Semana 6-8: Python ofensivo/defensivo",
             "desc": "Sockets, peticiones HTTP, scapy, automatización. Libro: Black Hat Python (2ª ed.). Crea tres scripts (solo sobre tus propias VMs o redes autorizadas): escáner de puertos TCP, cliente-servidor y verificador de cabeceras HTTP. Esto es fundamental en seguridad, pero nunca escanees redes ajenas sin permiso."},
            {"title": "Semana 9-10: Git avanzado y bash scripting",
             "desc": "Flujo de trabajo con ramas, pull requests, protección de ramas, hooks. Simula colaboración con otra cuenta. Escribe scripts en bash para automatizar hooks de Git, tareas de despliegue simple y análisis de logs del sistema. Bash es el pegamento de DevSecOps."},
            {"title": "Semana 11-12: Documentación del proyecto",
             "desc": "Escribe un README profesional para tu escáner de red y tus scripts de bash. Explica qué hace cada herramienta, cómo usarla y por qué es útil en seguridad. Un buen portafolio incluye documentación clara."}
        ],
        "high_time_weeks": [0, 2, 3],  # Linux, Python y bash scripting requieren más dedicación
        "subtopics": [
            {"name": "Linux profundo (filesystem, procesos, logs, bash)", "slug": "linux-profundo"},
            {"name": "Redes TCP/IP, DNS, HTTP/S, firewalls", "slug": "redes"},
            {"name": "Python ofensivo/defensivo", "slug": "python-seguridad"},
            {"name": "Git y bash scripting", "slug": "git-bash"}
        ]
    },
    2: {
        "title": "DevOps + seguridad integrada — meses 3 a 7",
        "sub": "Docker · CI/CD seguro · AWS · secrets",
        "weeks": [
            {"title": "Semana 1-2: Docker seguro",
             "desc": "Dockerfile multi-stage, rootless, escaneo de imágenes con Trivy. Libro: Docker Deep Dive (completo). Practica creando imágenes seguras y reduciendo la superficie de ataque."},
            {"title": "Semana 3-4: AWS IAM, seguridad base y automatización con boto3",
             "desc": "IAM (usuarios, roles, políticas de mínimo privilegio), CloudTrail, Security Hub. Activa MFA y crea políticas granulares. Usa boto3 (Python) para automatizar tareas como listar buckets sin cifrar o rotar credenciales. Es una habilidad muy demandada."},
            {"title": "Semana 5-6: CI/CD seguro",
             "desc": "GitHub Actions con SAST (Bandit/Semgrep), secrets en Secrets Manager, escaneo de imagen en pipeline. Todo con mentalidad de 'no confiar en nada'."},
            {"title": "Semana 7-8: OWASP Top 10 práctica",
             "desc": "Usa Juice Shop (principalmente) y DVWA para explotar y mitigar las 5-6 vulnerabilidades más comunes: SQLi, XSS, IDOR, broken authentication y security misconfiguration. No te disperses intentando cubrir todas."},
            {"title": "Semana 9-12: Proyecto integrador",
             "desc": "API REST dockerizada, pipeline completo con SAST, Trivy, despliegue en EC2 con IAM restrictivo. Incluye scripts de bash para automatizar el despliegue local y la auditoría. Documenta decisiones de seguridad."}
        ],
        "high_time_weeks": [2, 4],
        "subtopics": [
            {"name": "Docker seguro", "slug": "docker-seguro"},
            {"name": "AWS IAM, CloudTrail y boto3", "slug": "aws-iam-boto3"},
            {"name": "CI/CD seguro (GitHub Actions)", "slug": "cicd-seguro"},
            {"name": "Manejo de secretos", "slug": "secretos"},
            {"name": "OWASP Top 10 (principales)", "slug": "owasp"}
        ]
    },
    3: {
        "title": "Explorar ofensivo y defensivo — meses 7 a 11",
        "sub": "Pentesting básico · SOC · elegir camino",
        "weeks": [
            {"title": "Semana 1-4: TryHackMe y fundamentos ofensivos",
             "desc": "Completa los paths 'Intro to Pentesting' y 'Web Hacking'. Familiarízate con Kali Linux, Nmap, Metasploit básico. Todo en entornos controlados."},
            {"title": "Semana 5-8: Laboratorio personal",
             "desc": "Monta un entorno con Kali y Metasploitable 3 / DVWA. Ejecuta y documenta 5 ataques: SQLi, XSS, escalada de privilegios, etc. Escribe writeups claros como si fueran reportes profesionales."},
            {"title": "Semana 9-12: Cloud security y logs",
             "desc": "Ataques a AWS: escalación en IAM, S3 buckets públicos, metadata service. Usa CloudGoat de Rhino Security Labs (entorno vulnerable en AWS diseñado para practicar) en lugar de tu cuenta real. Detección con CloudWatch y GuardDuty. Publica writeups en blog o GitHub."}
        ],
        "high_time_weeks": [0, 1],
        "subtopics": [
            {"name": "Pentesting básico (Kali, Nmap)", "slug": "pentesting-basico"},
            {"name": "Ataques web (OWASP)", "slug": "ataques-web"},
            {"name": "Cloud security attacks (CloudGoat)", "slug": "cloud-attacks"},
            {"name": "Monitoreo y detección (CloudWatch)", "slug": "monitoreo"}
        ]
    },
    4: {
        "title": "Infraestructura segura como código — meses 11 a 15",
        "sub": "Terraform · Kubernetes security · compliance",
        "weeks": [
            {"title": "Semana 1-4: Terraform a fondo",
             "desc": "Lee Terraform: Up & Running (caps 1-5). Crea una VPC segura con subnets públicas/privadas, security groups restrictivos. Practica la destrucción y recreación de entornos completos."},
            {"title": "Semana 5-6: Política como código",
             "desc": "Integra Checkov y tfsec en GitHub Actions. Define reglas personalizadas con Open Policy Agent (OPA)."},
            {"title": "Semana 7-8: Kubernetes security",
             "desc": "Minikube, RBAC, network policies, pod security standards, escaneo de manifiestos con kubesec. Para detección de amenazas en runtime, prueba Falco, la herramienta estándar de monitoreo de actividad sospechosa en K8s."},
            {"title": "Semana 9-12: Proyecto estrella",
             "desc": "Infraestructura completa con Terraform: EC2/ECS + RDS en subred privada, ALB, CloudTrail, Security Hub. Pipeline con políticas de seguridad antes del despliegue. Modela amenazas con STRIDE. Documenta todo con diagramas y scripts de bash para automatizar pruebas."}
        ],
        "high_time_weeks": [0, 3],
        "subtopics": [
            {"name": "Terraform seguro", "slug": "terraform"},
            {"name": "Policy as Code (Checkov, OPA)", "slug": "policy-as-code"},
            {"name": "Kubernetes security (Falco)", "slug": "kubernetes"},
            {"name": "Threat modeling (STRIDE)", "slug": "threat-modeling"}
        ]
    },
    5: {
        "title": "Búsqueda de empleo remoto — meses 15 a 18",
        "sub": "Certificaciones · portafolio final · posicionamiento",
        "weeks": [
            {"title": "Semana 1-4: Certificación prioritaria 1",
             "desc": "AWS Solutions Architect Associate. Si quieres entender de verdad cada servicio y su rol en seguridad, elige el curso de Adrian Cantrill (más profundo y técnico). Si necesitas aprobar rápido, el de Stephane Maarek es más directo. Ambos funcionan, pero Cantrill te da mejor base para entrevistas."},
            {"title": "Semana 5-8: Certificación prioritaria 2",
             "desc": "CompTIA Security+ o AWS Security Specialty, según tu camino. La primera es más teórica y reconocida globalmente; la segunda es específica de AWS y muy valorada en roles cloud."},
            {"title": "Semana 9-12: Portafolio y búsqueda activa",
             "desc": "Perfecciona 3-4 proyectos en GitHub (incluye los scripts de bash, herramientas de automatización y writeups). Optimiza LinkedIn. Aplica en plataformas LATAM: arc.dev, Revelo, Getón Jobs. Revelo es actualmente la más usada para trabajo remoto en dólares desde LATAM."}
        ],
        "high_time_weeks": [0, 1],
        "subtopics": [
            {"name": "AWS Solutions Architect Associate", "slug": "aws-saa"},
            {"name": "CompTIA Security+ / AWS Security Specialty", "slug": "security-cert"},
            {"name": "Portafolio y LinkedIn (Revelo, arc.dev)", "slug": "empleabilidad"}
        ]
    }
}

# --- Inicialización de base de datos con soporte de migración simple ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS phases (
            id INTEGER PRIMARY KEY,
            tasks TEXT DEFAULT '[]',
            hours TEXT DEFAULT '{}',
            library TEXT DEFAULT '[]',
            pdf TEXT,
            pdf_name TEXT
        )
    ''')
    # Si la tabla ya existía sin la columna pdf_name, la añadimos
    cols = [row[1] for row in conn.execute("PRAGMA table_info(phases)").fetchall()]
    if 'pdf_name' not in cols:
        conn.execute('ALTER TABLE phases ADD COLUMN pdf_name TEXT')
        conn.commit()
    conn.commit()
    conn.close()

init_db()

# --- Páginas principales ---
@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    progress = {}
    for phase_id in PHASES:
        row = conn.execute('SELECT tasks FROM phases WHERE id = ?', (phase_id,)).fetchone()
        if row:
            tasks = json.loads(row[0] or '[]')
            total = len(PHASES[phase_id]['weeks'])
            completed = sum(tasks) if len(tasks) == total else 0
            progress[phase_id] = (completed, total)
        else:
            progress[phase_id] = (0, len(PHASES[phase_id]['weeks']))
    conn.close()
    return render_template('index.html', phases=PHASES, progress=progress)

@app.route('/phase/<int:phase_id>')
def phase_detail(phase_id):
    if phase_id not in PHASES:
        return "Fase no encontrada", 404
    phase_data = PHASES[phase_id]
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT tasks, hours, library, pdf, pdf_name FROM phases WHERE id = ?', (phase_id,)).fetchone()
    conn.close()
    state = {
        "tasks": json.loads(row[0] or '[]') if row else [],
        "hours": json.loads(row[1] or '{}') if row else {},
        "library": json.loads(row[2] or '[]') if row else [],
        "pdf": row[3] if row else None,
        "pdf_name": row[4] if row and row[4] else (row[3] if row else None)
    }
    return render_template('phase.html', phase_id=phase_id, phase=phase_data, state=state)

# --- Placeholder de exámenes ---
@app.route('/exam/<int:phase_id>/<slug>')
def exam_placeholder(phase_id, slug):
    if phase_id not in PHASES:
        return "Fase no encontrada", 404
    # Buscar el subtopic por slug
    subtopic = next((s for s in PHASES[phase_id]['subtopics'] if s['slug'] == slug), None)
    if not subtopic:
        return "Examen no encontrado", 404
    return render_template('exam.html', phase_id=phase_id, slug=slug, subtopic=subtopic)

# --- API REST (sin autenticación; para desarrollo local) ---
# ⚠️ Si despliegas en un servidor público, protege estas rutas con autenticación.

@app.route('/api/state/<int:phase_id>', methods=['GET'])
def get_state(phase_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT tasks, hours, library, pdf, pdf_name FROM phases WHERE id = ?', (phase_id,)).fetchone()
    conn.close()
    if row:
        return jsonify({
            "tasks": json.loads(row[0] or '[]'),
            "hours": json.loads(row[1] or '{}'),
            "library": json.loads(row[2] or '[]'),
            "pdf": row[3],
            "pdf_name": row[4] or row[3]
        })
    return jsonify({"tasks": [], "hours": {}, "library": [], "pdf": None, "pdf_name": None})

@app.route('/api/state', methods=['POST'])
def save_state():
    data = request.get_json()
    phase_id = data['phaseId']
    phase_data = data['data']
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        INSERT INTO phases (id, tasks, hours, library, pdf, pdf_name)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            tasks = excluded.tasks,
            hours = excluded.hours,
            library = excluded.library,
            pdf = COALESCE(excluded.pdf, phases.pdf),
            pdf_name = COALESCE(excluded.pdf_name, phases.pdf_name)
    ''', (
        phase_id,
        json.dumps(phase_data.get('tasks', [])),
        json.dumps(phase_data.get('hours', {})),
        json.dumps(phase_data.get('library', [])),
        phase_data.get('pdf'),
        phase_data.get('pdf_name')
    ))
    conn.commit()
    conn.close()
    return jsonify(success=True)

@app.route('/api/upload-pdf/<int:phase_id>', methods=['POST'])
def upload_pdf(phase_id):
    if 'pdf' not in request.files:
        return jsonify(error='No se envió archivo'), 400
    file = request.files['pdf']
    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return jsonify(error='Solo PDF'), 400
    # Usar timestamp para evitar colisiones
    filename = f"phase-{phase_id}-{int(time.time())}.pdf"
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    conn = sqlite3.connect(DB_PATH)
    original_name = file.filename
    conn.execute('UPDATE phases SET pdf = ?, pdf_name = ? WHERE id = ?', (filename, original_name, phase_id))
    conn.commit()
    conn.close()
    return jsonify(filename=filename, pdf_name=original_name)

@app.route('/api/rename-pdf/<int:phase_id>', methods=['POST'])
def rename_pdf(phase_id):
    data = request.get_json()
    new_name = data.get('pdf_name')
    if not new_name:
        return jsonify(error='Nombre requerido'), 400
    conn = sqlite3.connect(DB_PATH)
    conn.execute('UPDATE phases SET pdf_name = ? WHERE id = ?', (new_name, phase_id))
    conn.commit()
    conn.close()
    return jsonify(success=True)

@app.route('/api/delete-pdf/<int:phase_id>', methods=['POST'])
def delete_pdf(phase_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT pdf FROM phases WHERE id = ?', (phase_id,)).fetchone()
    if row and row[0]:
        try:
            os.remove(os.path.join(UPLOAD_FOLDER, row[0]))
        except FileNotFoundError:
            pass
        conn.execute('UPDATE phases SET pdf = NULL, pdf_name = NULL WHERE id = ?', (phase_id,))
        conn.commit()
    conn.close()
    return jsonify(success=True)

# --- Archivos estáticos ---
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# --- Inicio del servidor ---
if __name__ == '__main__':
    # En producción, no usar debug=True. Usar un servidor WSGI como gunicorn.
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)