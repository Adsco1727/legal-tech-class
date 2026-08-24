from pathlib import Path
import json

root = Path.cwd()
nb = root / 'ledger_production_readiness.ipynb'
print(f'PWD={root}')
print(f'RUNNING_NOTEBOOK: {nb}')

with nb.open('r', encoding='utf-8') as f:
    data = json.load(f)

ns = {'__name__': '__main__'}
failures = []
exec_count = 0

for cell in data.get('cells', []):
    if cell.get('cell_type') != 'code':
        continue
    src = ''.join(cell.get('source', []))
    exec_count += 1
    try:
        exec(compile(src, str(nb), 'exec'), ns, ns)
        print(f'CELL_{exec_count}: PASS')
    except Exception as e:
        print(f'CELL_{exec_count}: FAIL: {type(e).__name__}: {e}')
        failures.append((exec_count, type(e).__name__, str(e)))
        break

print(f'TOTAL_CODE_CELLS: {exec_count}')
print('RESULT: PASS' if not failures else 'RESULT: FAIL')
if failures:
    raise SystemExit(1)
