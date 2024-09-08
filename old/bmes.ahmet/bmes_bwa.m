function [samfile,sams]=bmes_bwa(fastqfile, genomefastafile)
% fastqfile and genomefastafile can be URLs or local files. We'll download
% here if URL is given.
% If no inputs are given, we run it for an example fastq file described in
% the example usage below.
%{
Example Usage:
==============
In this example, I will align a fastq file of short reads that were
produced in an experiment with the bacterium Rhodopseudomonas palustris.

In your own study, you would need to obtain/download your own fastq. Some
public repositories (e.g., NCBI) have specific tools used for downloading
fastq files.

I will use a small fastq file that I created as a subsample of a real
publicly available data.

>> fastqfile = 'http://sacan.biomed.drexel.edu/lib/exe/fetch.php?rev=&media=course:binf:nextgen:bwademo:example.small.fastq';


You would need to do a little online search to find the genome file of an
organism you want to map the fastq reads to. NCBI is a good place to get
the genome fasta sequence files.
With a google search, I was able to find the genome of the bacterium
Rhodopseudomonas palustris at https://www.ncbi.nlm.nih.gov/nuccore/NC_005296.1
I downloaded the genome into a fasta file using my browser and then went
back to my browser download list to extract the following URL.

>> genomefastafile = 'https://www.ncbi.nlm.nih.gov/sviewer/viewer.cgi?tool=portal&save=file&log$=seqview&db=nuccore&report=fasta&id=39933080&conwithfeat=on';

With the files and urls properly set, now I am ready to map the fastq file to the genome file.


>> [samfile, sams] = bmes_bwa( fastqfile, genomefastafile )

The sams structure array will contain the mapping information for each of
reads that were in the fastq file.
%}
%by Ahmet Sacan

if ~exist('fastqfile','var')
	warning(sprintf('No fastqfile and genomefastafile input given.\n   Using example files for demonstration purposes only.\n   You must provide your own inputs for the problem you are investivating.'));
	fastqfile = 'http://sacan.biomed.drexel.edu/lib/exe/fetch.php?rev=&media=course:binf:nextgen:bwademo:example.small.fastq';
	genomefastafile = 'https://www.ncbi.nlm.nih.gov/sviewer/viewer.cgi?tool=portal&save=file&log$=seqview&db=nuccore&report=fasta&id=39933080&conwithfeat=on';
end


%% Set up DATADIR
% Since genome files and fastq files can be very large, you need to keep it
% in a different folder than your source files. (So that when you submit
% your work, I don't end up with many copies of these large data files).
% If you want to use a different folder, set it here.
DATADIR=[bmes.datadir '/bwafiles'];
if ~bmes.isfolder(DATADIR); mkdir(DATADIR); end


%% Set up BWA path.
% if you already have a bwa installed on your computer, you can use its
% path instead.
BWAEXE = [DATADIR '/bwa.exe'];

%% Download bwa if not already there
if ~bmes.isfileandnotempty(BWAEXE)
	if ispc
		zipfile=bmes.downloadurl('http://sacan.biomed.drexel.edu/ftp/prg/bwa.cyg.w64.zip',[DATADIR '/bwa.cyg.w64.zip']);
		fs=unzip(zipfile,DATADIR);
		movefile([DATADIR '/bwa.cyg.w64.exe'], BWAEXE);
	else
		BWAEXE=bmes.downloadurl('http://sacan.biomed.drexel.edu/ftp/prg/bwa.maci64.exe',BWAEXE);
		system(['chmod ugo+rwx "' BWAEXE '"']);
	end
end

%% Sanity checks in case the above steps failed.
if ~bmes.isfolder(DATADIR); error(sprintf('DATADIR folder [%s] does not exist.', DATADIR)); end
if ~bmes.isfileandnotempty(BWAEXE); error(sprintf('BWA program [%s] does not exist.', BWAEXE)); end

fastqfile = bmes.downloadurl(fastqfile);


%% Index the reference genome.
% Indexing can be a time-consuming step that should be done only once. We'll
% use the presence of *.bwt file to decide whether we have indexed it
% before.
if ~bmes.isfileandnotempty([genomefastafile '.bwt'])
	genomefastafile = bmes.downloadurl(genomefastafile);
end
if ~bmes.isfileandnotempty([genomefastafile '.bwt'])
	system([BWAEXE ' index "' genomefastafile '"' ]);
end

%% Align sequence reads to the reference genome
% It's also a good idea to check if we have performed this step before.
% Let's use *.sam for the resulting filename and use presence of this
% file to determine whether we have done this alignment step before.
% Note that if you change the genomefile or fastqfile and the samfile was
% previously created with a different genomefile and/or fastqfile, the
% results would no longer be correct.
samfile=[fastqfile '.sam'];
if ~bmes.isfileandnotempty(samfile)
	% using 4 threads. assuming most computer will have at least 4 threads
	% available.
	system([BWAEXE ' mem -t ' bmes.numcputhreads ' "' genomefastafile '"' ' "' fastqfile '" > "' samfile '"']);
end

% if sams is not requested as an output, return here.
if nargout<2; return; end


%% Read the alignment results using samread().
% samread() is available in Matlab's bioinformatics toolbox. If you donot
% have samread() or are not working in Matlab, google for other options.
% SAM files are text files. Google SAM format specification to explore what
% types of data is being provided. e.g., see:
% https://samtools.github.io/hts-specs/SAMv1.pdf
sams = samread(samfile);
