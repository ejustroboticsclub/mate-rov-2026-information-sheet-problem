# mate-rov-2026-information-sheet-problem

library for providing solution to second part of task 2.2 in MATE-ROV-2026. the task includes getting an information sheet and providing threat levels to each oil platform and each subsea asset. After completing the solution in the repo we should tag the latest commit to be used as a mark when we add this project as a dependency to the ROV workspace.

## Required tools for development

### 1. uv
uv is the current best python project manager and we need it to sync dependencies across different projects. you can find how to install it from its [docs](https://docs.astral.sh/uv/). Learning how to use uv will make deployment much easier especially when we don't have time for solving dependency issues.

### 2. just (optional)
you will notice that I added the important commands in the Justfile. you can copy paste them in the terminal to run them normally or you can install just for doing something like:
```
just test
```
for testing with pytest. To install it you can see its official [website](https://just.systems/).

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

