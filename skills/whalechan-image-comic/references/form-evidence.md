# Proportion evidence — H1

Use within the assigned candidate review for QA9, QA10 and QA11. The frozen proportion_check determines measured versus visible-only evidence. Measurement remains part of that review.

## Measured

Run scripts/measure-form.py on the original candidate using its frozen target and acceptance range. Mark skull top excluding hair/headwear, chin, pelvis, knee and sole along the anatomical centerline. Inspect the overlay and correct misplaced landmarks. Report the actual calculated ratio and candidate/target/overlay hashes.

This example illustrates the measured object; coordinates, hashes and ratios come from the actual candidate:

```json
{
  "candidate_sha256": "64 lowercase hexadecimal characters",
  "measurement_method": "pose-neutralized-skeleton",
  "target_source": "custom",
  "target_sha256": "64 lowercase hexadecimal characters",
  "mean_head_ratio": 5.0,
  "acceptance_range": [4.85, 5.15],
  "head_axis": {"top": [500, 100], "chin": [500, 260]},
  "body_segments": [
    {"name": "chin_to_pelvis", "start": [500, 260], "end": [500, 500]},
    {"name": "pelvis_to_knee", "start": [500, 500], "end": [500, 690]},
    {"name": "knee_to_sole", "start": [500, 690], "end": [500, 900]}
  ],
  "calculated_head_ratio": 5.0,
  "measurement_overlay": "/absolute/path/measurement.png",
  "measurement_overlay_sha256": "64 lowercase hexadecimal characters"
}
```

QA9/10 stores this object at evidence.form_evidence; QA11 stores it at form_evidence. The measured object includes candidate_sha256 in every version. QA11 fills an omitted top-level report candidate_sha256; its nested measured evidence still requires the actual candidate hash. The target hash binds the frozen proportion. The overlay path and hash identify the inspected measurement artifact.

## Visible-only

For a planned close-up or partial-body view, provide form_evidence with mode: visible-only, a specific reason and nonempty observed_cues. QA9/10 sets gates.H1 to NA and includes candidate_sha256 in this object. QA11 lists H1 in checked and binds the candidate through the top-level report hash; its compact format has no per-gate verdict map. Describe the visible proportions and report the measurement limitation at delivery. A shot planned as measurable requires measured evidence.

## Version-specific verdicts

Use [review-workflow.md](review-workflow.md) for QA11 core/minor findings and [qa-rubric.md](qa-rubric.md) for frozen QA9/10 strict verdicts. This reference defines measurement evidence only.
