#!/bin/bash
s=`uname -a`; if [ "${s#CYGWIN}" == "$s" ]; then export amicygwin=no; else export amicygwin=yes; fi

function main_windows(){
	if [[ -z "$condadir" ]]; then condadir="$CONDA_PREFIX"; fi
	if [[ -z "$condadir" ]]; then
		if [[ -f "C:/ProgramData/Anaconda/python.exe" ]]; then
			condadir="C:/ProgramData/Anaconda";
		elif [[ -f "C:/ProgramData/Anaconda3/python.exe" ]]; then
			condadir="C:/ProgramData/Anaconda3";
		elif [[ -f "$USERPROFILE/Anaconda/python.exe" ]]; then
			condadir="$USERPROFILE/Anaconda/python.exe"
		elif [[ -f "$USERPROFILE/Anaconda3/python.exe" ]]; then
			condadir="$USERPROFILE/Anaconda3/python.exe"
		else
			>&2 echo "I could not locate Anaconda in the usual places. You can still use this script, but you must provide the location of the Anaconda directory (e.g., 'C:/ProgramData/Anaconda3') as the second argument to this function."
			return
		fi
	fi
	oldpath="$PATH"
	oldcondadir="$CONDA_PREFIX"
	newpath="$oldpath"
	for subdir in '' 'Library/mingw-w64' 'Library/usr/bin' 'Library/bin' 'Scripts'; do
		dir=$(cygpath "$condadir/$subdir")
		newpath="$dir:$newpath"
	done
	jupyterexe="$condadir/Scripts/jupyter.exe";
	jupyterexe=$(cygpath -m "$jupyterexe")
	#jupyterexe_=$(echo "${jupyterexe// /\\ }")  #add backslash before spaces.

	echo export PATH="$newpath"
	export PATH="$newpath"
	export CONDA_PREFIX="$condadir"

	if [[ ! -z "$notebookfile" ]]; then
		cmd="\"$jupyterexe\" notebook --NotebookApp.disable_check_xsrf=True \"$notebookfile\" &"
	else
		cmd="\"$jupyterexe\" notebook &"
	fi
	echo "---NOTICE: Running command: "; echo "$cmd";
	eval "$cmd"
	status=$?
	export PATH="$oldpath"
	export CONDA_PREFIX="$oldcondadir"
	if [[ "$status" -ne 0 ]]; then
		>&2 echo "--- NOTICE: Received an error while trying to run jupyter."
		if [[ "$condadir" == *" "* ]]; then
			>&2 echo "Having a space character in the location you installed Anaconda is sometimes a problem."
			>&2 echo  "Try removing and reinstalling Anaconda. Select 'for All Users' when installing Anaconda."
		fi
	fi
}
function main_mac(){
	echo "This script has not been tested for Mac/Linux and may not work."
	jupyterexe=$(which jupyter 2>/dev/null)
	if [[ -z "$jupyterexe" ]]; then
		jupyterexe2="$HOME/opt/anaconda3/bin/jupyter"
		if [[ -f "$jupyterexe2" ]]; then jupyterexe="$jupyterexe2";
		else >&2 echo 'Cannot locate jupyter executable location. Make sure jupyter is on your PATH'; jupyterexe='jupyter'; fi
	fi
	if [[ ! -z "$notebookfile" ]]; then
		cmd="\"$jupyterexe\" notebook --NotebookApp.disable_check_xsrf=True \"$notebookfile\" &";
	else
		cmd="\"$jupyterexe\" notebook &";
	fi
	echo "---NOTICE: Running command: "; echo "$cmd &";
	eval "$cmd"
}


function main() {
	#% notebookdir can be a folder where you want to start from or an ipynb filename you want to load or a py file (or any other file) you want to edit.
	notebookdir="$1"
	condadir="$2"

	if [[ -z "$notebookdir" ]]; then notebookdir="./"; fi
	notebookdir=$(realpath "$notebookdir")
	notebookdir="${notebookdir//\\//}";

	if [[ ! -d "$notebookdir" ]]; then
		notebookfile="$notebookdir";
		notebookdir=$(dirname "$notebookdir")
		if [[ ! -f "$notebookfile" ]]; then
			notebookfile_base=$(basename -- "$notebookfile")
			ext="${notebookfile_base##*.}"
			if [[ -z "$ext" ]]; then
				>&2 echo "No such file or folder: [$notebookfile]"
				return;
			fi
			touch "$notebookfile";
			if [[ "$ext" == "ipynb" ]]; then
				echo '{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 4}' >> "$notebookfile";
			fi
		fi
		notebookfile=$(basename -- "$notebookfile")
	fi

	oldpwd=$(pwd);
	cd "$notebookdir";
	if [[ "$amicygwin" == "yes" ]]; then
		main_windows "$@"
	else
		main_mac "$@"
	fi
	cd "$oldpwd"


}
main "$@"
