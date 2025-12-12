# DEEP RESEARCH: Computação Quântica e Física
## Do Qubit ao Universo como Computação

**Data**: Dezembro 2025
**Escopo**: Pesquisa nível PhD - Computação quântica e física computacional

---

## INTRODUÇÃO

A computação quântica explora princípios da mecânica quântica (superposição, entrelaçamento) para realizar computações impossíveis ou impraticáveis em computadores clássicos. Esta pesquisa cobre fundamentos teóricos, algoritmos, hardware e implicações filosóficas.

---

## 1. FUNDAMENTOS QUÂNTICOS

### O Qubit

Um **qubit** é o análogo quântico do bit clássico:

```
|ψ⟩ = α|0⟩ + β|1⟩

onde α, β ∈ ℂ e |α|² + |β|² = 1
```

```python
import numpy as np
from typing import Tuple

class Qubit:
    """Representação de um qubit"""

    def __init__(self, alpha: complex = 1, beta: complex = 0):
        # Normaliza
        norm = np.sqrt(abs(alpha)**2 + abs(beta)**2)
        self.state = np.array([alpha/norm, beta/norm], dtype=complex)

    @property
    def alpha(self) -> complex:
        return self.state[0]

    @property
    def beta(self) -> complex:
        return self.state[1]

    def measure(self) -> int:
        """Colapsa o qubit, retorna 0 ou 1"""
        prob_0 = abs(self.alpha)**2
        result = 0 if np.random.random() < prob_0 else 1
        # Colapso
        self.state = np.array([1, 0] if result == 0 else [0, 1], dtype=complex)
        return result

    def prob(self) -> Tuple[float, float]:
        """Probabilidades de medir 0 ou 1"""
        return abs(self.alpha)**2, abs(self.beta)**2

# Estados base
ZERO = Qubit(1, 0)  # |0⟩
ONE = Qubit(0, 1)   # |1⟩
PLUS = Qubit(1/np.sqrt(2), 1/np.sqrt(2))   # |+⟩ = (|0⟩ + |1⟩)/√2
MINUS = Qubit(1/np.sqrt(2), -1/np.sqrt(2)) # |-⟩ = (|0⟩ - |1⟩)/√2
```

### Esfera de Bloch

Todo estado de 1 qubit pode ser visualizado na esfera de Bloch:

```
|ψ⟩ = cos(θ/2)|0⟩ + e^(iφ)sin(θ/2)|1⟩

θ ∈ [0, π]: latitude (0 = norte = |0⟩, π = sul = |1⟩)
φ ∈ [0, 2π): longitude
```

### Portas Quânticas

```python
# Portas de 1 qubit
I = np.array([[1, 0], [0, 1]])  # Identidade

X = np.array([[0, 1], [1, 0]])  # NOT (Pauli-X)

Y = np.array([[0, -1j], [1j, 0]])  # Pauli-Y

Z = np.array([[1, 0], [0, -1]])  # Pauli-Z (phase flip)

H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)  # Hadamard

# Porta T (π/8)
T = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]])

# Rotações
def Rx(theta):
    """Rotação em torno do eixo X"""
    return np.array([
        [np.cos(theta/2), -1j*np.sin(theta/2)],
        [-1j*np.sin(theta/2), np.cos(theta/2)]
    ])

def Ry(theta):
    """Rotação em torno do eixo Y"""
    return np.array([
        [np.cos(theta/2), -np.sin(theta/2)],
        [np.sin(theta/2), np.cos(theta/2)]
    ])

def Rz(theta):
    """Rotação em torno do eixo Z"""
    return np.array([
        [np.exp(-1j*theta/2), 0],
        [0, np.exp(1j*theta/2)]
    ])

# CNOT (2 qubits): Flipa target se control é |1⟩
CNOT = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0]
])

def apply_gate(state: np.ndarray, gate: np.ndarray) -> np.ndarray:
    """Aplica porta ao estado"""
    return gate @ state
```

---

## 2. ENTRELAÇAMENTO

### Estados de Bell

