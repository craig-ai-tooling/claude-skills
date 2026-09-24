# Guide

## Step 1 — Do the thing

```yaml
kind: Example
metadata:
  name: poctest-example
```

## Step 2 — Verify

```bash
echo done
```

Back to [home](index.md).

Registration token placeholders stay clean:

```yaml
stylus:
  site:
    edgeHostToken: <registration-token>
```

```bash
export TOKEN="$REGISTRATION_TOKEN"
```
