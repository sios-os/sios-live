"""Run constitutional training export and embedding training."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 1. Export constitutional training data
print("=== Constitutional Training Data Export ===")
from anubis.constitutional_training import ConstitutionalTrainer
trainer = ConstitutionalTrainer(Path("."))
result = trainer.export_training_data()
print(f"Exported {result['pair_count']} training pairs to {result['path']}")
print(f"Categories: {result['categories']}")
print(f"Laws covered: {result['laws']}")
print()

# 2. Train custom embeddings
print("=== Custom Embedding Training ===")
try:
    from anubis.custom_embeddings import EmbeddingTrainer
    from anubis.knowledge import KnowledgeBase
    from anubis.registry import Registry

    registry = Registry(Path("registry"))
    kb = KnowledgeBase(Path("knowledge"), registry)
    docs = kb.library_documents()
    print(f"Found {len(docs)} knowledge documents")

    if docs:
        documents = [d.content for d in docs]
        trainer = EmbeddingTrainer(dimensions=384)
        model = trainer.train(documents, model_name="anubis-embed-v1")
        save_result = model.save(Path("memory/custom_embed_model.json"))
        print(f"Trained embedding model: vocab={len(model.vocabulary)}, dims={model.dimensions}")
        print(f"Saved: {save_result}")

        # Evaluate
        eval_result = trainer.evaluate_retrieval(model, documents, documents[:20])
        print(f"Evaluation: hit_rate={eval_result.get('hit_rate', 0):.2%}")
    else:
        print("No knowledge documents found — skipping embedding training")
except Exception as e:
    print(f"Embedding training error: {e}")

print()
print("=== Done ===")
