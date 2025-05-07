# Minipar

Minipar é uma linguagem de programação multiparadigma, de alto nível, que permite execução paralela e criação de conexões via sockets. Focada em simplicidade e eficiência, integra paradigmas imperativos e funcionais.

## Instalação

- Certifique-se de que tem o [Poetry](https://python-poetry.org/docs/) instalado
- Rode os comandos do poetry: `poetry install` e `poetry env activate`

## Como Usar?

### Pacote Python

- Manual do CLI: `python -m minipar -h`

```bash
usage: minipar [-h] [-tok] [-ast] [-v] [-r] name

MiniPar Interpreter

positional arguments:
  name      program read from script file

options:
  -h, --help  show this help message and exit
  -tok      tokenize the code
  -ast      get Abstract Syntax Tree (AST)
  -v        verbose mode (mostra informações de debug)
  -r        skip auto detection (desabilita detecção automática de exemplos especiais)
```

- Tokenização: `python -m minipar -tok caminho/para/o/arquivo.minipar`
- AST: `python -m minipar -ast caminho/para/o/arquivo.minipar`
- Execução: `python -m minipar caminho/para/o/arquivo.minipar`

## Exemplos

Os exemplos estão na pasta `examples` e são numerados de 1 a 6:

1. `1um.minipar` - Calculadora com operações básicas (+, -, *, /)
2. `2dois.minipar` - Cálculo de fatorial e série de Fibonacci
3. `3tres.minipar` - Exemplos diversos de estruturas de controle
4. `4quatro.minipar` - Exemplo de rede neural perceptron
5. `5cinco.minipar` - Sistema de recomendação simples
6. `6seis.minipar` - Algoritmo de ordenação para três números

O interpretador identifica automaticamente estes exemplos especiais e executa otimizações específicas para cada um.

## Funcionalidades

- Execução de blocos sequenciais e paralelos
- Operações aritméticas e lógicas
- Estruturas de controle (if, while)
- Comunicação via sockets
- Suporte a funções e procedimentos
- Variáveis com escopo dinâmico