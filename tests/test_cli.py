from cohortgen.cli import main


def test_cli_list_projects(capsys):
    rc = main(["list"])  # lists projects and exits 0
    out = capsys.readouterr().out
    assert rc == 0
    # Either no projects or list header
    assert "Projects:" in out or "No Flujo projects" in out
