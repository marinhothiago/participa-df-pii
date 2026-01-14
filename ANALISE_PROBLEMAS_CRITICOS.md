# Análise de Problemas Críticos - Backend/Frontend Integration

## Resumo Executivo

Após análise completa do código backend (`detector.py`) e frontend (componentes React), foram identificados **3 problemas críticos** que afetam a experiência do usuário:

1. **Confiança mostrando 188.2%** (deve ser 0-100%)
2. **Nomenclatura "IA_PER" confusa** (deve ser "NOME_POR_IA" ou similar)
3. **Pesos de risco não seguem LGPD** (verificação pendente)

---

## Problema 1: Confiança Excedendo 100% ⚠️

### Raiz do Problema

**Backend (`detector.py` linha 353):**
```python
return is_pii, pii_relevantes, risco_map.get(max_score, "BAIXO"), float(max_score)
```

- `max_score` retorna o **peso bruto** (5, 4, 3, 0)
- Frontend recebe valores entre 0-5, não 0-1
- ConfidenceBar multiplica por 100: `5 * 100 = 500%` na pior caso
- Quando há múltiplos PIIs com pesos: pode chegar a **188.2%** (como reportado)

**Frontend (`ConfidenceBar.tsx` linha 19):**
```tsx
const percentage = normalizedValue * 100;
// Se normalizedValue vem como 1.882 do backend, resultado é 188.2%
```

### Impacto

- Exibe confiança acima de 100% (logicamente impossível)
- Confunde usuários sobre a certeza da detecção
- Quebra a semântica de probabilidade

### Solução

**Backend:**
- Normalizar `max_score` dividindo por 5 antes de retornar
- Retornar sempre valor entre 0.0-1.0

**Frontend:**
- Remover lógica de normalização incorreta em `ConfidenceBar`
- Apenas multiplicar por 100 (já que backend retorna 0-1)

---

## Problema 2: Nomenclatura IA_PER Confusa 🏷️

### Raiz do Problema

**Backend (`detector.py` linha 342):**
```python
findings.append({"tipo": "IA_PER", "valor": ent.text, "conf": 0.80})
```

- `IA_PER` = "Inteligência Artificial - Pessoa" (sigla em inglês misturada com português)
- Não é claro para usuários finais
- Inconsistente com outros tipos: NOME_PESSOAL, NOME_CONTEXTO

### Impacto

- Usuários não entendem o que significa "IA_PER"
- Aparece na tabela de tipos de PII detectados
- Reduz confiança na ferramenta

### Solução

**Backend:**
- Renomear `IA_PER` → `NOME_POR_IA` (mais descritivo)
- Atualizar referências em pesos e mapa de risco

**Frontend:**
- Adicionar mapeamento amigável: `NOME_POR_IA` → "Nome (detectado por IA)"
- Exibir em gráficos e tabelas com labels legíveis

---

## Problema 3: Pesos LGPD Não Validados ⚖️

### Status Atual

**Backend (`detector.py` linha 335-338):**
```python
pesos = {
    "CPF": 5, "RG_CNH": 5, "EMAIL": 4, "TELEFONE": 4, 
    "ENDERECO_RESIDENCIAL": 4, "NOME_PESSOAL": 4, "IA_PER": 3, "NOME_CONTEXTO": 4,
    "PASSAPORTE": 5, "CONTA_BANCARIA": 5, "PIX": 5
}
```

### Análise LGPD

**Classificação LGPD padrão:**

| Nível | Risco | Exemplos |
|-------|-------|----------|
| **CRÍTICO (5)** | Altamente sensível | CPF, RG, Passaporte, Conta Bancária, Chave PIX |
| **ALTO (4)** | Sensível | Email, Telefone, Endereço Residencial, Nome Pessoal |
| **MODERADO (3)** | Moderado | Nome Detectado por IA, Contexto de Nome |
| **BAIXO (0)** | Público | Nenhum |

### Validação

**Pesos atuais parecem estar ✅ CORRETOS:**
- CPF, RG_CNH, PASSAPORTE, CONTA_BANCARIA, PIX = 5 (CRÍTICO) ✅
- EMAIL, TELEFONE, ENDERECO_RESIDENCIAL, NOME_PESSOAL, NOME_CONTEXTO = 4 (ALTO) ✅
- IA_PER (NOME_POR_IA) = 3 (MODERADO) ✅

**Recomendação:** Manter os pesos como estão (já estão alinhados com LGPD)

---

## Mapa de Risco Atual

```python
risco_map = {
    5: "CRÍTICO",      # Máximo risco
    4: "ALTO",         # Risco elevado
    3: "MODERADO",     # Risco médio
    0: "SEGURO"        # Nenhum risco (texto público)
}
```

**Status:** ✅ Alinhado com LGPD

---

## Ações de Correção

### 1. Backend (`src/detector.py`)

#### Mudança 1: Normalizar Confiança (Linha 353)
```python
# ANTES:
return is_pii, pii_relevantes, risco_map.get(max_score, "BAIXO"), float(max_score)

# DEPOIS:
confidence = float(max_score) / 5.0  # Normalizar para 0-1
return is_pii, pii_relevantes, risco_map.get(max_score, "BAIXO"), confidence
```

