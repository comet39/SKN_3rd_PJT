import os

base_dir = "ready-to-go-backend"

structure = {
    "": ["app.py", "config.py", "requirements.txt", "Dockerfile", "README.md"],
    "modules/document_processor": [
        "__init__.py", "crawler.py", "parser.py", "preprocessor.py", "chunker.py"
    ],
    "modules/vector_db": [
        "__init__.py", "db.py", "metadata_db.py"
    ],
    "modules/rag": [
        "__init__.py", "query_analyzer.py", "context_builder.py", "search.py"
    ],
    "modules/llm": [
        "__init__.py", "interface.py", "prompts.py", "postprocessor.py"
    ],
    "api": [
        "__init__.py", "chat.py", "documents.py", "metadata.py", "session.py", "admin.py"
    ],
    "models": [
        "__init__.py", "chat.py", "document.py", "metadata.py"
    ],
    "utils": [
        "__init__.py", "logger.py", "helpers.py"
    ],
    "tests": [
        "__init__.py", "test_document_processor.py", "test_vector_db.py", "test_rag.py", "test_api.py"
    ]
}

for subdir, files in structure.items():
    dir_path = os.path.join(base_dir, subdir)
    os.makedirs(dir_path, exist_ok=True)
    for file in files:
        file_path = os.path.join(dir_path, file)
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                # 파일 내용 주석으로 채워넣기
                if file.endswith(".py"):
                    f.write(f"# {file} - Auto-generated\n")
                elif file == "README.md":
                    f.write("# Ready To Go Backend\n\nDocumentation goes here.")
                elif file == "requirements.txt":
                    f.write("# Add your dependencies here\n")
                elif file == "Dockerfile":
                    f.write("# Dockerfile for containerizing the FastAPI app\n")
                elif file == "config.py":
                    f.write("# Configuration settings for the application\n")
                elif file == "app.py":
                    f.write("# Main FastAPI app entry point\n\nfrom fastapi import FastAPI\n\napp = FastAPI()\n")
