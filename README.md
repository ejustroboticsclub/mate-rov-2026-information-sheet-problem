# mate-rov-2026-information-sheet-problem

library for providing solution to second part of task 2.2 in MATE-ROV-2026. the task includes getting an information sheet and providing threat levels to each oil platform and each subsea asset. After completing the solution in the repo we should tag the latest commit to be used as a mark when we add this project as a dependency to the ROV workspace.

## General Resources

In order to find the resources for testing (examples) and format of this problem please go to the `2026 Product Demonstration Resources` section in the following link [https://materovcompetition.org/2026](https://materovcompetition.org/2026)

## Required tools for development

### 1. uv
uv is the current best python project manager and we need it to sync dependencies across different projects. you can find how to install it from its [docs](https://docs.astral.sh/uv/). Learning how to use uv will make deployment much easier especially when we don't have time for solving dependency issues.

### 2. just (optional)
you will notice that I added the important commands in the Justfile. you can copy paste them in the terminal to run them normally or you can install just for doing something like:
```
just test
```
for testing with pytest.\
To install it you can see its official [website](https://just.systems/). or install it with `uv` using `uv tool install rust-just`.

## Getting Started

1. Clone the repository and cd into it
```bash
git clone https://github.com/ejustroboticsclub/mate-rov-2026-information-sheet-problem.git information-sheet-problem
cd information-sheet-problem
```
1. run
```bash
uv sync
```

the above commands are enough to install all dependencies required for the project inside `.venv` file in root directory. it will also build the project as library.

## Usage
This package is intended to be added as a project dependency using uv:
```bash
uv add git+https://github.com/ejustroboticsclub/mate-rov-2026-information-sheet-problem
```
and then used inside the main workspace by importing it:
```python
from information_sheet_problem import analyze_iceberg

# def analyze_iceberg(
#     lat_degrees: int,
#     lat_minutes: int,
#     lat_seconds: int,
#     lat_hemisphere: str,
#     lon_degrees: int,
#     lon_minutes: int,
#     lon_seconds: int,
#     lon_hemisphere: str,
#     heading_degrees: float,
#     keel_depth: float,
#     platforms: list[Platform] = DEFAULT_PLATFORMS,
# ) -> AnalysisResult:

# example
analyze_iceberg(47, 39, 0, "N", 48, 37, 0, "W", 158, 99)
```
note that the API is still not determined and the above sample is just an example of what could be done. However this library is NOT responsible for handling taking the input from the user. This will probably be the responsibliy of the gui team since the input has to be manually taken.


## TODOs
- make sure that the input to your function is friendly (idk how to represent a geopoint inside a float tbh there is probably a better way)
- we probably need to write a function that takes seperate (hours,minutes,seconds) and convert them to a geopoint
