# Root conftest.py intentionally does not set DJANGO_DEBUG.
#
# pytest-django's pytest_load_initial_conftests hookimpl forces Django
# settings access (django.conf.settings) inside that same hook call, and
# pytest core registers its own pytest_load_initial_conftests (the one that
# actually loads this file) with trylast=True. Pluggy runs trylast impls
# last, so pytest-django always imports config.settings before this file's
# body — or any hookimpl defined in it — can run. No hook placed here, at
# any priority, can set DJANGO_DEBUG early enough.
#
# DJANGO_DEBUG=1 must therefore be supplied by the process that invokes
# pytest. Use `make test` (see the Makefile at the repo root), which
# exports it, or export it yourself in the shell/CI before running pytest.
