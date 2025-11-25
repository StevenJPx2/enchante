.PHONY: .poetry ## Check that poetry is installed
.poetry:
	@poetry -V || echo 'Please install the latest version of poetry: https://python-poetry.org/docs/#installation'

.PHONY: .pre-commit  ## Check that pre-commit is installed
.pre-commit:
	@pre-commit -V || echo 'Please install pre-commit: https://pre-commit.com/'

.PHONY: .install
install: .poetry .pre-commit
	poetry install

.PHONY: .release
release:
	poetry build
	poetry publish

