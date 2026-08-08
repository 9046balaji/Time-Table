import os
import glob
import json
import ast

def inspect_python_routes():
    route_files = glob.glob('backend/app/api/v1/*.py')
    routes = {}
    for rf in route_files:
        name = os.path.basename(rf)
        with open(rf, 'r', encoding='utf-8') as f:
            code = f.read()
        routes[name] = {
            'lines': len(code.splitlines()),
            'endpoints': [line.strip() for line in code.splitlines() if line.strip().startswith(('@router.get', '@router.post', '@router.put', '@router.delete'))]
        }
    return routes

def inspect_frontend_pages():
    page_files = glob.glob('frontend/src/app/**/page.tsx', recursive=True)
    pages = {}
    for pf in page_files:
        rel_path = os.path.relpath(pf, 'frontend/src/app')
        with open(pf, 'r', encoding='utf-8') as f:
            code = f.read()
        pages[rel_path] = {
            'lines': len(code.splitlines()),
            'has_use_effect': 'useEffect' in code,
            'has_api_call': 'fetch(' in code or 'api.' in code or 'axios' in code
        }
    return pages

def inspect_db_models():
    model_files = glob.glob('backend/app/models/*.py')
    models = {}
    for mf in model_files:
        name = os.path.basename(mf)
        with open(mf, 'r', encoding='utf-8') as f:
            code = f.read()
        classes = [line.strip() for line in code.splitlines() if line.strip().startswith('class ')]
        models[name] = {
            'lines': len(code.splitlines()),
            'classes': classes
        }
    return models

def run():
    routes = inspect_python_routes()
    pages = inspect_frontend_pages()
    models = inspect_db_models()

    print("=== BACKEND API ROUTES ===")
    print(json.dumps(routes, indent=2))

    print("\n=== FRONTEND PAGES ===")
    print(json.dumps(pages, indent=2))

    print("\n=== DB MODELS ===")
    print(json.dumps(models, indent=2))

if __name__ == '__main__':
    run()
