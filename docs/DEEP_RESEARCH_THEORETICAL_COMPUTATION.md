# DEEP RESEARCH: Computação Teórica
## Turing, Church, von Neumann e os Fundamentos da Computação

**Data**: Dezembro 2025
**Escopo**: Pesquisa nível PhD - Teoria da computação

---

## INTRODUÇÃO

A computação teórica estabelece o que é computável, o que é decidível, e quais são os limites fundamentais de qualquer sistema computacional. De Turing a Chomsky, os fundadores definiram o território onde toda a ciência da computação opera.

---

## 1. ALAN TURING (1912-1954)

### "On Computable Numbers" (1936)

Turing definiu formalmente o conceito de **algoritmo** através da Máquina de Turing:

**Definição Formal** (7-tupla):
```
M = (Q, Σ, Γ, δ, q₀, qₐ, qᵣ)

Q  = conjunto finito de estados
Σ  = alfabeto de entrada
Γ  = alfabeto da fita (Σ ⊆ Γ)
δ  = função de transição: Q × Γ → Q × Γ × {L, R}
q₀ = estado inicial
qₐ = estado de aceitação
qᵣ = estado de rejeição
```

### Implementação em Python

```python
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from enum import Enum

class Direction(Enum):
    LEFT = -1
    RIGHT = 1

@dataclass
class TuringMachine:
    """Máquina de Turing Universal"""
    states: set
    alphabet: set
    tape_alphabet: set
    transitions: Dict[Tuple[str, str], Tuple[str, str, Direction]]
    initial_state: str
    accept_state: str
    reject_state: str

    def run(self, input_string: str, max_steps: int = 10000) -> Optional[bool]:
        """Executa a máquina na entrada"""
        # Inicializa fita
        tape = list(input_string) + ['_'] * 100
        head = 0
        state = self.initial_state
        steps = 0

        while steps < max_steps:
            if state == self.accept_state:
                return True
            if state == self.reject_state:
                return False

            symbol = tape[head]
            key = (state, symbol)

            if key not in self.transitions:
                return False

            new_state, write_symbol, direction = self.transitions[key]
            tape[head] = write_symbol
            state = new_state
            head += direction.value

            # Expande fita se necessário
            if head < 0:
                tape = ['_'] + tape
                head = 0
            if head >= len(tape):
                tape.append('_')

            steps += 1

        return None  # Não parou (possível loop infinito)

# Exemplo: Reconhece {0^n 1^n | n ≥ 0}
tm = TuringMachine(
    states={'q0', 'q1', 'q2', 'q3', 'q4', 'qa', 'qr'},
    alphabet={'0', '1'},
    tape_alphabet={'0', '1', 'X', 'Y', '_'},
    transitions={
        ('q0', '0'): ('q1', 'X', Direction.RIGHT),
        ('q0', 'Y'): ('q3', 'Y', Direction.RIGHT),
        ('q1', '0'): ('q1', '0', Direction.RIGHT),
        ('q1', 'Y'): ('q1', 'Y', Direction.RIGHT),
        ('q1', '1'): ('q2', 'Y', Direction.LEFT),
        ('q2', '0'): ('q2', '0', Direction.LEFT),
        ('q2', 'Y'): ('q2', 'Y', Direction.LEFT),
        ('q2', 'X'): ('q0', 'X', Direction.RIGHT),
        ('q3', 'Y'): ('q3', 'Y', Direction.RIGHT),
        ('q3', '_'): ('qa', '_', Direction.RIGHT),
        ('q0', '_'): ('qa', '_', Direction.RIGHT),
    },
    initial_state='q0',
    accept_state='qa',
    reject_state='qr'
)

print(tm.run("0011"))  # True
print(tm.run("0001"))  # False
```

### O Problema da Parada

**Teorema**: Não existe máquina de Turing que decide, para toda MT M e entrada w, se M para em w.

**Prova por Contradição**:
```python
def halting_problem_proof():
    """
    Prova informal do problema da parada

    Suponha que existe HALT(M, w) que decide se M para em w.
    Construa D(M):
        se HALT(M, M): loop infinito
        senão: pare

    D(D) para?
    - Se D(D) para → HALT(D,D)=True → D entra em loop → contradição
    - Se D(D) não para → HALT(D,D)=False → D para → contradição

    Portanto, HALT não pode existir.
    """
    pass
```

