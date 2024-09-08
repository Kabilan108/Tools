function [genecountfile,genetable]=bmes_featurecounts(samfile, genomeannotfile,genefield,genecountfile)
% samfile and gtffile can be URLs or local files. We'll download
% here if URL is given.
% genefield represents what information you want to extract from the
% genomeannotfile. Annotation files you download from NCBI would have a
% 'gene' field. Those from other sources may have 'gene_id' field. If you
% get a warning from featurecounts program that it cannot find a gene
% identifier attribute, the genefield variable you are trying to extract
% does not exist in the GTF file. featurecounts warning will also list
% potential attributes you can choose from, such as locus_tag or ID. You
% can also use Dbxref attribute, but would need to extract relevant gene id
% or symbol from that once you get the output from this function.
% If genecountfile argument is given, we use it. Otherwise a
% genecountfile name automatically determined.
%{
Example Usage:
==============
In this example, I will use featureCounts.exe program to identify and count
the genes that the sam reads are located at.

We'll just call bmes_bwa with no inputs to get a sample sam file for
demonstration purposes.

>> samfile = bmes_bwa();


You would need to do a little online search to find the genome annotation file of an
organism you want to annotate the sam entries with. NCBI is a good place to get
the genome annotation files.
With a google search, I was able to find the genome information for the
bacterium Rhodopseudomonas palustris at:
https://www.ncbi.nlm.nih.gov/genome/?term=Rhodopseudomonas%20palustris[Organism]&cmd=DetailsSearch
I downloaded the genome annotation in GFF format using my browser and then went
back to my browser download list to extract the following URL.

>> genomeannotfile = 'ftp://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/195/775/GCF_000195775.1_ASM19577v1/GCF_000195775.1_ASM19577v1_genomic.gff.gz';

With the files and urls properly set, now I am ready to map the fastq file to the genome file.


>> [genecountfile,genetable] = bmes_featurecounts( samfile, genomeannotfile )

%}
%by Ahmet Sacan

if ~exist('samfile','var')
	warning(sprintf('No samfile and genomeannotfile input given.\n   Using example files for demonstration purposes only.\n   You must provide your own inputs for the problem you are investivating.'));
	samfile = bmes_bwa();
	genomeannotfile = 'ftp://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/195/775/GCF_000195775.1_ASM19577v1/GCF_000195775.1_ASM19577v1_genomic.gff.gz';
end

if ~exist('genefield','var')||isempty(genefield); genefield='product'; end


samfile = bmes.downloadurl(samfile);
if ~exist('genecountfile','var')||isempty(genecountfile)
	genecountfile=[samfile '.' genefield '.genecount'];
end

if ~bmes.isfileandnotempty(genecountfile)
	%% Set up DATADIR
	% Since genome files and fastq files can be very large, you need to keep it
	% in a different folder than your source files. (So that when you submit
	% your work, I don't end up with many copies of these large data files).
	% If you want to use a different folder, set it here.
	DATADIR=[bmes.datadir '/featurecounts'];
	if ~bmes.isfolder(DATADIR); mkdir(DATADIR); end


	%% Set up featurecounts path.
	% if you already have a bwa installed on your computer, you can use its
	% path instead.
	FEATCOUNTSEXE = bmes_getfeaturecountsexe();


	%% Sanity checks in case the above steps failed.
	if ~bmes.isfolder(DATADIR); error(sprintf('DATADIR folder [%s] does not exist.', DATADIR)); end
	if ~bmes.isfileandnotempty(FEATCOUNTSEXE); error(sprintf('FeatureCounts program [%s] does not exist.', FEATCOUNTSEXE)); end

	genomeannotfile = bmes.downloadurl(genomeannotfile);

	%% GenomeAnnot file may be a gz file. unzip if necessary
	if strcmp(genomeannotfile(end-2:end),'.gz')
		fs=gunzip(genomeannotfile);
		genomeannotfile=fs{1};
	end



	%% Produce the genecount file.
	if ~bmes.isfileandnotempty(genecountfile)
		cmd=['"' FEATCOUNTSEXE '" -a "' genomeannotfile '"' ' -o "' genecountfile '"  "' samfile '"' ' -O --tmpDir "' bmes.tempdir '" -T 32 -t exon -g ' genefield];
		fprintf('--- NOTICE: Running command:\n   %s\n',cmd);
		[~,s]=system(cmd);
		fprintf('%s\n',s);
		if ~isempty(strfind(s,'failed to find the gene identifier attribute'))
			warning(sprintf('featurecounts has reported that it cannot find the gene identifier [%s].\nWhen calling bmes_featurecounts(), you should select as genefield one of the identifiers that are avaiable in the GTF file.',genefield));
			tok=regexp(s,'attributes included in your \w+ annotation (?:is|are) ''([^'']+)','tokens','once');
			if ~isempty(tok)
				attribs=regexp(tok{1},'(\w+)=','tokens');
				attribs=[attribs{:}];
				if ~isempty(attribs)
					warning(sprintf('Valid gene identifiers available in the GTF file are:\n   %s.\n   Use one of these identifiers as the genefield argument when calling bmes_featurecounts().',strjoin(attribs, ', ')));
				end
			end
			delete(genecountfile);
			error('featurecounts produced an output file, but I removed it, because it is not a useful one, since you did not provide a correct gene identifier to be reported. Carefully read the messages above to fix any issues.');
		end
		if ~bmes.isfileandnotempty(genecountfile)
			error('featurecounts failed to produced an output file. Carefully read the messages above to fix any issues.');
		end
	end
end



if nargout>1
	%% Read the genecount results.
	genetable = readtable(genecountfile, 'HeaderLines',1,'FileType','text');
end
