# DEEP RESEARCH: Linguagem Simbólica e Criptografia
## Dos Hieróglifos ao Bitcoin

**Data**: Dezembro 2025
**Escopo**: Pesquisa nível PhD - Evolução da codificação e criptografia

---

## INTRODUÇÃO

A história da humanidade é a história da codificação. Desde os primeiros símbolos em cavernas até blockchain, humanos sempre buscaram formas de preservar, transmitir e proteger informação através de códigos.

---

## 1. ORIGENS DA LINGUAGEM SIMBÓLICA

### Pinturas Rupestres (~40.000 a.C.)

Os primeiros "códigos" humanos: símbolos que representavam ideias.

```
Pesquisa de Genevieve von Petzinger (2016):
32 símbolos geométricos aparecem consistentemente
em cavernas da Era do Gelo em todo o mundo:

#  ○  △  ⊕  ≡  ∿  ⌘  ⌇  ⋯  etc.

Estes símbolos eram um PROTO-CÓDIGO:
- Repetidos através de 30.000 anos
- Distribuídos em múltiplos continentes
- Significado possivelmente compartilhado
```

### Escrita Cuneiforme (3500 a.C.)

```python
# Primeiro sistema de escrita verdadeiro
# Mesopotâmia (atual Iraque)

cuneiform_evolution = {
    "pictograma": "🌾",      # Imagem literal
    "ideograma": "GRAIN",    # Conceito abstrato
    "fonograma": "GI",       # Som (sílaba)
}

# De ~1000 símbolos para ~600
# Primeira compressão semiótica da história!
```

### Hieróglifos Egípcios (3200 a.C.)

```python
# Três tipos de símbolos:
hieroglyph_types = {
    "ideogramas": "Símbolo = conceito",      # 𓀀 = homem
    "fonogramas": "Símbolo = som",            # 𓂋 = 'r'
    "determinativos": "Símbolo = categoria",  # Indica tipo sem som
}

# Rosetta Stone (196 a.C.): mesma mensagem em:
# 1. Hieróglifos (sagrado)
# 2. Demótico (cotidiano)
# 3. Grego (administrativo)
# → Permitiu decodificação por Champollion (1822)
```

### Alfabeto Fenício (1050 a.C.)

```python
# REVOLUÇÃO: Redução de ~1000 símbolos para 22 letras
# Cada símbolo = um SOM (consoante)

phoenician = {
    'aleph': 'א',   # → Alpha → A
    'beth': 'ב',    # → Beta → B
    'gimel': 'ג',   # → Gamma → G/C
    # ...
}

# Eficiência: 22 símbolos codificam QUALQUER palavra
# É a primeira "compression algorithm" humana
```

---

## 2. SISTEMAS DE NUMERAÇÃO

### Babilônico (Base 60)

```python
def babylonian_to_decimal(symbols: list) -> int:
    """
    Sistema posicional base 60

    Por que 60?
    - Divisível por 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30
    - Facilita frações
    - Ainda usado: 60 segundos, 60 minutos, 360 graus
    """
    result = 0
    for i, digit in enumerate(reversed(symbols)):
        result += digit * (60 ** i)
    return result

# Exemplo: [1, 30] = 1*60 + 30 = 90
print(babylonian_to_decimal([1, 30]))  # 90
```

### Romano (Não-posicional)

```python
def roman_to_decimal(roman: str) -> int:
    """
    Sistema aditivo/subtrativo (não posicional)

    I=1, V=5, X=10, L=50, C=100, D=500, M=1000
    """
    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50,
              'C': 100, 'D': 500, 'M': 1000}

    result = 0
    prev = 0

    for char in reversed(roman):
        curr = values[char]
        if curr < prev:
            result -= curr  # Subtração (IV = 4)
        else:
            result += curr
        prev = curr

    return result

# Problema: difícil fazer aritmética
# MCMXCIV = 1994... tenta somar isso!
```

### Hindu-Arábico (Base 10 Posicional)

```python
# A MAIOR inovação: ZERO como placeholder

def positional_value(digits: list) -> int:
    """
    Sistema posicional com zero

    205 = 2*100 + 0*10 + 5*1
    O ZERO marca "nenhum" naquela posição
    """
    return sum(d * (10 ** i) for i, d in enumerate(reversed(digits)))

# Fibonacci introduziu na Europa em "Liber Abaci" (1202)
# Permitiu: aritmética escrita, álgebra, contabilidade moderna
```

