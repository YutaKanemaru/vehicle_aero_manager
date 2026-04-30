---
mode: "agent"
description: "Commit and push recent implementation changes with conventional commit messages"
---

最近の実装内容を Conventional Commits 形式で論理的なまとまりに分割してコミットし、push してください。

## 手順

1. **変更内容の把握**
   ```
   git status
   git diff --stat
   ```

2. **変更を論理的なまとまりに分類**
   各ファイルを以下のタイプに分類する:
   | Type | 対象 |
   |---|---|
   | `feat` | 新機能・新エンドポイント・新コンポーネント |
   | `fix` | バグ修正 |
   | `refactor` | 動作変更なしのコード整理 |
   | `docs` | `docs/specs/`・`.github/`・`CLAUDE.md`・README |
   | `chore` | `pyproject.toml`・`package.json`・Docker設定・マイグレーション |
   | `test` | `tests/`・`backend/scripts/test_*.py` |

3. **コミット実行**
   まとまりごとに順番に実行:
   ```
   git add <files>
   git commit -m "<type>(<scope>): <message>"
   ```
   スコープ例: `viewer`, `ride-height`, `templates`, `geometry`, `case-run`, `auth`, `api`, `docs`

4. **プッシュ**
   ```
   git push
   ```

5. **確認**
   ```
   git log --oneline -5
   ```

## ルール

- **1コミット = 1論理変更** — 関係のないファイルを同じコミットに混ぜない
- **コミットメッセージは英語**
- **空コミット禁止** — `git status` で変更がないファイルは `add` しない
- **`git add .` は使わない** — ファイルを明示的に指定する
- **スコープは省略可** — 変更範囲が広い場合は `(<scope>)` を省略してよい
- **コードを変更しない** — コミットするのみ

## 例

```
feat(ride-height): add --unit flag to test_ride_height.py
docs(specs): update geometry-spec with test scripts section
chore: add .github/prompts/ and CLAUDE.md
```
