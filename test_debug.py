#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

# Casos problemáticos
casos = [
    ("Encaminhar para o Dr. Lucas Silva responsável pelo departamento.", "Dr. Lucas Silva"),
    ("O responsável Dr. Augusto da Administração Regional", "Dr. Augusto da Admin")
]

cargos_autoridade = {"DRA", "DR", "SR", "SRA", "PROF", "DOUTOR", "DOUTORA"}

for texto_original, nome in casos:
    print(f"\n{'='*60}")
    print(f"Texto: {texto_original}")
    print(f"Nome encontrado: {nome}")
    
    # Simular onde o nome inicia (aproximado)
    start_index = texto_original.find(nome)
    print(f"Start index: {start_index}")
    
    pre_text = texto_original[max(0, start_index-100):start_index].upper()
    pos_text = texto_original[start_index:min(len(texto_original), start_index+100)].upper()
    
    print(f"\nPre-text (100 chars before): '{pre_text}'")
    print(f"Pos-text (100 chars after): '{pos_text}'")
    
    # Verifica cargo
    for cargo in cargos_autoridade:
        if re.search(rf"\b{cargo}\.?\s*$", pre_text):
            print(f"\n✓ Cargo '{cargo}' encontrado no final de pre_text")
            
            # Verifica instituição/função no pos_text
            instituicoes = ["SECRETARIA", "ADMINISTRACAO", "DEPARTAMENTO", "DIRETORIA", "GDF", "SEEDF", "RESPONSAVEL", "DA ADMINISTRACAO"]
            found = False
            for inst in instituicoes:
                if inst in pos_text:
                    print(f"✓ Instituição/função '{inst}' encontrada no pos_text")
                    found = True
                    break
            
            if found:
                print(f"  ==> DEVE SER IGNORADO (imune)")
            else:
                print(f"✗ Nenhuma instituição/função encontrada")
                print(f"  Procurando por: {instituicoes}")


