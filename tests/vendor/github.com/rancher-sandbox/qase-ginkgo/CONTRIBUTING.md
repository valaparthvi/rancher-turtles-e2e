# Contributing to qase-ginkgo

`qase-ginkgo` accepts contributions via GitHub issues and pull requests.
This document outlines the process to get your pull request accepted.

`qase-ginkgo` does accept external contributions in general,
however the team's time is limited.

`qase-ginkgo` does not have release cycle defined, so it might take a long
time for external contributions to be commented on, let alone reviewed and
merged.

## Start With An Issue

Prior to creating a pull request it is a good idea to [create an issue].
This is especially true if the change request is something large.
The bug, feature request, or other type of issue can be discussed prior to
creating the pull request. This can reduce rework.

[Create an issue]: https://github.com/rancher-sandbox/qase-ginkgo/issues/new

## Pull Requests

Pull requests for a code change should reference the issue they are related to.

This will enable issues to serve as a central point of reference for a change.
For example, if a pull request fixes or completes an issue the commit or
pull request should include:

```md
Refers #123
```

In this case 123 is the corresponding issue number.

We leave issues open, until the quality assurance team reviewed them.

## Semantic Versioning

Elemental follows [semantic versioning](https://semver.org/).

This does not cover other tools included in `qase-ginkgo`.

## Coding Style

`qase-ginkgo` expects its Go code to be formatted with `goimports`.

Elemental further follows the style guidelines at

  - [Effective Go](https://go.dev/doc/effective_go) and
  - [Go Wiki Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)
  - [Go Style At Google](https://google.github.io/styleguide/go/guide)
