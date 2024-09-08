function [fastqfile]=bmes_fastqdump(srrid,onlygetname)
% Download an SRR file by its id from SRA (NCBI Sequence Archieve)
%{
Example Usage:
==============
>> bmes_fastqdump('SRR8482616');
%}
%by Ahmet Sacan

if ~exist('srrid','var')
	warning(sprintf('No SRR ID input given.\n   Using example SRR ID SRR8482616 for demonstration purposes only.\n'));
	srrid='SRR8482616';
end

%% Set up DATADIR AND fasqtfile
% Since genome files and fastq files can be very large, you need to keep it
% in a different folder than your source files. (So that when you submit
% your work, I don't end up with many copies of these large data files).
% If you want to use a different folder, set it here.
DATADIR=[bmes.datadir '/srr'];
if ~bmes.isfolder(DATADIR); mkdir(DATADIR); end

%fastq-dump produces a fastq.gz file, fasterq-dump produces a .fastq file.
%fastqfile=[DATADIR '/' srrid '.fastq.gz'];
fastqfile=[DATADIR '/' srrid '.fastq'];
if exist('onlygetname','var')&&onlygetname; return; end
if bmes.isfileandnotempty(fastqfile); return; end

%% Set up featurecounts path.
% if you already have a fastqdump installed on your computer, you can use its
% path instead.
FASTQDUMPEXE = bmes_getfastqdumpexe();


%% Sanity checks in case the above steps failed.
if ~bmes.isfolder(DATADIR); error(sprintf('DATADIR folder [%s] does not exist.', DATADIR)); end
if ~bmes.isfileandnotempty(FASTQDUMPEXE); error(sprintf('Fastqdump program [%s] does not exist.', FASTQDUMPEXE)); end




%%
fprintf('--- NOTICE: Please wait. Downloading SRR: %s...\n', srrid);
cdold=pwd; % need to chdir into fastqdump folder. otherwise it complains (at least when Ahmet tried)
cd(fileparts(FASTQDUMPEXE));
%fastq-dump produces a fastq.gz file, fasterq-dump produces a .fastq file.
%system(['fast-dump --outdir "' DATADIR '" --gzip --split-3 ' srrid ])
system(['fasterq-dump -O "' DATADIR '" ' srrid ])
cd(cdold);

if ~bmes.isfileandnotempty(fastqfile);
	error(sprintf('fastq-dump failed to produce the expected file [%s]',fastqfile));
end
