import os
import tempfile
import openpyxl
import dpo_system.src.ledger_io as mod

print(mod.SHEET_HEADERS['GOVERNANCE_QUEUE'])
p = os.path.join(tempfile.gettempdir(), 'xledgertest.xlsx')
mod.create_ledger_workbook(p)
wb = openpyxl.load_workbook(p)
print([c.value for c in wb['GOVERNANCE_QUEUE'][1]])
