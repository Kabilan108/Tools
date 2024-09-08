function [fastqdumpexe]=bmes_getfastqdumpexe()
% Returns the path to the fastqdump executable.
%
% fastqdump is available within the sra-toolkit software. You can download
% the software for yourself. This function is provided for your
% convenience. It will download a precompiled version of sra-toolkit.
%by Ahmet Sacan

DATADIR = bmes.datadir;
sratoolkitdir=[DATADIR '/sratoolkit'];
if ispc; fastqdumpexe = [sratoolkitdir '/bin/fastq-dump.exe'];
else fastqdumpexe = [sratoolkitdir '/bin/fastq-dump']; end

%% Download featurecounts if not already there
if ~bmes.isfileandnotempty(fastqdumpexe)
	if ispc
		zipfile=bmes.downloadurl('http://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/current/sratoolkit.current-win64.zip',[DATADIR '/sratoolkit.current-win64.zip']);
		fs=unzip(zipfile,DATADIR);
	elseif ismac
		gzfile=bmes.downloadurl('http://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/current/sratoolkit.current-mac64.tar.gz',[DATADIR '/sratoolkit.current-mac64.tar.gz']);
		fs=gunzip(gzfile,DATADIR);
		fs=untar(fs{1},DATADIR);
		%system(['chmod ugo+rwx "' fastqdumpexe '"']);
	else
		error('Unsupported system');
	end
	bmes.mkdirif(sratoolkitdir);
	movefile([fs{1} '/*'],sratoolkitdir); %assuming the first entry is the top folder name

	system([sratoolkitdir '/bin/vdb-config']);
end
