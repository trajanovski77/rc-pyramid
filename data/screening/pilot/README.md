# Pilot

Pre-registered pilot under `docs/protocol.md` §7, coded 2026-09-05. Both criteria met.

| File | Contents |
|---|---|
| `pilot_sample.json` | The draw: seed 20260907, n = 40, stratified for physical substrate |
| `pilot_coderA.packet-blank.csv` | Coder A worklist as issued |
| `pilot_coderB.packet-blank.csv` | Coder B worklist as issued, same records, different order |
| `pilot_coderA.csv` | Coder A, final |
| `pilot_coderA.as-submitted.csv` | Coder A as first submitted, before one §0.5 re-code |
| `pilot_coderB.csv` | Coder B, final |
| `pilot_agreement.json` | All statistics |
| `pilot_disagreements.csv` | The one family disagreement, reconciled |

## Result

```
Cohen's kappa (family)      0.9542    criterion >= 0.70    met
raw agreement               97.5%     39/40
Gwet's AC1                  0.9719
Krippendorff's alpha        0.9548
subclass                    20/20
unassignable, eligible      3.2% / 3.2%   criterion <= 5%   met
unassignable, all records   22.5% / 25.0%
```

Reproduce:

```
python3 scripts/screen.py pilot-kappa --a data/screening/pilot/pilot_coderA.csv \
                                      --b data/screening/pilot/pilot_coderB.csv
```

It writes `pilot_disagreements.new.csv` rather than overwriting the reconciled file.

## Two caveats

No record was assigned F3 or F4 by either coder, so the kappa covers F1, F2 and
unassignable only. The other two families have no inter-rater evidence.

Coders are identified as Coder A and Coder B and are not named. The same labels denote the
same two people in `../dryrun/pilot/`, the 2026-08-28 preliminary check.

Re-codes are logged in `docs/deviations.md` under `codebook.md` §0.5.
