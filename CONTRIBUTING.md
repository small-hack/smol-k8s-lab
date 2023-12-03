# Contributing

Please be nice. The maintainers are very soft.

Otherwise, please feel free to contribute anything: Issues (bug reports and feature requests), Pull requests, and Discussions

# Submitting Pull Requests

If it's a doc fix, don't worry about testing, just explain what you're fixing and we're a-ok 👍

If it's a code fix, please:
- don't forget to bump the version in [`pyproject.toml`](https://github.com/small-hack/smol-k8s-lab/blob/main/pyproject.toml#L3)
- test your code before submitting it and explain how you tested it in the pull request

## Development

We're open to unit, integration, and ci testing btw! We just don't have any because we weren't stable enough to justify them yet. 🤦

### Prereqs

- [poetry](https://python-poetry.org/docs/#installation) to manage our dependencies and virtual environments for python.
- [pre-commit](https://pre-commit.com/index.html#install) to manage pre-commit hooks, mostly related to poetry

```bash
git clone git@github.com:small-hack/smol-k8s-lab.git
cd smol-k8s-lab
pre-commit install
```

### virtual environment

Install the project locally after cloning it.

```bash
# this installs a local version of smol-k8s-lab that points to your cloned repo directly
poetry install
```

And then you can do all your development in a virtual environment by running:

```bash
# this sources the virtual env for this project
poetry shell

# this will print your version you're working on
smol-k8s-lab --version
```

When you're done playing with your environment, you can just type `exit` to leave the shell :)