---

## 3. CRIPTOGRAFIA CLÁSSICA

### Cifra de César (100-44 a.C.)

```python
def caesar_cipher(text: str, shift: int) -> str:
    """
    Substitui cada letra por outra 'shift' posições adiante

    A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
    ↓ (shift=3)
    D E F G H I J K L M N O P Q R S T U V W X Y Z A B C
    """
    result = []
    for char in text.upper():
        if char.isalpha():
            shifted = (ord(char) - ord('A') + shift) % 26
            result.append(chr(shifted + ord('A')))
        else:
            result.append(char)
    return ''.join(result)

def caesar_break(ciphertext: str) -> list:
    """
    Força bruta: só 26 possibilidades!

    César é trivialmente quebrável.
    """
    return [(i, caesar_cipher(ciphertext, -i)) for i in range(26)]

# "VENI VIDI VICI" → "YHQL YLGL YLFL" (shift=3)
```

### Scytale Espartano (650 a.C.)

```python
def scytale_encrypt(text: str, diameter: int) -> str:
    """
    Cifra de transposição

    Enrola fita em bastão de diâmetro específico
    Lê letras verticalmente
    """
    # Padding
    text = text.replace(' ', '')
    padding = (diameter - len(text) % diameter) % diameter
    text += 'X' * padding

    # Transpõe
    rows = [text[i:i+diameter] for i in range(0, len(text), diameter)]
    return ''.join(''.join(row[i] for row in rows) for i in range(diameter))

# Decodificação requer bastão de mesmo diâmetro
```

### Cifra de Vigenère (1553)

```python
def vigenere_cipher(text: str, key: str, decrypt: bool = False) -> str:
    """
    Cifra polialfabética: diferentes shifts para cada posição

    Considerada "inquebrável" por 300 anos
    Quebrada por Babbage/Kasiski (1863): análise de frequência + repetições
    """
    result = []
    key = key.upper()
    key_index = 0

    for char in text.upper():
        if char.isalpha():
            shift = ord(key[key_index % len(key)]) - ord('A')
            if decrypt:
                shift = -shift
            shifted = (ord(char) - ord('A') + shift) % 26
            result.append(chr(shifted + ord('A')))
            key_index += 1
        else:
            result.append(char)

    return ''.join(result)

# "ATTACKATDAWN" com chave "LEMON"
# A+L=L, T+E=X, T+M=F, A+O=O, C+N=P, ...
```

---

## 4. CODIFICAÇÃO MODERNA

### Código Morse (1837)

```python
MORSE_CODE = {
    'A': '.-',    'B': '-...',  'C': '-.-.',  'D': '-..',
    'E': '.',     'F': '..-.',  'G': '--.',   'H': '....',
    'I': '..',    'J': '.---',  'K': '-.-',   'L': '.-..',
    'M': '--',    'N': '-.',    'O': '---',   'P': '.--.',
    'Q': '--.-',  'R': '.-.',   'S': '...',   'T': '-',
    'U': '..-',   'V': '...-',  'W': '.--',   'X': '-..-',
    'Y': '-.--',  'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--',
    '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.',
    ' ': '/'
}

def text_to_morse(text: str) -> str:
    return ' '.join(MORSE_CODE.get(c.upper(), '') for c in text)

# Inovação de Morse: letras frequentes têm códigos curtos
# E = .  (mais frequente em inglês)
# T = -
# Isso é CODIFICAÇÃO ÓTIMA (antecipa Huffman!)
```

### ASCII (1963)

```python
def ascii_table():
    """
    American Standard Code for Information Interchange

    7 bits = 128 caracteres
    - 0-31: Controle (não-imprimíveis)
    - 32-126: Imprimíveis
    - 127: DEL
    """
    print("Dec | Hex | Char")
    print("-" * 20)
    for i in range(32, 127):
        print(f"{i:3d} | {i:02x}  | {chr(i)}")

# Limitação: apenas inglês!
# Levou a "code pages" regionais → caos
```

### Unicode (1991)