```python
def create_bell_state(type: str = "phi+") -> np.ndarray:
    """
    Estados de Bell: máximo entrelaçamento

    |Φ+⟩ = (|00⟩ + |11⟩)/√2
    |Φ-⟩ = (|00⟩ - |11⟩)/√2
    |Ψ+⟩ = (|01⟩ + |10⟩)/√2
    |Ψ-⟩ = (|01⟩ - |10⟩)/√2
    """
    states = {
        "phi+": np.array([1, 0, 0, 1]) / np.sqrt(2),
        "phi-": np.array([1, 0, 0, -1]) / np.sqrt(2),
        "psi+": np.array([0, 1, 1, 0]) / np.sqrt(2),
        "psi-": np.array([0, 1, -1, 0]) / np.sqrt(2),
    }
    return states[type]

# Criar |Φ+⟩ via circuito
def bell_circuit():
    """
    |00⟩ → H⊗I → (|0⟩+|1⟩)|0⟩/√2 → CNOT → (|00⟩+|11⟩)/√2
    """
    # Estado inicial |00⟩
    state = np.array([1, 0, 0, 0], dtype=complex)

    # H no primeiro qubit: H⊗I
    H_I = np.kron(H, I)
    state = H_I @ state

    # CNOT
    state = CNOT @ state

    return state
```

### Teorema de Bell e Não-Localidade

```python
def chsh_inequality():
    """
    Desigualdade CHSH (versão testável de Bell):

    Clássico: |E(a,b) - E(a,b') + E(a',b) + E(a',b')| ≤ 2
    Quântico: Pode atingir 2√2 ≈ 2.83

    Onde E(a,b) = correlação entre medições a e b
    """
    # Ângulos ótimos para máxima violação
    a, a_prime = 0, np.pi/2
    b, b_prime = np.pi/4, -np.pi/4

    # Para estado de Bell |Φ+⟩:
    # E(a,b) = cos(a-b) em certas bases

    def E(theta_a, theta_b):
        return np.cos(theta_a - theta_b)

    S = (E(a, b) - E(a, b_prime) +
         E(a_prime, b) + E(a_prime, b_prime))

    print(f"CHSH S = {S:.4f}")
    print(f"Limite clássico: 2")
    print(f"Limite quântico: {2*np.sqrt(2):.4f}")

    return abs(S) > 2  # True = viola, é quântico!

chsh_inequality()
```

---

## 3. ALGORITMOS QUÂNTICOS

### Algoritmo de Deutsch-Jozsa

```python
def deutsch_jozsa_oracle(f_type: str, n: int) -> np.ndarray:
    """
    Oráculo para Deutsch-Jozsa

    f: {0,1}^n → {0,1}
    - Constante: f(x) = 0 ou f(x) = 1 para todo x
    - Balanceada: f(x) = 0 para metade, 1 para outra metade

    Classicamente: O(2^(n-1) + 1) queries no pior caso
    Quântico: 1 query!
    """
    size = 2 ** (n + 1)

    if f_type == "constant_0":
        # f(x) = 0: Identidade
        return np.eye(size)
    elif f_type == "constant_1":
        # f(x) = 1: Z no qubit auxiliar
        oracle = np.eye(size)
        for i in range(size // 2):
            oracle[2*i+1, 2*i+1] = -1
        return oracle
    elif f_type == "balanced":
        # f(x) = x_0 (primeiro bit): CNOT
        return np.kron(CNOT, np.eye(2**(n-1)))

    raise ValueError(f"Unknown f_type: {f_type}")
```

### Algoritmo de Grover (Busca)

