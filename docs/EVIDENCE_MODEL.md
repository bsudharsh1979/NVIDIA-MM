# Evidence model

Implemented types: `COURSE_SOURCE`, `EXPECTED_RESULT`, `SIMULATED_RESULT`, `ACTUAL_RUN`, `TUTOR_INTERPRETATION`, `EXTERNAL_RESEARCH`.

Rules:

- TwinStateEngine always emits `SIMULATED_RESULT`.
- Notebook stored outputs in this clone are mostly absent → do not label blank outputs as `ACTUAL_RUN`.
- Assessment loss/accuracy gates from 05 are `EXPECTED_RESULT` until a learner imports a real log.
- Experiment importer stores raw JSON/CSV/logs unchanged.
