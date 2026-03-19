default:
  just --list

test:
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest # disable plugins due to ros2 in pythonpath

clean:
  git clean -fxfd --dry-run
