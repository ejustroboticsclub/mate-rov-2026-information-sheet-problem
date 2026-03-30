default:
  just --list

test:
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -p pytest_cov # disable plugins due to ros2 in pythonpath

clean:
  git clean -fxfd -e '*venv' -e '.env' --dry-run
