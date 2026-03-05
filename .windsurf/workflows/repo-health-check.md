---
description: Quality Gate
---

# Repo Health Check

```bash
python3 ~/github/platform/tools/repo_health_check.py --profile python-package --path .
```

- [ ] name, version, description, readme, authors in pyproject.toml
- [ ] test.yml + publish.yml mit `needs: test`
