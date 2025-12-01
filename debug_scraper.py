import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"


def listar_todas_tarefas():
    """Lista todas as tarefas com detalhes"""
    try:
        response = requests.get(f"{BASE_URL}/scraper/listar-tarefas")
        dados = response.json()

        print("\n" + "="*70)
        print("📋 TODAS AS TAREFAS")
        print("="*70)
        print(json.dumps(dados, indent=2, ensure_ascii=False))
        print("="*70 + "\n")

        return dados

    except Exception as e:
        print(f"❌ Erro ao listar tarefas: {e}")
        return None


def monitorar_tarefa(tarefa_id, intervalo=5, max_tentativas=60):
    """Monitora uma tarefa específica até conclusão"""
    print(f"\n🔍 Monitorando tarefa: {tarefa_id}\n")

    tentativa = 0
    while tentativa < max_tentativas:
        try:
            response = requests.get(f"{BASE_URL}/scraper/status/{tarefa_id}")
            status_data = response.json()

            status = status_data.get("status", "desconhecido")
            progresso = status_data.get("progresso", 0)
            mensagem = status_data.get("mensagem", "")
            total = status_data.get("total_produtos", 0)

            print(f"[{tentativa+1}/{max_tentativas}] Status: {status.upper()} | "
                  f"Progresso: {progresso}% | Produtos: {total}")
            print(f"   Mensagem: {mensagem}\n")

            # Se concluída, obter resultados
            if status == "concluido":
                print("✅ Tarefa concluída! Buscando resultados...\n")
                resultado = requests.get(
                    f"{BASE_URL}/scraper/resultados/{tarefa_id}").json()
                print(
                    f"Total de produtos coletados: {resultado['total_produtos']}")

                # Mostrar primeiros 3 produtos
                if resultado['produtos']:
                    print("\n📦 Primeiros 3 produtos:")
                    for idx, produto in enumerate(resultado['produtos'][:3], 1):
                        print(f"\n{idx}. {produto.get('titulo', 'Sem título')}")
                        print(f"   URL: {produto.get('url')}")
                        print(f"   Preço: {produto.get('preco')}")
                        print(f"   Categoria: {produto.get('categoria')}")
                break

            # Se erro, parar
            if status == "erro":
                erro = status_data.get("erro")
                print(f"❌ Erro na tarefa: {erro}\n")
                break

            tentativa += 1
            time.sleep(intervalo)

        except Exception as e:
            print(f"❌ Erro ao monitorar: {e}\n")
            tentativa += 1
            time.sleep(intervalo)


def health_check():
    """Verifica se a API está rodando"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ API Status: {response.json()}")
        return True
    except:
        print("❌ API não está respondendo em http://localhost:8000")
        return False


if __name__ == "__main__":
    print("🚀 SCRIPT DE DEBUG - WEB SCRAPER API\n")

    # Verificar saúde
    if not health_check():
        print("\n⚠️ Inicie a API primeiro: python seu_arquivo.py")
        exit(1)

    # Menu
    while True:
        print("\n" + "="*70)
        print("O QUE VOCÊ QUER FAZER?")
        print("="*70)
        print("1. Listar TODAS as tarefas")
        print("2. Monitorar uma tarefa específica")
        print("3. Sair")
        print("="*70)

        opcao = input("\nDigite a opção (1-3): ").strip()

        if opcao == "1":
            listar_todas_tarefas()

        elif opcao == "2":
            tarefa_id = input("Digite o ID da tarefa: ").strip()
            monitorar_tarefa(tarefa_id)

        elif opcao == "3":
            print("\n👋 Até logo!\n")
            break

        else:
            print("❌ Opção inválida")
