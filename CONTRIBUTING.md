# Contributing to SnapGuard

First off, thank you for considering contributing to SnapGuard! It's people like you that make SnapGuard such a great tool.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report for SnapGuard. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

**Before Submitting A Bug Report:**
* Check the [issues](link-to-issues) to see if the problem has already been reported. If it has and the issue is still open, add a comment to the existing issue instead of opening a new one.
* Make sure you're using the latest version of SnapGuard.
* Determine if your bug is really a bug and not an issue with your environment (e.g., btrfs or overlayfs availability on your system).

**How Do I Submit A Good Bug Report?**
Bugs are tracked as [GitHub issues](link-to-issues). Create an issue and provide the following information:

* **Use a clear and descriptive title** for the issue to identify the problem.
* **Describe the exact steps which reproduce the problem** in as many details as possible.
* **Provide specific examples to demonstrate the steps**. Include links to files or GitHub projects, or copy/pasteable snippets, which you use in those examples.
* **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
* **Explain which behavior you expected to see instead and why.**
* **Include screenshots and animated GIFs** which show you following the described steps and clearly demonstrate the problem.
* **If the problem is related to performance or memory**, include a CPU profile capture and a memory heap snapshot with your report.
* **If the problem is related to file system operations**, include relevant details about your file system setup and permissions.
* **Include details about your environment**:
  * Which version of SnapGuard are you using?
  * What's the name and version of your OS?
  * Are you using BTRFS, OverlayFS, or both?
  * Can you reliably reproduce the issue? And if not, how often does it happen?

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for SnapGuard, including completely new features and minor improvements to existing functionality.

**Before Submitting An Enhancement Suggestion:**
* Check if there's already a feature that provides your suggested enhancement.
* Determine if your enhancement is related to the core SnapGuard functionality.
* Check if the enhancement has already been suggested. If it has, add a comment to the existing request instead of opening a new one.

**How Do I Submit A Good Enhancement Suggestion?**
Enhancement suggestions are tracked as [GitHub issues](link-to-issues). Create an issue and provide the following information:

* **Use a clear and descriptive title** for the issue to identify the suggestion.
* **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
* **Provide specific examples to demonstrate the steps**. Include copy/pasteable snippets which you use in those examples.
* **Describe the current behavior** and **explain which behavior you expected to see instead** and why.
* **Include screenshots and animated GIFs** which help you demonstrate the steps or point out the part of SnapGuard which the suggestion is related to.
* **Explain why this enhancement would be useful** to most SnapGuard users.
* **List some other applications where this enhancement exists.**
* **Specify which version of SnapGuard you're using.**
* **Specify the name and version of your OS.**

### Pull Requests

The process described here has several goals:
* Maintain SnapGuard's quality
* Fix problems that are important to users
* Engage the community in working toward the best possible tool
* Enable a sustainable system for maintainers to review contributions

Please follow these steps to have your contribution considered by the maintainers:

1. Follow all instructions in the [pull request template](link-to-pr-template)
2. Follow the [styleguides](#styleguides)
3. After you submit your pull request, verify that all status checks are passing
4. Request a review from one of the maintainers

While the prerequisites above must be satisfied prior to having your pull request reviewed, the reviewer(s) may ask you to complete additional work, tests, or other changes before your pull request can be ultimately accepted.

## Styleguides

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line
* Consider starting the commit message with an applicable emoji:
    * 🎨 `:art:` when improving the format/structure of the code
    * 🐎 `:racehorse:` when improving performance
    * 📝 `:memo:` when writing docs
    * 🐛 `:bug:` when fixing a bug
    * 🔥 `:fire:` when removing code or files
    * 💚 `:green_heart:` when fixing CI builds
    * ✅ `:white_check_mark:` when adding tests
    * 🔒 `:lock:` when dealing with security
    * ⬆️ `:arrow_up:` when upgrading dependencies
    * ⬇️ `:arrow_down:` when downgrading dependencies

### Python Styleguide

All Python code should adhere to [PEP 8](https://www.python.org/dev/peps/pep-0008/).

Additionally:
* Use 4 spaces for indentation
* Use double quotes for strings that contain single quotes
* Use single quotes for strings that contain double quotes
* Prefer string interpolation over concatenation
* Always use parentheses for multi-line imports
* Include docstrings for all classes and functions
* Avoid mutable default arguments
* Keep line length to 100 characters or less

### Documentation Styleguide

* Use [Markdown](https://daringfireball.net/projects/markdown) for documentation.
* Reference methods and classes in markdown with the custom `{@link Class#method}` syntax.
* Place an empty line between paragraphs.
* Use sentence case for titles and headings.

## Additional Notes

### Issue and Pull Request Labels

This section lists the labels we use to help us track and manage issues and pull requests.

* `bug` - Issues for bugs in the code
* `enhancement` - Issues for new features or improvements
* `documentation` - Issues related to documentation
* `good first issue` - Good issues for newcomers
* `help wanted` - Issues that need assistance
* `duplicate` - Issues that have been reported before
* `wontfix` - Issues that will not be fixed
* `invalid` - Issues that are not relevant or cannot be reproduced

## Thank You!

Your contributions to open source, large or small, make great projects like this possible. Thank you for taking the time to contribute.
