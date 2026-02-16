def chunk_text(text: str, chunk_size: int = 200, overlap: int = 30):
    """
    Split text into overlapping chunks.
    """

    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    return chunks