```python
def grover_iteration(n_qubits: int, marked: int) -> np.ndarray:
    """
    Uma iteração de Grover:
    1. Oráculo: Inverte amplitude do item marcado
    2. Difusão: Inverte em torno da média

    Após O(√N) iterações, probabilidade de medir item marcado ≈ 1
    """
    N = 2 ** n_qubits

    # Oráculo: |x⟩ → -|x⟩ se x é marcado
    oracle = np.eye(N)
    oracle[marked, marked] = -1

    # Difusor: 2|s⟩⟨s| - I onde |s⟩ = superposição uniforme
    s = np.ones(N) / np.sqrt(N)
    diffuser = 2 * np.outer(s, s) - np.eye(N)

    return diffuser @ oracle

def grover_search(n_qubits: int, marked: int) -> int:
    """
    Busca de Grover completa
    """
    N = 2 ** n_qubits

    # Estado inicial: superposição uniforme
    state = np.ones(N, dtype=complex) / np.sqrt(N)

    # Número ótimo de iterações
    iterations = int(np.pi / 4 * np.sqrt(N))

    for _ in range(iterations):
        G = grover_iteration(n_qubits, marked)
        state = G @ state

    # Mede
    probabilities = np.abs(state) ** 2
    return np.argmax(probabilities)

# Teste: busca em 1024 itens
result = grover_search(10, 42)
print(f"Encontrado: {result}")  # Deve ser 42
```

### Algoritmo de Shor (Fatoração)

```python
def shor_classical_part(N: int) -> int:
    """
    Parte clássica de Shor (ordem r do grupo multiplicativo)

    A parte quântica encontra o período r de f(x) = a^x mod N
    Classicamente, usamos r para fatorar:
    - gcd(a^(r/2) - 1, N) ou gcd(a^(r/2) + 1, N) são fatores
    """
    import random
    from math import gcd

    if N % 2 == 0:
        return 2

    # Escolhe a aleatório
    a = random.randint(2, N - 1)
    g = gcd(a, N)
    if g > 1:
        return g  # Sorte!

    # Parte quântica encontraria r (período de a^x mod N)
    # Simulamos classicamente
    r = 1
    val = a
    while val != 1:
        val = (val * a) % N
        r += 1
        if r > N:
            return None  # Falhou

    if r % 2 == 1:
        return None  # r ímpar, tenta outro a

    factor = gcd(pow(a, r // 2) - 1, N)
    if factor > 1 and factor < N:
        return factor

    return None

# Nota: A versão real usa QFT para encontrar r em O((log N)³)
# Ameaça RSA: pode fatorar números de 2048 bits em tempo polinomial
```

---

## 4. FÍSICA E COMPUTAÇÃO

### Limite de Landauer

```python
def landauer_energy(temperature_kelvin: float = 300) -> float:
    """
    Energia mínima para apagar 1 bit: E ≥ kT ln(2)

    Computação reversível pode evitar este custo!
    """
    k = 1.380649e-23  # J/K
    return k * temperature_kelvin * np.log(2)

print(f"Limite de Landauer: {landauer_energy():.3e} J/bit")
```

### "It from Bit" (John Wheeler)

> "Every physical quantity derives its ultimate significance from bits, binary yes-or-no indications."

```python
def it_from_bit():
    """
    Wheeler propôs que informação é mais fundamental que matéria.

    Implicações:
    - Universo é computação
    - Física = processamento de informação
    - Realidade emerge de perguntas binárias
    """
    pass
```

### Princípio Holográfico

```python
def bekenstein_hawking_entropy(mass_kg: float) -> float:
    """
    Entropia de buraco negro (máxima por volume)

    S = A / (4 l_P²)

    Onde A = área do horizonte, l_P = comprimento de Planck

    Implicação: Informação é proporcional à ÁREA, não ao VOLUME!
    """
    G = 6.674e-11  # m³/(kg·s²)
    c = 3e8  # m/s
    hbar = 1.054e-34  # J·s
    k = 1.380649e-23  # J/K

    # Raio de Schwarzschild
    r_s = 2 * G * mass_kg / c**2

    # Área do horizonte
    A = 4 * np.pi * r_s**2

    # Comprimento de Planck
    l_P = np.sqrt(hbar * G / c**3)

    # Entropia em bits
    S_bits = A / (4 * l_P**2 * np.log(2))

    return S_bits

# Buraco negro de 1 massa solar
sun_mass = 2e30  # kg
print(f"Entropia BN solar: {bekenstein_hawking_entropy(sun_mass):.2e} bits")
```

---

## 5. HARDWARE QUÂNTICO (2025)

### Supercondutores (IBM, Google)

