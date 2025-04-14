# RAG Backend Tests

This directory contains unit tests for the RAG backend application. The tests are written using pytest and the FastAPI TestClient.

## Test Categories

1. **Basic API tests** (`test_api.py`): Tests for basic API functionality including document uploads, listing, deletion, and querying.

2. **Embedding Format Tests** (`test_embedding_formats.py`): Tests specifically focused on the JSON string vs Python list embedding format issue.

3. **Embedding Solution Tests** (`test_embedding_solution.py`): Tests to verify the solution for the embedding format issue works correctly.

## Running the Tests

To run all tests:

```bash
cd document-rag-app/rag-backend
pytest -xvs tests/
```

To run a specific test file:

```bash
pytest -xvs tests/test_api.py
```

To run a specific test function:

```bash
pytest -xvs tests/test_api.py::test_list_documents
```

## Test Environment

The tests use an in-memory SQLite database instead of PostgreSQL to make them faster and eliminate dependencies. This is configured in `conftest.py`.

## Mocking

External services like OpenAI API are mocked to ensure tests don't make actual API calls or depend on external services. 