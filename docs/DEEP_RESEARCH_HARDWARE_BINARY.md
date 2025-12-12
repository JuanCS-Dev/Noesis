# DEEP RESEARCH: Hardware e Código Binário
## De Babbage aos Processadores Modernos

**Data**: Dezembro 2025
**Escopo**: Pesquisa nível PhD - Evolução do hardware e representação binária

---

## INTRODUÇÃO

A evolução do hardware de computação representa uma das maiores conquistas da engenharia humana. De engrenagens mecânicas a transistores de 2nm, cada geração multiplicou capacidades por ordens de magnitude.

---

## 1. PIONEIROS MECÂNICOS

### Charles Babbage (1791-1871)

**Máquina Diferencial** (1822): Calculava polinômios pelo método das diferenças finitas.

**Máquina Analítica** (1837): Primeiro design de computador programável:
- **Mill** (processador): Operações aritméticas
- **Store** (memória): 1000 números de 50 dígitos
- **Cartões perfurados**: Programa e dados
- **Impressora**: Output

### Ada Lovelace (1815-1852)

Primeiro programa documentado (números de Bernoulli):

```python
# Algoritmo de Ada Lovelace (reconstruído)
def bernoulli_numbers(n: int) -> list:
    """
    Números de Bernoulli pelo método de Ada

    B_0 = 1
    B_n = -Σ(k=0 to n-1) C(n+1,k) * B_k / (n+1)
    """
    from math import comb

    B = [0] * (n + 1)
    B[0] = 1

    for m in range(1, n + 1):
        B[m] = -sum(comb(m + 1, k) * B[k] for k in range(m)) / (m + 1)

    return B

print(bernoulli_numbers(10))
```

Ada previu que a máquina poderia manipular qualquer símbolo com regras definidas - não apenas números.

---

## 2. SISTEMA BINÁRIO

### Leibniz e o Binário (1703)

```python
def leibniz_binary_table():
    """
    Leibniz publicou 'Explication de l'Arithmétique Binaire'
    mostrando que qualquer número pode ser representado com 0 e 1
    """
    print("Tabela de Leibniz:")
    print("Dec | Bin")
    print("-" * 12)
    for i in range(16):
        print(f" {i:2d} | {bin(i)[2:]:>4s}")
```

### Representação de Inteiros

```python
import struct

# Unsigned integers
def unsigned_binary(n: int, bits: int = 8) -> str:
    """Inteiro sem sinal"""
    return format(n, f'0{bits}b')

# Complemento de 2 (signed)
def twos_complement(n: int, bits: int = 8) -> str:
    """
    Complemento de 2: números negativos

    Para -n: inverta bits de n e some 1
    Range: [-2^(n-1), 2^(n-1) - 1]
    """
    if n >= 0:
        return format(n, f'0{bits}b')
    else:
        return format((1 << bits) + n, f'0{bits}b')

print(f" 5 em 8 bits: {twos_complement(5, 8)}")   # 00000101
print(f"-5 em 8 bits: {twos_complement(-5, 8)}")  # 11111011

# IEEE 754 Floating Point
def float_to_binary(f: float) -> str:
    """
    IEEE 754 single precision (32 bits):
    - 1 bit: sinal
    - 8 bits: expoente (bias 127)
    - 23 bits: mantissa

    (-1)^s × 1.mantissa × 2^(expoente-127)
    """
    packed = struct.pack('>f', f)
    binary = ''.join(format(byte, '08b') for byte in packed)

    sign = binary[0]
    exponent = binary[1:9]
    mantissa = binary[9:]

    return f"S={sign} E={exponent} M={mantissa}"

print(float_to_binary(3.14))
print(float_to_binary(-0.1))  # Nota: 0.1 não é representável exatamente!
```

---

## 3. PORTAS LÓGICAS

### Álgebra Booleana em Circuitos

```python
# Simulação de portas lógicas
def AND(a: int, b: int) -> int:
    return a & b

def OR(a: int, b: int) -> int:
    return a | b

def NOT(a: int) -> int:
    return 1 - a

def NAND(a: int, b: int) -> int:
    """NAND é universal: qualquer circuito pode ser construído apenas com NAND"""
    return NOT(AND(a, b))

def XOR(a: int, b: int) -> int:
    return a ^ b

# Half Adder: soma 2 bits
def half_adder(a: int, b: int) -> tuple:
    """
    A + B = (Sum, Carry)

    Sum = A XOR B
    Carry = A AND B
    """
    return XOR(a, b), AND(a, b)

# Full Adder: soma 3 bits (para encadear)
def full_adder(a: int, b: int, cin: int) -> tuple:
    """
    A + B + Cin = (Sum, Cout)
    """
    sum1, carry1 = half_adder(a, b)
    sum2, carry2 = half_adder(sum1, cin)
    return sum2, OR(carry1, carry2)

# Ripple Carry Adder (4 bits)
def ripple_carry_adder(a: list, b: list) -> tuple:
    """
    Soma dois números de 4 bits

    Latência: O(n) - carry propaga bit a bit
    """
    assert len(a) == len(b) == 4

    result = []
    carry = 0

    for i in range(4):
        s, carry = full_adder(a[i], b[i], carry)
        result.append(s)

    return result, carry

# Teste: 5 + 3 = 8
a = [1, 0, 1, 0]  # 5 em binário (LSB first)
b = [1, 1, 0, 0]  # 3 em binário
result, overflow = ripple_carry_adder(a, b)
print(f"5 + 3 = {result} (overflow={overflow})")  # [0, 0, 0, 1] = 8
```

