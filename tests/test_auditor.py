import pytest
from pathlib import Path
from app.core.auditor import AtlasAuditor

def test_atlas_audit_integrity():
    """
    Runs the full AtlasAuditor suite to ensure JSON and SQLite 
    integrity, referential consistency, and FTS sync.
    """
    root = Path(__file__).parent.parent
    auditor = AtlasAuditor(
        data_path=root / 'data' / 'languages.json',
        db_path=root / 'language_atlas.sqlite'
    )
    
    success, errors, warnings = auditor.run_all()
    
    # We treat errors as test failures
    if not success:
        error_msg = "\n".join(errors)
        pytest.fail(f"Atlas Audit failed with errors:\n{error_msg}")

def test_semantic_orphans_report():
    """
    Check for semantic orphans and report them as warnings.
    """
    root = Path(__file__).parent.parent
    auditor = AtlasAuditor()
    auditor.run_all()
    
    if auditor.warnings:
        print(f"\n[AUDIT WARNINGS] {len(auditor.warnings)} issues found:")
        for w in auditor.warnings:
            print(f"  - {w}")
    
    # We don't fail the test for warnings, but we ensure the check runs.
    assert True
