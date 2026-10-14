# Lab 5: Static Code Analysis — Issues Report

| Issue | Type | Line(s) | Description | Fix Approach |
|---|---|---|---|---|
| Hardcoded supervisor password | Security | 10 | Password is stored directly in the source code. | Read the password from an environment variable. |
| Unsafe `eval()` calls | Security | 62, 80 | Expressions are executed as Python code and may allow unintended operations. | Replace `eval()` with restricted arithmetic evaluation and use `print()` for the final message. |
| Bare exception handling | Reliability | 23–24 | Errors are silently ignored, hiding the cause of failures. | Validate inputs and handle expected exceptions explicitly. |
| Weak MD5 checksum | Security | 31 | Bandit flags MD5 as a weak hashing algorithm. | Use SHA-256 for the fingerprint. |
| Mutable default argument | Code quality / Bug | 12 | The `history=[]` list can be shared between function calls. | Use `None` and initialize a new list inside the function. |
| Unused variable | Code quality | 54 | `total_units` is calculated but never used. | Remove the unused calculation or use it in the report. |
| Unused imports | Code quality | 2, 4 | `logging` and `os` were unused in the original version. | Remove unused imports or use them appropriately. |
| Non-standard function names | Style | Multiple | Functions use camelCase instead of Python's snake_case convention. | Rename functions and update all callers. |
| Manual file handling | Resource management | 34–35, 40–41, 63–64 | Files are opened and closed manually. | Use `with open(...)` context managers. |
| Formatting violations | Style | Multiple | Missing blank lines, long lines and trailing whitespace violate style rules. | Apply Flake8 formatting corrections. |
