import sys
from pathlib import Path
import paramiko

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

try:
    from src.p4_llm_controller import processar_pacote_e_consultar_llm
except ModuleNotFoundError:
    from p4_llm_controller import processar_pacote_e_consultar_llm


def executar_injecao_remota(
    tipo_ataque="DDoS",
    quantidade=50,
    vm_ip="192.168.56.101",
    vm_user="p4",
    vm_pass="p4",
):
    """Conecta via SSH à VM, executa a injeção de pacotes no namespace h1 e notifica o controlador."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            vm_ip, username=vm_user, password=vm_pass, timeout=5
        )

        cmd_find_h1 = "pgrep -f 'mininet:h1'"
        stdin, stdout, stderr = client.exec_command(cmd_find_h1)
        pids = stdout.read().decode().strip().split("\n")
        pid_h1 = pids[0] if pids and pids[0] else None

        if pid_h1:
            cmd_mnexec = f"echo {vm_pass} | sudo -S mnexec -a {pid_h1} python3 /home/{vm_user}/injetor_real.py --tipo {tipo_ataque} --qtd {quantidade}"
        else:
            cmd_mnexec = f"echo {vm_pass} | sudo -S mnexec -a $(pgrep -f 'mininet:h1' | head -n 1) python3 /home/{vm_user}/injetor_real.py --tipo {tipo_ataque} --qtd {quantidade}"

        stdin, stdout, stderr = client.exec_command(cmd_mnexec)
        saida = stdout.read().decode()
        erro = stderr.read().decode()

        client.close()

        mapa_ips = {
            "DDoS": "10.0.0.142",
            "PortScan": "10.0.0.50",
            "Botnet": "10.0.0.99",
            "BENIGN": "10.0.0.1",
        }
        src_ip = mapa_ips.get(tipo_ataque, "10.0.0.1")

        processar_pacote_e_consultar_llm(
            src_ip=src_ip, dst_ip="10.0.0.2", protocolo="TCP", pacotes=quantidade
        )

        return True, saida

    except Exception as e:
        return False, f"Erro de Conexão SSH: {str(e)}"