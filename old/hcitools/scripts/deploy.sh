#!/usr/bin/bash

# Only continue if in the top-level directory
if grep -q [\/\\]hci-tools$ <<< $PWD; then
    :
else
    echo "Please run this script from the top-level of hci-tools/"
    exit 1
fi

# Use conda environment
eval "$(conda shell.bash hook)"
conda activate hcitools

# Remove old files
rm docs/*.md docs/assets/* dist/*

# Rebuild package and distribution wheels
python -m pip install --upgrade build
python -m build

# Install the most recent build
python -m pip install -e .

# Remove egg files
rm -r hcitools.egg-info

for nb in docs/examples/*.ipynb; do
    # Convert notebook
    jupyter nbconvert $nb  \
        --to markdown  \
        --output-dir=docs  \
        --execute \
        --NbConvertApp.output_files_dir=assets

    for fig in docs/examples/iframe_figures/*.html; do
        # Extract names
        nb_name=$(grep -P '(?<=\/)\w+(?=.ipynb)' -o <<< $nb)
        fig_name=$(grep -P 'figure_\d+\.html' -o <<< $fig)

        # Define old and new paths
        old_path="$(grep -P '(?<=docs\/examples\/).*' -o <<< $fig)"
        new_path="assets/${nb_name}_${fig_name}"

        # Move figure
        mv $fig "docs/$new_path"

        # Escape characters in paths
        old_path=$(sed 's_/_\\/_g' <<< $old_path)
        new_path=$(sed 's_/_\\/_g' <<< $new_path)

        # Replace paths in markdown file
        sed -i "s/$old_path/$new_path/g" "docs/${nb_name}.md"
    done

    # Delete empty figure directory
    rm -r docs/examples/iframe_figures
done

# Rebuild documentation
pdoc ./hcitools/ -o ./docs/ --docformat numpy --math --logo logo.png
