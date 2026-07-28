# Evidence Index

Timestamp (UTC): 2026-07-21T15:15:47Z
Branch: main
Commit: 566ef62c

## Gate Mapping

| Gate | Artifact ID | Artifact | Path | SHA-256 |
|---|---|---|---|---|
| Gate 0/1 | E-003-A | Runtime boundary map | dpo_system/config/runtime_boundary.yaml | 2B7B32FA12D8C743784C5294745EE35DA50B570CEC420972ECB149852437AFCA |
| Gate 1 | E-004-B | Contract schemas | dpo_system/contracts/transaction_contract.yaml | 4C36A0D7112CD52415A82A043E711923E928C0D6DD3E808D687E58CAC226264B |
| Gate 1 | E-004-B | Contract schemas | dpo_system/contracts/approval_contract.yaml | 34AC93D5E24C7200CC11E793CB3B51627C2644B3E3F150A3C796788E48A2FE74 |
| Gate 1/5 | E-008-F | Secrets scan (code/config scope) | dpo_system/evidence/EXECUTED_EVIDENCE/secrets_scan_code_scope.txt | 93097974B372BCF6E39EA7B1427DDCC09CBC7DEFB778CB0A974A01A378DE3096 |
| Gate 1/5 | E-006-I | Idempotency test output | dpo_system/evidence/EXECUTED_EVIDENCE/idempotency_test_output.txt | E5B1B5F61CA82B87863F774C809150B13F5E19834D41CF9756FBAA4528BBF656 |
| Gate 1/5 | E-006-I | Idempotency test JSON results | dpo_system/evidence/EXECUTED_EVIDENCE/idempotency_test_results.json | 282872FAD9B37FEB1DF5B390B9AF00761598A60BD875F045AF83B2DAA693F792 |
| Gate 0 | E-002-J | Ownership matrix report | dpo_system/evidence/STRUCTURAL_EVIDENCE/ownership_matrix_report.md | 2E7B719057E96FDB24E19F6C8767EE6FC5F89901C5EBF28FE6F06484161C95D5 |
| Gate 2 | E-009-K | Intake reconciliation report | dpo_system/evidence/STRUCTURAL_EVIDENCE/intake_reconciliation_report.txt | BFBF94B0E2A58A4F40FA749525C75EAFDAC5A6133417A7A72B72F79DAC6811B5 |
| Gate 3 | E-010-L | KPI reconciliation report | dpo_system/evidence/STRUCTURAL_EVIDENCE/kpi_reconciliation_report.txt | AECD35845B639CC6F628914B15FCEE9344C7B749919E368A372579A8BD1DDCEC |
| Gate 5 | E-005 | Boundary tests (executed) | dpo_system/evidence/EXECUTED_EVIDENCE/boundary_test_output.txt | 53B52EEB5AC3E46A8F416710EA28A03DA1940EAF4D9D80740630F2ED2E6F8576 |
| Gate 5 | E-004 | Contract tests (executed) | dpo_system/evidence/EXECUTED_EVIDENCE/contract_test_output.txt | 4B689CAD42EA89783FA8165E227A89CFA5532CDC3422DD36EE6325502F3D1760 |
| Gate 5 | E-011-TEST | Full test suite (executed) | dpo_system/evidence/EXECUTED_EVIDENCE/pytest_dpo_system_tests.txt | DF8520811D3F3539F4E12547FBD9B5E9C037C62D09165705CB13D5DF554FA786 |
| Gate 5 | E-011-TEST | Unified run_all output | dpo_system/evidence/EXECUTED_EVIDENCE/run_all_output.txt | CBF194C9F237EED8DA06D6F049071F247581FBD1350DF247D87E6221C543EE25 |
| Gate 6 | E-012-H | Rollback simulation report | dpo_system/evidence/EXECUTED_EVIDENCE/rollback_simulation_report.txt | 1DD8A8D79E59D9D08606CFB1C673E50523633E69E49991FE0E85D1C513E9D1CD |
| Gate 5 support | E-013-G | Evidence checksum bundle | dpo_system/evidence/CHECKSUM_MANIFEST.sha256 | self-excluded manifest |

## Notes

- Checksum manifest excludes its own hash to avoid recursive invalidation.
- Maker/Checker signatures are captured in dpo_system/EVIDENCE_MANIFEST_TASK_ACCOMPLISHMENTS.md.
- Evidence placeholders E-002, E-009, and E-010 are now populated with hashed artifacts.
- Executed run artifacts are organized under dpo_system/evidence/EXECUTED_EVIDENCE/.
- Structural/design and simulation-support artifacts are organized under dpo_system/evidence/STRUCTURAL_EVIDENCE/.

