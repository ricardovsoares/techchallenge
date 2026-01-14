# Tech Challenge: Book Scraper & API
Este projeto foi desenvolvido como uma solução para o Tech Challenge do curso Engenharia de Machine Learning, com foco em aquisição de dados, desenvolvimento de API e boas práticas de engenharia de software.

A aplicação foi desenvolvida com FastAPI e tem como objetivo coletar dados de livros um site externo (https://books.toscrape.com/), consolidá-los em uma base local em arquivo .csv e disponibilizar esses dados para consulta via API. Todo o projeto está conteinerizado com Docker e foi publicado no Render, facilitando o deploy e a execução em ambiente de produção. Além da camada de crawling e consultas de livros, a aplicação também oferece uma API de cadastro de usuários e autenticação via JWT, com persistência em PostgreSQL. Com isso, é possível controlar acesso às rotas protegidas e manter o gerenciamento de usuários de forma consistente e auditável.
Por fim também foi desenvolvido uma camada de Machine Learning para treinar o modelo com RandomForestClassifier, realizar predição, predição em batch, exportar dados de treinmento e features para utilização em modelos de machine learning, todas essas rotas necessitam de autenticação JWT.

A documentção de toda as rotas foi desenvolvida com Swagger. 

Link da apresentação do projeto: https://drive.google.com/drive/folders/10NLZR6VAp1xJUFE3M6rlHec4U7b0x9NQ?usp=drive_link

Link do GitHub: https://github.com/ricardovsoares/techchallenge

Link da Aplicação: https://app-l7f4.onrender.com/docs.

## Arquitetura do Projeto
A aplicação foi desenvolvida em FastAPI

![Logo](Diagrama_Arquitetura.jpg)



## Documentação das APIs

Este documento descreve as APIs de Livros, Machine Learning (ML), Scraping e Usuários, fornecendo detalhes sobre suas rotas e exemplos de uso.

Sumário
- [API Livros](#api-livros) 
  - Visão Geral
  - Base URL
  - Autenticação
  - Rotas
  - Exemplos de Chamadas no Browser (fetch)
- [API ML](#api-ml)
  - Visão Geral
  - Base URL
  - Autenticação
  - Rotas
  - Exemplos de Chamadas no Browser (fetch)
- [API Scraping](#api-scraping)
  - Visão Geral
  - Base URL
  - Autenticação
  - Rotas
  - Exemplos de Chamadas no Browser (fetch)
- [API Usuarios](#api-usuarios)
  - Visão Geral
  - Base URL
  - Autenticação
  - Rotas
  - Exemplos de Chamadas no Browser (fetch)

---

## API Livros

Visão Geral (API Livros)
A API de Livros permite gerenciar e consultar informações sobre livros, incluindo listagem, busca por critérios, categorias e estatísticas.

Base URL (API Livros)
https://app-l7f4.onrender.com

Autenticação (API Livros)
Nenhuma autenticação explícita é necessária para as rotas desta API.

### Rotas (API Livros)

```sh
*   GET /health
    *   Propósito: Verifica a saúde e disponibilidade da API.
    *   Parâmetros: Nenhum.
    *   Autenticação: Nenhuma.
    *   Códigos de Resposta:
        *   200 OK: A API está operacional.
```
```sh
*   GET /
    *   Propósito: Lista todos os livros disponíveis, com opções de paginação.
    *   Parâmetros de Query:
        *   limite (int, opcional): Número máximo de livros a retornar por página.
        *   paginacao (int, opcional): Número da página de resultados a retornar.
    *   Autenticação: Nenhuma.
    *   Códigos de Resposta:
        *   200 OK: Retorna uma lista de livros.
```

```sh
*   GET /search
    *   Propósito: Buscar livros por título ou categoria. Pelo menos um dos parâmetros é obrigatório.
    *   Parâmetros de Query:
        *   title (str, opcional): Título parcial do livro para busca.
        *   category (str, opcional): Categoria do livro para busca.
    *   Autenticação: Nenhuma.
    *   Códigos de Resposta:
        *   200 OK: Retorna uma lista de livros que correspondem aos critérios.
        *   400 Bad Request: Se nenhum parâmetro title ou category for fornecido.
```

```sh
*   GET /categories
    *   Propósito: Lista todas as categorias de livros únicas presentes na base de dados.
    *   Parâmetros: Nenhum.
    *   Autenticação: Nenhuma.
    *   Códigos de Resposta:
        *   200 OK: Retorna uma lista de strings, cada uma representando uma categoria.
```

```sh
*   GET /insights/statistics
    *   Propósito: Retorna estatísticas gerais sobre os livros, como total, preço médio, etc.
    *   Parâmetros: Nenhum.
    *   Autenticação: Nenhuma.
    *   Códigos de Resposta:
        *   200 OK: Retorna um objeto JSON com as estatísticas.
```

```sh
*   GET /insights/top-rated
    *   Propósito: Retorna uma lista dos livros mais bem avaliados.
    *   Parâmetros de Query:
        *   limit (int, opcional): O número máximo de livros mais bem avaliados a retornar.
    *   Autenticação: Nenhuma.
    *   Códigos de Resposta:
        *   200 OK: Retorna uma lista de livros.
```

```sh
*   GET /insights/price-range
    *   Propósito: Retorna livros que estão dentro de uma faixa de preço especificada.
    *   Parâmetros de Query:
        *   min_price (float, obrigatório): O preço mínimo da faixa.
        *   max_price (float, obrigatório): O preço máximo da faixa.
    *   Autenticação: Nenhuma.
    *   Códigos de Resposta:
        *   200 OK: Retorna uma lista de livros dentro da faixa de preço.
        *   400 Bad Request: Se min_price for maior que max_price.
```

```sh
*   GET /{book_id}
    *   Propósito: Retorna os detalhes de um livro específico pelo seu ID.
    *   Parâmetros de Path:
        *   book_id (int, obrigatório): O ID único do livro.
    *   Autenticação: Nenhuma.
    *   Códigos de Resposta:
        *   200 OK: Retorna o objeto do livro.
        *   404 Not Found: Se nenhum livro com o book_id fornecido for encontrado.
```

### Exemplos de Chamadas no Browser (fetch) (API Livros)

GET /health
https://app-l7f4.onrender.com/health
```sh
Response JSON (Exemplo):
{
  "status": "ok"
}
```

GET / (Listar todos os livros com limite e paginação)
https://app-l7f4.onrender.com/?limite=2&paginacao=1
```sh
Response JSON (Exemplo):
[
  {
    "id": 1,
    "titulo": "O Senhor dos Anéis",
    "categoria": "Fantasia",
    "preco": 49.90,
    "avaliacao": 4.8
  },
  {
    "id": 2,
    "titulo": "1984",
    "categoria": "Distopia",
    "preco": 35.50,
    "avaliacao": 4.5
  }
]

```

GET /search (Buscar por título)
'https://app-l7f4.onrender.com/search?title=Senhor
```sh
Response JSON (Exemplo):
{
    "id": 1,
    "titulo": "O Senhor dos Anéis",
    "categoria": "Fantasia",
    "preco": 49.90,
    "avaliacao": 4.8
}
```


GET /categories
'https://app-l7f4.onrender.com/categories'
```sh
Response JSON (Exemplo):
{
    "Fantasia",
    "Distopia",
    "Ficção Científica",
    "Romance"
}
```

GET /insights/statistics
https://app-l7f4.onrender.com/insights/statistics
```sh
Response JSON (Exemplo):
{
    "total_books": 100,
    "total_categories": 15,
    "average_price": 42.75,
    "min_price": 15.00,
    "max_price": 120.00,
    "average_rating": 4.2,
    "category_distribution":
      "Fantasia": 20,
      "Distopia": 10,
      "Ficção Científica": 15,
      "Romance": 25,
      "Outros": 30
}
```

GET /insights/top-rated (com limite)
'https://app-l7f4.onrender.com/insights/top-rated?limit=1'
```sh
Response JSON (Exemplo):
{
    "id": 1,
    "titulo": "O Senhor dos Anéis",
    "categoria": "Fantasia",
    "preco": 49.90,
    "avaliacao": 4.8
}
```

GET /insights/price-range
https://app-l7f4.onrender.com/insights/price-range?min_price=30.00&max_price=50.00
```sh
Response JSON (Exemplo):
[
  {
    "id": 1,
    "titulo": "O Senhor dos Anéis",
    "categoria": "Fantasia",
    "preco": 49.90,
    "avaliacao": 4.8
  },
  {
    "id": 2,
    "titulo": "1984",
    "categoria": "Distopia",
    "preco": 35.50,
    "avaliacao": 4.5
  }
]
```

GET /{book_id}
https://app-l7f4.onrender.com/1'
```sh
Response JSON (Exemplo):
{
  "id": 1,
  "titulo": "O Senhor dos Anéis",
  "categoria": "Fantasia",
  "preco": 49.90,
  "avaliacao": 4.8
}
`
```
---

## API ML

Visão Geral (API ML)
A API de Machine Learning oferece funcionalidades para extração de features, geração de dados de treinamento e realização de predições. A maioria das rotas exige autenticação.

Base URL (API ML)
https://app-l7f4.onrender.com

Autenticação (API ML)
Todas as rotas, exceto /health, exigem um token de autenticação válido no cabeçalho Authorization no formato Bearer SEU_TOKEN_JWT.

### Rotas (API ML)

```sh
*   GET /health
    *   Propósito: Verifica a saúde e disponibilidade da API.
    *   Parâmetros: Nenhum.
    *   Autenticação: Nenhuma.
    *   Códigos de Resposta:
        *   200 OK: A API está operacional.
```
```sh
*   GET /features
    *   Propósito: Extrai features de livros para uso em modelos de Machine Learning.
    *   Parâmetros de Query:
        *   livro_id (int, opcional): ID de um livro específico para extrair features. Se omitido, pode extrair de múltiplos livros.
        *   limite (int, obrigatório): Número máximo de conjuntos de features a retornar (entre 1 e 10000).
        *   normalizar (bool, obrigatório): Indica se as features extraídas devem ser normalizadas.
    *   Autenticação: Bearer Token.
    *   Códigos de Resposta:
        *   200 OK: Retorna uma lista de features.
        *   401 Unauthorized: Se o token de autenticação estiver ausente ou for inválido.
        *   422 Unprocessable Entity: Erro de validação dos parâmetros.
```
```sh
*   GET /training-data
    *   Propósito: Gera um conjunto de dados para treinamento de modelos de Machine Learning.
    *   Parâmetros de Query:
        *   limite (int, opcional): Número máximo de amostras de dados a gerar.
        *   test_size (float, opcional): Proporção do conjunto de dados a ser reservada para teste (valor entre 0.1 e 0.5).
    *   Autenticação: Bearer Token.
    *   Códigos de Resposta:
        *   200 OK: Retorna o conjunto de dados de treinamento e teste.
        *   401 Unauthorized: Se o token de autenticação estiver ausente ou for inválido.
        *   422 Unprocessable Entity: Erro de validação dos parâmetros.
```
```sh
*   POST /predictions
    *   Propósito: Realiza uma predição para um único conjunto de features fornecido.
    *   Parâmetros de Body (JSON):
        *   PredictionRequestSchema: Um objeto JSON contendo as features para a predição.
            *   Exemplo: {"feature1": 1.2, "feature2": 3.4, "feature_n": 5.6}
    *   Autenticação: Bearer Token.
    *   Códigos de Resposta:
        *   200 OK: Retorna o resultado da predição.
        *   401 Unauthorized: Se o token de autenticação estiver ausente ou for inválido.
        *   422 Unprocessable Entity: Erro de validação do corpo da requisição.
```
```sh
*   POST /predictions/batch
    *   Propósito: Realiza predições em lote para múltiplos conjuntos de features.
    *   Parâmetros de Body (JSON):
        *   BatchPredictionRequestSchema: Uma lista de objetos JSON, onde cada objeto contém as features para uma predição.
            *   Exemplo: [{"feature1": 1.2, "feature2": 3.4}, {"feature1": 5.6, "feature2": 7.8}]
    *   Autenticação: Bearer Token.
    *   Códigos de Resposta:
        *   200 OK: Retorna uma lista de resultados de predição.
        *   401 Unauthorized: Se o token de autenticação estiver ausente ou for inválido.
        *   422 Unprocessable Entity: Erro de validação do corpo da requisição.
```
```sh
*   POST /train
    *   Propósito: Inicia o processo de treinamento de um modelo de Machine Learning.
    *   Parâmetros: Nenhum (ou parâmetros de configuração de treinamento no body, se aplicável, não especificado).
    *   Autenticação: Bearer Token.
    *   Códigos de Resposta:
        *   200 OK: Indica que o treinamento foi iniciado com sucesso.
        *   401 Unauthorized: Se o token de autenticação estiver ausente ou for inválido.
```

### Exemplos de Chamadas no Browser (fetch) (API ML)

GET /health
https://app-l7f4.onrender.com/ml/health'
```sh
Response JSON (Exemplo):
{
  "status": "ok"
}
```

GET /features (com token)
const tokenML = 'SEU_TOKEN_JWT'; // Substitua pelo seu token JWT
https://app-l7f4.onrender.com/ml/features?limite=1&normalizar=true',
```
  headers: {
    'Authorization': Bearer ${tokenML}
  }
```
```sh
Response JSON (Exemplo):
`json
[
  {
    "livro_id": 1,
    "feature_titulo_length": 0.5,
    "feature_categoria_encoded": 0.2,
    "feature_preco_normalized": 0.7,
    "feature_avaliacao_scaled": 0.9,
    "feature_palavra_chave_1": 0.1,
    "feature_palavra_chave_2": 0.3,
    "[CAMPO_EXATO_NÃO_INFORMADO_NO_CÓDIGO]": "..."
  }
]
```

POST /predictions (com token e body)
const tokenML = 'SEU_TOKEN_JWT'; // Substitua pelo seu token JWT
https://app-l7f4.onrender.com/ml/predictions',
```
headers={"Authorization": f"Bearer {token}"},
    json={
            "preco": 25.50,
            "rating": 4.5,
            "categoria": "Fiction"
        }
```
```sh
Response JSON (Exemplo):
{
  "prediction": 0.75,
  "model_version": "1.0.0",
}
```
---

## API Scraping

Visão Geral (API Scraping)
A API de Scraping permite iniciar e monitorar tarefas de coleta de dados da web. A rota para iniciar uma tarefa exige autenticação.

Base URL (API Scraping)
https://app-l7f4.onrender.com

Autenticação (API Scraping)
A rota POST /iniciar exige um token de autenticação válido no cabeçalho Authorization no formato Bearer SEU_TOKEN_JWT. As outras rotas não exigem autenticação explícita.

### Rotas (API Scraping)
```sh
*   POST /iniciar
    *   Propósito: Inicia uma nova tarefa de scraping com base na configuração fornecida.
    *   Parâmetros de Body (JSON):
        *   ConfiguracaoScraper: Um objeto JSON contendo as configurações para a tarefa de scraping.
            *   Exemplo: {"url": "http://example.com", "depth": 2, "selectors": ["h1", "p"]}
    *   Autenticação: Bearer Token.
    *   Códigos de Resposta:
        *   200 OK: Retorna o ID da tarefa de scraping iniciada.
        *   401 Unauthorized: Se o token de autenticação estiver ausente ou for inválido.
        *   422 Unprocessable Entity: Erro de validação do corpo da requisição.
```
```sh
*   GET /status/{tarefa_id}
    *   Propósito: Retorna o status atual de uma tarefa de scraping específica.
    *   Parâmetros de Path:
        *   tarefa_id (str, obrigatório): O ID único da tarefa de scraping.
    *   Autenticação: Nenhuma.
    *   Códigos de Resposta:
        *   200 OK: Retorna o status da tarefa.
        *   404 Not Found: Se a tarefa_id não for encontrada.
```
```sh
*   GET /resultados/{tarefa_id}
    *   Propósito: Retorna os resultados completos de uma tarefa de scraping concluída.
    *   Parâmetros de Path:
        *   tarefa_id (str, obrigatório): O ID único da tarefa de scraping.
    *   Autenticação: Nenhuma.
    *   Códigos de Resposta:
        *   200 OK: Retorna os dados coletados pela tarefa.
        *   404 Not Found: Se a tarefa_id não for encontrada.
        *   409 Conflict: Se a tarefa ainda não estiver concluída.
```
```sh
*   GET /listar-tarefas
    *   Propósito: Lista todos os IDs de tarefas de scraping que foram iniciadas.
    *   Parâmetros: Nenhum.
    *   Autenticação: Nenhuma.
    *   Códigos de Resposta:
        *   200 OK: Retorna uma lista de IDs de tarefas.
```
```sh
*   GET /listar-tarefas-detalhado
    *   Propósito: Lista detalhes completos de todas as tarefas de scraping.
    *   Parâmetros: Nenhum.
    *   Autenticação: Nenhuma.
    *   Códigos de Resposta:
        *   200 OK: Retorna uma lista de objetos, cada um com detalhes de uma tarefa.
```
```sh
*   GET /health
    *   Propósito: Verifica a saúde e disponibilidade da API.
    *   Parâmetros: Nenhum.
    *   Autenticação: Nenhuma.
    *   Códigos de Resposta:
        *   200 OK: A API está operacional.
```

### Exemplos de Chamadas no Browser (fetch) (API Scraping)

GET /health
https://app-l7f4.onrender.com/scraping/health'
```sh
Response JSON (Exemplo):
{
  "status": "ok"
}
```

POST /iniciar (com token e body) https://app-l7f4.onrender.com/scraping/iniciar'
```
const tokenScraping = 'SEU_TOKEN_JWT'; // Substitua pelo seu token JWT
const configScraper = {
        "url_inicial": "https://books.toscrape.com/index.html",
        "section_selector": "section",
        "li_selector": "li.col-xs-6.col-sm-4.col-md-3.col-lg-3",
        "next_page_selector": "ul.pager li.next a",
        "max_paginas": 5,
        "salvar_excel": true
    }
```
```sh
Response JSON (Exemplo):
{
  "tarefa_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "iniciada"
}
```

GET /status/{tarefa_id} https://app-l7f4.onrender.com/scraping/status/${tarefaId}
```
const tarefaId = 'a1b2c3d4-e5f6-7890-1234-567890abcdef'; // Substitua pelo ID da sua tarefa
```
```sh
Response JSON (Exemplo):
{
  "tarefa_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "em_progresso",
  "progresso": 75,
  "mensagens": ["Coletando dados da página 1", "Processando página 2"]
}
```
---

## API Usuarios

Visão Geral (API Usuários)
A API de Usuários gerencia o registro, autenticação e informações de usuários. Algumas rotas exigem autenticação JWT ou privilégios de administrador.

Base URL (API Usuários)
https://app-l7f4.onrender.com

Autenticação (API Usuários)
*   GET /logado exige um token JWT válido no cabeçalho Authorization no formato Bearer SEU_TOKEN_JWT.
*   DELETE /{usuario_id} exige que o usuário autenticado tenha privilégios de administrador.
*   POST /login e POST /signup são rotas para autenticação e criação de usuários, respectivamente, e não exigem token prévio.

### Rotas (API Usuários)
```sh
*   GET /logado
    *   Propósito: Verifica se o usuário está autenticado e retorna seus dados.
    *   Parâmetros: Nenhum.
    *   Autenticação: Bearer Token (JWT).
    *   Códigos de Resposta:
        *   200 OK: Retorna os dados do usuário autenticado.
        *   401 Unauthorized: Se o token JWT estiver ausente, for inválido ou expirado.
```
```sh
*   POST /signup
    *   Propósito: Cria um novo usuário no sistema.
    *   Parâmetros de Body (JSON):
        *   Objeto JSON com os dados do novo usuário.
            *   Exemplo: {"username": "novo_usuario", "email": "novo@example.com", "password": "senha_segura"}
    *   Autenticação: Nenhuma.
    *   Códigos de Resposta:
        *   201 Created: Usuário criado com sucesso.
        *   400 Bad Request: Se o username ou email já estiver em uso.
        *   422 Unprocessable Entity: Erro de validação dos dados do usuário.
```
```sh
*   GET /
    *   Propósito: Lista todos os usuários registrados no sistema.
    *   Parâmetros: Nenhum.
    *   Autenticação: Nenhuma (pode ser restrita a admins em uma implementação real).
    *   Códigos de Resposta:
        *   200 OK: Retorna uma lista de objetos de usuário.
```
```sh
*   GET /{usuario_id}
    *   Propósito: Retorna os detalhes de um usuário específico pelo seu ID.
    *   Parâmetros de Path:
        *   usuario_id (int, obrigatório): O ID único do usuário.
    *   Autenticação: Nenhuma (pode ser restrita em uma implementação real).
    *   Códigos de Resposta:
        *   200 OK: Retorna o objeto do usuário.
        *   404 Not Found: Se nenhum usuário com o usuario_id fornecido for encontrado.
```
```sh
*   PUT /{usuario_id}
    *   Propósito: Atualiza os dados de um usuário existente.
    *   Parâmetros de Path:
        *   usuario_id (int, obrigatório): O ID único do usuário a ser atualizado.
    *   Parâmetros de Body (JSON):
        *   Objeto JSON com os campos a serem atualizados.
            *   Exemplo: {"email": "atualizado@example.com", "is_active": false}
    *   Autenticação: Pode exigir Bearer Token do próprio usuário ou de um administrador.
    *   Códigos de Resposta:
        *   200 OK: Usuário atualizado com sucesso.
        *   404 Not Found: Se o usuario_id não for encontrado.
        *   401 Unauthorized: Se o token estiver ausente ou for inválido.
        *   403 Forbidden: Se o usuário não tiver permissão para atualizar.
        *   422 Unprocessable Entity: Erro de validação dos dados.
```
```sh
*   DELETE /{usuario_id}
    *   Propósito: Exclui um usuário do sistema.
    *   Parâmetros de Path:
        *   usuario_id (int, obrigatório): O ID único do usuário a ser excluído.
    *   Autenticação: Bearer Token de um usuário com privilégios de administrador.
    *   Códigos de Resposta:
        *   204 No Content: Usuário excluído com sucesso.
        *   401 Unauthorized: Se o token estiver ausente ou for inválido.
        *   403 Forbidden: Se o usuário autenticado não for um administrador.
        *   404 Not Found: Se o usuario_id não for encontrado.
```
```sh
*   POST /login
    *   Propósito: Autentica um usuário e retorna um token JWT para acesso a rotas protegidas.
    *   Parâmetros de Body (JSON):
        *   Objeto JSON com as credenciais do usuário.
            *   Exemplo: {"username": "meu_usuario", "password": "minha_senha"}
    *   Autenticação: Nenhuma (esta é a rota para obter o token).
    *   Códigos de Resposta:
        *   200 OK: Retorna um token JWT.
        *   401 Unauthorized: Credenciais inválidas (username ou password incorretos).
        *   422 Unprocessable Entity: Erro de validação dos dados de login.
```

### Exemplos de Chamadas no Browser (fetch) (API Usuários)

POST /signup (Criar novo usuário) https://app-l7f4.onrender.com/users/signup'
```
const newUser = {
  "username": "teste_user",
  "email": "teste@example.com",
  "password": "senha_segura123"
};
```
```sh
Response JSON (Exemplo):
{
  "id": 101,
  "username": "teste_user",
  "email": "teste@example.com",
  "is_active": true,
  "is_admin": false,
  "[CAMPO_EXATO_NÃO_INFORMADO_NO_CÓDIGO]": "..."
}
```

POST /login (Obter token JWT) 'https://app-l7f4.onrender.com/users/login'
```
const credentials = {
  "username": "teste_user",
  "password": "senha_segura123"
};
```
```sh
Response JSON (Exemplo):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0ZV91c2VyIiwiZXhwIjoxNzA1NTQzMjAwfQ.S0m3T0k3N_Jv7W_T0k3N_Jv7W_T0k3N_Jv7W_T0k3N_Jv7W_T0k3N_Jv7W",
  "token_type": "bearer"
}
```

GET /logado (Com token JWT) https://app-l7f4.onrender.com/users/logado
```
const userToken = 'SEU_TOKEN_JWT'; // Substitua pelo token obtido no login
  headers: {
    'Authorization': Bearer ${userToken}
  }
```
```sh
Response JSON (Exemplo):
{
  "id": 101,
  "username": "teste_user",
  "email": "teste@example.com",
  "is_active": true,
  "is_admin": false,
  "[CAMPO_EXATO_NÃO_INFORMADO_NO_CÓDIGO]": "..."
}
```

GET / (Listar todos os usuários) https://app-l7f4.onrender.com/users/'
```sh
Response JSON (Exemplo):
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_active": true,
    "is_admin": true
  },
  {
    "id": 101,
    "username": "teste_user",
    "email": "teste@example.com",
    "is_active": true,
    "is_admin": false
  }
]
```

DELETE /{usuario_id} (Com token de administrador) https://app-l7f4.onrender.com/users/${userIdToDelete}
```
const adminToken = 'SEU_TOKEN_JWT_ADMIN'; // Substitua pelo token de um usuário administrador
const userIdToDelete = 101; // ID do usuário a ser excluído
```
```sh
Response (Exemplo):
*   204 No Content (sem corpo de resposta)
```