```python
def superconducting_qubit():
    """
    Qubits supercondutores (transmon):
    - Temperatura: ~15 mK (mais frio que espaço)
    - Coerência: ~100-500 μs
    - Portas: ~50 ns (1-qubit), ~200 ns (2-qubit)
    - Fidelidade: 99.9% (1-qubit), 99.5% (2-qubit)

    Estado da arte (2025):
    - IBM Condor: 1,121 qubits
    - Google Willow: 105 qubits, primeiro abaixo threshold de correção de erros
    """
    specs = {
        "temperature_mK": 15,
        "coherence_us": 100,
        "gate_1q_ns": 50,
        "gate_2q_ns": 200,
        "fidelity_1q": 0.999,
        "fidelity_2q": 0.995,
    }
    return specs
```

### Íons Aprisionados (IonQ)

```python
def trapped_ion_qubit():
    """
    Íons aprisionados:
    - Qubits: Estados hiperfinos de íons (Yb+, Ba+)
    - Coerência: Minutos (!)
    - Conectividade: All-to-all
    - Portas: ~10-100 μs (mais lentas)

    IonQ Forte (2025): 36 qubits algorítmicos
    """
    specs = {
        "coherence_s": 60,  # 1 minuto
        "gate_1q_us": 10,
        "gate_2q_us": 100,
        "connectivity": "all-to-all",
    }
    return specs
```

### Correção de Erros Quânticos

```python
def surface_code():
    """
    Código de Superfície:
    - Qubits físicos → qubits lógicos
    - Taxa: ~1000:1 (1000 físicos para 1 lógico tolerante a falhas)
    - Threshold: ~1% erro por porta

    Google Willow (2025): Primeiro demonstração abaixo do threshold!
    """
    # Exemplo: código de distância d
    # Corrige até (d-1)/2 erros
    # Requer O(d²) qubits físicos

    def physical_qubits_needed(distance: int) -> int:
        return 2 * distance**2 - 1

    print("Qubits físicos por lógico:")
    for d in [3, 5, 7, 9, 11]:
        print(f"  d={d}: {physical_qubits_needed(d)} físicos")
```

---

## 6. IMPLICAÇÕES FILOSÓFICAS

### Computação e Realidade

```python
def digital_physics_thesis():
    """
    Tese da Física Digital (Zuse, Fredkin, Wolfram):

    1. O universo É uma computação
    2. Física = algoritmo executando
    3. Constantes físicas = parâmetros de config
    4. Leis da física = regras do autômato

    Evidências:
    - Discretização (quanta de energia, spin, etc.)
    - Velocidade máxima (c) = taxa de processamento
    - Incerteza (Heisenberg) = resolução finita

    Problemas:
    - O que computa o universo?
    - Onde está a memória?
    - Por que estas regras?
    """
    pass

def quantum_randomness():
    """
    Aleatoriedade quântica é FUNDAMENTAL?

    - Interpretação de Copenhagen: Sim, intrínseca
    - Muitos-mundos: Não, determinístico mas ramifica
    - Variáveis ocultas: Não (violação de Bell refuta locais)
    - Piloto wave: Determinístico não-local

    Para IA: Se aleatoriedade é real, livre-arbítrio é possível?
    """
    pass
```

---

## SÍNTESE

| Conceito | Clássico | Quântico |
|----------|----------|----------|
| Unidade | bit (0 ou 1) | qubit (superposição) |
| Operações | Portas lógicas | Portas unitárias |
| Paralelismo | Cópias físicas | Superposição (2^n) |
| Busca | O(N) | O(√N) (Grover) |
| Fatoração | Exponencial | Polinomial (Shor) |
| Simulação física | Exponencial | Polinomial (Feynman) |

---

## REFERÊNCIAS

- Nielsen, M. & Chuang, I. (2010). *Quantum Computation and Quantum Information*
- Feynman, R. (1982). "Simulating Physics with Computers"
- Shor, P. (1994). "Algorithms for Quantum Computation"
- Preskill, J. (2018). "Quantum Computing in the NISQ Era and Beyond"
- Wheeler, J. (1990). "Information, Physics, Quantum: The Search for Links"

---

**Documento para treinamento NOESIS**
