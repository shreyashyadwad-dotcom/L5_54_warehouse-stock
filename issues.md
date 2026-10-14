\# Lab 5: Static Code Analysis — Issues Report



| Issue | Type | Line(s) | Description | Fix Approach |

|---|---|---|---|---|

| Hardcoded supervisor password | Security | 10 | Password is stored directly in source code. | Read the password from an environment variable. |

| Unsafe `eval()` calls | Security | 62, 80 | Expressions are executed as Python code. | Use restricted arithmetic evaluation and replace the final call with `print()`. |

| Bare exception handling | Reliability | 23–24 | Errors are silently ignored. | Validate inputs and handle expected errors explicitly. |

| Weak MD5 checksum | Security | 31 | Bandit flags MD5 as a weak hash. | Use SHA-256 for the fingerprint. |

| Mutable default argument | Bug | 12 | The `history=\[]` list can be shared across calls. | Use `None` and initialize a new list inside the function. |

| Unused variable | Code quality | 54 | `total\_units` is calculated but never used. | Remove the unused calculation. |

| Unused imports | Code quality | 2, 4 | `logging` and `os` are imported but unused. | Remove unused imports or use them appropriately. |

| Non-standard function names | Style | Multiple | Functions use camelCase rather than snake\_case. | Rename functions and update their callers. |

| Manual file handling | Resource management | 34–35, 40–41, 63–64 | Files are opened and closed manually. | Use `with open(...)` context managers. |

| Formatting violations | Style | Multiple | Missing blank lines, long lines and trailing whitespace. | Apply Flake8 formatting corrections. |