---

## 4. EVOLUÇÃO DO HARDWARE

### Linha do Tempo

```
1642  Pascal      Pascaline (mecânica)
1837  Babbage     Máquina Analítica (design)
1890  Hollerith   Cartões perfurados (IBM)
1941  Zuse        Z3 (primeiro programável funcional)
1945  ENIAC       Primeiro eletrônico de propósito geral
1947  Transistor  Bell Labs (Bardeen, Brattain, Shockley)
1958  IC          Primeiro circuito integrado (Kilby, Noyce)
1971  Intel 4004  Primeiro microprocessador (2,300 transistores)
1978  Intel 8086  Arquitetura x86
2020  Apple M1    5nm, 16B transistores
2024  NVIDIA H100 ~80B transistores
```

### Lei de Moore

```python
def moores_law(year: int, baseline_year: int = 1971,
               baseline_transistors: int = 2300) -> int:
    """
    Lei de Moore: transistores dobram a cada ~2 anos

    Previsão de Gordon Moore (1965): "The number of transistors on
    integrated circuits doubles about every two years."
    """
    years_elapsed = year - baseline_year
    doublings = years_elapsed / 2
    return int(baseline_transistors * (2 ** doublings))

# Previsões vs Realidade
predictions = {
    1971: (2300, moores_law(1971)),        # Intel 4004
    1985: (275000, moores_law(1985)),      # Intel 386
    2000: (42000000, moores_law(2000)),    # Pentium 4
    2020: (16000000000, moores_law(2020)), # Apple M1
}

print("Ano  | Real         | Previsão Moore")
for year, (real, pred) in predictions.items():
    print(f"{year} | {real:>12,} | {pred:>12,}")
```

---

## 5. ARQUITETURA DE PROCESSADORES

### Ciclo Fetch-Decode-Execute

```python
class SimpleCPU:
    """
    CPU simplificada com ciclo F-D-E
    """
    def __init__(self):
        self.memory = [0] * 256
        self.registers = [0] * 8  # R0-R7
        self.pc = 0  # Program Counter
        self.ir = 0  # Instruction Register
        self.running = True

    def fetch(self):
        """Busca instrução da memória"""
        self.ir = self.memory[self.pc]
        self.pc += 1

    def decode_execute(self):
        """Decodifica e executa"""
        opcode = (self.ir >> 12) & 0xF
        r1 = (self.ir >> 8) & 0xF
        r2 = (self.ir >> 4) & 0xF
        imm = self.ir & 0xFF

        if opcode == 0x0:    # HALT
            self.running = False
        elif opcode == 0x1:  # LOAD R, imm
            self.registers[r1] = imm
        elif opcode == 0x2:  # ADD R1, R2
            self.registers[r1] += self.registers[r2]
        elif opcode == 0x3:  # SUB R1, R2
            self.registers[r1] -= self.registers[r2]
        elif opcode == 0x4:  # MUL R1, R2
            self.registers[r1] *= self.registers[r2]
        elif opcode == 0x5:  # JMP addr
            self.pc = imm
        elif opcode == 0x6:  # JZ R, addr
            if self.registers[r1] == 0:
                self.pc = imm

    def run(self):
        while self.running and self.pc < len(self.memory):
            self.fetch()
            self.decode_execute()
```

### Pipeline

```
Estágio 1: Fetch      (IF)  - Busca instrução
Estágio 2: Decode     (ID)  - Decodifica, lê registradores
Estágio 3: Execute    (EX)  - ALU opera
Estágio 4: Memory     (MEM) - Acesso à memória
Estágio 5: Writeback  (WB)  - Escreve resultado

Tempo |  1  |  2  |  3  |  4  |  5  |  6  |  7  |
------+-----+-----+-----+-----+-----+-----+-----+
Inst1 | IF  | ID  | EX  | MEM | WB  |     |     |
Inst2 |     | IF  | ID  | EX  | MEM | WB  |     |
Inst3 |     |     | IF  | ID  | EX  | MEM | WB  |

→ Throughput: 1 instrução/ciclo (ideal)
→ Latência: 5 ciclos/instrução
```

### CISC vs RISC

