# `hcitools`

The `hcitools` package provides tools for analyzing and visualizing data
generated in high-content imaging experiments.


# Installation

```bash
# Clone repository
git clone -b prod git@mygithub.gsk.com:to561778/hci-tools.git

# Install package
python -m pip install -e hci-tools
```


# Usage

Package documentation is available [here](https://mygithub.gsk.com/pages/to561778/hci-tools/hcitools.html).
See [docs/examples](docs/examples/) for detailed guides for generating figures
and performing various analysis steps.


# Developer Instructions

Use the script below to set up a development environment for this package.

```bash
# Clone the repository
git clone -b dev git@mygithub.gsk.com:to561778/hci-tools.git
cd hci-tools

# Create conda environment
conda env create -f environment.yml
conda activate hcitools

# Install the package
python -m pip install -e .
```

> ### Deploying Changes
> Once changes have been made, use the `scripts/deploy.sh` script to rebuild the
> package wheel and update the documentation. This will also reinstall the
> package in the active environment.
>
> **Note:** Only run `deploy.sh` from the top-level hci-tools directory.
