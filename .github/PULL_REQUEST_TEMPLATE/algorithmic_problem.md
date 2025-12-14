---
name: Algorithmic Problem Contribution
about: Add a new algorithmic problem to Frontier-CS
title: '[Algorithmic] Add Problem {id}'
labels: algorithmic-problem
---

## Problem Overview

**Problem ID**:
**Category**: <!-- optimization / construction / interactive -->
**Difficulty**: <!-- easy / medium / hard -->

### Description
<!-- Brief description of the problem -->


## Checklist

### Required Files
- [ ] `statement.txt` - Problem description
- [ ] `config.yaml` - Time/memory limits, test count
- [ ] `testdata/` - At least one public test case (1.in, 1.ans)
- [ ] `chk.cc` or `interactor.cc` - Checker or interactor

### Problem Structure
```
algorithmic/problems/{id}/
├── statement.txt
├── config.yaml
├── testdata/
│   ├── 1.in
│   └── 1.ans
└── chk.cc (or interactor.cc)
```

### Testing
- [ ] Verified checker/interactor compiles
- [ ] Tested with sample solution
- [ ] Problem registered and accessible via judge API

## Additional Notes
<!-- Any additional context or special requirements -->

