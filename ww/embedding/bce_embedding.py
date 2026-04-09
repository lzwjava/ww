from BCEmbedding import EmbeddingModel  # type: ignore[reportMissingImports]

# list of sentences
sentences = ["sentence_0", "sentence_1"]

# init embedding model
model = EmbeddingModel(model_name_or_path="maidalun1020/bce-embedding-base_v1")

# extract embeddings
embeddings = model.encode(sentences)