### Conexão com Computação
- **Turing-completude**: Linguagens que simulam MT
- **Halting problem**: Base de muitos resultados de indecidibilidade
- **Universal TM**: Fundamento de computadores programáveis

---

## 2. ALONZO CHURCH (1903-1995)

### Cálculo Lambda (1936)

Church criou um sistema formal para computação baseado em **funções**:

**Sintaxe**:
```
<expr> ::= <var>                    // Variável
         | λ<var>.<expr>            // Abstração
         | <expr> <expr>            // Aplicação
```

**Regras de Redução**:
- **α-conversão**: λx.E ≡ λy.E[x/y] (renomeação)
- **β-redução**: (λx.E) A → E[x/A] (aplicação)
- **η-conversão**: λx.(E x) ≡ E se x não livre em E

### Implementação em Python

```python
from dataclasses import dataclass
from typing import Union, Set

@dataclass
class Var:
    """Variável"""
    name: str
    def __repr__(self): return self.name

@dataclass
class Abs:
    """Abstração: λx.body"""
    param: str
    body: 'Expr'
    def __repr__(self): return f"(λ{self.param}.{self.body})"

@dataclass
class App:
    """Aplicação: func arg"""
    func: 'Expr'
    arg: 'Expr'
    def __repr__(self): return f"({self.func} {self.arg})"

Expr = Union[Var, Abs, App]

def free_vars(expr: Expr) -> Set[str]:
    """Retorna variáveis livres"""
    if isinstance(expr, Var):
        return {expr.name}
    elif isinstance(expr, Abs):
        return free_vars(expr.body) - {expr.param}
    else:  # App
        return free_vars(expr.func) | free_vars(expr.arg)

def substitute(expr: Expr, var: str, replacement: Expr) -> Expr:
    """E[x/R] - substitui x por R em E"""
    if isinstance(expr, Var):
        return replacement if expr.name == var else expr
    elif isinstance(expr, Abs):
        if expr.param == var:
            return expr  # x está ligado
        elif expr.param in free_vars(replacement):
            # α-conversão necessária
            new_param = expr.param + "'"
            new_body = substitute(expr.body, expr.param, Var(new_param))
            return Abs(new_param, substitute(new_body, var, replacement))
        else:
            return Abs(expr.param, substitute(expr.body, var, replacement))
    else:  # App
        return App(
            substitute(expr.func, var, replacement),
            substitute(expr.arg, var, replacement)
        )

def beta_reduce(expr: Expr) -> Expr:
    """Um passo de β-redução"""
    if isinstance(expr, App) and isinstance(expr.func, Abs):
        return substitute(expr.func.body, expr.func.param, expr.arg)
    return expr

# Church numerals
ZERO = Abs('f', Abs('x', Var('x')))  # λf.λx.x
ONE = Abs('f', Abs('x', App(Var('f'), Var('x'))))  # λf.λx.f x
SUCC = Abs('n', Abs('f', Abs('x',
    App(Var('f'), App(App(Var('n'), Var('f')), Var('x'))))))
```

### Tese de Church-Turing

> Uma função é efetivamente computável se e somente se é computável por uma Máquina de Turing (equivalentemente: por cálculo lambda).

**Equivalência**: MT ≡ λ-calculus ≡ funções μ-recursivas

### Conexão com Computação
- **Linguagens funcionais**: Haskell, Lisp, ML
- **Closures**: Funções de primeira classe
- **Higher-order functions**: map, filter, reduce

---

## 3. JOHN VON NEUMANN (1903-1957)

### Arquitetura von Neumann (1945)

O "First Draft of a Report on EDVAC" estabeleceu a arquitetura que todos os computadores modernos seguem:

```
┌─────────────────────────────────────────────┐
│                  CPU                         │
│  ┌─────────┐    ┌──────────────────────┐    │
│  │ Control │    │        ALU           │    │
│  │  Unit   │    │ (Arithmetic Logic)   │    │
│  └────┬────┘    └──────────┬───────────┘    │
│       │                    │                 │
│       └────────┬───────────┘                 │
│                │                             │
│         ┌──────┴──────┐                      │
│         │  Registers  │                      │
│         └──────┬──────┘                      │
└────────────────┼────────────────────────────┘
                 │
        ┌────────┴────────┐
        │    Memory       │
        │ (Program+Data)  │
        └─────────────────┘
```

