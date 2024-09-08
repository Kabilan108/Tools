# Changelog

## v0.2.2 (2022.09.16)

### Fix

- `plot.distplot` - Fixed bug noticed in hci-dashboard
- `preprocess.clean_data` - Fixed typo


## v0.2.1 (2022.09.15)

### Fix

- Update package version in setup.cfg


## v0.2.0 (2022.09.15)

### Structure

### Fix

- Removed dependency on sklearn for the `plot` module.
- Fixed weird behavior of `plot.heatmap` when `clust_rows=True`

### Feature

- Added `scripts/` directory with `deploy.sh` script for building
  package wheels and documentation (Developer feature)
- Added built-in datasets accessible via `hcitools.datasets`
- Splt `hcitools.process` module into `hcitools.preprocess` and
  `hcitools.analysis`

### Documentation

- Created package documentation using `pdoc`
- Hosted documentation via github pages
- Added examples in Jupyter notebooks


## v0.1.0 (2022.09.08)

- First release of `hcitools`
