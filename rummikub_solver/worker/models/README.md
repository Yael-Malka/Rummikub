# Model Weights

ML weights used by the worker inference pipeline.

Expected files:

- `worker/models/stage1/best.pt`
- `worker/models/stage2/best.pt`
- `worker/models/stage2/metadata.json`

Keep large `.pt` files out of Git. Copy them into the stage folders locally before running inference.