### Ciclo Fetch-Decode-Execute

```python
class VonNeumannMachine:
    """Simulador de arquitetura von Neumann"""

    def __init__(self, memory_size: int = 256):
        self.memory = [0] * memory_size
        self.registers = {'A': 0, 'B': 0, 'PC': 0, 'IR': 0}
        self.running = True

    def load_program(self, program: list, start: int = 0):
        for i, instruction in enumerate(program):
            self.memory[start + i] = instruction

    def fetch(self):
        self.registers['IR'] = self.memory[self.registers['PC']]
        self.registers['PC'] += 1

    def decode_execute(self):
        ir = self.registers['IR']
        opcode = (ir >> 8) & 0xFF
        operand = ir & 0xFF

        if opcode == 0x01:    # LOAD A, [addr]
            self.registers['A'] = self.memory[operand]
        elif opcode == 0x02:  # STORE A, [addr]
            self.memory[operand] = self.registers['A']
        elif opcode == 0x03:  # ADD A, [addr]
            self.registers['A'] += self.memory[operand]
        elif opcode == 0x04:  # JMP addr
            self.registers['PC'] = operand
        elif opcode == 0x05:  # JZ addr (jump if zero)
            if self.registers['A'] == 0:
                self.registers['PC'] = operand
        elif opcode == 0xFF:  # HALT
            self.running = False

    def run(self):
        while self.running:
            self.fetch()
            self.decode_execute()
```

### Autômatos Celulares

Von Neumann também criou a teoria de **autômatos auto-replicantes**, demonstrando que máquinas podem se reproduzir.

```python
def game_of_life_step(grid):
    """
    Autômato celular de Conway
    (simplificação das ideias de von Neumann)
    """
    rows, cols = len(grid), len(grid[0])
    new_grid = [[0]*cols for _ in range(rows)]

    for i in range(rows):
        for j in range(cols):
            neighbors = sum(
                grid[(i+di) % rows][(j+dj) % cols]
                for di in [-1, 0, 1]
                for dj in [-1, 0, 1]
                if not (di == 0 and dj == 0)
            )

            if grid[i][j] == 1:
                new_grid[i][j] = 1 if neighbors in [2, 3] else 0
            else:
                new_grid[i][j] = 1 if neighbors == 3 else 0

    return new_grid
```

### Conexão com Computação
- **Todos os computadores modernos**: Arquitetura von Neumann
- **Stored program**: Programas e dados na mesma memória
- **Autômatos celulares**: Vida artificial, simulação

---

## 4. STEPHEN KLEENE (1909-1994)

### Expressões Regulares (1956)

Kleene formalizou padrões de texto como **álgebra**:

```
Operações:
- Concatenação: ab
- União: a|b
- Estrela de Kleene: a* (zero ou mais)
```

### Teoria da Recursão

Kleene definiu funções **primitivas recursivas** e **μ-recursivas**:

```python
# Funções Primitivas Recursivas
def zero(): return 0
def successor(n): return n + 1
def projection(i, *args): return args[i]

# Composição: h(x) = f(g1(x), g2(x), ...)
def compose(f, *gs):
    return lambda *args: f(*[g(*args) for g in gs])

# Recursão Primitiva: h(0) = f; h(n+1) = g(n, h(n))
def primitive_recursion(f, g):
    def h(n, *args):
        if n == 0:
            return f(*args)
        return g(n-1, h(n-1, *args), *args)
    return h

# Adição via recursão primitiva
# add(0, y) = y
# add(n+1, y) = succ(add(n, y))
add = primitive_recursion(
    lambda y: y,  # f(y) = y
    lambda n, prev, y: successor(prev)  # g(n, add(n,y), y) = succ(add(n,y))
)
```

### Conexão com Computação
- **Regex**: grep, sed, linguagens de programação
- **Autômatos finitos**: Lexers, parsers
- **Computabilidade**: Classes de funções computáveis

---