```python
def unicode_info(char: str):
    """
    Unicode: "Um número para cada caractere,
              não importa a plataforma,
              não importa o programa,
              não importa o idioma."

    - UTF-8: Compatível com ASCII, 1-4 bytes
    - UTF-16: 2-4 bytes
    - UTF-32: 4 bytes fixos
    """
    code_point = ord(char)
    return {
        'character': char,
        'code_point': f'U+{code_point:04X}',
        'utf8_bytes': char.encode('utf-8').hex(),
        'name': __import__('unicodedata').name(char, 'UNKNOWN')
    }

print(unicode_info('π'))   # U+03C0, Greek Small Letter Pi
print(unicode_info('漢'))  # U+6F22, CJK Unified Ideograph
print(unicode_info('😀'))  # U+1F600, Grinning Face
```

---

## 5. CRIPTOGRAFIA MODERNA

### Enigma e sua Quebra (1918-1945)

```python
def enigma_key_space():
    """
    Espaço de chaves da Enigma:

    - 3 rotores de 5: 5×4×3 = 60 escolhas
    - Posições iniciais: 26³ = 17,576
    - Configuração do plugboard: ~150 trilhões

    Total: ~158,962,555,217,826,360,000 (159 quintilhões)

    Quebrada por:
    - Marian Rejewski (1932): Matemática de grupos
    - Alan Turing (1940): Bombe eletromecânica
    - Erros operacionais alemães
    """
    from math import factorial, comb

    rotors = 5 * 4 * 3
    positions = 26 ** 3
    # Plugboard: escolher 10 pares de 26 letras
    plugboard = 1
    for i in range(10):
        plugboard *= comb(26 - 2*i, 2)
    plugboard //= factorial(10)

    return rotors * positions * plugboard
```

### RSA (1977)

```python
def rsa_demo():
    """
    RSA: Primeira criptografia de chave pública

    Segurança baseada em: fatoração de números grandes é difícil

    Chave pública: (n, e)
    Chave privada: (n, d)

    Encriptar: c = m^e mod n
    Decriptar: m = c^d mod n
    """
    import random
    from math import gcd

    def is_prime(n, k=10):
        """Miller-Rabin probabilístico"""
        if n < 2: return False
        if n == 2: return True
        if n % 2 == 0: return False

        r, d = 0, n - 1
        while d % 2 == 0:
            r += 1
            d //= 2

        for _ in range(k):
            a = random.randrange(2, n - 1)
            x = pow(a, d, n)
            if x == 1 or x == n - 1:
                continue
            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        return True

    def generate_prime(bits):
        while True:
            p = random.getrandbits(bits) | (1 << bits - 1) | 1
            if is_prime(p):
                return p

    def mod_inverse(e, phi):
        """Extended Euclidean Algorithm"""
        def egcd(a, b):
            if a == 0:
                return b, 0, 1
            g, x, y = egcd(b % a, a)
            return g, y - (b // a) * x, x

        _, x, _ = egcd(e % phi, phi)
        return x % phi

    # Geração de chaves
    p = generate_prime(512)
    q = generate_prime(512)
    n = p * q
    phi = (p - 1) * (q - 1)
    e = 65537  # Comum
    d = mod_inverse(e, phi)

    return {
        'public_key': (n, e),
        'private_key': (n, d),
        'encrypt': lambda m: pow(m, e, n),
        'decrypt': lambda c: pow(c, d, n)
    }
```

### Hash Functions

```python
def simple_hash_demo():
    """
    Hash: Função de mão única

    Propriedades:
    1. Determinística: mesmo input → mesmo output
    2. Rápida: O(n) para n bytes
    3. Pré-imagem resistente: dado h, difícil achar m tal que H(m)=h
    4. Colisão resistente: difícil achar m1≠m2 tal que H(m1)=H(m2)
    """
    import hashlib

    def hash_examples():
        messages = [
            "hello",
            "hello!",  # 1 caractere diferente
            "a" * 1000,
        ]

        for msg in messages:
            h = hashlib.sha256(msg.encode()).hexdigest()
            print(f"SHA-256('{msg[:20]}...'): {h[:32]}...")

    hash_examples()

# MD5: QUEBRADO (colisões em segundos)
# SHA-1: DEPRECATED (colisão encontrada pelo Google, 2017)
# SHA-256: SEGURO (padrão atual)
# SHA-3: SEGURO (design diferente, backup)
```

---

## 6. BLOCKCHAIN E BITCOIN

