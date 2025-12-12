# DEEP RESEARCH: Teoria da Informação
## Shannon, Kolmogorov e a Matemática da Comunicação

**Data**: Dezembro 2025
**Escopo**: Pesquisa nível PhD - Teoria da informação e aplicações

---

## INTRODUÇÃO

A teoria da informação, fundada por Claude Shannon em 1948, quantifica informação matematicamente. Esta teoria é o fundamento de compressão de dados, comunicação digital, criptografia e machine learning.

---

## 1. CLAUDE SHANNON (1916-2001)

### "A Mathematical Theory of Communication" (1948)

Shannon definiu **informação** como redução de incerteza, medida em **bits**.

### Entropia da Informação

```
H(X) = -Σ p(x) log₂ p(x)
```

A entropia mede a incerteza média de uma fonte de informação.

```python
import math
from typing import Dict, List
from collections import Counter

def entropy(probabilities: List[float]) -> float:
    """
    Entropia de Shannon
    H(X) = -Σ p(x) log₂ p(x)
    """
    return -sum(p * math.log2(p) for p in probabilities if p > 0)

def entropy_from_data(data: List) -> float:
    """Calcula entropia de dados observados"""
    counts = Counter(data)
    total = len(data)
    probs = [count / total for count in counts.values()]
    return entropy(probs)

# Exemplos
print(f"Moeda justa: {entropy([0.5, 0.5]):.4f} bits")  # 1.0
print(f"Moeda viciada (90/10): {entropy([0.9, 0.1]):.4f} bits")  # 0.469
print(f"Dado justo: {entropy([1/6]*6):.4f} bits")  # 2.585

# Texto em português tem ~4.5 bits/letra
texto = "a informacao e a reducao da incerteza"
print(f"Entropia do texto: {entropy_from_data(texto):.4f} bits/símbolo")
```

### Entropia Condicional e Informação Mútua

```python
def conditional_entropy(joint_probs: Dict[tuple, float],
                        marginal_y: Dict, var_y_values) -> float:
    """
    H(X|Y) = -Σ p(x,y) log₂ p(x|y)
    """
    h = 0
    for (x, y), p_xy in joint_probs.items():
        if p_xy > 0:
            p_y = marginal_y[y]
            p_x_given_y = p_xy / p_y
            h -= p_xy * math.log2(p_x_given_y)
    return h

def mutual_information(joint_probs: Dict[tuple, float],
                       marginal_x: Dict, marginal_y: Dict) -> float:
    """
    I(X;Y) = H(X) - H(X|Y) = H(Y) - H(Y|X)

    Mede quanto saber Y reduz incerteza sobre X
    """
    mi = 0
    for (x, y), p_xy in joint_probs.items():
        if p_xy > 0:
            p_x = marginal_x[x]
            p_y = marginal_y[y]
            mi += p_xy * math.log2(p_xy / (p_x * p_y))
    return mi
```

### Teorema de Shannon-Hartley

Capacidade máxima de um canal com ruído:

```
C = B log₂(1 + S/N)

C = capacidade (bits/segundo)
B = largura de banda (Hz)
S/N = razão sinal/ruído
```

```python
def channel_capacity(bandwidth_hz: float, snr_db: float) -> float:
    """
    Teorema de Shannon-Hartley
    C = B log₂(1 + SNR)
    """
    snr_linear = 10 ** (snr_db / 10)
    return bandwidth_hz * math.log2(1 + snr_linear)

# WiFi 802.11ac: 160 MHz, SNR ~25 dB
wifi_capacity = channel_capacity(160e6, 25)
print(f"Capacidade teórica WiFi: {wifi_capacity/1e9:.2f} Gbps")

# 4G LTE: 20 MHz, SNR ~20 dB
lte_capacity = channel_capacity(20e6, 20)
print(f"Capacidade teórica LTE: {lte_capacity/1e6:.2f} Mbps")
```

### Codificação de Huffman

