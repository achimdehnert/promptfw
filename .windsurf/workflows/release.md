---
description: Publish iil-promptfw to PyPI
---

# Release — PyPI Publish

## Build + Publish

```bash
bash ~/github/platform/scripts/publish-package.sh ~/github/promptfw
```

## Test-Upload

```bash
bash ~/github/platform/scripts/publish-package.sh ~/github/promptfw --test
```

## Verify

```bash
pip index versions iil-promptfw 2>/dev/null | head -3
```
