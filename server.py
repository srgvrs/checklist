import os
import json
import sqlite3
from flask import Flask, request, jsonify, render_template, send_from_directory

app = Flask(__name__)
DB_PATH = 'roadmap.db'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Contenido detallado de cada fase (el diccionario grande que ya tenías)
PHASES = {
    1: {
        "title": "Fundamentos — meses 1 a 3",
        "sub": "Linux · redes · Python · Git",
        "weeks": [
            {"title": "Semana 1-3: Linux profundo",
             "desc": "Sistema de archivos, permisos, procesos, logs del sistema (journalctl), systemd, bash scripting. Lectura obligatoria: The Linux Command Line (completo). Práctica: instala Ubuntu Server en VM y realiza todas las tareas del libro."},
            {"title": "Semana 4-5: Redes",
             "desc": "Modelo TCP/IP, DNS, HTTP/HTTPS, handshake TLS, firewalls (iptables/nftables). Usa tcpdump y Wireshark para capturar tráfico. Lectura: Computer Networking: A Top-Down Approach (capítulos 1-4)."},
            {"title": "Semana 6-8: Python ofensivo/defensivo",
             "desc": "Sockets, peticiones HTTP, scapy, automatización. Libro: Black Hat Python (2ª ed.). Crea tres scripts: escáner de puertos TCP, cliente-servidor y verificador de cabeceras HTTP."},
            {"title": "Semana 9-10: Git avanzado",
             "desc": "Flujo de trabajo con ramas, pull requests, protección de ramas, hooks. Simula colaboración con otra cuenta."},
            {"title": "Semana 11-12: Documentación del proyecto",
             "desc": "Escribe un README profesional para tu escáner de red. Explica qué hace, cómo usarlo y por qué es útil en seguridad."}
        ],
        "high_time_weeks": [0, 2],
        "subtopics": [
            {"name": "Linux profundo (filesystem, procesos, logs, bash)", "slug": "linux-profundo"},
            {"name": "Redes TCP/IP, DNS, HTTP/S, firewalls", "slug": "redes"},
            {"name": "Python ofensivo/defensivo", "slug": "python-seguridad"},
            {"name": "Git", "slug": "git"}
        ]
    },
    2: {
        "title": "DevOps + seguridad integrada — meses 3 a 7",
        "sub": "Docker · CI/CD seguro · AWS · secrets",
        "weeks": [
            {"title": "Semana 1-2: Docker seguro",
             "desc": "Dockerfile multi-stage, rootless, escaneo de imágenes con Trivy. Libro: Docker Deep Dive (completo)."},
            {"title": "Semana 3-4: AWS IAM y seguridad base",
             "desc": "IAM (usuarios, roles, políticas de mínimo privilegio), CloudTrail, Security Hub. Activa MFA y crea políticas granulares."},
            {"title": "Semana 5-6: CI/CD seguro",
             "desc": "GitHub Actions con SAST (Bandit/Semgrep), secrets en Secrets Manager, escaneo de imagen en pipeline."},
            {"title": "Semana 7-8: OWASP Top 10 práctica",
             "desc": "Usa Juice Shop y DVWA para explotar y mitigar cada vulnerabilidad del Top 10."},
            {"title": "Semana 9-12: Proyecto integrador",
             "desc": "API REST dockerizada, pipeline completo con SAST, Trivy, despliegue en EC2 con IAM restrictivo. Documenta decisiones de seguridad."}
        ],
        "high_time_weeks": [2, 4],
        "subtopics": [
            {"name": "Docker seguro", "slug": "docker-seguro"},
            {"name": "AWS IAM y CloudTrail", "slug": "aws-iam"},
            {"name": "CI/CD seguro (GitHub Actions)", "slug": "cicd-seguro"},
            {"name": "Manejo de secretos", "slug": "secretos"},
            {"name": "OWASP Top 10", "slug": "owasp"}
        ]
    },
    3: {
        "title": "Explorar ofensivo y defensivo — meses 7 a 11",
        "sub": "Pentesting básico · SOC · elegir camino",
        "weeks": [
            {"title": "Semana 1-4: TryHackMe y fundamentos ofensivos",
             "desc": "Completa los paths 'Intro to Pentesting' y 'Web Hacking'. Familiarízate con Kali Linux, Nmap, Metasploit básico."},
            {"title": "Semana 5-8: Laboratorio personal",
             "desc": "Monta un entorno con Kali y Metasploitable 3 / DVWA. Ejecuta y documenta 5 ataques: SQLi, XSS, escalada de privilegios, etc. Escribe writeups."},
            {"title": "Semana 9-12: Cloud security y logs",
             "desc": "Ataques a AWS: escalación en IAM, S3 buckets públicos, metadata service. Detección con CloudWatch y GuardDuty. Publica writeups en blog/GitHub."}
        ],
        "high_time_weeks": [0, 1],
        "subtopics": [
            {"name": "Pentesting básico (Kali, Nmap)", "slug": "pentesting-basico"},
            {"name": "Ataques web (OWASP)", "slug": "ataques-web"},
            {"name": "Cloud security attacks", "slug": "cloud-attacks"},
            {"name": "Monitoreo y detección (CloudWatch)", "slug": "monitoreo"}
        ]
    },
    4: {
        "title": "Infraestructura segura como código — meses 11 a 15",
        "sub": "Terraform · Kubernetes security · compliance",
        "weeks": [
            {"title": "Semana 1-4: Terraform a fondo",
             "desc": "Lee Terraform: Up & Running (caps 1-5). Crea una VPC segura con subnets públicas/privadas, security groups restrictivos."},
            {"title": "Semana 5-6: Política como código",
             "desc": "Integra Checkov y tfsec en GitHub Actions. Define reglas personalizadas con Open Policy Agent (OPA)."},
            {"title": "Semana 7-8: Kubernetes security",
             "desc": "Minikube, RBAC, network policies, pod security standards, escaneo de manifiestos con kubesec."},
            {"title": "Semana 9-12: Proyecto estrella",
             "desc": "Infraestructura completa con Terraform: EC2/ECS + RDS en subred privada, ALB, CloudTrail, Security Hub. Pipeline que aplica políticas antes del despliegue. Modela amenazas con STRIDE."}
        ],
        "high_time_weeks": [0, 3],
        "subtopics": [
            {"name": "Terraform seguro", "slug": "terraform"},
            {"name": "Policy as Code (Checkov, OPA)", "slug": "policy-as-code"},
            {"name": "Kubernetes security", "slug": "kubernetes"},
            {"name": "Threat modeling (STRIDE)", "slug": "threat-modeling"}
        ]
    },
    5: {
        "title": "Búsqueda de empleo remoto — meses 15 a 18",
        "sub": "Certificaciones · portafolio final · posicionamiento",
        "weeks": [
            {"title": "Semana 1-4: Certificación prioritaria 1",
             "desc": "AWS Solutions Architect Associate. Curso de Adrian Cantrill o Stephane Maarek + exámenes de práctica."},
            {"title": "Semana 5-8: Certificación prioritaria 2",
             "desc": "CompTIA Security+ o AWS Security Specialty, según tu camino."},
            {"title": "Semana 9-12: Portafolio y búsqueda activa",
             "desc": "Perfecciona 3-4 proyectos en GitHub. Optimiza LinkedIn. Aplica en plataformas LATAM (arc.dev, Getón Jobs, Revelo)."}
        ],
        "high_time_weeks": [0, 1],
        "subtopics": [
            {"name": "AWS Solutions Architect Associate", "slug": "aws-saa"},
            {"name": "CompTIA Security+ / AWS Security Specialty", "slug": "security-cert"},
            {"name": "Portafolio y LinkedIn", "slug": "empleabilidad"}
        ]
    }
}

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
    # Si la tabla ya existía sin pdf_name, la agregamos
    cols = [row[1] for row in conn.execute("PRAGMA table_info(phases)").fetchall()]
    if 'pdf_name' not in cols:
        conn.execute('ALTER TABLE phases ADD COLUMN pdf_name TEXT')
        conn.commit()
    conn.commit()
    conn.close()

