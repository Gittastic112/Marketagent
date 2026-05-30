import os
import re

ROUTERS_DIR = "/Users/mananmaheshwari/Documents/Codex/Market Intelligence App/market-intelligence-md-files copy/backend/app/api/routers"

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # Add ApiResponse import if not present
    if 'ApiResponse' not in content:
        # Find the last import from app.api.schemas
        schema_import = re.search(r'from app\.api\.schemas import (.*?)\n', content)
        if schema_import:
            content = content.replace(schema_import.group(0), f'from app.api.schemas import ApiResponse, {schema_import.group(1)}\n')
        else:
            # just put it after the last import
            imports_end = [m.end() for m in re.finditer(r'import .*\n|from .* import .*\n', content)]
            if imports_end:
                idx = imports_end[-1]
                content = content[:idx] + "from app.api.schemas import ApiResponse\n" + content[idx:]

    # 1. Update response_model in @router decorators
    # Match @router.something(..., response_model=Foo, ...)
    # But only if it's not already ApiResponse
    def repl_response_model(m):
        prefix = m.group(1)
        resp_model = m.group(2)
        suffix = m.group(3)
        if resp_model.startswith('ApiResponse'):
            return m.group(0)
        return f"{prefix}response_model=ApiResponse[{resp_model}]{suffix}"
    
    content = re.sub(r'(@router\.[a-z]+\([^)]*?)response_model=([^,)]+)([^)]*\))', repl_response_model, content)

    # 2. Update return type hints
    # def func_name(...) -> Foo:
    def repl_return_type(m):
        func_def = m.group(1)
        ret_type = m.group(2)
        if ret_type.startswith('ApiResponse'):
            return m.group(0)
        # Avoid double wrapping if some return types are already wrapped
        return f"{func_def}-> ApiResponse[{ret_type}]:"
    
    content = re.sub(r'(def [a-zA-Z_0-9]+\([^)]*\)\s*)->\s*([^:]+):', repl_return_type, content)

    # 3. Update return statements
    # Match return <expr>
    # Note: this is tricky with multi-line returns.
    # We will use a regex that looks for `return ` not followed by `ApiResponse`
    def repl_return_stmt(m):
        indent = m.group(1)
        expr = m.group(2)
        if expr.startswith('ApiResponse'):
            return m.group(0)
        return f"{indent}return ApiResponse(data={expr})"
    
    # Simple regex for single line returns
    content = re.sub(r'^([ \t]+)return (?!ApiResponse)(.+)$', repl_return_stmt, content, flags=re.MULTILINE)

    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated {os.path.basename(filepath)}")

for filename in os.listdir(ROUTERS_DIR):
    if filename.endswith(".py") and filename != "__init__.py":
        process_file(os.path.join(ROUTERS_DIR, filename))
