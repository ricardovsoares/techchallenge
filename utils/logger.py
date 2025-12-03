
import logging
import os
import sys


def configura_logger(nome_modulo: str, nome_arquivo: str, nivel: int = logging.DEBUG) -> logging.Logger:
    """
    Configura e retorna um logger que escreve mensagens em um arquivo e no console.

    Esta função garante que o logger seja configurado apenas uma vez por nome de módulo,
    evitando a duplicação de handlers e mensagens de log.

    Args:
        nome_modulo (str): O nome do módulo que está solicitando o logger (geralmente __name__).
                           Isso ajuda a identificar a origem da mensagem de log.
        nome_arquivo (str): O nome do arquivo onde os logs serão salvos (ex: "app.log", "erros.log").
                            O arquivo será criado dentro da pasta 'logs/'.
        nivel (int, optional): O nível mínimo de logging a ser processado.
                               Padrões para logging.DEBUG (todos os níveis).
                               Outras opções: logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL.

    Returns:
        logging.Logger: Uma instância do logger configurada e pronta para uso.

    Raises:
        IOError: Se houver um problema de permissão ou outro erro ao tentar criar
                 o diretório 'logs/' ou o arquivo de log.

    Exemplo de Uso:
        # No início do seu arquivo Python (ex: main.py, api/v1/endpoints/livro.py)
        from utils.logger import configura_logger
        logger = configura_logger(__name__, "meu_modulo.log")

        # Para usar o logger
        logger.debug("Esta é uma mensagem de depuração.")
        logger.info("Informação importante sobre a execução.")
        logger.warning("Um aviso ocorreu, mas a execução continua.")
        logger.error("Um erro grave que precisa de atenção.")
        logger.critical("Erro crítico! A aplicação pode parar.")
    """
    # 1. Obter uma instância do logger para o nome do módulo
    logger = logging.getLogger(nome_modulo)

    # 2. Evitar a duplicação de handlers se o logger já foi configurado
    #    Isso é crucial porque getLogger() retorna a mesma instância se chamado com o mesmo nome.
    if logger.handlers:
        return logger

    # 3. Definir o nível mínimo de logging para o logger
    logger.setLevel(nivel)

    # 4. Definir o formato das mensagens de log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 5. Criar a pasta 'logs/' se ela não existir
    pasta_logs = "logs"
    try:
        os.makedirs(pasta_logs, exist_ok=True)
    except OSError as e:
        # Tratamento de erro se a pasta não puder ser criada
        print(
            f"ERRO: Não foi possível criar o diretório de logs '{pasta_logs}': {e}", file=sys.stderr)
        # Ainda tenta configurar o StreamHandler para que os logs apareçam no console
        # mas o FileHandler não será adicionado.
        pass  # Continua para configurar o StreamHandler

    # 6. Configurar o FileHandler para escrever em arquivo
    log_file_path = os.path.join(pasta_logs, nome_arquivo)
    try:
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(nivel)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Tratamento de erro se o arquivo de log não puder ser criado/escrito
        print(
            f"ERRO: Não foi possível configurar o FileHandler para '{log_file_path}': {e}", file=sys.stderr)
        # Se o FileHandler falhar, o StreamHandler ainda pode funcionar.

    # 7. Configurar o StreamHandler para exibir no console (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(nivel)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
