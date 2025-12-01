# estado.py
"""
Arquivo centralizado para estado compartilhado entre módulos.
Evita problemas de importação circular.
"""

from typing import Dict
import threading
from datetime import datetime

# ✅ DICIONÁRIO GLOBAL COMPARTILHADO
tarefas_estado: Dict = {}

# ✅ LOCK PARA THREAD-SAFETY
tarefas_lock = threading.Lock()


def criar_tarefa(tarefa_id: str) -> None:
    """Cria uma nova tarefa no estado"""
    with tarefas_lock:
        tarefas_estado[tarefa_id] = {
            "status": "aguardando",
            "progresso": 0,
            "mensagem": "Aguardando início da execução...",
            "resultados": None,
            "erro": None,
            "timestamp_criacao": datetime.now().isoformat(),
            "timestamp_conclusao": None
        }
    print(f"✅ Tarefa {tarefa_id} criada | Total: {len(tarefas_estado)}")


def atualizar_tarefa(tarefa_id: str, **kwargs) -> None:
    """Atualiza campos de uma tarefa"""
    with tarefas_lock:
        if tarefa_id in tarefas_estado:
            tarefas_estado[tarefa_id].update(kwargs)


def obter_tarefa(tarefa_id: str) -> Dict:
    """Obtém informações de uma tarefa"""
    with tarefas_lock:
        if tarefa_id in tarefas_estado:
            return tarefas_estado[tarefa_id].copy()
    return None


def obter_todas_tarefas() -> Dict:
    """Obtém todas as tarefas"""
    with tarefas_lock:
        return {tid: info.copy() for tid, info in tarefas_estado.items()}


def limpar_concluidas() -> int:
    """Limpa tarefas concluídas e retorna quantidade"""
    with tarefas_lock:
        concluidas = [k for k, v in tarefas_estado.items()
                      if v["status"] == "concluido"]
        for tid in concluidas:
            del tarefas_estado[tid]
    return len(concluidas)
