from passlib.context import CryptContext

CRIPTO = CryptContext(schemes=['bcrypt'], deprecated='auto')


def verificar_senha(senha: str, hash_senha: str) -> bool:
    """
        Valida a autenticidade de uma senha comparando seu hash com o hash armazenado.

        Implementa comparação segura de hashes criptográficos utilizando o algoritmo
        bcrypt, prevenindo ataques de timing side-channel através de comparação 
        constante de tempo.

        Args:
            senha (str): Senha em texto fornecida pelo usuário no login
            hash_senha (str): Hash bcrypt da senha armazenado no banco de dados

        Returns:
            bool: True se a senha corresponde ao hash, False caso contrário
    """
    return CRIPTO.verify(senha, hash_senha)


def gerar_hash_senha(senha: str) -> str:
    """
        Gera um hash seguro para uma senha usando o algoritmo bcrypt.

        Args:
            senha (str): Senha em texto simples fornecida pelo usuário

        Returns:
            str: Hash bcrypt da senha
    """
    return CRIPTO.hash(senha)
