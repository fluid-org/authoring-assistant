#!/bin/bash

OUTPUT_FILE="artifact-authoring-assistant.zip"
rm -f "$OUTPUT_FILE"
EXCLUDES=("node_modules" ".git" ".github" "dist" ".idea" ".venv-chart" "logs" "obsolete" "paper" "target" "tex-common" ".gitignore"
 ".gitattributes" "authoringAssistant.iml" "yarn.lock" "package.lock" ".gitmodules" "README.md")

EXCLUDE_PATTERNS=()
for p in "${EXCLUDES[@]}"; do
  EXCLUDE_PATTERNS+=("-x" "$p" "-x" "$p/*" "-x" "./$p" "-x" "./$p/*")
done
EXCLUDE_PATTERNS+=("-x" "$OUTPUT_FILE" "-x" "./$OUTPUT_FILE")

zip -r -q "$OUTPUT_FILE" . "${EXCLUDE_PATTERNS[@]}"
echo "Artifact generated $OUTPUT_FILE"