```python
# CISC (x86): Instruções complexas, variáveis
x86_example = """
; Soma array em x86 (CISC)
mov ecx, [length]
mov eax, 0
loop_start:
    add eax, [array + ecx*4 - 4]
    dec ecx
    jnz loop_start
"""

# RISC (ARM): Instruções simples, fixas
arm_example = """
; Soma array em ARM (RISC)
    ldr r0, =array
    ldr r1, =length
    ldr r1, [r1]
    mov r2, #0
loop:
    ldr r3, [r0], #4
    add r2, r2, r3
    subs r1, r1, #1
    bne loop
"""
```

---

## 6. HARDWARE MODERNO

### GPUs

```python
def gpu_architecture():
    """
    GPU NVIDIA (2025):

    - Streaming Multiprocessors (SMs): ~100+
    - CUDA cores por SM: ~128
    - Total CUDA cores: ~16,000+
    - Tensor cores: Operações de matriz
    - Memória HBM: ~80 GB, ~3 TB/s

    Modelo de programação SIMT:
    - Single Instruction, Multiple Threads
    - Milhares de threads executam mesma instrução
    """
    pass

# Pseudocódigo CUDA
cuda_example = """
__global__ void vector_add(float* a, float* b, float* c, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        c[i] = a[i] + b[i];
    }
}

// Lança 1 milhão de threads em paralelo!
vector_add<<<blocks, threads>>>(a, b, c, 1000000);
"""
```

### TPUs (Tensor Processing Units)

```python
def tpu_systolic_array():
    """
    TPU usa arrays sistólicos para multiplicação de matrizes

    Dados fluem através de array 2D de unidades de processamento
    Cada unidade: multiply-accumulate (MAC)

    Throughput: O(n²) MACs por ciclo para matriz n×n
    """
    # Simulação simplificada
    def systolic_matmul(A, B):
        """
        Multiplicação de matriz via array sistólico

        A (m×k), B (k×n) → C (m×n)
        """
        import numpy as np
        m, k = A.shape
        _, n = B.shape

        # Em hardware real, dados "fluem" através do array
        # Aqui, simulamos o resultado
        C = np.zeros((m, n))

        for i in range(m):
            for j in range(n):
                for l in range(k):
                    C[i, j] += A[i, l] * B[l, j]

        return C

    return systolic_matmul
```

---

## 7. DO BINÁRIO AO ALTO NÍVEL

### Hierarquia de Abstração

```
Nível 7: Aplicação     (Python, JavaScript)
Nível 6: Framework     (TensorFlow, React)
Nível 5: Linguagem     (C, Rust)
Nível 4: Assembly      (x86, ARM)
Nível 3: ISA           (Instruction Set)
Nível 2: Microarquitetura (Pipeline, Cache)
Nível 1: Lógica Digital (Portas, Flip-flops)
Nível 0: Física        (Transistores, Elétrons)
```

### Compilação

```python
def compilation_pipeline():
    """
    Código Fonte → Executável

    1. Lexer: Código → Tokens
    2. Parser: Tokens → AST
    3. Semantic Analysis: Tipos, escopos
    4. IR Generation: AST → LLVM IR
    5. Optimization: Constant folding, inlining, etc.
    6. Code Generation: IR → Assembly
    7. Assembler: Assembly → Object code
    8. Linker: Objects → Executable
    """
    pass

# Exemplo: x = a + b * c
example_flow = """
Código:   x = a + b * c

Tokens:   [ID:x, ASSIGN, ID:a, PLUS, ID:b, MULT, ID:c]

AST:      Assign
          /    \\
         x     Add
              /   \\
             a    Mult
                 /   \\
                b     c

IR (SSA): %1 = load a
          %2 = load b
          %3 = load c
          %4 = mul %2, %3
          %5 = add %1, %4
          store %5, x

x86:      mov eax, [b]
          imul eax, [c]
          add eax, [a]
          mov [x], eax
"""
```

---

## SÍNTESE

| Era | Tecnologia | Escala | Velocidade |
|-----|------------|--------|------------|
| 1940s | Válvulas | 10³ ops/s | kHz |
| 1960s | Transistores | 10⁶ ops/s | MHz |
| 1980s | VLSI | 10⁹ ops/s | ~GHz |
| 2000s | Multi-core | 10¹² ops/s | GHz |
| 2020s | GPUs/TPUs | 10¹⁵ ops/s | - |

---

## REFERÊNCIAS

- Hennessy, J. & Patterson, D. (2017). *Computer Architecture: A Quantitative Approach*
- Tanenbaum, A. (2012). *Structured Computer Organization*
- Harris, D. & Harris, S. (2012). *Digital Design and Computer Architecture*
- Patterson, D. & Hennessy, J. (2020). *Computer Organization and Design: RISC-V Edition*

---

**Documento para treinamento NOESIS**
