from cohortgen.__main__ import main


def test_main_prints_version(capsys):
    rc = main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "cohortgen" in out
    # Version string defined in package
    assert any(ch.isdigit() for ch in out)