init_db()

# Rutas de páginas
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

# API: obtener estado
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

# API: guardar estado
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

# Subir PDF
@app.route('/api/upload-pdf/<int:phase_id>', methods=['POST'])
def upload_pdf(phase_id):
    if 'pdf' not in request.files:
        return jsonify(error='No se envió archivo'), 400
    file = request.files['pdf']
    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return jsonify(error='Solo PDF'), 400
    filename = f"phase-{phase_id}-{os.times().elapsed}.pdf"
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    conn = sqlite3.connect(DB_PATH)
    original_name = file.filename
    conn.execute('UPDATE phases SET pdf = ?, pdf_name = ? WHERE id = ?', (filename, original_name, phase_id))
    conn.commit()
    conn.close()
    return jsonify(filename=filename, pdf_name=original_name)

# Renombrar PDF
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

# Eliminar PDF
@app.route('/api/delete-pdf/<int:phase_id>', methods=['POST'])
def delete_pdf(phase_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT pdf FROM phases WHERE id = ?', (phase_id,)).fetchone()
    if row and row[0]:
        try:
            os.remove(os.path.join(UPLOAD_FOLDER, row[0]))
        except:
            pass
        conn.execute('UPDATE phases SET pdf = NULL, pdf_name = NULL WHERE id = ?', (phase_id,))
        conn.commit()
    conn.close()
    return jsonify(success=True)

# Servir archivos estáticos (CSS, JS)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# Servir PDFs subidos
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)