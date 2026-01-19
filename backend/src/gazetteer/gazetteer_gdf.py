import os
import json

def carregar_gazetteer_gdf():
    """
    Lê o arquivo gazetteer_gdf.json e retorna um set com todos os nomes, siglas e aliases institucional do GDF.
    """
    # Caminho absoluto para garantir compatibilidade
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'gazetteer_gdf.json')
    if not os.path.exists(json_path):
        # Fallback: tenta na raiz do backend/src
        json_path = os.path.join(base_dir, '..', 'gazetteer', 'gazetteer_gdf.json')
    if not os.path.exists(json_path):
        return set()
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    termos = set()
    for org in data.get('orgaos', []):
        termos.add(org.get('nome', '').strip().lower())
        termos.add(org.get('sigla', '').strip().lower())
        for alias in org.get('aliases', []):
            termos.add(alias.strip().lower())
    # Adicione outros tipos se existirem (escolas, hospitais, etc)
    for tipo in ['escolas', 'hospitais', 'programas']:
        for item in data.get(tipo, []):
            termos.add(item.get('nome', '').strip().lower())
            termos.add(item.get('sigla', '').strip().lower())
            for alias in item.get('aliases', []):
                termos.add(alias.strip().lower())
    return termos