## 5. NOAM CHOMSKY (1928-)

### Hierarquia de Chomsky (1956)

```
Tipo 0: Gramáticas irrestritas (Máquinas de Turing)
   ↑
Tipo 1: Gramáticas sensíveis ao contexto (Linear Bounded Automata)
   ↑
Tipo 2: Gramáticas livres de contexto (Pushdown Automata)
   ↑
Tipo 3: Gramáticas regulares (Finite Automata)
```

```python
from enum import IntEnum

class ChomskyType(IntEnum):
    REGULAR = 3           # a → bA | b
    CONTEXT_FREE = 2      # A → γ (qualquer γ)
    CONTEXT_SENSITIVE = 1 # αAβ → αγβ (|γ| ≥ 1)
    UNRESTRICTED = 0      # α → β (qualquer)

def classify_grammar(productions: dict) -> ChomskyType:
    """Classifica gramática na hierarquia de Chomsky"""
    is_regular = True
    is_cf = True
    is_cs = True

    for lhs, rhs_list in productions.items():
        # Regular: A → aB ou A → a
        for rhs in rhs_list:
            if len(lhs) > 1:
                is_regular = False
                is_cf = False
            if not lhs.isupper():
                is_regular = False
                is_cf = False

    if is_regular:
        return ChomskyType.REGULAR
    if is_cf:
        return ChomskyType.CONTEXT_FREE
    if is_cs:
        return ChomskyType.CONTEXT_SENSITIVE
    return ChomskyType.UNRESTRICTED
```

### Conexão com Computação
- **Compiladores**: Parsing usa gramáticas livres de contexto
- **XML/JSON**: Linguagens de markup são CFG
- **Linguística computacional**: NLP, processamento de texto

---

## CONCEITOS FUNDAMENTAIS

### P vs NP

**P**: Problemas decidíveis em tempo polinomial
**NP**: Problemas verificáveis em tempo polinomial

```python
def is_in_P(problem):
    """
    Exemplo: Ordenação - O(n log n)
    Podemos RESOLVER em tempo polinomial
    """
    pass

def is_in_NP(problem, certificate):
    """
    Exemplo: SAT - dado certificado (atribuição), verificamos em O(n)
    Podemos VERIFICAR em tempo polinomial
    """
    pass

# A grande questão: P = NP?
# Se sim: todo problema verificável é resolvível eficientemente
# Se não: existem problemas "inerentemente difíceis"
```

### Classes de Complexidade

```
EXPSPACE
    ↑
PSPACE = NPSPACE (Savitch)
    ↑
EXPTIME
    ↑
NP ← NP-completo (Cook-Levin: SAT)
↑
P
↑
L (espaço logarítmico)
```

### Decidibilidade

```python
# DECIDÍVEL: Existe MT que sempre para com resposta
def decidable_example():
    """É n primo?"""
    def is_prime(n):
        if n < 2: return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0: return False
        return True
    return is_prime

# SEMI-DECIDÍVEL: MT para se "sim", pode não parar se "não"
def semi_decidable_example():
    """Existe prova de P em sistema S?"""
    pass  # Enumera provas, para se encontra

# INDECIDÍVEL: Nenhuma MT decide
# - Problema da parada
# - Equivalência de programas
# - Teorema de Rice: propriedades não-triviais de programas
```

---

## SÍNTESE

| Teórico | Contribuição | Impacto |
|---------|--------------|---------|
| Turing | Máquina Universal | Modelo de computação |
| Church | Cálculo Lambda | Programação funcional |
| von Neumann | Arquitetura | Hardware moderno |
| Kleene | Recursão, Regex | Fundamentos teóricos |
| Chomsky | Hierarquia | Compiladores, NLP |

---

## REFERÊNCIAS

- Turing, A. (1936). "On Computable Numbers"
- Church, A. (1936). "An Unsolvable Problem of Elementary Number Theory"
- von Neumann, J. (1945). "First Draft of a Report on EDVAC"
- Kleene, S. (1956). "Representation of Events in Nerve Nets"
- Chomsky, N. (1956). "Three Models for the Description of Language"
- Sipser, M. (2012). *Introduction to the Theory of Computation*

---

**Documento para treinamento NOESIS**
