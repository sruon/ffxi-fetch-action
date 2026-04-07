# ffxi-fetch-action

GitHub Action to download FFXI DAT files from R2. Resolves file patterns against a version manifest, caches across runs.

## Usage

```yaml
- uses: sruon/ffxi-fetch-action@v1
  id: ffxi
  with:
    files: |
      ROM/306/61.DAT
      ROM/306/62.DAT
    output-dir: dat
  env:
    BUCKET_KEY_ID: ${{ secrets.BUCKET_KEY_ID }}
    BUCKET_APP_KEY: ${{ secrets.BUCKET_APP_KEY }}

- run: echo "FFXI version: ${{ steps.ffxi.outputs.version }}"
```

## File list from a file

```yaml
- uses: sruon/ffxi-fetch-action@v1
  with:
    files-from: .ffxi-files
  env:
    BUCKET_KEY_ID: ${{ secrets.BUCKET_KEY_ID }}
    BUCKET_APP_KEY: ${{ secrets.BUCKET_APP_KEY }}
```

`.ffxi-files`:
```
# Zone geometry
ROM/306/61.DAT
ROM/306/62.DAT

# All NPC data
ROM/119/*

ROM/0/69.DAT
```

## Globs

| Pattern | Matches |
|---|---|
| `ROM/306/61.DAT` | Exact file |
| `ROM/306/*` | Everything in ROM/306/ |
| `ROM/*/0.DAT` | 0.DAT in every ROM subdirectory |

## Pinning a version

```yaml
- uses: sruon/ffxi-fetch-action@v1
  with:
    version: "30260304_1"
    files: ROM/306/61.DAT
  env:
    BUCKET_KEY_ID: ${{ secrets.BUCKET_KEY_ID }}
    BUCKET_APP_KEY: ${{ secrets.BUCKET_APP_KEY }}
```

## Inputs

| Input | Description | Default |
|---|---|---|
| `files` | File paths, one per line. Globs work. | |
| `files-from` | Path to a file with paths (`#` comments ok). | |
| `output-dir` | Where to write files | `dat` |
| `version` | FFXI version to fetch | `latest` |
| `cache` | Cache files across runs | `true` |

## Outputs

| Output | Description |
|---|---|
| `version` | FFXI version fetched |
| `files-count` | Files resolved |

## Auth

Set `BUCKET_KEY_ID` and `BUCKET_APP_KEY` as env vars. Read-only key recommended.

## Caching

Handled internally via `actions/cache`. Cache key = FFXI version + file list hash. Busts when either changes.