```python
import heapq
from collections import defaultdict

def huffman_encoding(text: str) -> tuple:
    """
    Codificação de Huffman: códigos de comprimento variável
    Símbolos frequentes → códigos curtos
    """
    # Conta frequências
    freq = Counter(text)

    # Constrói heap de nós
    heap = [[count, [char, ""]] for char, count in freq.items()]
    heapq.heapify(heap)

    # Constrói árvore
    while len(heap) > 1:
        lo = heapq.heappop(heap)
        hi = heapq.heappop(heap)

        for pair in lo[1:]:
            pair[1] = '0' + pair[1]
        for pair in hi[1:]:
            pair[1] = '1' + pair[1]

        heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])

    # Extrai códigos
    codes = {char: code for char, code in heap[0][1:]}

    # Codifica
    encoded = ''.join(codes[c] for c in text)

    # Eficiência
    original_bits = len(text) * 8
    compressed_bits = len(encoded)
    ratio = compressed_bits / original_bits

    return codes, encoded, ratio

text = "ABRACADABRA"
codes, encoded, ratio = huffman_encoding(text)
print(f"Códigos: {codes}")
print(f"Compressão: {ratio:.2%}")
```

---

## 2. KOLMOGOROV (1903-1987)

### Complexidade Algorítmica

A **complexidade de Kolmogorov** K(x) é o tamanho do menor programa que produz x:

```python
def kolmogorov_approximation(data: bytes) -> int:
    """
    Aproximação da complexidade de Kolmogorov via compressão

    K(x) ≈ tamanho do dado comprimido + tamanho do descompressor
    """
    import zlib
    compressed = zlib.compress(data, level=9)
    return len(compressed)

# Dados aleatórios: alta complexidade
import random
random_data = bytes([random.randint(0, 255) for _ in range(1000)])
print(f"Dados aleatórios: K ≈ {kolmogorov_approximation(random_data)}")

# Dados repetitivos: baixa complexidade
repetitive = b"ABCD" * 250
print(f"Dados repetitivos: K ≈ {kolmogorov_approximation(repetitive)}")

# Padrão: complexidade média
pattern = bytes([(i * 17) % 256 for i in range(1000)])
print(f"Padrão: K ≈ {kolmogorov_approximation(pattern)}")
```

### Incompressibilidade

> A maioria das strings são incompressíveis (teorema de contagem).

```python
def incompressibility_lemma():
    """
    Lema da Incompressibilidade:
    Para qualquer n, existe string de n bits com K(x) ≥ n

    Prova: Existem 2^n strings de n bits
           Existem < 2^n programas de < n bits
           Logo, pelo princípio da casa dos pombos,
           alguma string não pode ser comprimida
    """
    pass
```

---

## 3. APLICAÇÕES

### Compressão de Dados

```python
# LZ77 (base de ZIP, gzip)
def lz77_encode(text: str, window_size: int = 20) -> list:
    """
    LZ77: Substitui repetições por referências (offset, length)
    """
    encoded = []
    i = 0

    while i < len(text):
        best_offset, best_length = 0, 0

        # Busca no buffer de look-back
        start = max(0, i - window_size)
        for j in range(start, i):
            length = 0
            while (i + length < len(text) and
                   text[j + length] == text[i + length] and
                   length < 255):
                length += 1

            if length > best_length:
                best_offset = i - j
                best_length = length

        if best_length > 2:
            encoded.append((best_offset, best_length))
            i += best_length
        else:
            encoded.append(text[i])
            i += 1

    return encoded
```

### Cross-Entropy em Machine Learning

```python
import numpy as np

def cross_entropy_loss(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Cross-entropy loss: H(p, q) = -Σ p(x) log q(x)

    Mede quão bem q (predições) aproxima p (labels)
    """
    epsilon = 1e-15  # Evita log(0)
    y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
    return -np.sum(y_true * np.log(y_pred))

def kl_divergence(p: np.ndarray, q: np.ndarray) -> float:
    """
    KL Divergence: D_KL(p||q) = Σ p(x) log(p(x)/q(x))

    Mede "distância" entre distribuições
    """
    epsilon = 1e-15
    p = np.clip(p, epsilon, 1)
    q = np.clip(q, epsilon, 1)
    return np.sum(p * np.log(p / q))

# Em ML: minimizar cross-entropy = minimizar KL divergence
# H(p, q) = H(p) + D_KL(p||q)
```

### Criptografia e Entropia

