# Data Correction Workflow

This folder is used to manually correct extracted/cleaned FTA records before evaluation.

## Structure

- inputs/: raw input files to be corrected
- rules/: correction rules
- outputs/: corrected outputs
- reports/: correction reports
- apply_data_corrections.py: correction script

## Rule file

Start from:
- rules/correction_rules.template.json

Main keys:
- drop_fault_codes: remove records by fault code
- merge_fault_codes: remap old code to new code
- global_replacements: exact-match replacements for fields
- regex_replacements: regex-based cleanup for description/causes/parameters
- global_drop: regex-based global drop rules for causes/parameters
- record_overrides: per-code overrides

Per-code override supports:
- component
- description
- remove_causes
- add_causes
- set_causes
- remove_parameters
- add_parameters
- set_parameters

## Usage

Example:

python evaluation/data_correction/apply_data_corrections.py \
  --input outputs/kb_cleaned.json \
  --rules evaluation/data_correction/rules/correction_rules.template.json \
  --output evaluation/data_correction/outputs/kb_corrected.json \
  --report evaluation/data_correction/reports/kb_corrected.report.json

## Notes

- Input can be either a list of records or a payload with a records field.
- Output keeps original payload fields and updates records + record_count.
- correction.stats in output records how many items were dropped/merged.
