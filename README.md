# Minipar

<!-- markdownlint-disable -->

Minipar é uma linguagem de programação de alto nível, multiparadigma, que possibilita a execução de blocos de código em paralelo na sua estrutura, bem como uma fácil criação de conexões através do uso de sockets. Desenvolvida com foco na simplicidade e eficiência, Minipar integra paradigmas de programação imperativa e funcional, permitindo que os desenvolvedores escolham a abordagem que melhor se adapta às necessidades de seus projetos.

## Instalação

- Certifique-se de que tem o [Poetry](https://python-poetry.org/docs/) instalado
- Clone o repositório: `git clone https://github.com/ThiagoORuby/minipar-interpreter.git`
- Rode os comandos do poetry: `poetry install` e `poetry shell`

## Como Usar?

#### Pacote Python

- Manual do CLI: `python -m minipar -h`

```bash
usage: minipar [-h] [-tok] [-ast] name

MiniPar Interpreter

positional arguments:
  name    	program read from script file

options:
  -h, --help  show this help message and exit
  -tok    	tokenize the code
  -ast    	get Abstract Syntax Tree (AST)
```

- Tokenização: `python -m minipar -tok caminho/para/o/arquivo.minipar`
- AST: `python -m minipar -ast caminho/para/o/arquivo.minipar`
- Execução: `python -m minipar caminho/para/o/arquivo.minipar`

#### Executável

- Certifique-se de que tem o [Make](https://www.gnu.org/software/make/) instalado
- Rode o comando `make compile` para gerar o executável
- Os comandos do CLI são equivalentes

#### Exemplo de uso:

- Código Minipar

```python
num: number = 10
func count(n: number) -> void{
  while(n >= 0)
  {
	print(n)
	n = n - 1
  }
}
count(num)
```

- Tokenização

```bash
({num, ID}, 1) | line: 1
({:, :}, 1) | line: 1
({number, TYPE}, 1) | line: 1
({=, =}, 1) | line: 1
({10, NUMBER}, 1) | line: 1
({func, FUNC}, 3) | line: 3
({count, ID}, 3) | line: 3
({(, (}, 3) | line: 3
({n, ID}, 3) | line: 3
({:, :}, 3) | line: 3
({number, TYPE}, 3) | line: 3
({), )}, 3) | line: 3
({->, RARROW}, 3) | line: 3
({void, TYPE}, 3) | line: 3
({{, {}, 3) | line: 3
({while, WHILE}, 4) | line: 4
({(, (}, 4) | line: 4
({n, ID}, 4) | line: 4
({>=, GTE}, 4) | line: 4
({0, NUMBER}, 4) | line: 4
({), )}, 4) | line: 4
({{, {}, 5) | line: 5
({print, ID}, 6) | line: 6
({(, (}, 6) | line: 6
({n, ID}, 6) | line: 6
({), )}, 6) | line: 6
({n, ID}, 7) | line: 7
({=, =}, 7) | line: 7
({n, ID}, 7) | line: 7
({-, -}, 7) | line: 7
({1, NUMBER}, 7) | line: 7
({}, }}, 8) | line: 8
({}, }}, 9) | line: 9
({count, ID}, 11) | line: 11
({(, (}, 11) | line: 11
({num, ID}, 11) | line: 11
({), )}, 11) | line: 11
```

- AST

```python
Module(stmts=[Assign(left=ID(type='NUMBER', token={num, ID}, decl=True),
                     right=Constant(type='NUMBER', token={10, NUMBER})),
              FuncDef(name='count',
                      return_type='VOID',
                      params={'n': ('NUMBER', None)},
                      body=[While(condition=Relational(type='BOOL',
                                                       token={>=, GTE},
                                                       left=ID(type='NUMBER',
                                                               token={n, ID},
                                                               decl=False),
                                                       right=Constant(type='NUMBER',
                                                                      token={0, NUMBER})),
                                  body=[Call(type='FUNC',
                                             token={print, ID},
                                             id=ID(type='FUNC',
                                                   token={print, ID},
                                                   decl=False),
                                             args=[ID(type='NUMBER',
                                                      token={n, ID},
                                                      decl=False)],
                                             oper=''),
                                        Assign(left=ID(type='NUMBER',
                                                       token={n, ID},
                                                       decl=False),
                                               right=Arithmetic(type='NUMBER',
                                                                token={-, -},
                                                                left=ID(type='NUMBER',
                                                                        token={n, ID},
                                                                        decl=False),
                                                                right=Constant(type='NUMBER',
                                                                               token={1, NUMBER})))])]),
              Call(type='FUNC',
                   token={count, ID},
                   id=ID(type='FUNC', token={count, ID}, decl=False),
                   args=[ID(type='NUMBER', token={num, ID}, decl=False)],
                   oper='')])
```

- Execução

```bash
10
9
8
7
6
5
4
3
2
1
0
```

## Manual de Referência da Linguagem

### 1. Convenções Léxicas

Em Minipar, os identificadores de variáveis podem ser qualquer cadeia de letras, dígitos e sublinhados que não começam com um dígito, seguindo o padrão de nomes de grande parte das linguagens de programação.

As seguintes palavras chaves são reservadas e não podem ser usadas como nome de variáveis:

|        |           |          |       |
| ------ | --------- | -------- | ----- |
| break  | c_channel | continue | else  |
| false  | func      | if       | par   |
| return | s_channel | true     | while |

Cadeias de caracteres literais devem ser delimitadas por aspas duplas. Enquanto comentários podem ser tanto de caráter simples, como multilinha:

```python
# um comentário simples
```

```cpp
/* Um
comentário
multilinha
*/
```

As seguintes cadeias denotam outros itens léxicos:

- `+, -, *, /, %, !`
- `==, !=, <=, >=, <, >, =`
- `&&, ||, (, ), {, }`

### 2. Valores e Tipos

Minipar é uma _linguagem estaticamente tipada_. Isso significa que na declaração de variáveis, é necessário definir seu tipo, sendo inalterável durante toda a execução do código. Existem 7 tipos básicos em Minipar:

| Tipo        | Descrição                                                            |
| ----------- | -------------------------------------------------------------------- |
| `number`    | Representa números inteiros e reais                                  |
| `string`    | Representa uma sequência de caracteres                               |
| `bool`      | Representa um valor booleano (`true` ou `false`)                     |
| `void`      | Representa um valor vazio associado ao retorno de funções            |
| `func`      | Representa uma rotina de código, com parâmetros e um tipo de retorno |
| `c_channel` | Representa uma referência para um canal socket cliente               |
| `s_channel` | Representa uma referência para um canal socket servidor              |

### 3. Comandos

#### 3.1. Declarações

#### 3.2. Estruturas de Controle

#### 3.3. Estruturas de Paralelisação

#### 3.4. Estruturas de conexão

### 4. Expressões

#### 4.1. Operadores Aritiméticos

#### 4.2. Operadores Relacionais

#### 4.3. Operadores Lógicos

#### 4.4. Ordem de Precedência

#### 4.5. Chamadas de função

### 5. Biblioteca Padrão

#### 5.1. Entrada e Saída

#### 5.2. Conversão de Tipos

#### 5.3. Manipulação de Strings

#### 5.4. Outros
