# Contribution Guide

## Tidiness

* Whenever a step is changed or a new step is added, the [step description](./STEPS.md) should be updated.
* Wherever possible, type hints should be used
* 3 and more def parameters should be separated with newlines like this:
  ```python
  def my_func(
      param1: str,
      param2: int,
      param3: bool
  ) -> None:
  ```
* KISS

## Git

Always use a feature branch

```shell
git checkout -b [IssueNo]_my-new-feature
```

Always rebase before pushing:

```shell
git fetch --prune origin
git rebase origin/dev
```

Always commit with a [good commit message](https://cbea.ms/git-commit/), which starts with the Issue number.
Include a sign-off statement, which can be done like so:

```shell
git commit -s
```

Push into a new branch and open a PR.

Example:

```shell
git push origin [IssueNo]_my-new-feature
```

## Layout

This project uses a [flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/).