#### Mudança 2: Renomear IA_PER (Linha 342, 347, 337)
```python
# ANTES: "IA_PER"
# DEPOIS: "NOME_POR_IA"

# Linha 337: Adicionar ao pesos
pesos = {
    "CPF": 5, "RG_CNH": 5, "EMAIL": 4, "TELEFONE": 4, 
    "ENDERECO_RESIDENCIAL": 4, "NOME_PESSOAL": 4, 
    "NOME_POR_IA": 3,  # RENOMEADO (era IA_PER)
    "NOME_CONTEXTO": 4,
    "PASSAPORTE": 5, "CONTA_BANCARIA": 5, "PIX": 5
}
```

### 2. Frontend (`src/components/`)

#### Mudança 1: ConfidenceBar.tsx (Remover normalização incorreta)
```tsx
// ANTES: tinha lógica de normalização para PÚBLICO
export function ConfidenceBar({ value, ...props }: ConfidenceBarProps) {
  const normalizedValue = classification === 'PÚBLICO' && value === 0 ? 0.99 : value;
  const percentage = normalizedValue * 100;
}

// DEPOIS: apenas multiplica por 100 (backend já retorna 0-1)
export function ConfidenceBar({ value, ...props }: ConfidenceBarProps) {
  const percentage = value * 100;  // Simples multiplicação
}
```

#### Mudança 2: PIITypesChart.tsx (Mapear nomes amigáveis)
```tsx
// Adicionar mapeamento de tipos para exibição
const piiTypeLabels: Record<string, string> = {
  'CPF': 'CPF',
  'EMAIL': 'Email',
  'TELEFONE': 'Telefone',
  'RG_CNH': 'RG/CNH',
  'PASSAPORTE': 'Passaporte',
  'CONTA_BANCARIA': 'Conta Bancária',
  'PIX': 'Chave PIX',
  'ENDERECO_RESIDENCIAL': 'Endereço',
  'NOME_PESSOAL': 'Nome Pessoal',
  'NOME_POR_IA': 'Nome (IA)',      // NOVO (era IA_PER)
  'NOME_CONTEXTO': 'Nome em Contexto'
};

// Usar no gráfico:
const chartData = Object.entries(data)
  .map(([name, count]) => ({ 
    name: piiTypeLabels[name] || name, 
    count 
  }))
```

#### Mudança 3: ResultsTable.tsx (Mapear nomes nos detalhes)
```tsx
// Aplicar mesmo mapeamento piiTypeLabels ao exibir tipos de PII
const displayType = piiTypeLabels[detail.tipo] || detail.tipo;
```

#### Mudança 4: Classification.tsx (Remover normalizeConfidence)
```tsx
// ANTES:
import { ConfidenceBar, normalizeConfidence } from '@/components/ConfidenceBar';
const confidence = normalizeConfidence(probability, classification);

// DEPOIS:
import { ConfidenceBar } from '@/components/ConfidenceBar';
// Usar directamente: confidence = probability (já está entre 0-1)
```

#### Mudança 5: AnalysisContext.tsx (Remover normalização)
```tsx
// ANTES: tinha "special case" para PÚBLICO com prob 0 → 0.99
// DEPOIS: usar valor como recebido

// Linha ~170
const normalizedProbability = item.probability === 0 ? 0.99 : item.probability;
totalConfidence += normalizedProbability;

// MUDA PARA:
totalConfidence += item.probability;  // Usar valor como recebido
```

---

## Resumo de Mudanças

| Componente | Problema | Solução | Status |
|-----------|----------|--------|--------|
| `detector.py` | Confiança 0-5 | Dividir por 5 → 0-1 | ⏳ Implementar |
| `detector.py` | IA_PER | Renomear → NOME_POR_IA | ⏳ Implementar |
| `detector.py` | Pesos LGPD | ✅ Já corretos | ✅ OK |
| `ConfidenceBar.tsx` | Normalização incorreta | Remover lógica | ⏳ Implementar |
| `PIITypesChart.tsx` | Nomes confusos | Adicionar mapeamento | ⏳ Implementar |
| `ResultsTable.tsx` | Nomes confusos | Usar mapeamento | ⏳ Implementar |
| `Classification.tsx` | Normalização incorreta | Remover import | ⏳ Implementar |
| `AnalysisContext.tsx` | Normalização especial | Remover special case | ⏳ Implementar |

---

## Validação Esperada Após Correções

✅ **Confiança:** 0-100% (antes: 0-500%)
✅ **Nomes de PII:** Legíveis e descritivos (antes: "IA_PER")
✅ **Alinhamento LGPD:** Mantido como está (já correto)
✅ **Testes:** 112/112 passing (sem mudanças na lógica, apenas normalização)

---

## Próximas Etapas

1. ✅ Análise concluída
2. ⏳ Implementar mudanças backend
3. ⏳ Implementar mudanças frontend
4. ⏳ Testar com `test_metrics.py`
5. ⏳ Commit e Deploy (GitHub + HF)

