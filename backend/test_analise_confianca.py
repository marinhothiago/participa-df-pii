import json
import os
import json

# Garantir que os arquivos de saída existem antes de qualquer leitura
for arquivo in ["resultado_amostra_v2.json", "resultado_v94.json"]:
    output_dir = 'backend/data/output'
    output_file = os.path.join(output_dir, arquivo)
    if not os.path.exists(output_file):
        os.makedirs(output_dir, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([], f)

# Comparar v2 com v94
for versao, arquivo in [("v2 (antes)", "resultado_amostra_v2.json"), ("v9.4 (depois)", "resultado_v94.json")]:
    with open(f'backend/data/output/{arquivo}', 'r', encoding='utf-8') as f:
        dados = json.load(f)
    confianças = [float(d['confianca'].replace('%', '')) for d in dados]
    media = sum(confianças) / len(confianças) if confianças else 0
    confianças_sorted = sorted(confianças)
    mediana = confianças_sorted[len(confianças_sorted)//2] if confianças else 0
    acima_85 = sum(1 for c in confianças if c >= 85)
    acima_90 = sum(1 for c in confianças if c >= 90)
    abaixo_50 = sum(1 for c in confianças if c < 50)
    publicos = sum(1 for d in dados if 'PÚBLICO' in d['classificacao'] and 'NÃO' not in d['classificacao'])
    nao_publicos = sum(1 for d in dados if 'NÃO PÚBLICO' in d['classificacao'])
    print(f'\n{"="*50}')
    print(f'📊 {versao}')
    print(f'{"="*50}')
    print(f'Total de registros: {len(dados)}')
    print(f'Públicos: {publicos} | Não Públicos: {nao_publicos}')
    print(f'Media confianca: {media:.1f}%')
    print(f'Mediana: {mediana:.1f}%')
    print(f'>= 90%: {acima_90} ({acima_90/len(dados)*100:.1f}%)' if confianças else '>= 90%: 0 (0.0%)')
    print(f'>= 85%: {acima_85} ({acima_85/len(dados)*100:.1f}%)' if confianças else '>= 85%: 0 (0.0%)')
    print(f'< 50%: {abaixo_50} ({abaixo_50/len(dados)*100:.1f}%)' if confianças else '< 50%: 0 (0.0%)')

# Mostrar registros com baixa confianca na v9.4
print(f'\n{"="*50}')
print(f'Registros com confianca < 50% na v9.4:')
print(f'{"="*50}')
with open('backend/data/output/resultado_v94.json', 'r', encoding='utf-8') as f:
    dados = json.load(f)
import json

# Garantir que os arquivos de saída existem antes do teste
for versao, arquivo in [("v2 (antes)", "resultado_amostra_v2.json"), ("v9.4 (depois)", "resultado_v94.json")]:
    output_dir = 'backend/data/output'
    output_file = os.path.join(output_dir, arquivo)
    if not os.path.exists(output_file):
        os.makedirs(output_dir, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
    with open(output_file, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    confianças = [float(d['confianca'].replace('%', '')) for d in dados]
    media = sum(confianças) / len(confianças) if confianças else 0
    confianças_sorted = sorted(confianças)
    mediana = confianças_sorted[len(confianças_sorted)//2] if confianças else 0
    acima_85 = sum(1 for c in confianças if c >= 85)
    acima_90 = sum(1 for c in confianças if c >= 90)
    abaixo_50 = sum(1 for c in confianças if c < 50)
    publicos = sum(1 for d in dados if 'PÚBLICO' in d['classificacao'] and 'NÃO' not in d['classificacao'])
    nao_publicos = sum(1 for d in dados if 'NÃO PÚBLICO' in d['classificacao'])
    print(f'\n{"="*50}')
    print(f'📊 {versao}')
    print(f'{"="*50}')
    print(f'Total de registros: {len(dados)}')
    print(f'Públicos: {publicos} | Não Públicos: {nao_publicos}')
    print(f'Media confianca: {media:.1f}%')
    print(f'Mediana: {mediana:.1f}%')
    print(f'>= 90%: {acima_90} ({acima_90/len(dados)*100:.1f}%)' if confianças else '>= 90%: 0 (0.0%)')
    print(f'>= 85%: {acima_85} ({acima_85/len(dados)*100:.1f}%)' if confianças else '>= 85%: 0 (0.0%)')
    print(f'< 50%: {abaixo_50} ({abaixo_50/len(dados)*100:.1f}%)' if confianças else '< 50%: 0 (0.0%)')

# Mostrar registros com baixa confianca na v9.4
print(f'\n{"="*50}')
print(f'Registros com confianca < 50% na v9.4:')
print(f'{"="*50}')
output_file = os.path.join('backend/data/output', 'resultado_v94.json')
with open(output_file, 'r', encoding='utf-8') as f:
    dados = json.load(f)
for d in dados:
    conf = float(d['confianca'].replace('%', ''))
    if conf < 50:
        print(f'ID {d["id"]}: {conf:.1f}% - {d["identificadores"][:80]}...')