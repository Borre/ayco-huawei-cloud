#!/usr/bin/env bash
# Deploy AYCO Agent Tools mock server on Dify ECS
# Usage: bash scripts/deploy-agent-tools.sh
set -euo pipefail

ECS_IP="${ECS_IP:?FATAL: ECS_IP no definida — usa terraform output dify_eip}"
SSH_KEY="${SSH_KEY_PATH:-~/.ssh/ayco-demo}"
SERVICE_NAME="ayco-tools"

echo "=== Deploying Agent Tools Mock to $ECS_IP ==="

ssh -i "$SSH_KEY" root@$ECS_IP "mkdir -p /opt/ayco/tools"

# Create mock server
ssh -i "$SSH_KEY" root@$ECS_IP "cat > /opt/ayco/tools/server.py << 'PYEOF'
from flask import Flask, jsonify, request
import random, uuid
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'tools': ['aplicar_plan_pago', 'consultar_buro', 'generar_carta']})

@app.route('/aplicar_plan_pago', methods=['POST'])
def aplicar_plan():
    data = request.get_json() or {}
    deuda = data.get('deuda', 50000)
    plan = data.get('plan', 'fijo')
    planes = {
        'fijo': {'plazo': 12, 'cuota': round(deuda/12*1.15, 2)},
        'quita': {'plazo': 1, 'cuota': round(deuda*0.6, 2)},
        'reestructura': {'plazo': 24, 'cuota': round(deuda/24*1.25, 2)}
    }
    p = planes.get(plan, planes['fijo'])
    return jsonify({'plan_id': str(uuid.uuid4())[:8], 'tipo': plan, 'cuota_mensual': p['cuota'], 'plazo_meses': p['plazo']})

@app.route('/consultar_buro', methods=['POST'])
def consultar_buro():
    data = request.get_json() or {}
    cliente_id = data.get('cliente_id', 'CLI-001')
    return jsonify({'cliente_id': cliente_id, 'score': random.randint(580, 720), 'historial': random.choice(['SIN_ATRASOS', 'ATRASO_30', 'ATRASO_60']), 'alertas': random.randint(0, 3)})

@app.route('/generar_carta', methods=['POST'])
def generar_carta():
    data = request.get_json() or {}
    return jsonify({'carta_id': str(uuid.uuid4())[:8], 'tipo': data.get('tipo', 'recordatorio'), 'texto': 'Carta generada exitosamente', 'pdf_url': '/cartas/carta-XXXX.pdf'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8400)
PYEOF"

# Create systemd service
ssh -i "$SSH_KEY" root@$ECS_IP "cat > /etc/systemd/system/$SERVICE_NAME.service << 'EOF'
[Unit]
Description=AYCO Agent Tools Mock Server
After=network.target
[Service]
Type=simple
User=root
WorkingDirectory=/opt/ayco/tools
ExecStart=/usr/bin/python3 server.py
Restart=on-failure
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF"

# Install flask if needed, then start
ssh -i "$SSH_KEY" root@$ECS_IP "pip3 install flask 2>&1 | tail -1 && systemctl daemon-reload && systemctl enable $SERVICE_NAME && systemctl restart $SERVICE_NAME"

sleep 2
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' "http://$ECS_IP:8400/health")
if [ "$HTTP_CODE" = "200" ]; then
    echo "Agent Tools UP: http://$ECS_IP:8400"
else
    echo "WARNING: Agent Tools returned HTTP $HTTP_CODE"
    exit 1
fi
