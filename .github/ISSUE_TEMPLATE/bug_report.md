name: Bug report
about: Create a ticket to report a software bug
title: ''
labels: '["Triage", "T: Bug"]'
assignees:
  - evilaliv3

body:
- type: textarea
    id: bug-description
    attributes:
      label: Describe the bug
      description: Please provide a clear and concise description of what the bug is.
    validations:
      required: true

- type: textarea
    id: bug-reproducibility
    attributes:
      label: Describe how to reproduce the bug
      description: Please provide instructions on how to reproduce the bug.
    validations:
      required: true

- type: textarea
    id: bug-context
    attributes:
      label: Additional context
      description: Please attach information about the context and possibly some screenshot to explain the prolem.
    validations:
      required: true
