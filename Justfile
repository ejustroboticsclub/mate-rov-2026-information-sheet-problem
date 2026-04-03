# lists recipes
default:
  just --list

# ruff format
fmt:
  uv run ruff format

# ruff check
lint:
  uv run ruff check

# ty check
type:
  uv run ty check

# pytest
test:
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -p pytest_cov # disable plugins due to ros2 in pythonpath

# formats, lints, type checks and runs tests
test-all:
  just fmt
  just lint
  just type
  just test

[doc('dry run of git clean. use clean force to delete')]
clean mode="dry":
    git clean -fxfd -e '*venv' -e '.env' {{ if mode == "force" { "" } else { "--dry-run" } }}