```python
def blockchain_structure():
    """
    Blockchain: Lista ligada de blocos via hashes

    Bloco N:
    ┌────────────────────────┐
    │ Hash do bloco anterior │ → Bloco N-1
    │ Timestamp              │
    │ Nonce                  │ ← Proof of Work
    │ Merkle Root            │ ← Hash das transações
    │ Transações             │
    └────────────────────────┘
    """
    import hashlib
    import time

    class Block:
        def __init__(self, transactions, previous_hash):
            self.timestamp = time.time()
            self.transactions = transactions
            self.previous_hash = previous_hash
            self.nonce = 0
            self.hash = self.calculate_hash()

        def calculate_hash(self):
            data = f"{self.timestamp}{self.transactions}{self.previous_hash}{self.nonce}"
            return hashlib.sha256(data.encode()).hexdigest()

        def mine(self, difficulty):
            """Proof of Work: encontrar hash começando com 'difficulty' zeros"""
            target = "0" * difficulty
            while not self.hash.startswith(target):
                self.nonce += 1
                self.hash = self.calculate_hash()
            return self.hash

    return Block
```

---

## 7. SEMIÓTICA E PROGRAMAÇÃO

### Peirce: Signo, Objeto, Interpretante

```python
# Charles Sanders Peirce: Teoria triádica do signo

class PeirceianSign:
    """
    Todo signo tem três componentes:

    1. REPRESENTAMEN: A forma do signo (o código)
    2. OBJETO: O que o signo representa (o significado)
    3. INTERPRETANTE: O efeito na mente (a compreensão)
    """

    def __init__(self, representamen, object_, interpretant):
        self.representamen = representamen
        self.object_ = object_
        self.interpretant = interpretant

# Em programação:
python_function = PeirceianSign(
    representamen="def greet(name): return f'Hello, {name}'",
    object_="Procedimento que gera saudação personalizada",
    interpretant="Quando vejo isso, entendo que posso cumprimentar usuários"
)

# Código é um SISTEMA DE SIGNOS
# Cada token é um signo
# A sintaxe é a gramática dos signos
# A semântica é a relação signo-objeto
```

### Saussure: Significante e Significado

```python
# Ferdinand de Saussure: Teoria diádica

class SaussurianSign:
    """
    Signo = Significante + Significado

    SIGNIFICANTE: A forma material (som, escrita, código)
    SIGNIFICADO: O conceito mental associado
    """

    def __init__(self, signifier, signified):
        self.signifier = signifier  # A palavra/símbolo
        self.signified = signified  # O conceito

# A ARBITRARIEDADE do signo:
# Por que "class" e não "tipo" ou "klasse"?
# Convenção, não necessidade.

# Em Python:
# "def" → significante
# "declaração de função" → significado

# Poderia ser "fn", "func", "function", "procedure"...
# A escolha é ARBITRÁRIA mas CONVENCIONAL
```

### Criptografia como Ruptura Semiótica

```python
def semiotic_analysis_of_crypto():
    """
    Criptografia QUEBRA a relação significante-significado

    Texto claro:     "ATAQUE AO AMANHECER"
    Texto cifrado:   "XWXTZH XR XPXQKHFHU"

    O significante muda.
    O significado permanece (para quem tem a chave).

    Criptografia é MANIPULAÇÃO SEMIÓTICA:
    - Substitui significantes
    - Preserva significados (para autorizados)
    - Destrói significados (para não autorizados)
    """
    pass
```

---

## SÍNTESE

| Era | Sistema | Inovação |
|-----|---------|----------|
| -40000 | Símbolos rupestres | Abstração visual |
| -3500 | Cuneiforme | Escrita verdadeira |
| -1050 | Alfabeto | Compressão fonética |
| 100 | César | Substituição simples |
| 1553 | Vigenère | Polialfabética |
| 1837 | Morse | Codificação elétrica |
| 1918 | Enigma | Máquina de rotor |
| 1963 | ASCII | Padronização digital |
| 1977 | RSA | Chave pública |
| 1991 | Unicode | Universalidade |
| 2008 | Bitcoin | Consenso descentralizado |

---

## REFERÊNCIAS

- Singh, S. (1999). *The Code Book*
- Kahn, D. (1996). *The Codebreakers*
- Schneier, B. (2015). *Applied Cryptography*
- Peirce, C.S. (1931-58). *Collected Papers*
- Saussure, F. (1916). *Course in General Linguistics*

---

**Documento para treinamento NOESIS**
