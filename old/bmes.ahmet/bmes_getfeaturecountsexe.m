function [featurecountsexe]=bmes_getfeaturecountsexe()
% Returns the path to the featureCounts executable.
%
% featureCounts is available within the Subread software. You can download
% and compile the software for yourself. This function is provided for
% your convenience. It will download a precompiled version of
% featureCounts.
%by Ahmet Sacan

DATADIR = bmes.datadir;
if ispc; featurecountsexe = [DATADIR '/featurecounts.w64.exe'];
else featurecountsexe = [DATADIR '/featurecounts.maci64.exe']; end

%% Download featurecounts if not already there
if ~bmes.isfileandnotempty(featurecountsexe)
	if ispc
		%		zipfile=bmes.downloadurl('http://sacan.biomed.drexel.edu/ftp/prg/featurecounts.cyg.w64.zip',[DATADIR '/bwa.featurecounts.w64.zip']);
		%		fs=unzip(zipfile,DATADIR);
		%		movefile([DATADIR '/featureCounts.exe'], featurecountsexe);
		featurecountsexe=bmes.downloadurl('http://sacan.biomed.drexel.edu/ftp/prg/featurecounts.w64.exe',featurecountsexe);
	else
		featurecountsexe=bmes.downloadurl('http://sacan.biomed.drexel.edu/ftp/prg/featurecounts.maci64.exe',featurecountsexe);
		system(['chmod ugo+rwx "' featurecountsexe '"']);
	end
end


%handle download error:
f=fopen(featurecountsexe,'r');
baddownload=strcmp(fread(f,1,'*char'),'<');
fclose(f);
if baddownload
	delete(featurecountsexe);
	error('Download failed. File may not be available on server.');
end
