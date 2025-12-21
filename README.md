# __SKLS AI CORE__
_by Anton Kozlov_

## Overview

SKLS AI CORE is a comprehensive knowledge graph and language processing system that provides:
- Text embedding capabilities with ChromaDB storage
- LLM-based content generation with Pydantic model support
- Neo4j graph database management for knowledge graphs
- Flexible logging configuration

## Installation

### From PyPI (Coming soon)
```bash
pip install skls-core
```

### From Source
```bash
git clone <repository-url>
cd skls_core
pip install .
```

### Development Installation
```bash
git clone <repository-url>
cd skls_core
pip install -e .[dev]
```

## Dependencies

The package includes the following components:
- **skls_embeddings**: For creating and managing text embeddings using various backend services and storing them in vector databases
- **skls_generator**: For generating Pydantic models using LLMs with self-correction capabilities
- **skls_neo4j**: For managing Neo4j graph databases and creating knowledge graphs

## Usage Example

### Using Embeddings
```python
from skls_embeddings import EmbeddingClient, ChromaClient

# Create embedding client
embed_client = EmbeddingClient(base="http://localhost:8080")

# Create ChromaDB client
chroma_client = ChromaClient(embed_client)

# Store a text chunk
chunk_id = chroma_client.store_chunk("Sample text for embedding")
```

### Using Generator
```python
from skls_generator.generator import Generator
from skls_generator.gen_backends.google_gen import GoogleGenAI

# Create a generator with Google GenAI backend
gen_ai = GoogleGenAI()
generator = Generator(client=gen_ai)

# Define your Pydantic model
from pydantic import BaseModel
class Person(BaseModel):
    name: str
    age: int

# Generate an instance
person = generator.generate_one_shot(Person, prompt="Generate a person with a random name and age")
```

### Using Neo4j
```python
from skls_neo4j.neo4j_manager import Neo4jGraphManager

# Connect to Neo4j
manager = Neo4jGraphManager(uri="bolt://localhost:7687", auth=("user", "password"))
```

## Configuration

The package provides flexible logging configuration:
```python
from skls_embeddings import LoggerConfig
import logging

# Set up custom logging
LoggerConfig.setup_logging(level=logging.DEBUG)

# Or use a custom logger
custom_logger = logging.getLogger("my_app")
LoggerConfig.set_custom_logger(custom_logger)
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Run formatter and linter (`black .` and `flake8 .`)
6. Commit your changes (`git commit -m 'Add some amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