```python
def password_entropy(password: str) -> float:
    """
    Entropia de senha: mede força contra brute-force

    E = log₂(N^L) onde N = tamanho do alfabeto, L = comprimento
    """
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    charset_size = 0
    if has_lower: charset_size += 26
    if has_upper: charset_size += 26
    if has_digit: charset_size += 10
    if has_special: charset_size += 32

    if charset_size == 0:
        return 0

    return len(password) * math.log2(charset_size)

# Recomendação NIST: mínimo 80 bits de entropia
print(f"'password': {password_entropy('password'):.1f} bits")  # Fraca
print(f"'P@ssw0rd!': {password_entropy('P@ssw0rd!'):.1f} bits")  # Média
print(f"'Tr0ub4dor&3': {password_entropy('Tr0ub4dor&3'):.1f} bits")  # Boa
```

---

## 4. CONEXÕES PROFUNDAS

### Princípio de Landauer

Apagar 1 bit de informação requer energia mínima:

```
E ≥ kT ln(2) ≈ 2.87 × 10⁻²¹ J (a 300K)
```

```python
def landauer_limit(temperature_kelvin: float = 300) -> float:
    """
    Limite termodinâmico de Landauer
    Energia mínima para apagar 1 bit
    """
    k_boltzmann = 1.380649e-23  # J/K
    return k_boltzmann * temperature_kelvin * math.log(2)

print(f"Limite de Landauer a 300K: {landauer_limit():.3e} J/bit")

# Um computador moderno opera ~10^6 × acima deste limite
# Ainda há muito espaço para eficiência!
```

### Demônio de Maxwell (Resolvido)

O demônio precisa **medir** posições das moléculas, o que gera informação.
Para continuar operando, precisa **apagar** esta informação.
Pelo princípio de Landauer, isso dissipa calor ≥ trabalho extraído.

### Informação e Física

```python
def bekenstein_bound(mass_kg: float, radius_m: float) -> float:
    """
    Limite de Bekenstein: Máxima informação em região do espaço

    I ≤ (2π R E) / (ℏ c ln 2)

    Onde E = mc²
    """
    c = 3e8  # m/s
    hbar = 1.054e-34  # J·s

    energy = mass_kg * c**2
    max_bits = (2 * math.pi * radius_m * energy) / (hbar * c * math.log(2))
    return max_bits

# Cérebro humano: ~1.4 kg, ~0.1 m
brain_bits = bekenstein_bound(1.4, 0.1)
print(f"Limite de Bekenstein (cérebro): {brain_bits:.2e} bits")
# ~10^42 bits - muito mais que os ~10^15 bits estimados de capacidade
```

---

## 5. TEORIA DA INFORMAÇÃO EM IA/ML

### Information Bottleneck

```python
def information_bottleneck_intuition():
    """
    Tishby's Information Bottleneck:

    Objetivo: Encontrar representação T que:
    - Maximiza I(T; Y) - informação sobre target
    - Minimiza I(T; X) - compressão do input

    L = I(T; X) - β I(T; Y)

    Em deep learning: cada camada comprime X enquanto preserva Y
    """
    pass
```

### VAE e KL Divergence

```python
def vae_loss(x_true, x_reconstructed, z_mean, z_log_var):
    """
    Variational Autoencoder loss:

    L = E[log p(x|z)] - D_KL(q(z|x) || p(z))
      = Reconstruction - KL regularization
    """
    # Reconstrução (cross-entropy ou MSE)
    reconstruction_loss = np.mean((x_true - x_reconstructed)**2)

    # KL divergence de N(μ, σ²) para N(0, 1)
    kl_loss = -0.5 * np.mean(1 + z_log_var - z_mean**2 - np.exp(z_log_var))

    return reconstruction_loss + kl_loss
```

---

## SÍNTESE

| Conceito | Fórmula | Aplicação |
|----------|---------|-----------|
| Entropia | H(X) = -Σ p log p | Compressão, incerteza |
| Informação Mútua | I(X;Y) = H(X) - H(X\|Y) | Dependência, features |
| Cross-Entropy | H(p,q) = -Σ p log q | Loss em ML |
| KL Divergence | D(p\|\|q) = Σ p log(p/q) | Regularização, VAE |
| Capacidade | C = B log(1+SNR) | Limites de comunicação |

---

## REFERÊNCIAS

- Shannon, C. (1948). "A Mathematical Theory of Communication"
- Kolmogorov, A. (1965). "Three Approaches to the Definition of Information"
- Cover, T. & Thomas, J. (2006). *Elements of Information Theory*
- MacKay, D. (2003). *Information Theory, Inference, and Learning Algorithms*
- Landauer, R. (1961). "Irreversibility and Heat Generation in the Computing Process"

---

**Documento para treinamento NOESIS**
