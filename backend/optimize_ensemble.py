"""
Script de otimização de pesos do ensemble (BERT, spaCy, regex) para maximizar F1-score no benchmark LGPD.
"""
import itertools
import json
import os
from backend.tests.test_diagnostico_motor_dataset_lgpd import DATASET_LGPD
from src.detector import PIIDetector


def run_benchmark_with_weights(detector, weights):
    # Altera os pesos do ensemble dinamicamente
    detector.ensemble_weights = weights
    tp = fp = fn = tn = 0
    for texto, contem_pii, _, _ in DATASET_LGPD:
        resultado = detector.detect_extended(texto)
        pred = resultado['classificacao'] != 'PÚBLICO'
        if pred and contem_pii:
            tp += 1
        elif pred and not contem_pii:
            fp += 1
        elif not pred and contem_pii:
            fn += 1
        else:
            tn += 1
    precisao = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precisao * recall / (precisao + recall) if (precisao + recall) > 0 else 0
    return f1, precisao, recall, tp, fp, fn, tn


def grid_search():
    best_f1 = 0
    best_weights = None
    results = []
    detector = PIIDetector()  # Instancia uma vez só!
    for bert_w, spacy_w, regex_w in itertools.product([0.7, 0.8, 0.9, 1.0, 1.1], repeat=3):
        weights = {'bert': bert_w, 'spacy': spacy_w, 'regex': regex_w}
        f1, prec, rec, tp, fp, fn, tn = run_benchmark_with_weights(detector, weights)
        results.append({'weights': weights, 'f1': f1, 'precisao': prec, 'recall': rec, 'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn})
        if f1 > best_f1:
            best_f1 = f1
            best_weights = weights
        print(f"Testando pesos: {weights} => F1: {f1:.4f} | Precisão: {prec:.4f} | Recall: {rec:.4f}")
    print(f"\nMelhores pesos encontrados: {best_weights} | F1-score: {best_f1:.4f}")
    with open('data/output/ensemble_gridsearch_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    grid_search()